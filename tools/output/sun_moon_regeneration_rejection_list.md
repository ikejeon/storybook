# Sun and Moon Regeneration Rejection List

Generated: 2026-05-07T16:58:00+00:00

No newly regenerated 32-scene set was produced in this environment, so there are no new provider outputs to accept or reject.

## Current Stale Draft Art Rejected For Bulk Review

The existing Sun and Moon generated-draft scene art remains usable only as app/demo art. It is not approved for the next production art review because it predates `tiger-character-sheet-v2.png`.

Pages requiring regeneration before review:

- `page-003.png` through `page-018.png`: tiger-facing forest, deception, door, chase, and resolution scenes need regeneration from the approved antagonist tiger anchor.
- `page-001.png` through `page-032.png`: full set should be regenerated together for style/character consistency before human creative review.

Primary rejection reasons for the stale set:

- Tiger still reads too cute/friendly in visible app evidence.
- Some cover/card art contains awkward subject crops inside the bitmap.
- The set mixes older draft generation directions with the newer 32-page story structure.

The next acceptable action is either:

```bash
OPENAI_API_KEY=... python3 tools/generate_sun_moon_scene_art.py --provider openai-responses
```

or:

```bash
python3 tools/generate_sun_moon_scene_art.py --provider manual-import --manual-source-dir shared-content/assets/manual-import/images/sun-and-moon
```
