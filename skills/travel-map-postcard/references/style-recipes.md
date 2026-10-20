# Editorial art direction

Use these when the user permits creative art direction. They are starting points, not accepted templates or fixed coordinate layouts. Inspect every original photo before choosing a view or palette.

## A coherent set

Use the local place name in its local language/script as the main title, with a smaller English geographic subtitle. Japan: `東京` / `TOKYO`; Korea: `서울` / `SEOUL`. Verify names against the identified location and local use; multilingual places need a place-appropriate choice rather than a country-wide mechanical translation. When the local language is English, avoid duplicating the same words. Major title size, spacing and line length should be optically balanced, not forced to a fixed width.

Pair a script-capable local face for the main title with a restrained serif English subtitle/callout. `title_language`, `subtitle_language` and optional local `title_font_path`/`subtitle_font_path` are supported. Check the host for suitable CJK fonts, or use a separately obtained font such as Noto CJK under its own license. The renderer refuses missing glyphs. It does not verify translation quality. Never bundle proprietary system fonts.

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
