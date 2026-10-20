# Validation record

Release: v0.1.0. Date: 2026-10-21.

## Automated behavior

40 tests passed on Windows with no skips. Run from the repository root:

```bash
python -m unittest discover -s tests -v
```

The tests use synthetic fixtures and mocked network responses. They require neither private photographs nor live map downloads.

| Area | Behaviors checked |
|---|---|
| Photo preservation | Full dimensions and EXIF orientation; unchanged input files; protected regions and pixels outside overlay alpha; exact recomposition; overwrite refusal |
| Geographic evidence | Unknown-location refusal; exact-pin evidence; visible approximation wording; uniform north-up projection; clipping and cover projection; exclusion of nonphysical bay boundaries; no fabricated contour mode |
| Layout and emphasis | Cloud-based attenuation; subject protection with glow; valid sourced highlight IDs; marker/text clearance; captions not cut by subject masks; light-corner glow without moving strokes |
| Titles and fonts | Japanese titles with English subtitles; Hangul-capable font selection; incompatible missing-glyph rejection |
| Real imagery | Geographic placement; source-hash validation; background-dependent relief; missing-background refusal; alpha-only adaptation preserving source RGB and cartography; sourced photographic symbol evidence |
| Retrieval | Bounded area/tile counts; cache reuse and integrity; corrupt-cache refusal; partial-response refusal; HTTP denial handling |

Font-specific tests can skip when their fonts are unavailable; none skipped on the exercised Windows host. Structural skill validation checks packaging and frontmatter, not visual quality.

## Local photo exercises

Four travel photos were produced, visually reviewed, accepted and copied to a local desktop archive. Photos, derivatives, private configurations and detailed review receipts are excluded from this public repository.

| Scene | Native displayed dimensions | Final treatment |
|---|---:|---|
| Hong Kong harbour | 1707 × 1280 | Real shoreline hierarchy, brighter important lines, Chinese title and English subtitle |
| Macao landmark tower | 1280 × 2033 | Sourced tower footprint and core roads, selective glow, Chinese title and English subtitle |
| Tokyo waterfront | 2268 × 4032 | Real bay map and sourced photographic landmark symbol; separately authorized conservative photo repair |
| Nara hillside | 1280 × 1825 | Color-free line map, subtle directional glow, Japanese title and English subtitle |

For the final Hong Kong, Macao and Nara lossless PNGs, independent verification found zero changed pixels outside overlay alpha, zero changed protected pixels and zero recomposition mismatch. Original source hashes were unchanged. These pixel claims concern lossless PNG masters, not JPEG viewing exports.

Tokyo's separately authorized repair intentionally changed the photo base at its native size while keeping the accepted overlay byte-identical. Mean absolute RGB change was approximately 0.868/255; the maximum change was 6/255. It does not satisfy or claim the unchanged-photo invariant. The one-off repair procedure is not part of this skill.

All four desktop JPEG exports decoded at their native dimensions and matched their working-copy SHA-256 hashes.

Location recognition used visible clues, published location sources and geographic records. The photos had no GPS: the mapped capture areas are researched inferences, not confirmed exact camera coordinates. Four examples do not establish a calibrated geolocation benchmark.

## Limits

- Windows was exercised live. macOS/Linux font lookup is implemented but has not been exercised on those platforms.
- The skill contains no standalone vision model, DEM/contour generator or worldwide imagery service.
- Map and imagery providers have separate terms and availability limits. Their content is not covered by the software's MIT license.
- CMYK and transparent photo inputs fail explicitly instead of silently changing their appearance.
- Technical checks do not replace visual inspection, source evaluation or user acceptance.
