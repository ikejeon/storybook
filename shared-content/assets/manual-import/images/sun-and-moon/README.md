# Sun and Moon Manual Scene Art Import

Place externally generated or commissioned PNG drafts for The Sun and the Moon here, using exact filenames:

- `page-001.png`
- `page-002.png`
- `page-003.png`
- `page-004.png`
- `page-005.png`
- `page-006.png`
- `page-007.png`
- `page-008.png`
- `page-009.png`
- `page-010.png`
- `page-011.png`
- `page-012.png`
- `page-013.png`
- `page-014.png`
- `page-015.png`
- `page-016.png`
- `page-017.png`
- `page-018.png`
- `page-019.png`
- `page-020.png`
- `page-021.png`
- `page-022.png`
- `page-023.png`
- `page-024.png`
- `page-025.png`
- `page-026.png`
- `page-027.png`
- `page-028.png`
- `page-029.png`
- `page-030.png`
- `page-031.png`
- `page-032.png`

Then run:

```bash
python3 tools/generate_sun_moon_scene_art.py --provider manual-import --manual-source-dir shared-content/assets/manual-import/images/sun-and-moon
```

The script copies files into `shared-content/assets/generated-draft/images/scenes/sun-and-moon/`, updates `image_manifest.json`, keeps status as `generated_draft`, and syncs the iOS Swift package resources.

Do not place final commissioned art here. Final art belongs in the `final/` asset tier only after complete review metadata exists.
