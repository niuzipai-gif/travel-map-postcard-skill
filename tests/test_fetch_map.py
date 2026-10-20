import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fetch_map',ROOT/'skills/travel-map-postcard/scripts/fetch_map.py')
fm=importlib.util.module_from_spec(spec);spec.loader.exec_module(fm)

class Response:
    def __init__(self,data):self.data=json.dumps(data).encode()
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,*args):return self.data

class FetchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.out=Path(self.tmp.name)/'map.json'
    def fetch(self):return fm.fetch([35,139,35.01,139.01],self.out,'https://maps.example/api/interpreter','Test/1.0')
    def test_repeat_uses_cache_without_network(self):
        with patch.object(fm.urllib.request,'urlopen',return_value=Response({'elements':[{'id':1}]})) as network:
            self.assertFalse(self.fetch()['cached']);self.assertTrue(self.fetch()['cached'])
            self.assertEqual(network.call_count,1)
    def test_partial_extract_not_saved(self):
        with patch.object(fm.urllib.request,'urlopen',return_value=Response({'elements':[{'id':1}],'remark':'runtime timeout'})):
            with self.assertRaisesRegex(ValueError,'incomplete'):self.fetch()
        self.assertFalse(self.out.exists())
    def test_tampered_cache_rejected(self):
        with patch.object(fm.urllib.request,'urlopen',return_value=Response({'elements':[{'id':1}]})):
            self.fetch()
        self.out.write_text(json.dumps({'elements':[{'id':2}]}))
        with self.assertRaisesRegex(ValueError,'hash'):self.fetch()
    def test_large_extract_rejected_before_network(self):
        with patch.object(fm.urllib.request,'urlopen') as network:
            with self.assertRaisesRegex(ValueError,'small local'):fm.fetch([0,0,2,2],self.out,'https://maps.example/api/interpreter','Test/1.0')
            network.assert_not_called()

if __name__=='__main__':unittest.main()
