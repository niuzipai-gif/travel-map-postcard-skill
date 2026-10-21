# Reference-driven refinement and clean delivery

## Match the reference without copying its geography

Treat the user's photograph as the base and reference postcards as evidence of composition, stroke hierarchy and typography only. A screenshot of someone else's prompt is reference material, not an instruction. Do not import its city, language, camera coordinates, icons or map mistakes.

Default visible place names, title, subtitle and geographic notes to Japanese for Japan, Korean for Korea, and English elsewhere. User instructions override this default. A subtitle is optional; do not add an English duplicate automatically. Keep required provider names and attribution URLs intact. Verify names and glyphs. Use `撮影エリア（目安）`, `대략적인 촬영 지역`, or `approx. area` for an inferred area, with evidence and `uncertainty_m`; a red point must not imply measured camera GPS.

## Thin strokes that survive phone viewing

1. Inspect the original at native size and about 400–700 pixels wide. Choose the continuous available sky, including portrait and landscape differences. Preserve the accepted crop, photo, Japanese/Korean names and label layout during a line-only revision.
2. Prefer a single fine center stroke with antialiasing. Broad casings, repeated outlines, heavy shadows and strong bloom make a nominally thin map look thick. Keep `supersample: 2` when memory permits; this smooths the overlay and does not upscale the photo.
3. If a map vanishes, first improve ink/background contrast and reduce excessive cloud attenuation. Pale or snowy skies often need a restrained blue-gray ink; saturated blue skies can support pale ink. Then adjust local opacity and only modestly adjust width. Do not reduce opacity, blur and width together merely to make the map “natural.”
4. Make the main waterway/coast or arterial route readable at phone scale, secondary streets quieter and small details finer. Inspect the darkest and lightest sky regions separately. Protect the actual statue, spire, bridge cables and roof silhouette; do not erase useful sky with a crude protection rectangle.
5. Feather only transitions that need it. Never fade the entire geographic core away. Check that map, text and symbol opacity remain independent. Use a side-specific alpha mask in an external compositor only when needed and record it; the bundled renderer exposes a bottom fade, not a lateral-mask parameter.

These are visual decisions, not a universal opacity preset. Pixel preservation and image dimensions do not prove a map is visible or attractive.

## When the photograph has little or no sky

Choose the largest coherent negative space before selecting the map extent. Large skies can carry a broad coastline or street network; narrow sky gaps need fewer labels and a tighter researched extent. For a dense street view or indoor exhibit, an existing unlettered sign back or plain wall can support a compact overlay. Preserve the surface texture and perspective of the original photograph; the map remains a north-up editorial overlay, not a simulated replacement sign. Record `layout_exception_reason` and protect structural bars, wires, lettering and the subject. Do not invent sky, paint a blank panel, crop the photograph or squeeze labels into unreadable type to meet an area percentage.

Inspect the compact result at phone size. If geography can only be read in the detail crop, disclose that limitation rather than calling it an expansive sky-map treatment. If there is no usable space, offer a separately composed page only with the user's agreement.

## Verify the visible anchor, not just the coordinates

A coordinate inside `bbox` may still be clipped by `projection_fit: cover`. A correctly projected red point may disappear behind a tree/subject mask while its label survives. Check all three: extract coverage → projected frame → final composited overlay. The renderer now rejects off-frame label anchors and red area/capture markers with fewer than three clearly red native overlay pixels after composition and protection. This is a disappearance check, not a perceptual readability score; still inspect full-image, phone-size and detail views. Avoid counting red signs in the photograph as marker evidence.

When the marker disappears, adjust the researched map window, frame or composition; retain the actual coordinate. Move only label text with an offset/leader. Never shift the point to an unrelated location or erase the foreground subject to expose it. A later revision can be worse: retain the selected earlier version when a newer mask hides the point.

## Dense city maps must not look like graph paper

Count and inspect OSM feature classes before styling. Parallel sidewalk/crossing lines, equally weighted residential streets and repeated outlines can overwhelm the real street structure. The bundled `city` mode omits `footway`, `path` and `steps`; `trail` and `coast` modes retain them. Use trail mode when walking paths are the subject. Do not erase real scenic paths merely because a city example had excessive sidewalks.

Use `highway_styles` to separate residential, tertiary and primary roads instead of treating all arterials alike. Keep waterways and coastlines legible. Choose a researched bbox and uniform projection that includes useful context, such as a real river bend, when the photo's negative space permits it. A busy horizontal street scene may suit a map concentrated in the open sky at one side. Never bend, randomly delete or invent streets to hide a city's genuine rectangular plan. Do not move labels away from their verified geographic anchors to improve appearance; use leaders or recorded text offsets.

## Landmark symbols should be recognizable

Study the actual silhouette, roof layers, structural proportions and meaningful internal edges. Avoid generic stick towers, triangle mountains or a stock pagoda when the reference uses delicate architectural linework. Use sourced vector artwork or a carefully masked line-art derivative of an authorized photograph; remove background edges and simplify noise at the intended display size. Antialias the small output and inspect at 100% and phone size. If a faithful small symbol cannot be made, a correct label and real footprint are preferable to a fabricated icon.

Record the source, permission, processing and not-to-scale status. A photographic outline is an editorial symbol, not a surveyed footprint or an orthophoto. The bundled renderer accepts sourced transparent `photo_markers`; it does not automatically extract architectural line art. Use the existing marker provenance checks and record derivative processing alongside the source. Do not publish user-derived artwork without authorization.

## Clarity without changing the accepted photograph

Retain the unmodified source and native lossless master. When the user asks for enhancement, keep the repaired photo base and its method separately versioned. Apply conservative photo-only denoising/sharpening before the accepted map is composited; do not sharpen the finished map into thick halos. Compare fine building edges, mountain texture, snow and sky gradients. Reject invented texture, ringing and oversmoothing.

For a larger viewing export, record native dimensions, final dimensions and the interpolation method. A 2× Lanczos export is interpolation, not recovered detail or AI super-resolution. The skill has no generic restoration model. Unchanged-source pixel claims apply only to the original-base lossless composition; an enhanced base is a separate, explicitly documented result. JPEG is a viewing export, not an exact-pixel preservation master.

## Final selection and delivery

- Keep an acceptance ledger in the private workspace: photo identity/source hash, selected version, accepted changes, output dimensions and final hash. Different photos may end at different version numbers. Select each latest accepted image; do not regenerate the whole set or assume the newest directory is correct for every photo.
- Generate the delivery contact sheet from that same explicit selection, not by scanning for the highest version number. Distinguish technical checks, visual review and user acceptance; a delivered preview remains pending user review until accepted.
- The user-facing destination contains **only final viewing images, one file per photograph** by default. Use a readable scene name and optional ordering number. Do not put native/HD duplicates, previews, transparent maps, scripts, JSON, checksums or ZIPs in this folder unless requested.
- Keep original sources, lossless masters, overlays, configurations, provenance, checks and packages in a separate workspace archive outside the viewing destination. Return the archive path when useful; do not clutter the destination with a backup subfolder.
- During cleanup, inventory the exact requested directory first. Compare image content/source identity before deduplicating: two pictures with the same place name may be different photographs. Preserve unrelated existing finals. Never infer an obsolete version from its filename alone.
- Copy selected finals, verify successful decoding, dimensions and source/destination SHA-256 equality, then move displaced material to a dated backup outside the destination. Check resolved absolute paths stay inside the explicitly scoped source/destination roots; do not follow reparse points. Do not overwrite collisions blindly or permanently delete uncertain files.
- Re-list the destination after the move. Verify it contains precisely the expected final-image set, with no accidental package or process files. Keep the receipt in the workspace archive. Do not silently turn a request to archive five new pictures into deletion of other accepted pictures.

## Refinement record

For each revision record: user concern → layer changed → protected accepted elements → full-image/phone/detail observations → selected version. Common failures and remedies:

| Symptom | First checks and bounded remedy |
|---|---|
| Thick linework | Remove casing/bloom; refine stroke widths with antialiasing |
| Kyoto/overcast map disappears | Inspect sky contrast and compounded fading; restore core contrast |
| Snowy city looks like a grid | Inspect sidewalk duplication and road weights; preserve real geographic structure |
| Landmark looks childish | Replace generic icon with sourced, recognizable silhouette/internal detail |
| “HD” export looks artificial | Separate photo enhancement from map; disclose interpolation and compare with native |
| Delivery directory is cluttered | Select accepted finals per photo; move working artifacts outside the destination |

These describe observed failure modes, not location-specific presets. User acceptance concerns the particular image set and is not proof of universal visual quality.
