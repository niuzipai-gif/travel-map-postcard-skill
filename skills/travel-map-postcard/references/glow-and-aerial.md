# Subtle glow and real aerial cores

This is an optional art direction for references combining luminous cartography with a realistic landmark/site core. Keep the full original travel photograph as the separate base. Do not use a generated aerial image as evidence of actual geography.

## Background compatibility comes first

Inspect the actual sky/sea behind the intended overlay. Choose ink hue, lightness and glow against that region, not against a fixed template. Pale blue overcast light often works with cool blue-gray ink; warm ivory can fit a dark or warm sky. Do not give every line a dark shadow: on a bright sky it can become a beveled technical drawing. Slight glow is a secondary edge effect, not the map's palette.

Check real aerial cores at whole-photo scale. A deep green/black satellite patch can look pasted onto a pale blue sky even with a feathered edge. Adjust **only the imagery layer** to the local background light and chroma, retaining its actual terrain/structure positions. Do not solve a mismatch by recoloring the travel photo. Preserve identifiable real detail rather than making the core uniformly invisible. If no treatment produces a coherent result, report that limitation instead of calling the composition accepted.

For an emphasis-alpha-only revision, use **adaptive opacity of the important photo marker only**, preserving its photographic RGB. Keep the surrounding map opacity, category styles, lettering and glow unchanged. A tower should be recognizable as the tower, not just a pale aerial block of its surrounding district. Use a genuine photographic cutout when that communicates the landmark better.

Choose the source lighting before tuning alpha. A brightly illuminated night tower may remain a distracting orange sticker on a pale sky even after fading; a sourced daylight view can retain a readable red/white structure with less contrast. Check the silhouette, size and actual base anchor together. Any small photographic context at its foot is part of a not-to-scale symbol, not georeferenced surrounding buildings.

For aerial hills, inspect the grass/trails separately from the dark forest around them. An editorial alpha mask may make peripheral forest lighter while retaining the original RGB and georeferencing. Do not use a hard brightness key: it can punch sky-colored holes through trees within the slope and erase natural texture. Smooth alpha changes over a broader neighborhood, inspect at phone width and full resolution, and keep the result labeled as an edited reveal. This is a composition-specific option, not an automatic grass detector or a site-boundary claim.

## Independent emphasis opacity

Both an `imagery` entry and a `photo_markers` entry accept:

```json
"adaptive_opacity": {"min":0.27, "max":0.64, "contrast_budget":0.25}
```

Values are opacity multipliers, so a higher value is more opaque. The helper compares emphasis source RGB with the aligned original-photo background, smoothly lowering alpha where the mismatch is stronger and bounding it so the core remains visible. `contrast_budget` limits normalized local RGB difference; it is a tuning parameter, not an aesthetic score. Per-entry `opacity` multiplies this map. Source RGB does not change. Soft reveal/cutout masks provide edge transitions. Inspect and tune landmarks independently; one range need not fit a bright tower and dark green hill.

Set composition `quiet_under_imagery: false` for alpha-only revisions. This disables the legacy coupling that reduced vector opacity according to aerial alpha. Do not adjust global `line_opacity`, vector styles or the entire overlay to blend one core. `cartography-overlay.png`, `aerial-overlay.png` and `photo-markers-overlay.png` are independent full-canvas layers. Cartography should remain byte-identical between emphasis-alpha trials when no captions/attribution change.

`opacity_adaptation` in the manifest records the mode, range, contrast budget and measured mean multiplier. This describes actual processing, not a guarantee of visual quality.

## Photographic landmark symbols

`photo_markers` are transparent photographic cutouts with their base/anchor at a verified landmark coordinate. They are deliberately not-to-scale symbols, unlike georeferenced orthophotos. Preserve their aspect ratio; do not present them as aerial imagery, building footprints or the photographer's GPS.

```json
"photo_markers": [{
  "path":"/absolute/path/tower-cutout.png",
  "lat":35.65856, "lon":139.74544,
  "evidence":"Verified landmark coordinate reference; not camera evidence",
  "not_to_scale_acknowledged":true,
  "height_fraction":0.17, "anchor_fraction":[0.5,0.99],
  "opacity":1,
  "adaptive_opacity":{"min":0.4,"max":0.78,"contrast_budget":0.29}
}]
```

`height_fraction` uses the photo's short edge (at most 0.35). The adjacent `.source.json` must contain the cutout `image_sha256`, actual `source_url`, `author`, `license`, `terms_url` and `attribution`. Keep the original photo/derivative hash chain and editing notice. Do not reconstruct obscured parts or mislabel generated art as real photography. Credits remain visible; retain source and license in the manifest. Do not bundle third-party photos in the MIT skill. Follow the photo's own license for its derivative.

## Glow

`glow.map` and `glow.text` each accept `ink`, `radius`, `opacity`, `shadow_ink`, `shadow_radius`, and `shadow_opacity`. Radius is relative to a 1300-pixel photo short edge. Typical map radii are 1.5–2.5px and text radii 2–3px, with moderate opacity. A broader, weaker bloom is added under the near halo. Keep the original fine stroke sharp. Avoid neon tubes, large bright clouds or a full-photo lighting effect.

Use `highlight_features` to select verified feature IDs from the existing map extract, and `glow.emphasis` to light only those strokes. It accepts the same glow settings. Set `fill_opacity: 0` for unfilled core outlines. For example, select physical shoreline segments around a harbor or the photographed building footprint and nearby core roads; do not brighten a named-waterbody boundary as if it were a real shore. A higher core brightness should remain clearly distinct from the surrounding streets without making the entire map equally luminous. Both ordinary and emphasized lines respect the title/subtitle/callout clearance masks.

Set shadow to zero initially. If needed, use very little after testing a compatible ink color. Check the photograph at phone width; glow must not wash out all detail, create a raised edge or turn a quiet map into the main subject.

When the user prefers unfilled cartography, remove `imagery`, `photo_markers` and geographic color fills instead of retaining a nearly invisible colored core. Keep the sourced lines and place labels.

For a visible light direction, `glow.map` optionally accepts `light_origin: [1, 0]` (upper right), `light_floor: 0.16` and `highlight_opacity: 0.48`. The normalized origin gives the broad direction of the halo's strength; the floor controls the far-side brightness. The optional highlight adds the glow ink to the existing stroke without moving geometry. Infer the direction from the actual photograph and record that it is visual art direction, not a measured sun position. Leave these fields absent to preserve the prior uniform glow. Adjust only the requested map/text layers; the underlying photograph is unchanged.

Glow is calculated on the map/text layers, then the photo subject protection mask is applied. Its spill may occupy additional sky pixels; preservation is still measured against the actual final RGBA alpha, with zero changes in protected areas and outside that alpha.

## Real imagery

`scripts/fetch_imagery.py` supports a bounded GSI `seamlessphoto` aerial patch in Japan, zoom 16–18, at most 36 unique tiles per patch, with a local hash-checked cache. It records each source URL/hash, the stitched image hash, north-up EPSG:3857 extent, provider, content terms and retrieval time. One request is checked before further requests. HTTP denials are not retried or bypassed. Transient SSL EOF/timeouts receive at most two same-endpoint retries; completed tiles are reused.

Official layer information: https://maps.gsi.go.jp/help/use.html

Official content terms: https://web1.gsi.go.jp/kikakuchousei/kikakuchousei40182.html

GSI terms require source attribution and identification of editing. Check the current layer-specific rights. Acquisition date is not inferred from download date; a mosaic may contain imagery from different dates. Outside Japan, use imagery already obtained under an appropriate license with verifiable georeferencing, or add an authorized provider integration. The helper does not provide global high-resolution imagery.

Example (coordinates illustrate a public landmark, not a photographer's GPS):

```bash
python scripts/fetch_imagery.py --bbox 35.6545 139.7404 35.6625 139.7504 --out /path/to/tokyo-tower.png --user-agent 'YourProject/1.0 (real project URL or contact)'
```

## Compositing

The `imagery` list in the composition config refers to an image and its adjacent `.source.json`. It requires matching `image_sha256`, `crs: EPSG:3857`, `orientation: north-up`, `bbox_south_west_north_east`, `source_url`, `terms_url` and `attribution`. Images with missing or mismatched metadata are refused.

```json
{
  "imagery": [{
    "path": "/path/to/tokyo-tower.png",
    "editorial_reveal_acknowledged": true,
    "reveal_polygon": [[0.3,0.06],[0.59,0.03],[0.82,0.18],[0.9,0.4],[0.78,0.72],[0.57,0.91],[0.27,0.83],[0.07,0.64],[0.08,0.32]],
    "feather_fraction": 0.045,
    "opacity": 0.97
  }]
}
```

The source image is placed at its real map extent using the same projection as the vectors. Do not independently stretch, mirror, move or enlarge it while pretending it still has the original geographic registration. `projection_align` can choose which part of an equally scaled cover view remains visible (default `[0.5,0.5]`; `[0.5,0]` aligns the north edge). Recheck all labels and foreground masks after this change.

For a raw-color mismatch, an imagery entry may include:

```json
"harmonize": {
  "mode": "background_relief",
  "contrast": 0.8,
  "detail_weight": 0.4,
  "color_retention": 0.04
}
```

All three values are in `[0,1]`. The compositor uses true aerial luminance and spatial detail as a neutral-centered soft-light texture over the **geographically aligned original-photo crop**, with limited original imagery chroma. This follows local background light and hue without introducing a separate dark island. It is an edited photographic texture, not untouched natural-color satellite imagery. More `detail_weight` reduces broad tonal blocks in favor of fine detail; `contrast` and entry `opacity` control visibility. Test both pale and dark backgrounds. These values are not universal defaults for all photos.

The manifest records the processing settings beside the unchanged source-image hash and geographic box. The original aerial file is untouched; no new coastline or structure is invented. The photo stays a separate unchanged base, and the same protected-subject and exact-recomposition checks apply.

The normalized `reveal_polygon` is an editorial alpha mask in the source image, not an assertion of coastline, property or park boundaries. Feather it without adding a false geographic outline. Actual shore outlines need sourced geometry. Quiet the vector ink under imagery so the true texture remains visible; leave surrounding cartography continuous rather than adding a rectangular map card.

The compositor visibly adds imagery attribution and its source URL. Retain these, the vector attribution, metadata and hashes. Imagery rights remain separate from the skill's software license. Do not bundle downloaded imagery, user photographs, or third-party examples in the public skill repository by default.
