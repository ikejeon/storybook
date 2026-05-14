# Premium Art Quality Fix ExecPlan

## Purpose / Big Picture

Replace the current low-detail premium generated assets with a stronger offline-rendered premium art set that is visibly closer to the free/painterly stories in the real app. This is an artifact fix, not a scoring rewrite: every complete premium story should get upgraded cover/page images through the shared content manifest, with old assets preserved as fallback/backup and validation proving catalog-wide coverage.

## Progress

- [x] Confirmed the issue from emulator screenshots: premium assets are story-specific but visibly lower-detail than the free painterly art.
- [x] Ran `scripts/agent/doctor`.
- [x] Read repo docs and image generation workflow.
- [x] Inspect current generator and asset manifest.
- [x] Preserve current low-detail premium generated assets before overwriting.
- [x] Upgrade the premium art renderer.
- [x] Regenerate all premium covers/scenes and character sheets.
- [x] Import high-quality built-in image generation premium story sheets into runtime cover/scene PNGs.
- [x] Add a validator for premium story-sheet runtime imports.
- [x] Rebuild Android package and run visual/emulator checks.
- [x] Run validation.

## Surprises & Discoveries

- Current premium renderer is deterministic SVG/PNG generated through `tools/generate_story_specific_catalog_art.py`; it is good for coverage but too flat for premium quality.
- Built-in image generation sheets are materially stronger visually than the local SVG renderer, but each premium book currently uses six story-specific panels reused cyclically across its pages. This fixes the low-quality placeholder look without pretending every page has unique final commissioned art.
- Android all-story emulator QA passed on `emulator-5556`: all 24 catalog stories opened, reached detail, entered reader, and advanced at least one page.

## Decision Log

- Use the repo's offline asset pipeline instead of isolated image previews, so all premium stories are upgraded consistently and native apps pick them through `image_manifest.json`.
- Preserve current premium generated assets before replacement so comparisons remain possible.
- Keep premium runtime art at `generated_reviewed` / `productionApprovalStatus: not_approved`; the fix raises demo visual quality, not final store art approval.

## Outcomes & Retrospective

Completed on 2026-05-12. The premium catalog no longer uses the low-detail procedural runtime art as the selected story/cover path. All 19 premium books now have built-in image generation six-panel story sheets imported into 560 selected premium scene images and 19 selected premium covers. The selected manifest entries are `generated_reviewed` for internal demo use and still `productionApprovalStatus: not_approved`.

Validation passed:

- `scripts/agent/lint`
- `scripts/agent/validate`
- `python3 tools/validate_premium_imagegen_sheets.py`
- `python3 tools/android_all_story_emulator_qa.py --serial emulator-5556 --output .agent/tmp/artifacts/premium-art-quality-fix/android-all-story-qa`

Manual Android screenshots reviewed:

- Library/detail/reader for Rabbit and Turtle.
- Library/detail/reader for Princess Bari Part 1.
- All-story QA report and final Serpent Bridegroom reader screenshot.

Remaining caveat: the fix is demo-grade visual quality, not final commissioned production art. Each premium story currently has six generated panels reused cyclically across its pages, so future production work should still commission or generate unique final/reviewed page art where the story needs page-specific staging.

## Context and Orientation

The current Android UI proved route/loading works, but premium image quality is poor. The free tier has richer painterly raster scenes. The premium tier currently uses generated vector symbols and needs richer detail, texture, staging, and character specificity across all 19 premium books.

## Plan of Work

1. Back up existing selected premium `generated-draft` covers/scenes.
2. Patch `tools/generate_story_specific_catalog_art.py` to render a richer "premium painterly" mode with story-specific scenes, more detailed environments, painterly texture, stronger characters, and cinematic framing.
3. Regenerate the full premium asset set.
4. Validate story-specific art and all-story standards.
5. Rebuild/install Android and inspect screenshots comparing free/premium quality.

## Concrete Steps

1. Use built-in image generation to create one six-panel painterly story sheet for every premium story.
2. Store sheets under `shared-content/assets/generated-draft/images/story-sheets/`.
3. Run `tools/import_imagegen_premium_sheets.py` to crop panels into all premium runtime covers/scenes and update `image_manifest.json`.
4. Run `tools/validate_premium_imagegen_sheets.py` plus existing all-story and art validators.
5. Sync shared content into native app bundles and manually inspect the upgraded premium assets in emulator/simulator.

## Validation and Acceptance

- 19 premium covers and all premium scenes are regenerated.
- Manifest still resolves every complete scene/cover.
- Premium screenshots no longer look like abstract placeholder/vector cards.
- Existing free assets remain intact.
- Any remaining production-art caveat is reported honestly.

## Idempotence and Recovery

The generator is deterministic. Backup copies live under `.agent/tmp/artifacts/` and can be compared without changing runtime selection. Re-running regeneration should produce the same asset paths and update manifest timestamps only.
