# Editorial art direction

Use these when the user permits creative art direction. They are starting points, not accepted templates or fixed coordinate layouts. Inspect every original photo before choosing a view or palette.

## A coherent set

Use Japanese titles and map labels for Japan, Korean for Korea, and English elsewhere by default; explicit user preferences take precedence. For example, `東京` with optional `日本`, or `서울` with optional `대한민국`. Do not automatically append English translations. Verify names against the identified location and local use. Major title size, spacing and line length should be optically balanced, not forced to a fixed width.

Use a script-capable face for titles and callouts, with restrained size and spacing. `title_language`, `subtitle_language` and optional local `title_font_path`/`subtitle_font_path` are supported. Check the host for suitable CJK fonts, or use a separately obtained font such as Noto CJK under its own license. The renderer refuses missing glyphs. It does not verify translation quality. Never bundle proprietary system fonts.

Choose a named geographic core that corresponds to the photographed subject. Keep the marker, leader and label distinct. Keep a recognizable warm or cool accent for the core while the surrounding road/shore structure remains secondary. Avoid invented quotes, routes, travel dates, GPS strings, decorative compasses or location claims.

## Four palette directions

| Scene | Main ink | Geographic accent | Background treatment |
|---|---|---|---|
| Harbour/night | Warm ivory | Pale gold shore | Quiet green-gray woodland and fine streets |
| Overcast architecture | Graphite with a green undertone | Champagne landmark outline | Wider real street/coast context, light building detail |
| Cool city/bay | Blue-gray | Copper landmark name | Subtle real water shape, clear coast and harbor structure |
| Hills/animals | Deep moss | Muted earth-gold paths | Quiet city grid, real woodland shapes with a very light tint |

Match the ink to the original light; do not apply a photo-wide color grade. Color fills belong only to sourced, closed geographic features. Never close an open shoreline/path into an invented polygon. Do not label vegetation boundaries as contours.

These palettes are suggestions only: inspect the actual local background. If real imagery is present, harmonize its tone/chroma separately and check that it reads as part of the map instead of a contrasting sticker. See [glow-and-aerial.md](glow-and-aerial.md). Do not give every image the same warm-white stroke, opacity or halo.

## Composition checks

- Reuse typographic rhythm, not the same rectangle/opacity for every photograph.
- A portrait map should flow behind a real tower/roof/treeline where the original permits it. A wide sky should receive a map view whose aspect ratio fits that space.
- Set `check_label_visibility: true` in reviewed compositions so subject masks cannot silently cut a name or its note. This complements visual inspection; it does not find photo subjects automatically.
- Keep the red area marker separate from an optional gold landmark footprint. A sourced landmark shape does not prove camera GPS.
- At phone scale, the title, the geographic core and the original subject should all remain identifiable. At full resolution, fine detail should still look deliberate.
- Retain native PNG masters; smaller review previews are not the exact-pixel preservation record.

For finer architectural symbols, visible thin strokes on pale skies, dense city streets, optional clarity enhancement and final-image-only delivery, use [refinement-and-delivery.md](refinement-and-delivery.md). Judge against the user's supplied composition references, not just a passing pixel test.
