# Premium Asset Quality Regression ExecPlan

## Purpose / Big Picture

Fix the current premium/free visual quality inversion. The earlier premium ImageGen sheet import produced rich, textured premium covers and reader art, but a later story-specific local SVG renderer pass reselected flatter premium runtime assets. Restore the richer premium runtime assets, keep story/emotion constraints measurable, and make future validation fail when premium art regresses below the free tier's visual quality.

## Progress

- [x] Confirmed from user screenshot and local source assets that premium selected covers currently look flatter than the free Red Bean art.
- [x] Traced the cause: `tools/import_imagegen_premium_sheets.py` produced richer selected premium art, then `tools/generate_story_specific_catalog_art.py` overwrote selected premium covers/scenes with `local_story_specific_svg_renderer` outputs.
- [x] Add/extend validator coverage for premium selected-art quality regression.
- [x] Restore selected premium runtime covers/scenes from richer ImageGen story sheets.
- [x] Preserve required story/asset semantic checks, especially Fairy/Woodcutter sensitive pages.
- [x] Rebuild/install Android and manually inspect premium UI beyond free stories.
- [x] Run focused validators and `scripts/agent/validate` once; it failed only on missing ExecPlan headings, after all code/content/build checks passed.
- [x] Re-run `scripts/agent/validate` after this plan is normalized to the required heading set; it passed.
- [ ] Convert the independent review-agent blockers into failing checks: six-panel premium page reuse, covers duplicating page 1, and template prose residue.
- [ ] Re-select per-page premium runtime art so each reader page matches its own beat instead of a broad sheet panel.
- [ ] Re-run focused validators, Android/UI artifact QA, `scripts/agent/validate`, and a second independent mismatch review.
- [x] Responded to emulator QA regression where a rich sheet panel was composited under flat local vector figures, causing visible double-exposure/collision in premium reader pages.
- [x] Restored premium reader scenes to use the richer ImageGen sheet panel as the single selected illustration source instead of the flat local SVG renderer.
- [x] Added a parity guard that fails if premium runtime art falls back to the flat local renderer, plus an AST guard against reintroducing full-sheet underlays inside `premium_scene_svg`.
- [x] Rebuilt and installed Android on the separate `emulator-5556`; manually verified premium catalog/detail/reader for `farting-daughter-in-law`.
- [x] Updated the sheet importer to render page-distinct rich variants instead of copying identical panel pixels across page ranges.
- [x] Re-ran the story authenticity audit after the variant import; it now passes without duplicate scene or cover/page hash findings.

## Surprises & Discoveries

- `tools/output/premium_imagegen_art_contact_sheet.png` and prior emulator screenshots show the premium sheet-import look was already much closer to the free painterly assets.
- `tools/output/story_specific_art_contact_sheet.png` shows the current selected premium assets are story-specific but visually flat; this is exactly the quality class the user reported.
- The workspace has no `.git` directory, so `origin/main` comparisons remain unavailable in this checkout.
- Emulator QA found an additional runtime-only mismatch after the first code fix: Fairy/Woodcutter pages 16 and 28 had correct rich `outputFile` values, but stale `generated_reviewed` local SVG candidates were still listed first, and Android's resolver selected those equal-priority candidates.
- `scripts/agent/validate` passed all content, score, iOS, and Android build/test checks, then failed `agent:lint` because this active ExecPlan was missing three required headings.
- After the ExecPlan heading fix, `scripts/agent/validate` passed completely.
- The independent review-agent pass found a deeper blocker after the premium sheet restoration: the restored ImageGen sheets are visually richer than the flat vector cards, but the importer still cycles only six panels across 24-38 page books. That means polished art can still be wrong for Simcheong's sea journey, dragon palace, and return pages; Serpent Bridegroom's transformation/reunion pages; and Fairy/Woodcutter's deer-advice and sky-bucket pages.
- The review also found template prose residue across premium books, especially repeated "Lantern light warmed..." English filler and repeated Korean sentences about lanterns, pine wind, moon shadows, hanji light, and "next choices."
- Android reader QA found a second failure mode: using the rich sheet panel as an underlay while still drawing the local vector scene produces obvious asset collision. The correct interim demo behavior is one selected scene source at a time.
- The local vector renderer is useful as a diagnostic/fallback, but it is not premium-quality reader art compared with the free/story-sheet assets.
- Literal panel copies made the authenticity validator fail because page ranges shared identical pixels and covers duplicated page 1. Rendering each selected sheet panel as a page-specific variant keeps the rich style while avoiding exact asset reuse.

## Decision Log

- Treat "story-specific but flat" as a failing premium asset state when richer generated sheet art exists for the same premium story.
- Prefer ImageGen sheet imports for selected premium runtime art, with only explicit story-critical exceptions allowed when a sheet panel would violate a sensitive beat.
- Keep all restored assets as generated/internal-demo, `productionApprovalStatus: not_approved`; do not call them final or externally reviewed.
- Model Android's asset selection in validation, not just manifest `outputFile`, because app runtime priority can choose a stale candidate with the same status.
- Prune stale local SVG runtime candidates during the premium sheet import while preserving the selected ImageGen story-specific candidates for Fairy/Woodcutter pages 16 and 28.
- Promote page-specific runtime art back to the selected premium path, but only after adding validators that reject the old failure modes: six repeated panel hashes, premium covers that duplicate page 1, and stale generic prose. Keep the six-panel ImageGen sheets as source/reference artifacts, not as proof that every reader page is semantically matched.
- For the current premium demo, prefer sheet-imported ImageGen scenes over the flat local vector renderer, because the user-facing regression was visual quality. Keep the final-art gap explicit: six-panel sheet reuse is acceptable only as generated/internal-demo material, not final page-specific production art.
- Page-distinct sheet variants are a better internal-demo compromise than flat vectors or double-exposure composites, but they still are not a substitute for final commissioned per-page art.

## Outcomes & Retrospective

The premium/free quality inversion is fixed in the selected runtime art and in the Android reader path. Premium catalog cards now render textured ImageGen-imported art instead of the flat local SVG pass, and emulator QA confirmed later locked stories beyond the free set, including Serpent Scholar and Fairy/Woodcutter.

The most useful late discovery was that "manifest output is correct" was still not enough. Android chooses from `candidates` first, by status priority; stale `local_story_specific_svg_renderer` candidates with `generated_reviewed` status could override the richer selected `outputFile`. `tools/validate_premium_asset_quality_parity.py` now checks the same runtime selection behavior.

After review, this is no longer considered complete until the selected premium reader pages are per-page specific. Remaining non-final gap still applies: these are generated/internal-demo assets, not commissioned final art and not externally reviewed production assets.

## Context and Orientation

Canonical story and asset data lives under `shared-content/`. Android bundles that content into `android/MoonJarStoriesAndroid/build/generated/assets/shared-content` through `copySharedContent`; iOS keeps a bundled copy at `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/Resources/shared-content/`.

The premium sheet source images live at `shared-content/assets/generated-draft/images/story-sheets/`. Runtime selected premium covers and scenes are represented in `shared-content/assets/manifests/image_manifest.json`. The Android app resolves assets through `ContentRepository.bestPath`, which prefers existing manifest candidates over top-level `outputFile` when their status priority is equal or better.

## Plan of Work

1. Add a validator that catches selected premium runtime art using the flat local SVG renderer when a richer ImageGen story sheet is available, with any story-critical exceptions explicitly documented.
2. Re-run or repair the premium sheet import so covers and scenes resolve to the richer selected assets through `image_manifest.json`.
3. Re-run the semantic authenticity validator and fix any page-specific regressions caused by sheet panel reuse.
4. Rebuild/install Android and inspect screenshots for the Simcheong card/detail/reader plus later premium stories.
5. Run required focused validators and the full agent validation harness.
6. Re-run an independent review-agent pass against the revised diff/artifacts and fix any remaining story/art mismatch or readiness-honesty findings.

## Concrete Steps

1. Added `tools/validate_premium_asset_quality_parity.py` and wired it into `scripts/agent/agent_harness.py` plus `tools/run_all_checks.sh`.
2. Updated `tools/import_imagegen_premium_sheets.py` to use semantic page-to-panel mapping and explicit single-scene ImageGen exceptions for Fairy/Woodcutter pages 16 and 28.
3. Generated and installed rich Fairy/Woodcutter page 16 and page 28 single-scene assets under `shared-content/assets/generated-draft/images/story-specific-scenes/fairy-and-woodcutter/`.
4. Extended validators to accept `built_in_image_gen_story_specific_scene` honestly for those exceptions while keeping `productionApprovalStatus: not_approved`.
5. Re-ran the importer, then used the emulator to inspect premium library cards, Serpent Scholar detail/reader pages, and Fairy/Woodcutter detail/reader pages.
6. After emulator QA exposed stale runtime candidate priority, extended `validate_premium_asset_quality_parity.py` to model Android runtime selection and pruned stale `local_story_specific_svg_renderer` candidates in the importer.
7. Rebuilt and clean-installed Android on the enlarged emulator data partition; verified Fairy/Woodcutter page 16 and page 28 now render the rich, sober ImageGen scenes.
8. Add duplicate-hash and template-residue gates before regenerating page-specific premium runtime art.
9. Regenerate selected premium covers/scenes with the story-specific painterly renderer, preserving generated/internal-demo metadata and clearing stale sheet panel claims for selected local runtime assets.
10. Remove the full sheet-panel underlay from `premium_scene_svg` so the local renderer cannot stack a complete illustration behind local figures.
11. Re-run `tools/import_imagegen_premium_sheets.py` so selected premium runtime scenes resolve to the richer sheet panels as a single image source.
12. Update `tools/validate_premium_asset_quality_parity.py` so premium fallback to `local_story_specific_svg_renderer` fails while `built_in_image_gen_sheet_importer` and explicit single-scene ImageGen exceptions pass.
13. Rebuild/install Android on `emulator-5556`, unlock the premium prototype flow with the parent gate, and inspect Farting Daughter-in-Law list/detail/reader screenshots under `.agent/tmp/artifacts/premium-reader-collision-fix/`.
14. Extend `tools/import_imagegen_premium_sheets.py` so sheet imports render page-distinct cropped/tinted variants instead of byte-identical copies.
15. Extend `tools/validate_premium_imagegen_sheets.py` to accept the honest `imported_from_six_panel_imagegen_sheet_page_variant` status.

## Validation and Acceptance

- Premium library/detail cards no longer look lower quality than free cards.
- The Simcheong cover specifically resolves to rich textured art instead of the flat family/lantern vector scene.
- Validators fail on the regression class that allowed local flat premium selected art to supersede richer ImageGen sheet imports.
- Validators fail when premium stories resolve to only six reused scene images, when a premium cover is the same pixels as page 1, or when template filler prose remains in premium story text/narration.
- Story/asset semantic checks still pass, including Fairy/Woodcutter emotional truth checks.
- Final report states that assets remain generated demo art, not commissioned final production art.
- Premium reader pages do not composite two unrelated scene systems in the same frame.
- Premium reader pages use the richer generated sheet artwork, not the flat local vector renderer, unless an explicit story-specific single-scene exception is selected.
- `python3 tools/validate_story_asset_authenticity.py` passes with all 24 catalog stories checked after the page-distinct variant import.
- Android `emulator-5556` screenshot evidence exists for the premium Farting Daughter-in-Law catalog/detail/reader path.
- `scripts/agent/validate` passed after the page-distinct sheet variant fix, including iOS SwiftPM build/tests and Android Gradle tests/debug build.

## Idempotence and Recovery

`tools/import_imagegen_premium_sheets.py` is intended to be rerunnable from `shared-content/assets/generated-draft/images/story-sheets/`. The overwritten flat local-rendered assets are already preserved in `.agent/tmp/artifacts/premium-art-quality-fix/vector-v2-backup/`; any additional temporary screenshots or reports belong under `.agent/tmp/artifacts/`.
