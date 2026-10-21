# Location evidence

Separate visible subject, capture area and exact camera position. Recognizing a tower does not locate the photographer. A map gazetteer identifies the tower, not the camera; a hotel address is not a window position. Sanity-check EXIF GPS against the scene.

1. Inspect signs, silhouettes, relative building positions, water/land relationships, language and terrain. Record visible observations before candidate names.
2. Search candidate plus discriminating clue in appropriate languages. Open an official venue/park/tourism reference and compare. A search snippet alone is weaker evidence.
3. Test alternatives: original vs replica, same-name sites, subject vs viewpoint, wrong region, mirrored photo. Copied pages are not independent evidence.
4. Use only supported precision. A verified area with unknown camera point is a normal success. Use a small red area dot plus a visible approximate-area label: `撮影エリア（目安）` for Japanese, `대략적인 촬영 지역` for Korean, or `approx. area` for English; keep the uncertainty radius in the configuration. An optional uncertainty circle is illustrative, not a measured confidence interval, and is off by default.
5. If competing cities remain plausible, ask for one clue and keep `unresolved`. Do not render a certain name while waiting. A user-selected location-free version omits geography and marker rather than fabricating a map.

Confidence is qualitative agent judgment, not a calibrated recognition accuracy percentage. A source proving that a landmark exists does not independently prove that this photograph depicts it; state the matching inference.

## Adversarial cases

- Eiffel-like towers: inspect adjacent hotels, linked bridges, tower base and hills to distinguish Paris, Macau, Las Vegas and other replicas.
- A wall reading `AMERICAN MEMORIAL PARK` conflicts with an unverified `O'AHU / HAWAII` overlay. Check the park name before inheriting geography from a style reference.
- Tokyo Tower behind Rainbow Bridge may be viewed from Odaiba; the tower coordinate is not the camera coordinate.
- A deer on a hill does not prove an exact summit. Match city basin, temples, terrain and signs; fall back to supported region.

## Minimal record

```json
{
  "status": "verified_area",
  "visible_subject": "Verified landmark(s)",
  "capture_area": "Researched region",
  "camera_status": "approximate",
  "confidence": "high for city; moderate for viewpoint area",
  "evidence": [{"url": "https://official.example/place", "supports": "Name and setting", "does_not_prove": "Exact camera location"}],
  "rejected_alternative": "Candidate and contradictory visible clue"
}
```

`verified_area` means sufficient researched evidence for using that area, not user-confirmed GPS. Exact pins need `camera_status: exact` and direct `camera_evidence`. Never publish private GPS, local paths or travel times in the reusable skill package.
