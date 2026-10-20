# Real map data

Prefer licensed vector geometry over screenshots. OSM roads, coastline, water and trails support editorial linework. A reference map being visible online does not automatically permit redistributing or tracing it.

`fetch_map.py` makes one small request to an explicitly selected HTTPS Overpass endpoint, records query, bbox, timestamps, URL and SHA-256, and reuses identical cached requests. It rejects empty or partial data and never silently hops endpoints. Geometry uses uniform Web Mercator scale, north up. Polar and antimeridian maps are unsupported.

For a few interactive user-requested extracts, an operator may deliberately choose `https://overpass-api.de/api/interpreter` after reviewing its [usage guidance](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html). Run requests sequentially. On 429/timeout/overload, retain evidence and retry later or deliberately choose a configured alternative; do not rotate to evade limits. Public instances are not a guaranteed backend for a widely used hosted service. Use your own instance, a contracted provider or licensed cached regional extracts for a production product.

Do not add public Nominatim as a generic automatic geocoder. Its [usage policy](https://operations.osmfoundation.org/policies/nominatim/) requires an informed developer decision, identifiable requests, caching, strict rate limits and other restrictions. This skill does not call Nominatim. The agent uses vision/research for location and inspected map features for coordinates. POI coordinates are not photo GPS.

## Modes

- `city`: street hierarchy and water; omit dense footways.
- `coast`: shores, water and sparse roads. Coast segments must not be arbitrarily closed into islands.
- `trail`: real paths, roads, streams and forest outlines. Forest outlines are not contours.
- True contours need documented DEM, CRS, units, interval and license. No DEM is bundled; use trail mode when unavailable and say so.

An extract bbox is a fetch window, not a location boundary. `--poi-pattern` finds named features inside it. Inspect tags and coordinates before using them. A cached extract is a dated snapshot, not a current trail-access claim.

## Attribution and QA

OSM data is [ODbL](https://www.openstreetmap.org/copyright). Keep `© OpenStreetMap contributors` and `openstreetmap.org/copyright` legible beside the map, and source/license links in the record. Review data-license obligations before distributing extracted databases. The software license does not relicense photos, fonts or map data.

Check coastline shape, street relationships and correct-shore label placement. No invented routes, contours, precise coordinates or scale bars. The bundled compositor omits a scale bar and decorative compass. Geometry/data provenance and visual quality need separate checks.
