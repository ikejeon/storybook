# Story Asset Authenticity Audit ExecPlan

## Purpose / Big Picture

Audit every complete catalog story and its selected visual assets for semantic fit: the art must match the story beat, character role, emotional tone, danger level, cultural context, key props, continuity, and child-safe adaptation boundaries. This pass must not stop at file existence or demo coverage. It should make story/art mismatches measurable, fix mismatches found in content, prompts, import mapping, manifests, or runtime draft assets, and keep asset status honest as generated/internal-demo material rather than final commissioned art.

## Progress

- [x] Read `AGENTS.md`, `README.md`, `docs/README.md`, `docs/PLANS.md`, and `docs/asset_production_pipeline.md`.
- [x] Ran `scripts/agent/doctor`.
- [x] Confirmed this workspace currently has no `.git` directory, so literal `origin/main` diff comparisons are unavailable unless another VCS source is provided.
- [x] Inventory every catalog story, page count, access tier, known core beats, emotional beats, cover, sheet, scene count, manifest mapping, findings, and required fixes.
- [x] Extend validators so story/art mismatch classes are checked mechanically where possible.
- [x] Fix story JSON, image prompts, story-sheet import mapping, manifests, reports, and generated draft assets where mismatches are found.
- [x] Generate or inspect contact sheets for every story and save audit artifacts under `.agent/tmp/artifacts/`.
- [x] Run an independent review-agent pass if available in this environment.
- [x] Run required focused validators and `scripts/agent/validate`.
- [x] Record the completed audit table, fixed items, validation results, and remaining non-final/human-review gaps.

## Surprises & Discoveries

- The current project directory and its parents up through `/Users/madmax/.openclaw/workspace-coder-ike` do not contain `.git`; `git status` from the repo path fails with “not a git repository.” The audit will use local before/after artifact snapshots and report this limitation honestly.
- The independent review-agent pass found the biggest actual mismatch class: 18 premium stories were still six-page/template-style prose expanded across full books, with generic image prompts and selected six-panel sheet crops cycling across 560 premium scene assets. That meant most premium books could pass existence/readiness checks while still missing folktale-specific beats.
- `fairy-and-woodcutter` had repaired text already, but its selected sheet-import art still collapsed many pages into broad panel ranges. The final selected runtime art now uses per-page generated scene assets with additional semantic overlays for wing robe, children-in-arms departure, sky bucket, rooster ending, and somber mouths on the departure beat.
- `sun-and-moon` selected generated-draft scenes already carried child-safe threat in the high-risk tiger pages; spot checks showed the tiger is meaningfully threatening without horror.
- Regenerating narration after story repairs correctly exposed stale audio-manifest text. Full synthetic narration and procedural ambient/UI sound drafts were regenerated so the manifests do not falsely point repaired text at old audio.
- The first full harness run failed because the iOS bundled copy of `shared-content/` was stale and the writing score emotion lexicon did not count story-specific phrases such as “solemn resolve” and “tender bittersweet.” Both were fixed and the final harness passed.
- A later independent review-agent pass found three blocker classes after the first green harness: generated/meta prose had leaked into premium page text, Korean/narration fields contained English fragments from compact expectation labels, and selected local-renderer manifest prompts were stale/generic instead of matching page `imagePrompt` values. Those checks were added to the authenticity validator before repair.
- The next review-agent pass correctly found that `fairy-and-woodcutter` pages 15, 16, and 18 still relied on subtle overlays on top of the generic premium scene scaffold. Page 15 did not read immediately as a sorrowful departure, page 16 did not read as the empty aftermath, and page 18 did not read as a sky-bucket ascent over mountains. This was a real mismatch even though the manifest and prompts were aligned.
- A final iOS smoke rerun after the content sync built, installed, and wrote the expected transcript/screenshot artifacts, but CoreSimulator's `simctl launch` process stopped responding before the harness returned. The stale smoke harness and launched app were terminated; the earlier iOS smoke pass remains recorded, and the full `scripts/agent/validate` harness passed after the final content and manifest fixes.

## Decision Log

- Treat semantic mismatch as broader than asset existence: a page can fail if a selected panel exists but depicts the wrong beat, wrong emotional valence, wrong threat posture, or an over-generic moralized version of a culturally specific tale.
- Keep generated artwork statuses as `generated_reviewed` or lower/internal-demo statuses only. Do not mark draft/generated assets as final or externally reviewed.
- Prefer adding deterministic validators and metadata expectations before fixing assets, so future imports cannot silently cycle panels onto the wrong beats.
- For premium runtime assets, prefer per-page `local_story_specific_svg_renderer` selected outputs over sheet-cycled selected outputs. Keep the six-panel imagegen sheets available as source/draft artifacts, but do not require selected runtime scenes to keep stale `sourceSheet` or `panelIndex` metadata once per-page art is selected.
- Expand validator emotion vocabulary when it recognizes authentic emotional terms from repaired stories, rather than flattening story prose into a small generic lexicon.

## Outcomes & Retrospective

Completed.

Findings fixed:

- Added a catalog-wide semantic audit validator and report: `tools/validate_story_asset_authenticity.py`, `tools/story_asset_semantic_expectations.py`, `tools/output/story_asset_authenticity_audit.md`, and `.agent/tmp/artifacts/story-asset-authenticity/story_asset_authenticity_snapshot.json`.
- Repaired 18 premium story JSON files from generic scaffolds into story-specific internal-demo drafts with folktale core terms, page-level `storyBeat` metadata, image prompts, audio prompts, vocabulary, summaries, themes, sensitivity notes, and honest internal-review wording via `tools/repair_premium_story_authenticity.py`.
- Preserved and tightened `fairy-and-woodcutter` sensitive beats: hidden wing robe framed as wrong, three-child warning, reveal before the third child, sorrowful one-child-in-each-arm departure, sky-bucket ascent, closed road, and rooster-longing ending.
- Regenerated 560 premium scene images, 19 premium covers, and 24 character sheets with selected per-page generated assets. The renderer now adds semantic overlays for high-risk/key props and emotional beats rather than relying only on generic figure/environment layouts.
- Added full-frame renderer compositions for the three Fairy/Woodcutter blocker pages: page 15 is now an outdoor sorrowful sky departure with the fairy holding one child in each arm and the woodcutter below, page 16 is an empty cottage aftermath with sandals and no figures, and page 18 is a sky-bucket ascent over mountains.
- Repaired generated/meta page prose and removed English fragments from Korean/narration fields across the premium repaired drafts. Korean emotional labels now come from Korean-language terms rather than English expectation labels.
- Updated local renderer manifest writes so selected runtime entries carry the page-level `imagePrompt`/`rawPrompt` instead of stale generic renderer prompts.
- Added cover/scene prompt safety wording for safe margins, no cropped faces/hands, and no text/watermark to reduce layout and generated-text failure modes.
- Tightened `tools/validate_story_asset_authenticity.py` with pixel-level visual signature checks for Fairy/Woodcutter pages 15, 16, and 18 so this specific indoor-tableau bleed-through cannot pass on prompt/manifest metadata alone.
- Updated premium sheet validation so six-panel sheets remain checked as source artifacts while selected runtime art may be per-page local generated art. Stale `sourceSheet`/`panelIndex` selected metadata is cleared for the local renderer.
- Regenerated `tools/output/image_prompts.md`, `tools/output/audio_prompts.md`, 1,396 synthetic narration entries/files, procedural ambient/UI/SFX draft audio, and synced canonical `shared-content/` into the iOS bundled resources.
- Generated full-catalog HTML contact sheets for all 24 stories under `.agent/tmp/artifacts/story-asset-authenticity/contact-sheets/`.

Validation:

- `python3 tools/validate_books.py` passed.
- `python3 tools/validate_story_quality.py` passed.
- `python3 tools/validate_all_story_standard.py` passed.
- `python3 tools/validate_story_specific_art.py` passed.
- `python3 tools/validate_premium_imagegen_sheets.py` passed.
- `python3 tools/validate_visual_system_readiness.py` passed.
- `python3 tools/validate_visual_layout.py` passed.
- `python3 tools/validate_story_asset_authenticity.py` passed.
- `scripts/agent/validate` passed after the final Fairy/Woodcutter visual repair, including SwiftPM build/tests and Android Gradle test/assembleDebug.
- `scripts/agent/smoke ios` passed earlier and saved `.agent/tmp/artifacts/ios-smoke-transcript.md`; a later rerun after final content sync built/installed and wrote screenshots/transcript but hung in CoreSimulator `simctl launch`, so the stale process was terminated. Android emulator manual smoke was not run because no attached Android device/emulator was needed for this content-only pass.

Remaining gaps:

- Visual art is still generated/internal-demo art, not commissioned final art.
- Narration and sound are synthetic/procedural drafts, not human-recorded or professionally mastered final audio.
- Cultural authenticity remains internal AI/repo review only; final release still needs Korean-language, Korean cultural, child-safety, and children’s editorial human signoff.
- Store/backend/compliance evidence remains capped by existing readiness validators: local stub/OpenAPI backend, missing final privacy/store/signing/product evidence, and no target parent/customer testing evidence.
- No `origin/main` comparison could be performed because this workspace has no `.git` metadata.

## Context and Orientation

Canonical story and asset truth lives under `shared-content/`. Complete catalog stories are listed in `shared-content/catalog.json`, story text and per-page metadata live in `shared-content/books/*.json`, character bibles live in `shared-content/characters/*.json`, and selected runtime image assets are resolved through `shared-content/assets/manifests/image_manifest.json`.

Premium story art currently comes from generated six-panel story sheets under `shared-content/assets/generated-draft/images/story-sheets/`. `tools/import_imagegen_premium_sheets.py` crops panels into runtime covers and scenes, while `tools/validate_premium_imagegen_sheets.py` verifies importer metadata and panel mapping. Free-story and runtime draft assets live under `shared-content/assets/books/` and `shared-content/assets/generated-draft/images/`.

Relevant reports and tools include `tools/output/story_specific_art_audit.md`, `tools/output/visual_layout_qa_report.md`, `tools/output/*contact_sheet*`, `tools/validate_story_specific_art.py`, `tools/validate_premium_imagegen_sheets.py`, `tools/repair_fairy_woodcutter_authenticity.py`, and `tools/generate_sun_moon_scene_art.py`.

## Plan of Work

1. Build a catalog-driven audit table with one row per complete story.
2. Inspect story JSON text, `storyBeat` metadata, `imagePrompt` fields, cover art, story sheet, runtime scene assets, and manifest panel mapping.
3. Add or extend validators for discovered mismatch classes, especially wrong panel-to-page ranges, known sensitive beat requirements, and false production-readiness/status claims.
4. Fix mismatches in the smallest appropriate layer: story text/prompts, mapping logic, manifest entries, reports, or regenerated/replaced draft assets.
5. Generate or inspect contact sheets for all stories and run manual visual checks on representative assets.
6. Run required focused validators and full harness validation.
7. Update this plan with findings, fixes, validation, and remaining non-final gaps.

## Concrete Steps

1. Run inventory scripts over catalog, books, image manifest, character bibles, and asset folders.
2. Save a machine-readable audit snapshot and Markdown table under `.agent/tmp/artifacts/story-asset-authenticity/` and/or `tools/output/`.
3. Review known high-risk stories first (`fairy-and-woodcutter`, `sun-and-moon`), then continue through the full catalog.
4. Patch validators and importer expectations before or alongside content/asset fixes.
5. Re-import or regenerate selected assets only through repo tooling or clearly marked generated-draft outputs.
6. Run:
   - `python3 tools/validate_books.py`
   - `python3 tools/validate_story_quality.py`
   - `python3 tools/validate_all_story_standard.py`
   - `python3 tools/validate_story_specific_art.py`
   - `python3 tools/validate_premium_imagegen_sheets.py`
   - `python3 tools/validate_visual_system_readiness.py`
   - `python3 tools/validate_visual_layout.py`
   - `scripts/agent/validate`

## Validation and Acceptance

- Every complete catalog story has an audit row containing slug, page count, access tier, known folktale core beats, sensitive emotional beats, scene asset count, cover path, story sheet path when applicable, mismatch findings, and required fixes.
- Validators fail on the mismatch classes fixed in this pass.
- Selected runtime scene and cover assets remain present and status-honest.
- Contact sheets or equivalent manual visual artifacts exist for every catalog story.
- Required validators and `scripts/agent/validate` pass, or any command that cannot run has a specific environment-backed explanation.
- Remaining gaps clearly distinguish internal-demo generated art from human cultural/editorial review and commissioned final art.

## Idempotence and Recovery

The audit scripts should be deterministic and catalog-driven. Generated reports can be rerun without manual cleanup. If a validator fails, inspect the exact story/page key and fix the source content, importer mapping, or manifest metadata rather than weakening the check. Temporary screenshots and review artifacts belong under `.agent/tmp/artifacts/`; durable reports can live under `tools/output/`.
