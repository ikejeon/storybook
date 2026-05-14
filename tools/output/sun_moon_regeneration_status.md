# Sun and Moon Scene Regeneration Status

Generated: 2026-05-11T00:55:00+00:00

- Image provider credentials available: `False`
- Scenes actually regenerated/imported this run: 32
- Scene target count: 32
- Status used for regenerated/imported art: `generated_draft`
- Final promotion remains blocked until human creative, cultural, child-safety, and crop review.

## Ready Commands

```bash
python3 tools/generate_asset_status_report.py
```
```bash
python3 tools/validate_assets.py
```
```bash
python3 tools/validate_production_readiness.py --level generated-draft
```
## Output Paths

- Job queue: `tools/output/sun_moon_scene_regeneration_jobs.json`
- Manual import folder: `shared-content/assets/manual-import/images/sun-and-moon`
- Generated draft scenes: `shared-content/assets/generated-draft/images/scenes/sun-and-moon`
- Contact sheet HTML: `tools/output/sun_moon_32_scene_contact_sheet.html`
- Contact sheet PNG, when Pillow is available: `build/screenshots/sun-moon-32-scene-contact-sheet.png`
- Rejection/blocker list: `tools/output/sun_moon_regeneration_rejection_list.md`
- Image manifest: `shared-content/assets/manifests/image_manifest.json`

## App Evidence Notes

- Fresh iOS simulator screenshot: `build/screenshots/current-pass/ios-launched.png`
- Fresh iOS simulator screenshot: `build/screenshots/current-pass/ios-reader-real-book-page3.png`
- Current visible Sun and Moon scene art is still pre-regeneration; use these screenshots as app-state evidence, not final art proof.
