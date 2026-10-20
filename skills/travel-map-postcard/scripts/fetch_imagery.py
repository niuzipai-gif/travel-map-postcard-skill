"""Download a small, cached, georeferenced GSI aerial patch; never upload a photo."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import io
import json
import math
import ssl
import time
from pathlib import Path
from threading import Event
import urllib.request
import urllib.error
from PIL import Image

GSI_URL='https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg'
SOURCE_URL='https://maps.gsi.go.jp/help/use.html'
TERMS_URL='https://web1.gsi.go.jp/kikakuchousei/kikakuchousei40182.html'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def world_pixel(lon,lat,z):
    total=256*2**z
    return (lon+180)/360*total,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*total


def inverse_pixel(x,y,z):
    total=256*2**z
    return x/total*360-180,math.degrees(math.atan(math.sinh(math.pi*(1-2*y/total))))


def fetch_gsi(bbox,output,user_agent,zoom=17):
    s,w,n,e=bbox
    if not (24<=s<n<=46 and 122<=w<e<=146):
        raise ValueError('This provider helper is restricted to small Japan extracts.')
    if zoom not in (16,17,18):raise ValueError('Choose zoom 16, 17 or 18.')
    if max(n-s,e-w)>.025:raise ValueError('Use a small landmark patch, not a regional download.')
    output=Path(output);meta_path=output.with_suffix('.source.json')
    if output.exists():
        if not meta_path.exists():raise ValueError('Existing imagery has no provenance.')
        meta=json.loads(meta_path.read_text(encoding='utf-8'))
        if meta['requested_bbox']!=bbox or meta['zoom']!=zoom or meta['image_sha256']!=sha(output):
            raise ValueError('Existing imagery parameters or hash differ; use a versioned path.')
        return {'cached':True,'path':str(output),'tiles':len(meta['tiles'])}
    left,top=world_pixel(w,n,zoom);right,bottom=world_pixel(e,s,zoom)
    left,top,right,bottom=math.floor(left),math.floor(top),math.ceil(right),math.ceil(bottom)
    x0,y0,x1,y1=left//256,top//256,(right-1)//256,(bottom-1)//256
    coords=[(x,y) for y in range(y0,y1+1) for x in range(x0,x1+1)]
    if len(coords)>36:raise ValueError('Patch exceeds the 36-tile request budget; reduce the area or zoom.')
    cache=output.parent/'gsi-tile-cache';cache.mkdir(parents=True,exist_ok=True)
    stopped=Event()
    def obtain(pair):
        if stopped.is_set():raise RuntimeError('Imagery request stopped after a provider error.')
        x,y=pair;url=GSI_URL.format(z=zoom,x=x,y=y)
        path=cache/f'{zoom}-{x}-{y}.jpg';record_path=path.with_suffix('.json')
        try:
            if path.exists():
                rec=json.loads(record_path.read_text(encoding='utf-8'))
                if rec['sha256']!=sha(path) or rec['url']!=url:raise ValueError('Cached tile provenance differs.')
            else:
                req=urllib.request.Request(url,headers={'User-Agent':user_agent,'Accept':'image/jpeg'})
                for attempt in range(3):
                    try:
                        with urllib.request.urlopen(req,timeout=25) as response:raw=response.read(512*1024+1)
                        break
                    except urllib.error.HTTPError:
                        raise
                    except (urllib.error.URLError,TimeoutError,ConnectionResetError) as error:
                        reason=getattr(error,'reason',error)
                        if not isinstance(reason,(ssl.SSLEOFError,TimeoutError,ConnectionResetError)) or attempt==2:
                            raise
                        time.sleep(.5*(attempt+1))
                if len(raw)>512*1024:raise ValueError('Tile exceeds its response budget.')
                with Image.open(io.BytesIO(raw)) as im:
                    if im.size!=(256,256):raise ValueError('Provider returned an unexpected tile.')
                    im.verify()
                path.write_bytes(raw)
                rec={'url':url,'sha256':sha(path),'retrieved_utc':datetime.now(timezone.utc).isoformat()}
                record_path.write_text(json.dumps(rec,indent=2),encoding='utf-8')
            return pair,path,rec
        except Exception:
            stopped.set();raise
    # Verify one response before scheduling more; no alternate endpoint or credential bypass.
    tiles=[obtain(coords[0])]
    if len(coords)>1:
        with ThreadPoolExecutor(max_workers=1) as pool:tiles.extend(pool.map(obtain,coords[1:]))
    mosaic=Image.new('RGB',((x1-x0+1)*256,(y1-y0+1)*256))
    for (x,y),path,rec in tiles:
        with Image.open(path) as im:mosaic.paste(im.convert('RGB'),((x-x0)*256,(y-y0)*256))
    cropped=mosaic.crop((left-x0*256,top-y0*256,right-x0*256,bottom-y0*256))
    output.parent.mkdir(parents=True,exist_ok=True);cropped.save(output)
    west,north=inverse_pixel(left,top,zoom);east,south=inverse_pixel(right,bottom,zoom)
    meta={'provider':'Geospatial Information Authority of Japan (GSI)',
          'layer':'seamlessphoto','source_url':SOURCE_URL,'terms_url':TERMS_URL,
          'attribution':'Aerial imagery: GSI (edited)',
          'license':'GSI content terms / Public Data License 1.0; check layer-specific rights',
          'crs':'EPSG:3857','orientation':'north-up','requested_bbox':bbox,
          'bbox_south_west_north_east':[south,west,north,east],'zoom':zoom,
          'dimensions':list(cropped.size),'image_sha256':sha(output),
          'downloaded_utc':datetime.now(timezone.utc).isoformat(),
          'capture_date':'Not inferred from retrieval date; mosaic can contain multiple acquisition dates.',
          'tiles':[rec for pair,path,rec in tiles]}
    meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'cached':False,'path':str(output),'tiles':len(tiles),'dimensions':list(cropped.size)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bbox',nargs=4,type=float,required=True)
    p.add_argument('--out',required=True);p.add_argument('--user-agent',required=True)
    p.add_argument('--zoom',type=int,default=17)
    args=p.parse_args()
    print(json.dumps(fetch_gsi(args.bbox,args.out,args.user_agent,args.zoom),ensure_ascii=False))
