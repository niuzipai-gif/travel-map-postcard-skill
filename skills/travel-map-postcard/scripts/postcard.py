"""Deterministic, photo-preserving map-layer compositor. See references/config.md."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageChops, ImageFilter, ImageStat


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_photo(path):
    with Image.open(path) as source:
        if source.mode == 'CMYK':
            raise ValueError('CMYK requires an explicit color-managed conversion; provide an RGB photo.')
        if source.mode == 'RGBA' and source.getchannel('A').getextrema()[0] < 255:
            raise ValueError('Transparent photo inputs require a user-chosen flattening background.')
        icc = source.info.get('icc_profile')
        image = ImageOps.exif_transpose(source).convert('RGB')
    return image, icc


def inspect(path):
    with Image.open(path) as im:
        exif = im.getexif()
        gps = exif.get_ifd(34853)
        orientation = exif.get(274, 1)
        original = im.size
    oriented, _ = read_photo(path)
    return {'file': str(path), 'sha256': digest(path), 'stored_size': original,
            'display_size': oriented.size, 'exif_orientation': orientation,
            'has_gps': bool(gps), 'gps_values': 'not exported; inspect locally only if needed'}


def mercator(lon, lat):
    if not (-180 <= lon <= 180 and -80 <= lat <= 80):
        raise ValueError('Coordinates outside the supported WGS84 range.')
    return math.radians(lon), math.log(math.tan(math.pi/4+math.radians(lat)/2))


def projection(bbox, width, height, fit='contain',align=(.5,.5)):
    s,w,n,e=bbox
    x0,y0=mercator(w,s); x1,y1=mercator(e,n)
    if x1 <= x0 or y1 <= y0:
        raise ValueError('Invalid or antimeridian-crossing bbox.')
    if fit not in ('contain','cover'):
        raise ValueError('projection_fit must be contain or cover.')
    scale=(max if fit=='cover' else min)(width/(x1-x0),height/(y1-y0))
    if len(align)!=2 or any(not 0<=v<=1 for v in align):raise ValueError('projection_align must contain two values in [0,1].')
    ox=(width-(x1-x0)*scale)*align[0];oy=(height-(y1-y0)*scale)*align[1]
    def point(lon,lat):
        x,y=mercator(lon,lat)
        return ox+(x-x0)*scale,oy+(y1-y)*scale
    return point,scale


def font(size, explicit=None, italic=False, family='times'):
    family_files={'times':('times.ttf','timesi.ttf'),'georgia':('georgia.ttf','georgiai.ttf')}
    if family not in family_files:
        raise ValueError('font_family must be times or georgia.')
    preferred='C:/Windows/Fonts/'+family_files[family][bool(italic)]
    candidates=([explicit] if explicit else [])+[preferred]+([
        'C:/Windows/Fonts/timesi.ttf','/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf'] if italic else [
        'C:/Windows/Fonts/times.ttf','/System/Library/Fonts/Supplemental/Times New Roman.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'])
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate,max(8,round(size)))
    raise FileNotFoundError('Pass --font with a local TrueType/OpenType serif font. Fonts are not bundled.')


def text_font(size, value, explicit=None, italic=False, family='times', language=None):
    """Choose a local script-capable face; never silently draw CJK tofu with a Latin face."""
    def supports(face):
        missing=bytes(face.getmask('\U0010ffff'))
        return all(c.isspace() or bytes(face.getmask(c))!=missing for c in value)
    if explicit and not Path(explicit).is_file():raise FileNotFoundError('The requested text font does not exist: '+str(explicit))
    script=('ko' if any('\uac00'<=c<='\ud7af' or '\u1100'<=c<='\u11ff' for c in value) else
            'ja' if any('\u3040'<=c<='\u30ff' or '\u3400'<=c<='\u9fff' for c in value) else None)
    language=(language or script or '').split('-')[0]
    if not script:
        face=font(size,explicit,italic,family)
        if supports(face):return face
        raise FileNotFoundError('This font lacks required glyphs; provide a script-capable font path.')
    windows={'ja':['YuGothL.ttc','YuGothR.ttc','msgothic.ttc'],
             'ko':['malgun.ttf','malgunbd.ttf'],
             'zh':['simsun.ttc','msyh.ttc']}
    candidates=([explicit] if explicit else [])
    if not explicit:
        candidates+=['C:/Windows/Fonts/'+f for f in windows.get(language,windows[script])]
        candidates+=['/System/Library/Fonts/AppleSDGothicNeo.ttc'] if language=='ko' else [
            '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc']
        candidates+=[
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc']
    for candidate in candidates:
        if not Path(candidate).is_file():continue
        face=ImageFont.truetype(candidate,max(8,round(size)))
        if supports(face):return face
    raise FileNotFoundError('No local font can render this title/label script; provide a script-capable font path.')


def supported_geometry(tags):
    # Named bays/administrative boundaries are not physical shorelines.
    return (tags.get('highway') in ('motorway','trunk','primary','secondary','tertiary','residential','unclassified','pedestrian','footway','path','steps')
            or tags.get('natural') in ('coastline','water','wood')
            or tags.get('waterway') in ('river','stream','canal')
            or tags.get('landuse') == 'forest' or tags.get('leisure') == 'park'
            or ('building' in tags and tags['building']!='no'))


def geometry_paths(data):
    seen=set()
    for el in data.get('elements',[]):
        if el['type']=='way' and supported_geometry(el.get('tags',{})) and len(el.get('geometry',[]))>1:
            seen.add(el['id'])
            yield el.get('tags',{}),el['geometry']
    for el in data.get('elements',[]):
        if el['type']=='relation' and supported_geometry(el.get('tags',{})):
            for member in el.get('members',[]):
                if member.get('type')=='way' and member.get('ref') not in seen and len(member.get('geometry',[]))>1:
                    seen.add(member.get('ref'))
                    yield el.get('tags',{}),member['geometry']


def validate(config, data, source):
    if config.get('mode','city') not in ('city','coast','trail'):
        raise ValueError('Supported map modes: city, coast, trail. No synthetic contour mode.')
    if config.get('supersample',2) not in (1,2):
        raise ValueError('supersample must be 1 or 2.')
    loc=config.get('location',{})
    if loc.get('status') not in ('verified_area','user_confirmed','gps_verified') or not loc.get('evidence'):
        raise ValueError('Location needs usable area-level evidence; ambiguous candidates must not render named maps.')
    rect=config['rect']; x,y,w,h=rect
    if min(x,y)<0 or min(w,h)<=0 or x+w>1 or y+h>1:
        raise ValueError('rect must fit the photo, in normalized x,y,width,height.')
    if not .15 <= w*h <= .25 and not config.get('layout_exception_reason'):
        raise ValueError('Map frame should cover 15–25%; record a reason for a composition exception.')
    bbox=config['bbox']; sb,wb,nb,eb=source['bbox_south_west_north_east']
    s,w,n,e=bbox
    if not (sb<=s<n<=nb and wb<=w<e<=eb):
        raise ValueError('Map view must be contained in the fetched extract.')
    if data.get('remark') or not data.get('elements'):
        raise ValueError('Incomplete or empty map extract.')
    for item in config.get('labels',[]):
        if not item.get('evidence'):
            raise ValueError('Every geographic label needs a coordinate/evidence reference.')
        if not (s<item['lat']<n and w<item['lon']<e):
            raise ValueError('Label is outside map view: '+item['text'])
        if item.get('role')=='capture' and loc.get('camera_status')!='exact':
            raise ValueError('Cannot use an exact camera pin without camera-location evidence.')
        if item.get('role')=='capture' and not loc.get('camera_evidence'):
            raise ValueError('Exact capture pin needs GPS or other direct camera evidence.')
        visible_text=item['text']+' '+item.get('note','')
        if item.get('role')=='area' and ('approx.' not in visible_text.lower() or item.get('uncertainty_m',0)<=0):
            raise ValueError('Area markers require visible approx. wording and an estimated uncertainty radius.')
    if sum(i.get('role') in ('area','capture') for i in config.get('labels',[]))>1:
        raise ValueError('Use only one red location marker.')
    for item in config.get('highlight_features',[]):
        if not item.get('evidence'):
            raise ValueError('Highlighted geography needs feature evidence.')
        if not any(el['type']==item['type'] and el['id']==item['id'] and el.get('geometry') for el in data['elements']):
            raise ValueError('Highlighted feature must exist in the sourced map extract.')
    for item in config.get('photo_markers',[]):
        if not item.get('evidence') or not item.get('not_to_scale_acknowledged'):
            raise ValueError('Photo marker requires sourced landmark evidence and not-to-scale acknowledgement.')
        if not (s<item['lat']<n and w<item['lon']<e):raise ValueError('Photo marker anchor must be inside the map view.')
    atmosphere=config.get('atmosphere',{})
    if not 0 <= atmosphere.get('cloud_strength',0) <= 1:
        raise ValueError('cloud_strength must be in [0,1].')
    if not 0 <= atmosphere.get('fade_start',.7) < 1:
        raise ValueError('fade_start must be in [0,1).')
    if not 0 <= atmosphere.get('distant_alpha',1) <= 1:
        raise ValueError('distant_alpha must be in [0,1].')
    if not 0 <= atmosphere.get('distant_blur_px',0) <= 3:
        raise ValueError('distant_blur_px must be in [0,3].')
    low,high=atmosphere.get('cloud_luma',[150,230])
    if not 0 <= low < high <= 255:
        raise ValueError('cloud_luma needs increasing thresholds in [0,255].')


def atmospheric_mask(photo, size, settings):
    """Attenuate only map ink using existing cloud light and a horizon fade."""
    rw,rh=size
    start=settings.get('fade_start',.7)
    distant=settings.get('distant_alpha',1)
    values=[]
    for y in range(rh):
        t=y/max(1,rh-1)
        depth=distant+(1-distant)*min(1,t/.45)
        horizon=max(0,1-max(0,(t-start)/(1-start)))
        horizon=horizon*horizon*(3-2*horizon)
        values.append(round(255*depth*horizon))
    gradient=Image.new('L',(1,rh));gradient.putdata(values)
    mask=gradient.resize(size)
    strength=settings.get('cloud_strength',0)
    if strength:
        low,high=settings.get('cloud_luma',[150,230])
        cloud=photo.convert('L').resize(size,Image.Resampling.BILINEAR)
        cloud=cloud.filter(ImageFilter.GaussianBlur(max(1,rw*.009)))
        cloud=cloud.point([round(255*(1-strength*min(1,max(0,(v-low)/(high-low))))) for v in range(256)])
        mask=ImageChops.multiply(mask,cloud)
    return mask


def geometry_style(tags):
    if tags.get('natural')=='coastline': return 'coast'
    if tags.get('natural')=='water' or 'waterway' in tags: return 'water'
    if tags.get('highway') in ('motorway','trunk','primary','secondary','tertiary'): return 'major'
    if tags.get('highway') in ('path','steps','footway'): return 'trail'
    if 'highway' in tags: return 'minor'
    if 'building' in tags: return 'building'
    return 'landscape'


def tracked_text(draw,xy,value,typeface,fill,tracking=0):
    x,y=xy
    for char in value:
        draw.text((x,y),char,font=typeface,fill=fill)
        x+=draw.textlength(char,font=typeface)+tracking
    return x


def glow_layer(layer,settings,unit=1):
    """Small two-scale bloom and optional contrast shadow; never blur the photo."""
    if not settings or not settings.get('enabled',True):return layer
    alpha=layer.getchannel('A')
    light_mask=None
    if 'light_origin' in settings:
        origin=settings['light_origin'];floor=settings.get('light_floor',.2)
        if len(origin)!=2 or not all(0<=v<=1 for v in origin) or not 0<=floor<=1:
            raise ValueError('Glow light_origin and light_floor must be normalized.')
        ox,oy=origin
        far=max(math.hypot(x-ox,y-oy) for x,y in [(0,0),(0,1),(1,0),(1,1)])
        light_mask=Image.new('L',(128,128))
        light_mask.putdata([round(255*(floor+(1-floor)*max(0,1-math.hypot(x/127-ox,y/127-oy)/far)))
                           for y in range(128) for x in range(128)])
        light_mask=light_mask.resize(layer.size,Image.Resampling.BILINEAR)
    result=Image.new('RGBA',layer.size)
    for radius,opacity,color in [
        (settings.get('shadow_radius',.8),settings.get('shadow_opacity',0),settings.get('shadow_ink',[39,57,64])),
        (settings.get('radius',3.5)*2.5,settings.get('opacity',.3)*.35,settings.get('ink',[255,242,211])),
        (settings.get('radius',3.5),settings.get('opacity',.3),settings.get('ink',[255,242,211]))]:
        if not 0<=opacity<=1 or not 0<=radius<=30:raise ValueError('Invalid glow radius or opacity.')
        if opacity:
            halo=Image.new('RGBA',layer.size,tuple(color)+(0,))
            glow_alpha=alpha.filter(ImageFilter.GaussianBlur(radius*unit)).point([round(v*opacity) for v in range(256)])
            if light_mask is not None:glow_alpha=ImageChops.multiply(glow_alpha,light_mask)
            halo.putalpha(glow_alpha)
            result=Image.alpha_composite(result,halo)
    result=Image.alpha_composite(result,layer)
    highlight=settings.get('highlight_opacity',0)
    if not 0<=highlight<=1:raise ValueError('Glow highlight_opacity must be normalized.')
    if highlight:
        highlight_alpha=alpha.point([round(v*highlight) for v in range(256)])
        if light_mask is not None:highlight_alpha=ImageChops.multiply(highlight_alpha,light_mask)
        bright=Image.new('RGBA',layer.size,tuple(settings.get('ink',[255,242,211]))+(0,))
        bright.putalpha(highlight_alpha)
        result=Image.alpha_composite(result,bright)
    return result


def harmonize_imagery(patch,background,settings):
    """Use real aerial detail as a background-colored relief; only the overlay is graded."""
    if settings.get('mode')!='background_relief':raise ValueError('Unknown aerial harmonization mode.')
    contrast=settings.get('contrast',.7)
    detail=settings.get('detail_weight',.55)
    chroma=settings.get('color_retention',.06)
    if not all(0<=v<=1 for v in (contrast,detail,chroma)):
        raise ValueError('Aerial harmonization settings must be in [0,1].')
    if background is None or background.size!=patch.size:
        raise ValueError('Background relief needs the aligned original-photo crop.')
    alpha=patch.getchannel('A')
    rgb=patch.convert('RGB')
    gray=ImageOps.autocontrast(rgb.convert('L'),cutoff=2)
    broad=gray.filter(ImageFilter.GaussianBlur(max(1,min(patch.size)*.045)))
    detail_gray=ImageChops.subtract(gray,broad,offset=128)
    tone=Image.blend(gray,detail_gray,detail)
    # Neutral-centered photographic texture carries geometry; the local sky supplies its light and palette.
    tone_rgb=Image.merge('RGB',(tone,tone,tone))
    texture=Image.blend(tone_rgb,rgb,chroma).point([round(128+(v-128)*contrast) for v in range(256)]*3)
    result=ImageChops.soft_light(background.convert('RGB'),texture).convert('RGBA')
    result.putalpha(alpha)
    return result


def marker_opacity(patch,background,settings,opacity=1):
    """Adapt only an emphasis photo's alpha to local RGB contrast. RGB pixels stay untouched."""
    if not 0<opacity<=1:raise ValueError('Marker opacity must be in (0,1].')
    original=patch.getchannel('A')
    if not settings:
        result=patch.copy();result.putalpha(original.point([round(v*opacity) for v in range(256)]))
        return result,{'mode':'constant','opacity':opacity}
    if background is None or background.size!=patch.size:
        raise ValueError('Adaptive marker opacity needs its aligned original-photo crop.')
    low=settings.get('min',.18);high=settings.get('max',.65)
    budget=settings.get('contrast_budget',.22)
    if not 0<low<=high<=1 or not 0<budget<=1:raise ValueError('Invalid adaptive marker opacity range or contrast budget.')
    difference=ImageChops.difference(patch.convert('RGB'),background.convert('RGB')).convert('L')
    difference=difference.filter(ImageFilter.GaussianBlur(max(.5,min(patch.size)*.008)))
    gain=difference.point([round(255*min(high,max(low,budget*255/max(1,v)))*opacity) for v in range(256)])
    result=patch.copy();result.putalpha(ImageChops.multiply(original,gain))
    visible=original.point([0]+[255]*255)
    return result,{'mode':'local_rgb_contrast','min':low,'max':high,'contrast_budget':budget,
        'opacity':opacity,'mean_multiplier':ImageStat.Stat(gain,visible).mean[0]/255,
        'scope':'emphasis photo alpha only; source RGB and vector-map opacity unchanged'}


def photo_marker_layer(entries,config_path,point,size,short_edge,background):
    """A real photo cutout anchored to a sourced landmark; deliberately a symbol, not an orthophoto."""
    layer=Image.new('RGBA',size);records=[]
    for entry in entries:
        if not entry.get('evidence') or not entry.get('not_to_scale_acknowledged'):
            raise ValueError('Photo marker needs landmark evidence and an explicit not-to-scale symbol acknowledgement.')
        path=Path(entry['path'])
        if not path.is_absolute():path=Path(config_path).parent/path
        meta=json.loads(path.with_suffix('.source.json').read_text(encoding='utf-8'))
        if digest(path)!=meta.get('image_sha256'):raise ValueError('Photo marker hash differs from provenance.')
        if not all(meta.get(k) for k in ('source_url','terms_url','attribution','author','license')):
            raise ValueError('Photo marker requires source, author, license, terms and attribution.')
        with Image.open(path) as im:patch=im.convert('RGBA')
        if patch.getchannel('A').getextrema()[0]==255:raise ValueError('Photo marker must have a genuine transparent cutout.')
        height=entry.get('height_fraction',.15)
        if not 0<height<=.35:raise ValueError('Photo marker height_fraction must be in (0,.35].')
        ph=max(1,round(short_edge*height));pw=max(1,round(patch.width/patch.height*ph))
        patch=patch.resize((pw,ph),Image.Resampling.LANCZOS)
        px,py=point(entry['lon'],entry['lat'])
        ax,ay=entry.get('anchor_fraction',[.5,1])
        if not 0<=ax<=1 or not 0<=ay<=1:raise ValueError('Photo marker anchor_fraction must be normalized.')
        left,top=round(px-pw*ax),round(py-ph*ay)
        box=(left,top,left+pw,top+ph)
        if left<0 or top<0 or box[2]>size[0] or box[3]>size[1]:raise ValueError('Photographic marker would be clipped; reduce its size or change the map view.')
        patch,adaptation=marker_opacity(patch,background.crop(box),entry.get('adaptive_opacity'),entry.get('opacity',1))
        placed=Image.new('RGBA',size);placed.paste(patch,box[:2])
        layer=Image.alpha_composite(layer,placed)
        records.append({'path':str(path),'metadata':meta,'projected_box':list(box),
            'landmark_anchor':{'lat':entry['lat'],'lon':entry['lon'],'evidence':entry['evidence']},
            'representation':'photographic symbol, not to map scale; not an aerial footprint or camera pin',
            'opacity_adaptation':adaptation})
    return layer,records


def imagery_layer(entries,config_path,data,point,size,background=None):
    """Place sourced orthophotos at their actual Web Mercator coordinates."""
    layer=Image.new('RGBA',size);records=[]
    for entry in entries:
        path=Path(entry['path'])
        if not path.is_absolute():path=Path(config_path).parent/path
        meta_path=path.with_suffix('.source.json')
        meta=json.loads(meta_path.read_text(encoding='utf-8'))
        if meta.get('crs')!='EPSG:3857' or meta.get('orientation')!='north-up':
            raise ValueError('Aerial imagery must have verified north-up EPSG:3857 georeferencing.')
        if digest(path)!=meta.get('image_sha256'):raise ValueError('Aerial imagery hash differs from provenance.')
        if not all(meta.get(k) for k in ('source_url','terms_url','attribution')):
            raise ValueError('Aerial imagery needs a source, terms and visible attribution.')
        s,w,n,e=meta['bbox_south_west_north_east']
        if not (s<n and w<e):raise ValueError('Invalid aerial imagery extent.')
        left,top=point(w,n);right,bottom=point(e,s)
        box=tuple(round(v) for v in (left,top,right,bottom))
        pw,ph=box[2]-box[0],box[3]-box[1]
        if min(pw,ph)<=0 or max(pw,ph)>max(size)*2:raise ValueError('Aerial extent does not fit this map view.')
        with Image.open(path) as im:patch=im.convert('RGBA').resize((pw,ph),Image.Resampling.LANCZOS)
        processing=entry.get('harmonize')
        if processing:
            if background is None:raise ValueError('Aerial harmonization needs the original photo background.')
            # Only the visible overlap is composited; padding outside the photo is discarded.
            region=background.crop(box)
            patch=harmonize_imagery(patch,region,processing)
        mask=Image.new('L',(pw,ph));md=ImageDraw.Draw(mask)
        polygon=entry.get('reveal_polygon')
        if not polygon or not entry.get('editorial_reveal_acknowledged'):
            raise ValueError('Specify an editorial reveal mask; it is not a geographic site boundary.')
        if any(not (0<=x<=1 and 0<=y<=1) for x,y in polygon):raise ValueError('Reveal polygon must be normalized.')
        md.polygon([(round(x*pw),round(y*ph)) for x,y in polygon],fill=255)
        feather=entry.get('feather_fraction',.06)
        opacity=entry.get('opacity',.95)
        if not 0<=feather<=.2 or not 0<opacity<=1:raise ValueError('Invalid aerial reveal settings.')
        mask=mask.filter(ImageFilter.GaussianBlur(min(pw,ph)*feather))
        patch.putalpha(ImageChops.multiply(patch.getchannel('A'),mask))
        patch,adaptation=marker_opacity(patch,background.crop(box) if background is not None else None,
            entry.get('adaptive_opacity'),opacity)
        placed=Image.new('RGBA',size);placed.paste(patch,box[:2])
        layer=Image.alpha_composite(layer,placed)
        records.append({'path':str(path),'metadata':meta,'projected_box':list(box),
                        'processing':processing or {'mode':'source_color'},
                        'opacity_adaptation':adaptation,
                        'reveal':'Editorial alpha reveal, not an asserted coastline/site boundary.'})
    return layer,records


def render(photo_path,data_path,config_path,outdir,font_path=None):
    config=json.loads(Path(config_path).read_text(encoding='utf-8'))
    data=json.loads(Path(data_path).read_text(encoding='utf-8'))
    source=json.loads(Path(data_path).with_suffix('.source.json').read_text(encoding='utf-8'))
    if digest(data_path)!=source['data_sha256']:
        raise ValueError('Map data hash differs from its provenance.')
    validate(config,data,source)
    out=Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Use an empty versioned output directory.')
    base,icc=read_photo(photo_path)
    W,H=base.size
    x,y,w,h=config['rect']; X,Y=round(W*x),round(H*y); mw,mh=round(W*w),round(H*h)
    ss=config.get('supersample',2); rw,rh=mw*ss,mh*ss
    lines=Image.new('RGBA',(rw,rh)); draw=ImageDraw.Draw(lines)
    point,scale=projection(config['bbox'],rw,rh,config.get('projection_fit','contain'),config.get('projection_align',[.5,.5]))
    ink=tuple(config.get('ink',[235,229,210]))
    strength=config.get('line_opacity',.46)
    if not 0<strength<=1:
        raise ValueError('line_opacity must be in (0,1].')
    defaults={'landscape':[.24,.55],'building':[.29,.60],'trail':[.32,.65],
              'minor':[.48,.85],'major':[.82,1.45],'water':[.82,1.65],'coast':[1,2.0]}
    styles={**defaults,**config.get('geometry_styles',{})}
    # Draw strong cartographic structure last: a fine street must not erase a coast.
    ordered=sorted(geometry_paths(data),key=lambda pair:list(defaults).index(geometry_style(pair[0])))
    count=0
    for tags,geometry in ordered:
        pts=[point(p['lon'],p['lat']) for p in geometry if 'lat' in p and 'lon' in p]
        if len(pts)<2: continue
        road=tags.get('highway','')
        trail=road in ('path','steps','footway')
        if config.get('mode')=='city' and trail: continue
        opacity,line_width=styles[geometry_style(tags)]
        category=geometry_style(tags)
        line_ink=tuple(config.get('geometry_inks',{}).get(category,ink))
        alpha=round(255*strength*opacity)
        width=max(1,round(ss*min(W,H)/1300*line_width))
        fill_opacity=config.get('geometry_fills',{}).get(category,0)
        if fill_opacity and pts[0]==pts[-1]:
            draw.polygon(pts,fill=line_ink+(round(255*strength*fill_opacity),))
        draw.line(pts,fill=line_ink+(alpha,),width=width,joint='curve'); count+=1
    # Full-bleed linework. Clouds modulate map alpha; the photograph is never retouched.
    atmosphere=config.get('atmosphere',{})
    fade=atmospheric_mask(base.crop((X,Y,X+mw,Y+mh)),(rw,rh),atmosphere)
    blur=atmosphere.get('distant_blur_px',0)
    if blur:
        focus=Image.new('L',(1,rh))
        focus.putdata([round(255*min(1,(y/max(1,rh-1))/.5)) for y in range(rh)])
        lines=Image.composite(lines,lines.filter(ImageFilter.GaussianBlur(blur*ss)),focus.resize((rw,rh)))
    lines.putalpha(ImageChops.multiply(lines.getchannel('A'),fade))
    background=(base.crop((X,Y,X+mw,Y+mh)).resize((rw,rh),Image.Resampling.LANCZOS)
                if config.get('imagery') or config.get('photo_markers') else None)
    imagery,imagery_records=imagery_layer(config.get('imagery',[]),config_path,data,point,(rw,rh),background)
    if imagery_records and config.get('quiet_under_imagery',True):
        quiet=imagery.getchannel('A').point([round(v*.78) for v in range(256)])
        lines.putalpha(ImageChops.multiply(lines.getchannel('A'),ImageChops.invert(quiet)))
    photo_markers,photo_marker_records=photo_marker_layer(config.get('photo_markers',[]),config_path,
        point,(rw,rh),ss*min(W,H),background)
    annotations=Image.new('RGBA',(rw,rh)); ad=ImageDraw.Draw(annotations)
    family=config.get('font_family','times')
    title_font=text_font(min(W,H)*config.get('title_size',.024)*ss,config['title'],
        config.get('title_font_path',font_path),family=family,language=config.get('title_language'))
    small_font=font(min(W,H)*config.get('credit_size',.0105)*ss,font_path,family=family)
    text_ink=ink+(round(255*config.get('text_opacity',.85)),)
    title_xy=config.get('title_xy',[.08,.05])
    title_pos=(rw*title_xy[0],rh*title_xy[1])
    title_end=tracked_text(ad,title_pos,config['title'],title_font,text_ink,
                           config.get('title_tracking',0)*min(W,H)*ss)
    clear=Image.new('L',(rw,rh));cd=ImageDraw.Draw(clear)
    if config.get('clear_text_backdrop',False):
        padding=min(W,H)*.012*ss
        cd.rectangle((title_pos[0]-padding,title_pos[1]-padding,
                      title_end+padding,title_pos[1]+title_font.size*2.25),fill=235)
    if config.get('subtitle'):
        subtitle_font=text_font(min(W,H)*config.get('subtitle_size',config.get('label_size',.014))*ss,
                           config['subtitle'],config.get('subtitle_font_path',font_path),
                           config.get('subtitle_italic',True),family,config.get('subtitle_language'))
        subtitle_pos=(rw*title_xy[0],rh*title_xy[1]+title_font.size*1.45)
        subtitle_end=tracked_text(ad,subtitle_pos,config['subtitle'],subtitle_font,text_ink,
                                  config.get('subtitle_tracking',0)*min(W,H)*ss)
        if config.get('clear_text_backdrop',False):
            cd.rectangle((subtitle_pos[0]-padding,subtitle_pos[1]-padding,
                          subtitle_end+padding,subtitle_pos[1]+subtitle_font.size*1.5+padding),fill=235)
        if config.get('header_rule',False):
            rule_y=subtitle_pos[1]+subtitle_font.size*2.1
            ad.line([(subtitle_pos[0],rule_y),(subtitle_pos[0]+rw*.12,rule_y)],
                    fill=ink+(150,),width=max(1,ss))
    label_boxes=[]
    feature_lines=Image.new('RGBA',(rw,rh));fd=ImageDraw.Draw(feature_lines)
    for feature in config.get('highlight_features',[]):
        el=next(el for el in data['elements'] if el['type']==feature['type'] and el['id']==feature['id'])
        pts=[point(p['lon'],p['lat']) for p in el['geometry']]
        color=tuple(feature.get('ink',ink))
        if pts[0]==pts[-1]:
            fd.polygon(pts,fill=color+(round(255*feature.get('fill_opacity',.12)),))
        fd.line(pts,fill=color+(240,),width=max(2,round(ss*min(W,H)/1300*feature.get('width',2.5))),joint='curve')
    for item in config.get('labels',[]):
        px,py=point(item['lon'],item['lat'])
        role=item.get('role','landmark'); rad=max(3,ss*min(W,H)*item.get('marker_size',.003))
        item_font=text_font(min(W,H)*item.get('size',config.get('label_size',.014))*ss,item['text'],
            item.get('font_path',config.get('label_font_path',font_path)),item.get('italic',True),family,item.get('language'))
        item_ink=tuple(item.get('ink',ink))+(round(255*item.get('opacity',config.get('text_opacity',.85))),)
        if role in ('area','capture'):
            if role=='area' and config.get('show_uncertainty_ring',False):
                uncertainty=item['uncertainty_m']/6378137/math.cos(math.radians(item['lat']))*scale
                ur=max(rad*3,uncertainty)
                # A light dashed perimeter conveys an approximate area without a target-like solid ring.
                for angle in range(0,360,12):
                    ad.arc((px-ur,py-ur,px+ur,py+ur),angle,angle+6,fill=(193,77,70,60),width=max(1,ss))
            ad.ellipse((px-rad,py-rad,px+rad,py+rad),fill=(193,59,55,235),outline=ink+(220,),width=ss)
        elif item.get('marker',True):
            ad.ellipse((px-rad*.55,py-rad*.55,px+rad*.55,py+rad*.55),fill=text_ink)
        dx,dy=item.get('offset',[.025,-.025]); tx,ty=px+dx*rw,py+dy*rh
        box=ad.multiline_textbbox((tx,ty),item['text'],font=item_font,spacing=item_font.size*.12)
        note_font=text_font(item_font.size*item.get('note_scale',.58),item.get('note',''),font_path,True,family)
        note_y=box[3]+item_font.size*.22
        if item.get('note'):
            note_box=ad.textbbox((tx,note_y),item['note'],font=note_font)
            box=(min(box[0],note_box[0]),min(box[1],note_box[1]),max(box[2],note_box[2]),max(box[3],note_box[3]))
        if box[0]<2 or box[1]<2 or box[2]>rw-2 or box[3]>rh-2:
            raise ValueError('Label would be clipped; adjust offset or bbox: '+item['text'])
        if (role in ('area','capture') or item.get('marker',True)) and box[0]-rad<px<box[2]+rad and box[1]-rad<py<box[3]+rad:
            raise ValueError('Location marker overlaps its label; adjust offset: '+item['text'])
        for prior in label_boxes:
            if box[0]<prior[2] and box[2]>prior[0] and box[1]<prior[3] and box[3]>prior[1]:
                raise ValueError('Geographic labels collide; adjust offsets.')
        label_boxes.append(box)
        if item.get('leader',False):
            # The leader ends at the verified map anchor, not the displaced text.
            endx=min(max(px,box[0]),box[2]);endy=min(max(py,box[1]),box[3])
            ad.line([(px,py),(endx,endy)],fill=item_ink,width=max(1,round(ss*min(W,H)/1300)))
        if item.get('emphasis',False) and config.get('clear_text_backdrop',False):
            cd.rectangle((box[0]-padding,box[1]-padding,box[2]+padding,box[3]+padding),fill=230)
        ad.multiline_text((tx,ty),item['text'],font=item_font,fill=item_ink,spacing=item_font.size*.12)
        if item.get('note'):ad.text((tx,note_y),item['note'],font=note_font,fill=item_ink)
    # Visible attribution stays beside the map, including the license URL for prints.
    credit='© OpenStreetMap contributors'
    credit_url='openstreetmap.org/copyright'
    cx,cy=config.get('credit_xy',[.08,.90])
    if config.get('credit_single_line',False):
        ad.text((rw*cx,rh*cy),credit+' · '+credit_url,font=small_font,fill=ink+(190,))
    else:
        ad.text((rw*cx,rh*cy),credit,font=small_font,fill=ink+(190,))
        ad.text((rw*cx,rh*cy+small_font.size*1.3),credit_url,font=small_font,fill=ink+(190,))
    if imagery_records or photo_marker_records:
        all_photo_records=imagery_records+photo_marker_records
        attribution=' · '.join(dict.fromkeys(record['metadata']['attribution'] for record in all_photo_records))
        source_urls=' · '.join(dict.fromkeys(record['metadata']['source_url'].replace('https://','') for record in all_photo_records))
        if config.get('photo_credit_compact',False):
            source_urls=' · '.join(dict.fromkeys(record['metadata']['terms_url'].replace('https://','') for record in all_photo_records))
        credit_y=rh*cy+small_font.size*(1.4 if config.get('credit_single_line',False) else 2.6)
        ad.text((rw*cx,credit_y),attribution,font=small_font,fill=ink+(220,))
        ad.text((rw*cx,credit_y+small_font.size*1.3),source_urls,font=small_font,fill=ink+(190,))
    if config.get('clear_text_backdrop',False):
        clear=clear.filter(ImageFilter.GaussianBlur(min(W,H)*.01*ss))
        lines.putalpha(ImageChops.multiply(lines.getchannel('A'),ImageChops.invert(clear)))
        feature_lines.putalpha(ImageChops.multiply(feature_lines.getchannel('A'),ImageChops.invert(clear)))
    glow=config.get('glow',{})
    unit=ss*min(W,H)/1300
    lines=glow_layer(lines,glow.get('map',{}),unit)
    feature_lines=glow_layer(feature_lines,glow.get('emphasis',{}),unit)
    annotations=glow_layer(annotations,glow.get('text',{}),unit)
    cartography=Image.alpha_composite(Image.alpha_composite(lines,feature_lines),annotations)
    local=Image.alpha_composite(Image.alpha_composite(imagery,cartography),photo_markers).resize((mw,mh),Image.Resampling.LANCZOS)
    overlay=Image.new('RGBA',(W,H)); overlay.paste(local,(X,Y))
    protected=Image.new('L',(W,H)); pd=ImageDraw.Draw(protected)
    for polygon in config.get('protected_polygons',[]):
        pd.polygon([(round(a*W),round(b*H)) for a,b in polygon],fill=255)
    if config.get('check_label_visibility',False):
        for item,box in zip(config.get('labels',[]),label_boxes):
            native=(X+int(box[0]/ss),Y+int(box[1]/ss),X+math.ceil(box[2]/ss),Y+math.ceil(box[3]/ss))
            crop=protected.crop(native)
            lost=crop.histogram()[255]/max(1,crop.width*crop.height)
            if lost>.005:
                raise ValueError('Label intersects a protected photo subject; reposition: '+item['text'])
    overlay.putalpha(ImageChops.multiply(overlay.getchannel('A'),ImageChops.invert(protected)))
    if not overlay.getchannel('A').getbbox():
        raise ValueError('Protection mask removed the whole layer.')
    # Release supersampled working buffers before creating the full-resolution composite.
    del lines,draw,annotations,ad,feature_lines,fd,fade,local,background
    final=Image.alpha_composite(base.convert('RGBA'),overlay).convert('RGB')
    out.mkdir(parents=True,exist_ok=True)
    save_args={'icc_profile':icc} if icc else {}
    base.save(out/'photo-base.png',**save_args)
    overlay.save(out/'map-overlay.png',**save_args)
    protected.save(out/'protected-mask.png')
    final.save(out/'postcard.png',**save_args)
    # Separate editable emphasis layers make alpha-only revisions and comparisons reviewable.
    if imagery_records or photo_marker_records:
        for filename,working in [('cartography-overlay.png',cartography),
                ('aerial-overlay.png',imagery),('photo-markers-overlay.png',photo_markers)]:
            separated=Image.new('RGBA',(W,H));separated.paste(working.resize((mw,mh),Image.Resampling.LANCZOS),(X,Y))
            separated.putalpha(ImageChops.multiply(separated.getchannel('A'),ImageChops.invert(protected)))
            separated.save(out/filename,**save_args);separated.close()
    del cartography,imagery,photo_markers
    (out/'composition.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    base.close(); overlay.close(); final.close(); protected.close()
    verification=verify(photo_path,out)
    record={'source_photo_sha256':digest(photo_path),'map_data_sha256':digest(data_path),
            'map_provenance':source,'dimensions':[W,H],'mode':config.get('mode'),
            'geometry_paths':count,'map_frame_fraction':w*h,'location':config['location'],
            'aerial_imagery':imagery_records,
            'photo_markers':photo_marker_records,
            'typography':{'title_language':config.get('title_language'),
                          'subtitle_language':config.get('subtitle_language'),
                          'title_font':str(title_font.path)},
            'verification':verification,'files':{f.name:digest(f) for f in out.iterdir() if f.is_file()},
            'photo_license':'user-provided; not included in the skill package',
            'limitations':['Visual identification is a researched inference, not photo geolocation ground truth.',
                           'OSM extract has roads, shores, water and paths; no elevation-derived contours.',
                           'PNG preservation is measured against EXIF-oriented decoded source pixels.']}
    (out/'manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    return record


def verify(photo_path,outdir):
    out=Path(outdir); source,_=read_photo(photo_path)
    with Image.open(out/'postcard.png') as im: final=im.convert('RGB')
    with Image.open(out/'map-overlay.png') as im: overlay=im.convert('RGBA')
    if source.size!=final.size or source.size!=overlay.size:
        raise ValueError('Aspect ratio or native dimensions changed.')
    with Image.open(out/'protected-mask.png') as im: protected=im.convert('L')
    # Verify in strips; Pillow only, no BLAS threads or full-photo numeric arrays.
    outside=compositing=protected_changes=changed_count=alpha_count=0
    width,height=source.size
    for y in range(0,height,128):
        box=(0,y,width,min(y+128,height));src=source.crop(box);over=overlay.crop(box)
        dst=final.crop(box);alpha=over.getchannel('A')
        changed=difference_mask(src,dst)
        zero_alpha=alpha.point([255]+[0]*255)
        outside+=ImageChops.multiply(changed,zero_alpha).histogram()[255]
        recomposed=Image.alpha_composite(src.convert('RGBA'),over).convert('RGB')
        compositing+=difference_mask(recomposed,dst).histogram()[255]
        protected_changes+=ImageChops.multiply(changed,protected.crop(box)).histogram()[255]
        changed_count+=changed.histogram()[255]
        alpha_count+=alpha.point([0]+[255]*255).histogram()[255]
    result={'passed':not(outside or compositing or protected_changes),
            'outside_alpha_changed_pixels':outside,'composition_mismatch_pixels':compositing,
            'protected_changed_pixels':protected_changes,'changed_pixel_fraction':changed_count/(width*height),
            'alpha_footprint_fraction':alpha_count/(width*height),'size':list(source.size)}
    source.close();final.close();overlay.close();protected.close()
    if not result['passed']: raise ValueError('Pixel preservation failed: '+json.dumps(result))
    return result


def difference_mask(a,b):
    channels=ImageChops.difference(a,b).split()
    diff=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
    return diff.point([0]+[255]*255)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='cmd',required=True)
    ip=sub.add_parser('inspect');ip.add_argument('photo')
    rp=sub.add_parser('render');rp.add_argument('--photo',required=True);rp.add_argument('--map',required=True)
    rp.add_argument('--config',required=True);rp.add_argument('--out',required=True);rp.add_argument('--font')
    vp=sub.add_parser('verify');vp.add_argument('--photo',required=True);vp.add_argument('--out',required=True)
    a=p.parse_args()
    if a.cmd=='inspect': result=inspect(a.photo)
    elif a.cmd=='verify': result=verify(a.photo,a.out)
    else:
        record=render(a.photo,a.map,a.config,a.out,a.font)
        result={'output':a.out,'paths':record['geometry_paths'],'verification':record['verification']}
    print(json.dumps(result,ensure_ascii=False,indent=2))
