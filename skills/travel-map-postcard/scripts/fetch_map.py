"""Fetch a small, cached OSM vector extract; never upload a photograph."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import urllib.parse
import urllib.request


def fetch(bbox, output, endpoint, user_agent, poi_pattern=None, buildings=False):
    s, w, n, e = bbox
    if not (-80 <= s < n <= 80 and -180 <= w < e <= 180):
        raise ValueError('Use a non-wrapping WGS84 bbox south,west,north,east.')
    if (n-s) * (e-w) > .05 or max(n-s, e-w) > .5:
        raise ValueError('This helper only supports small local extracts; use a regional dataset for larger maps.')
    if not endpoint.startswith('https://'):
        raise ValueError('Use an HTTPS Overpass endpoint.')
    bounds = ','.join(map(str, bbox))
    selection = ('way[highway~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified|pedestrian|footway|path|steps)$"]'
                 '('+bounds+');way[natural~"^(coastline|water)$"]('+bounds+');'
                 'way[waterway~"^(river|stream|canal)$"]('+bounds+');'
                 'way[landuse=forest]('+bounds+');way[natural=wood]('+bounds+');'
                 'way[leisure=park]('+bounds+');')
    if poi_pattern:
        selection += 'nwr[~"^(name|name:en|name:ja|name:zh)$"~'+json.dumps(poi_pattern, ensure_ascii=False)+',i]('+bounds+');'
    if buildings:
        selection += 'way[building]('+bounds+');'
    query = '[out:json][timeout:35];('+selection+');out geom;'
    key = hashlib.sha256((endpoint+'\n'+query).encode()).hexdigest()
    output = Path(output)
    metadata_path = output.with_suffix('.source.json')
    if output.exists():
        if metadata_path.exists() and json.loads(metadata_path.read_text(encoding='utf-8'))['query_sha256'] == key:
            data = json.loads(output.read_text(encoding='utf-8'))
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            if hashlib.sha256(output.read_bytes()).hexdigest() != metadata['data_sha256']:
                raise ValueError('Cached map hash differs from its provenance; do not reuse it.')
            if data.get('remark') or not data.get('elements'):
                raise ValueError('Cached extract is incomplete or empty.')
            return {'cached': True, 'elements': len(data['elements']), 'path': str(output)}
        raise FileExistsError('Output exists with different provenance; choose a versioned file.')
    req = urllib.request.Request(endpoint, data=urllib.parse.urlencode({'data': query}).encode(),
                                 headers={'User-Agent': user_agent, 'Accept': 'application/json'})
    # One bounded request; failures do not trigger endpoint hopping or retry storms.
    with urllib.request.urlopen(req, timeout=55) as response:
        raw = response.read(24*1024*1024+1)
    if len(raw) > 24*1024*1024:
        raise ValueError('Extract is too large; narrow the bbox.')
    data = json.loads(raw)
    if data.get('remark') or not data.get('elements'):
        raise ValueError('Overpass returned incomplete or empty data: '+str(data.get('remark', 'no elements')))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    meta = {'provider': 'OpenStreetMap contributors', 'license': 'ODbL-1.0',
            'license_url': 'https://www.openstreetmap.org/copyright', 'endpoint': endpoint,
            'bbox_south_west_north_east': bbox, 'fetched_at': datetime.now(timezone.utc).isoformat(),
            'osm_base': data.get('osm3s', {}).get('timestamp_osm_base'),
            'query': query, 'query_sha256': key, 'data_sha256': hashlib.sha256(raw).hexdigest()}
    metadata_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'cached': False, 'elements': len(data['elements']), 'path': str(output)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bbox', nargs=4, type=float, required=True, metavar=('S','W','N','E'))
    p.add_argument('--out', required=True)
    p.add_argument('--endpoint', required=True, help='Explicit operator-approved Overpass HTTPS endpoint')
    p.add_argument('--user-agent', required=True, help='Application name/version and actual contact or project URL')
    p.add_argument('--poi-pattern', help='Optional regex for a few named landmarks in this bbox')
    p.add_argument('--buildings', action='store_true', help='Include real building footprints for sparse street layouts')
    a=p.parse_args()
    print(json.dumps(fetch(a.bbox,a.out,a.endpoint,a.user_agent,a.poi_pattern,a.buildings),ensure_ascii=False))
