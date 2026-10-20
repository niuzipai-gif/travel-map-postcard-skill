import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fetch_imagery',ROOT/'skills/travel-map-postcard/scripts/fetch_imagery.py')
fi=importlib.util.module_from_spec(spec);spec.loader.exec_module(fi)


class ImageryFetchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.output=Path(self.tmp.name)/'aerial.png'
        self.bbox=[35.6545,139.7404,35.6625,139.7504]

    def test_large_or_unsupported_extract_does_not_touch_network(self):
        with patch.object(fi.urllib.request,'urlopen') as network:
            with self.assertRaises(ValueError):fi.fetch_gsi([22.1,113.5,22.2,113.6],self.output,'SyntheticTest/1.0')
            with self.assertRaises(ValueError):fi.fetch_gsi([35.60,139.7,35.69,139.79],self.output,'SyntheticTest/1.0')
            network.assert_not_called()

    def test_http_denial_is_not_retried_or_bypassed(self):
        error=urllib.error.HTTPError('https://example.com',403,'Forbidden',{},None)
        with patch.object(fi.urllib.request,'urlopen',side_effect=error) as network:
            with self.assertRaises(urllib.error.HTTPError):fi.fetch_gsi(self.bbox,self.output,'SyntheticTest/1.0')
            self.assertEqual(network.call_count,1)
            self.assertFalse(self.output.exists())

    def test_cache_reuse_and_tamper_rejection(self):
        Image.new('RGB',(32,32),(20,80,130)).save(self.output)
        metadata={'requested_bbox':self.bbox,'zoom':17,'image_sha256':fi.sha(self.output),'tiles':[{'synthetic':True}]}
        self.output.with_suffix('.source.json').write_text(json.dumps(metadata),encoding='utf-8')
        with patch.object(fi.urllib.request,'urlopen') as network:
            result=fi.fetch_gsi(self.bbox,self.output,'SyntheticTest/1.0')
            self.assertTrue(result['cached']);network.assert_not_called()
            Image.new('RGB',(32,32),(220,0,0)).save(self.output)
            with self.assertRaisesRegex(ValueError,'hash differ'):fi.fetch_gsi(self.bbox,self.output,'SyntheticTest/1.0')
            network.assert_not_called()


if __name__=='__main__':unittest.main()
