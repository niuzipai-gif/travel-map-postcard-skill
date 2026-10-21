# UTF-8 JSON configuration

The agent writes this after inspecting and researching the photo. The helper itself is not a vision model.

```json
{
  "title": "東京",
  "subtitle": "日本",
  "title_language": "ja",
  "subtitle_language": "ja",
  "mode": "city",
  "bbox": [35.0, 139.0, 35.04, 139.04],
  "rect": [0.06, 0.04, 0.70, 0.28],
  "projection_fit": "cover",
  "ink": [231, 225, 208],
  "line_opacity": 0.46,
  "text_opacity": 0.85,
  "title_size": 0.024,
  "title_xy": [0.08, 0.05],
  "credit_xy": [0.08, 0.90],
  "atmosphere": {
    "cloud_strength": 0.65,
    "cloud_luma": [160, 230],
    "fade_start": 0.70,
    "distant_alpha": 0.70,
    "distant_blur_px": 0.50
  },
  "location": {
    "status": "verified_area",
    "visible_subject": "Researched landmark",
    "capture_area": "Researched area",
    "camera_status": "approximate",
    "evidence": [{"url": "https://official.example/place", "supports": "Area identification", "does_not_prove": "Exact camera"}]
  },
  "labels": [{
    "text": "撮影エリア（目安）",
    "language": "ja",
    "lat": 35.02, "lon": 139.02,
    "role": "area", "uncertainty_m": 400,
    "offset": [0.025, -0.025],
    "evidence": "Verified map feature URL/id; region anchor, not camera GPS"
  }],
  "protected_polygons": [[[0.0,0.55],[1.0,0.55],[1.0,1.0],[0.0,1.0]]]
}
```

Example coordinates are illustrative, not an actual photo location. The title must match the researched real place. `bbox`: south,west,north,east. `rect`: normalized x,y,width,height. `title_xy`, `credit_xy` and label `offset` use the map rectangle; polygons use the whole photo. Ink is RGB bytes: choose against the actual background, such as ivory on dark sky or muted blue-gray on pale sky. These are not fixed per-country palettes.

Layout fraction is width × height, not the count of nontransparent pixels. Record both separately. If filling the available sky requires a larger frame, or avoiding subjects requires a smaller one, add `layout_exception_reason`. Do not enforce 15–25% at the cost of an isolated miniature map. Default title font is 2.4% of the photo short edge; keep it small. `label_size` defaults to 1.4%. Labels and credits need visual checks after protection masks are applied.

`projection_fit: cover` scales uniformly to fill the frame and clips peripheral geometry; choose the bbox so the useful feature and labels remain visible. `contain` is supported for explicit overview maps, but do not use it to squeeze a portrait-shaped map into a wide sky. Neither mode stretches coordinates. Edges now bleed out of the frame; the old elliptical vignette is removed.

`atmosphere` changes only map alpha and map focus, never the photo. `cloud_luma` is a pair of actual photo-luminance thresholds; bright existing clouds attenuate the ink by up to `cloud_strength`. Tune these against the original photograph (night skies need lower thresholds). `distant_alpha` and `distant_blur_px` make upper linework quieter; `fade_start` begins a smooth fade toward the bottom. This suggests spatial depth through overlay treatment; it does not change the original optical depth of field. The masks cannot automatically identify buildings: trace `protected_polygons` around their real silhouettes, not a large generic box.

Use roughly 2–4 labels. `area`: red point, recorded estimated uncertainty radius, mandatory visible approximation wording in the text or note: `approx.`, Japanese `目安` / `おおよそ`, or Korean `대략`. A radius is not a camera-coordinate measurement. Set `show_uncertainty_ring: true` only if a visible range circle helps; default false. `landmark`: quiet neutral dot, never a camera. `capture`: exact red pin, only with camera evidence. No more than one red marker. Geographical labels require coordinate provenance. `protected_polygons` set alpha to zero over people, animals and landmarks. Use `fetch_map.py --buildings` to include real building footprints when street lines alone look too sparse.

## Outputs

- `photo-base.png`: EXIF-oriented decoded source; local editable layer.
- `map-overlay.png`: full-canvas transparent RGBA map and annotations.
- With real-photo emphasis: separate `cartography-overlay.png`, `aerial-overlay.png` and `photo-markers-overlay.png` for map/annotations, georeferenced aerial texture and photographic landmark symbols.
- `protected-mask.png`: white means protected.
- `postcard.png`: lossless composition at original displayed dimensions.
- `composition.json`, `manifest.json`: layout, sources, hashes, pixel checks.

Input ICC is retained when present. Output PNGs omit EXIF, and sources are not overwritten. Verification compares decoded, EXIF-oriented source pixels, not JPEG file bytes: zero changes outside alpha, zero changes in protected areas, exact recomposition equality. A JPEG export cannot preserve this exact-pixel guarantee; retain the PNG master. No whole-photo paper texture is added because it would change original pixels.

Inspect at whole-image scale and 100% map detail. The map should occupy a coherent sky/sea region, with deliberate edge bleed and foreground occlusion where appropriate, not float in an oval in the middle of it. Check for clipped/colliding labels, lost credits, wrong place, excessive contrast, covered subjects or visible rectangle. Automated pixel checks do not prove geographic identity or visual quality.

## Core and visual hierarchy

Choose a core that matches the photographed subject. A generic neighborhood label alone is insufficient when a recognizable landmark is present. Use three levels: place title/core annotation, coast/main streets, and quiet minor streets/buildings/vegetation. Check the whole image at about 400–700 pixels wide before acceptance. Do not lower the entire map until its core is hard to see.

`geometry_styles` overrides category `[opacity, width]` pairs for `coast`, `water`, `major`, `minor`, `building`, `trail`, and `landscape`. Width is relative to a 1300-pixel photo short edge. The renderer draws strong structure after fine detail so overlapping minor paths cannot erase it. Vegetation boundaries have their own subdued style; they are not water or elevation contours.

`highway_styles` optionally overrides individual OSM highway classes using the same `[opacity, width]` units. For example, `{"residential":[0.30,0.55],"tertiary":[0.48,0.70],"secondary":[0.62,0.85],"primary":[0.78,1.00]}` establishes a finer city hierarchy. These are starting values, not a visibility guarantee. The opacity multiplies `line_opacity` and atmospheric alpha; inspect the combined result. Values must be finite with opacity in `[0,1]` and width in `(0,10]`; opacity zero omits that class. Supported names: `motorway`, `trunk`, `primary`, `secondary`, `tertiary`, `residential`, `unclassified`, `pedestrian`, `footway`, `path`, `steps`. Unspecified classes retain their category style. Local roads draw before larger arterials and water/coast edges. City mode (including omitted `mode`) omits footways, paths and steps; coast/trail modes retain them. Styles cannot restore a class excluded by the mode. These settings do not reshape geography or alter the original photo. See [refinement-and-delivery.md](refinement-and-delivery.md) for visibility and dense-grid checks.

For a core label, use per-label `size` (photo short-edge fraction), `emphasis: true`, `leader: true`, and a displaced `offset` that keeps its marker clear of all text. `note` adds smaller context below the main name, e.g. `text: "The Parisian\\nEiffel Tower"` with `note: "Approx. photo area"`. Approximate area markers still require `uncertainty_m`; visible `approx.` may appear in the note. `marker: false` is suitable for a waterbody name. `title_tracking` adds letter spacing, as a short-edge fraction. `clear_text_backdrop: true` locally removes map ink behind emphasized text using a soft alpha mask; it never paints a background over the photograph.

`highlight_features` contains real sourced features, e.g. `{ "type": "way", "id": 123, "evidence": "verified feature URL", "ink": [126,103,66], "width": 2.3, "fill_opacity": 0.12 }`. The ID must exist with geometry in the fetched extract. Closed features may receive a light fill; open paths remain open lines. A known landmark footprint does not prove the photographer's coordinates.

`font_family` supports `times` (default) and `georgia`, with local fallback fonts. `subtitle_size`, `subtitle_tracking`, `subtitle_italic` and `header_rule` tune a coherent editorial header. `credit_single_line: true` and `credit_size` allow compact attribution while retaining the provider and license URL. Never remove required attribution.

Use `title_language` and `subtitle_language` (`ja` / `ja` for Japan, `ko` / `ko` for Korea, otherwise `en` / `en` by default) to record the visible languages. Subtitles are optional; explicit user language choices override these defaults. Set per-label `language` for map names too. The renderer does not translate or enforce country-specific languages. Title/label font selection supports installed Japanese, Korean and Chinese faces on Windows plus local CJK candidates on macOS/Linux. `title_font_path`, `subtitle_font_path`, `label_font_path` and per-label `font_path` accept an absolute path to an installed font; the CLI `--font` remains a general fallback. Do not ship system fonts. Missing glyphs fail explicitly, rather than silently printing boxes. Other scripts need a suitable explicit font and a visual shaping check; this does not claim comprehensive worldwide typography support. The manifest records title language and the font actually used. Language/name correctness and visual hierarchy remain agent decisions.

`geometry_inks` maps the same categories to RGB accents. `geometry_fills` optionally assigns low-opacity fills to sourced closed shapes; open paths remain unfilled. Use restrained values such as 0.025–0.055 instead of tinting the entire photograph. `supersample` is 1 or 2; native rendering at 1 can reduce memory for a high-resolution source while preserving its native output dimensions. `check_label_visibility: true` rejects geographic captions that intersect protected subjects, rather than silently erasing letters with the foreground mask.

For optional luminous map/text treatment and georeferenced real aerial cores, see [glow-and-aerial.md](glow-and-aerial.md). `projection_align` defaults to `[0.5,0.5]`; changing it preserves uniform scale and north-up orientation while choosing which edges of a cover view are clipped. The `aerial_imagery` manifest field preserves each image's provenance and projected pixel box.

An imagery entry's optional `harmonize: {"mode":"background_relief", "contrast":0.8, "detail_weight":0.4, "color_retention":0.04}` follows the aligned original-photo background's hue/light. This is an edited aerial texture, recorded in the manifest, not an unaltered natural-color image. The photo itself is unchanged. Inspect the result against the local sky/sea: a soft edge alone does not make a mismatched dark color block acceptable.

The preferred alpha-only emphasis treatment is per-entry `adaptive_opacity: {"min":0.27,"max":0.64,"contrast_budget":0.25}`. It changes only real-photo marker alpha according to local RGB difference, retaining its RGB. Use `quiet_under_imagery: false` so emphasis opacity does not change vector opacity. Global map styles and `line_opacity` remain fixed. See [glow-and-aerial.md](glow-and-aerial.md) for `photo_markers`, a sourced photographic-cutout symbol mode distinct from orthophotos or map-scale footprints.
