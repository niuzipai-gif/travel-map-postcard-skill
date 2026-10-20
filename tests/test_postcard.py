import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import random
from PIL import Image, ImageDraw, ImageStat

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('postcard',ROOT/'skills/travel-map-postcard/scripts/postcard.py')
pc=importlib.util.module_from_spec(spec);spec.loader.exec_module(pc)


class PostcardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.photo=self.root/'input.png'
        pixels=random.Random(7).randbytes(800*1000*3)
        Image.frombytes('RGB',(1000,800),pixels).save(self.photo)
        self.data={'elements':[{'type':'way','id':1,'tags':{'highway':'primary'},'geometry':[
            {'lat':35.01,'lon':139.005},{'lat':35.02,'lon':139.02},{'lat':35.03,'lon':139.035}]}]}
        self.map=self.root/'map.json';self.map.write_text(json.dumps(self.data),encoding='utf-8')
        self.source={'bbox_south_west_north_east':[35,139,35.04,139.04],
                     'data_sha256':pc.digest(self.map),'license':'ODbL-1.0'}
        self.map.with_suffix('.source.json').write_text(json.dumps(self.source),encoding='utf-8')
        self.cfg={'bbox':[35,139,35.04,139.04],'rect':[.08,.04,.7,.28],
                  'title':'TEST CITY','location':{'status':'verified_area','camera_status':'approximate','evidence':['synthetic fixture']},
                  'labels':[{'text':'Area · approx. area','lat':35.02,'lon':139.02,'role':'area','uncertainty_m':200,'evidence':'synthetic'}],
                  'protected_polygons':[[[0,.5],[1,.5],[1,1],[0,1]]]}
        self.config=self.root/'config.json';self.out=self.root/'result'

    def run_render(self):
        self.config.write_text(json.dumps(self.cfg),encoding='utf-8')
        return pc.render(self.photo,self.map,self.config,self.out)

    def test_exact_preservation_and_recomposition(self):
        before=pc.digest(self.photo);report=self.run_render()
        self.assertTrue(report['verification']['passed'])
        self.assertGreater(report['verification']['changed_pixel_fraction'],0)
        self.assertEqual(pc.digest(self.photo),before)
        self.assertEqual(report['verification']['outside_alpha_changed_pixels'],0)
        self.assertEqual(report['verification']['protected_changed_pixels'],0)

    def test_mask_actually_removes_map_pixels(self):
        self.cfg['protected_polygons']=[[[.35,.1],[.55,.1],[.55,.3],[.35,.3]]]
        self.run_render()
        with Image.open(self.out/'map-overlay.png') as im: a=im.getchannel('A')
        self.assertIsNone(a.crop((350,80,550,240)).getbbox())
        self.assertIsNotNone(a.getbbox())

    def test_unknown_location_blocks(self):
        self.cfg['location']['status']='unresolved'
        with self.assertRaisesRegex(ValueError,'Location'):self.run_render()

    def test_bay_boundary_is_not_a_coastline(self):
        data=copy.deepcopy(self.data)
        bay=copy.deepcopy(data['elements'][0]);bay['id']=2;bay['tags']={'natural':'bay','name':'Large named bay'}
        data['elements'].append(bay)
        self.assertEqual(len(list(pc.geometry_paths(data))),1)

    def test_fake_contour_mode_blocks(self):
        self.cfg['mode']='invented_contours'
        with self.assertRaisesRegex(ValueError,'contour'):self.run_render()

    def test_exact_pin_without_camera_evidence_blocks(self):
        self.cfg['labels'][0]['role']='capture'
        with self.assertRaisesRegex(ValueError,'exact camera'):self.run_render()
        self.cfg['location']['camera_status']='exact'
        with self.assertRaisesRegex(ValueError,'camera evidence'):self.run_render()

    def test_approximation_must_be_visible(self):
        self.cfg['labels'][0]['text']='My exact viewpoint'
        with self.assertRaisesRegex(ValueError,'approx'):self.run_render()

    def test_corrupted_map_provenance_blocks(self):
        self.map.write_text(json.dumps({'elements':[]}),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'hash'):self.run_render()

    def test_clipped_label_blocks(self):
        self.cfg['labels'][0]['offset']=[2,0]
        with self.assertRaisesRegex(ValueError,'clipped'):self.run_render()

    def test_location_marker_cannot_hide_inside_its_caption(self):
        self.cfg['labels'][0]['offset']=[0,-.01]
        with self.assertRaisesRegex(ValueError,'marker overlaps'):self.run_render()

    def test_caption_cannot_be_silently_cut_by_foreground_mask(self):
        self.cfg['check_label_visibility']=True
        self.cfg['protected_polygons']=[[[0,0],[1,0],[1,.4],[0,.4]]]
        with self.assertRaisesRegex(ValueError,'protected photo subject'):self.run_render()

    def test_feature_emphasis_requires_real_sourced_geometry(self):
        self.cfg['highlight_features']=[{'type':'way','id':998,'evidence':'not in extract'}]
        with self.assertRaisesRegex(ValueError,'sourced map extract'):self.run_render()

    def test_source_orientation_normalized(self):
        raw=Image.open(self.photo);exif=Image.Exif();exif[274]=6
        self.photo=self.root/'rotated.jpg';raw.save(self.photo,exif=exif)
        report=self.run_render()
        self.assertEqual(report['dimensions'],[800,1000])
        self.assertTrue(report['verification']['passed'])
        with Image.open(self.out/'postcard.png') as im:self.assertFalse(im.getexif())

    def test_previous_result_not_overwritten(self):
        self.run_render();old=pc.digest(self.out/'postcard.png')
        with self.assertRaises(FileExistsError):self.run_render()
        self.assertEqual(pc.digest(self.out/'postcard.png'),old)

    def test_pixel_tampering_detected(self):
        self.run_render()
        path=self.out/'postcard.png'
        with Image.open(path) as im: modified=im.copy()
        p=modified.getpixel((1,799));modified.putpixel((1,799),tuple(255-v for v in p));modified.save(path)
        with self.assertRaisesRegex(ValueError,'preservation failed'):pc.verify(self.photo,self.out)

    def test_projection_north_up_equal_scale(self):
        project,_=pc.projection([35,139,35.04,139.04],600,300)
        west=project(139,35.02);east=project(139.04,35.02)
        north=project(139.02,35.04);south=project(139.02,35)
        self.assertLess(west[0],east[0]);self.assertLess(north[1],south[1])
        px_per_rad=(east[0]-west[0])/(pc.mercator(139.04,35.02)[0]-pc.mercator(139,35.02)[0])
        py_per_rad=(south[1]-north[1])/(pc.mercator(139.02,35.04)[1]-pc.mercator(139.02,35)[1])
        self.assertAlmostEqual(px_per_rad,py_per_rad,places=5)

    def test_cover_fills_sky_without_stretching_coordinates(self):
        point,scale=pc.projection([35,139,35.04,139.04],900,200,'cover')
        west=point(139,35.02);east=point(139.04,35.02)
        north=point(139.02,35.04);south=point(139.02,35)
        self.assertAlmostEqual(east[0]-west[0],900)
        self.assertGreater(south[1]-north[1],200)
        xscale=(east[0]-west[0])/(pc.mercator(139.04,35.02)[0]-pc.mercator(139,35.02)[0])
        yscale=(south[1]-north[1])/(pc.mercator(139.02,35.04)[1]-pc.mercator(139.02,35)[1])
        self.assertAlmostEqual(xscale,yscale,places=5)

    def test_existing_bright_clouds_attenuate_map_not_photo(self):
        photo=Image.new('RGB',(300,200),(60,60,60))
        photo.paste((235,235,235),(150,0,300,200))
        before=photo.tobytes()
        mask=pc.atmospheric_mask(photo,photo.size,
            {'cloud_strength':.8,'cloud_luma':[100,230],'fade_start':.8})
        self.assertGreater(mask.getpixel((30,80)),mask.getpixel((270,80)))
        self.assertEqual(mask.getpixel((30,199)),0)
        self.assertEqual(photo.tobytes(),before)

    def test_depth_composite_preserves_foreground_and_base(self):
        self.cfg['projection_fit']='cover'
        self.cfg['clear_text_backdrop']=True
        self.cfg['title_tracking']=.002
        self.cfg['glow']={'map':{'radius':2,'opacity':.5},'text':{'radius':3,'opacity':.4,'shadow_opacity':.3}}
        self.cfg['labels'][0].update(text='Area',note='Approx. photo area',emphasis=True,leader=True)
        self.cfg['highlight_features']=[{'type':'way','id':1,'evidence':'synthetic fixture'}]
        self.cfg['rect']=[0,0,1,.55]
        self.cfg['layout_exception_reason']='Test filling a large sky'
        self.cfg['atmosphere']={'cloud_strength':.7,'cloud_luma':[100,220],
                                'fade_start':.75,'distant_alpha':.5,'distant_blur_px':.5}
        self.cfg['protected_polygons']=[[[.44,.08],[.56,.08],[.65,1],[.35,1]]]
        report=self.run_render()
        self.assertTrue(report['verification']['passed'])
        self.assertEqual(report['verification']['outside_alpha_changed_pixels'],0)
        self.assertEqual(report['verification']['protected_changed_pixels'],0)

    def aerial_fixture(self):
        path=self.root/'aerial.png'
        Image.new('RGB',(100,100),(33,99,173)).save(path)
        meta={'image_sha256':pc.digest(path),'crs':'EPSG:3857','orientation':'north-up',
              'bbox_south_west_north_east':[35.01,139.01,35.03,139.03],
              'source_url':'https://example.com/synthetic-aerial','terms_url':'https://example.com/synthetic-terms',
              'attribution':'Synthetic test imagery'}
        path.with_suffix('.source.json').write_text(json.dumps(meta),encoding='utf-8')
        entry={'path':str(path),'editorial_reveal_acknowledged':True,
               'reveal_polygon':[[0,0],[1,0],[1,1],[0,1]],'feather_fraction':0,'opacity':1}
        return path,entry

    def test_aerial_is_at_its_geographic_position_not_arbitrary_pixel_rect(self):
        path,entry=self.aerial_fixture()
        point,_=pc.projection([35,139,35.04,139.04],1000,800)
        layer,records=pc.imagery_layer([entry],self.config,self.data,point,(1000,800))
        x,y=point(139.02,35.02)
        self.assertEqual(layer.getpixel((round(x),round(y))),(33,99,173,255))
        ox,oy=point(139.002,35.002)
        self.assertEqual(layer.getpixel((round(ox),round(oy)))[3],0)
        self.assertEqual(records[0]['metadata']['image_sha256'],pc.digest(path))

    def test_aerial_tampering_refused(self):
        path,entry=self.aerial_fixture()
        Image.new('RGB',(100,100),(200,0,0)).save(path)
        self.cfg['imagery']=[entry]
        with self.assertRaisesRegex(ValueError,'imagery hash'):self.run_render()

    def test_background_relief_preserves_geography_and_adapts_to_local_light(self):
        patch=Image.new('RGBA',(120,100),(18,64,22,255))
        draw=ImageDraw.Draw(patch)
        draw.rectangle((60,0,119,99),fill=(205,206,183,255))
        background=Image.new('RGB',patch.size,(155,205,235))
        original=patch.tobytes();base=background.tobytes()
        settings={'mode':'background_relief','contrast':.8,'detail_weight':.4,'color_retention':0}
        graded=pc.harmonize_imagery(patch,background,settings)
        # Actual bright/dark ground structures stay in their original positions, with cool sky chroma.
        left=graded.getpixel((20,50));right=graded.getpixel((100,50))
        self.assertLess(left[0],right[0]);self.assertLess(left[1],right[1])
        self.assertLess(left[0],left[1]);self.assertLess(left[1],left[2])
        raw_distance=sum(abs(a-b) for a,b in zip(patch.getpixel((20,50))[:3],(155,205,235)))
        new_distance=sum(abs(a-b) for a,b in zip(left[:3],(155,205,235)))
        self.assertLess(new_distance,raw_distance*.5)
        self.assertEqual(patch.tobytes(),original);self.assertEqual(background.tobytes(),base)
        dark=pc.harmonize_imagery(patch,Image.new('RGB',patch.size,(35,55,75)),settings)
        self.assertLess(ImageStat.Stat(dark.convert('L')).mean[0],ImageStat.Stat(graded.convert('L')).mean[0])

    def test_harmonized_aerial_retains_exact_composition_and_protection(self):
        path,entry=self.aerial_fixture()
        entry['harmonize']={'mode':'background_relief','contrast':.7}
        self.cfg['imagery']=[entry]
        report=self.run_render()
        self.assertTrue(report['verification']['passed'])
        self.assertEqual(report['aerial_imagery'][0]['metadata']['image_sha256'],pc.digest(path))
        self.assertEqual(report['aerial_imagery'][0]['processing']['mode'],'background_relief')

    def test_background_harmonization_requires_the_aligned_photo_crop(self):
        patch=Image.new('RGBA',(10,10),(30,70,30,255))
        with self.assertRaisesRegex(ValueError,'aligned original-photo'):
            pc.harmonize_imagery(patch,None,{'mode':'background_relief'})

    def test_local_script_title_with_english_subtitle(self):
        try:face=pc.text_font(44,'東京',language='ja')
        except FileNotFoundError:self.skipTest('No local Japanese font; provide one for the live exercise.')
        self.cfg.update(title='東京',subtitle='TOKYO',title_language='ja',subtitle_language='en',title_size=.04)
        report=self.run_render()
        self.assertEqual(report['typography']['title_language'],'ja')
        self.assertEqual(report['typography']['title_font'],str(face.path))
        self.assertTrue(report['verification']['passed'])

    def test_korean_title_uses_hangul_capable_local_font(self):
        try:face=pc.text_font(44,'서울',language='ko')
        except FileNotFoundError:self.skipTest('No local Korean font installed.')
        self.assertNotEqual(bytes(face.getmask('서')),bytes(face.getmask('\U0010ffff')))
        self.assertNotEqual(bytes(face.getmask('울')),bytes(face.getmask('\U0010ffff')))

    def test_incompatible_font_cannot_silently_print_missing_glyphs(self):
        latin=pc.font(44)
        missing=bytes(latin.getmask('\U0010ffff'))
        if bytes(latin.getmask('東'))!=missing:self.skipTest('Default font includes Japanese glyphs.')
        with self.assertRaisesRegex(FileNotFoundError,'script-capable'):
            pc.text_font(44,'東京',explicit=latin.path,language='ja')

    def test_adaptive_marker_opacity_changes_alpha_only_against_its_background(self):
        patch=Image.new('RGBA',(80,80),(180,70,25,220));original=patch.tobytes()
        settings={'min':.2,'max':.8,'contrast_budget':.18}
        near,record=pc.marker_opacity(patch,Image.new('RGB',patch.size,(170,85,40)),settings)
        far,_=pc.marker_opacity(patch,Image.new('RGB',patch.size,(30,220,245)),settings)
        self.assertGreater(near.getpixel((40,40))[3],far.getpixel((40,40))[3])
        self.assertEqual(near.convert('RGB').tobytes(),patch.convert('RGB').tobytes())
        self.assertEqual(far.convert('RGB').tobytes(),patch.convert('RGB').tobytes())
        self.assertEqual(patch.tobytes(),original)
        self.assertEqual(record['mode'],'local_rgb_contrast')

    def test_emphasis_opacity_does_not_change_the_vector_map_layer(self):
        path,entry=self.aerial_fixture()
        entry['adaptive_opacity']={'min':.2,'max':.3,'contrast_budget':.18}
        self.cfg.update(imagery=[entry],quiet_under_imagery=False)
        self.run_render()
        cartography=pc.digest(self.out/'cartography-overlay.png')
        emphasis=pc.digest(self.out/'aerial-overlay.png')
        self.out=self.root/'second-result'
        self.cfg['imagery'][0]['adaptive_opacity']={'min':.6,'max':.8,'contrast_budget':.3}
        result=self.run_render()
        self.assertEqual(pc.digest(self.out/'cartography-overlay.png'),cartography)
        self.assertNotEqual(pc.digest(self.out/'aerial-overlay.png'),emphasis)
        self.assertTrue(result['verification']['passed'])

    def photo_symbol_fixture(self):
        path=self.root/'photo-symbol.png'
        image=Image.new('RGBA',(40,100));ImageDraw.Draw(image).polygon([(20,0),(35,98),(5,98)],fill=(240,110,35,255));image.save(path)
        meta={'image_sha256':pc.digest(path),'source_url':'https://example.com/synthetic-photo',
            'terms_url':'https://example.com/synthetic-terms','attribution':'Synthetic photo fixture',
            'author':'Test fixture','license':'Synthetic test only'}
        path.with_suffix('.source.json').write_text(json.dumps(meta),encoding='utf-8')
        entry={'path':str(path),'lat':35.02,'lon':139.02,'evidence':'Synthetic landmark anchor',
            'not_to_scale_acknowledged':True,'height_fraction':.07,
            'adaptive_opacity':{'min':.3,'max':.6,'contrast_budget':.2}}
        return path,entry

    def test_real_photo_symbol_uses_landmark_anchor_and_preserves_original(self):
        path,entry=self.photo_symbol_fixture()
        self.cfg['photo_markers']=[entry]
        result=self.run_render()
        symbol=result['photo_markers'][0]
        self.assertEqual(symbol['landmark_anchor']['lat'],35.02)
        self.assertIn('not to map scale',symbol['representation'])
        self.assertEqual(symbol['metadata']['image_sha256'],pc.digest(path))
        self.assertTrue(result['verification']['passed'])
        with Image.open(self.out/'photo-markers-overlay.png') as im:self.assertIsNotNone(im.getchannel('A').getbbox())

    def test_photo_symbol_refuses_tampering_and_missing_anchor_evidence(self):
        path,entry=self.photo_symbol_fixture()
        self.cfg['photo_markers']=[entry]
        Image.new('RGBA',(40,100),(10,20,30,70)).save(path)
        with self.assertRaisesRegex(ValueError,'Photo marker hash'):self.run_render()
        entry['evidence']=''
        with self.assertRaisesRegex(ValueError,'Photo marker requires'):self.run_render()

    def test_glow_follows_selected_light_corner_without_moving_strokes(self):
        layer=Image.new('RGBA',(200,200))
        draw=ImageDraw.Draw(layer)
        draw.rectangle((25,165,35,175),fill=(40,70,85,180))
        draw.rectangle((165,25,175,35),fill=(40,70,85,180))
        before=layer.tobytes()
        lit=pc.glow_layer(layer,{'ink':[245,250,255],'radius':2,'opacity':.5,
            'light_origin':[1,0],'light_floor':.1,'highlight_opacity':.5})
        self.assertGreater(lit.getpixel((170,30))[0],lit.getpixel((30,170))[0])
        self.assertGreater(lit.getpixel((177,30))[3],lit.getpixel((37,170))[3])
        self.assertEqual(layer.tobytes(),before)
        self.assertEqual(lit.getpixel((0,0))[3],0)
        self.assertEqual(lit.getpixel((199,199))[3],0)

    def test_emphasis_glow_only_lights_sourced_feature_and_preserves_photo(self):
        self.cfg['labels']=[]
        self.cfg['title_xy']=[.01,.01]
        self.cfg['highlight_features']=[{'type':'way','id':1,'ink':[250,245,220],
            'width':1.5,'fill_opacity':0,'evidence':'Synthetic sourced feature'}]
        self.run_render()
        with Image.open(self.out/'map-overlay.png') as im:plain=im.copy()
        self.out=self.root/'emphasis-glow'
        self.cfg['glow']={'emphasis':{'ink':[255,250,230],'radius':2,'opacity':.7}}
        report=self.run_render()
        self.assertTrue(report['verification']['passed'])
        with Image.open(self.out/'map-overlay.png') as lit:
            # The sourced diagonal is well below the title and above the protected photo.
            self.assertNotEqual(plain.crop((180,80,650,220)).tobytes(),
                                lit.crop((180,80,650,220)).tobytes())
            self.assertEqual(plain.crop((80,35,210,65)).tobytes(),
                             lit.crop((80,35,210,65)).tobytes())


if __name__=='__main__':unittest.main()
