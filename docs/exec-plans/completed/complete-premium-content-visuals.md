# Complete Premium Content And Visual Draft Coverage

## Purpose / Big Picture

Close the repo-local content/story and visual/art blockers that say 19 premium books are metadata-only and all complete-book art is only generated draft. This plan turns every catalog book into a complete shared-content book with runtime art/audio/animation manifest coverage, and it upgrades complete-book runtime image entries to internally reviewed demo art where the current artifacts can honestly support that label.

This is not a final production asset pass. External children’s editor, Korean-language, cultural, child-safety, legal, commissioned final art, production character pack, licensing, and human review approvals remain external blockers.

## Progress

- [x] Read `README.md`, `docs/README.md`, and planning guidance.
- [x] Ran `scripts/agent/doctor`.
- [x] Identified hardcoded 5-book / 138-scene assumptions in validators, tests, harness, and visual reports.
- [x] Generate complete premium story JSON, character bibles, local draft art, synthetic draft narration, image/audio/layer manifest entries, and review ledgers.
- [x] Update validators/tests/harness to use catalog-derived counts.
- [x] Sync shared content into the iOS resource bundle.
- [x] Run content, asset, story, cultural, visual, native, smoke, and full validation harnesses.

## Surprises & Discoveries

- `tools/validate_books.py` explicitly required exactly 5 complete books and required premium books to remain `metadata_only`.
- iOS/Android shared-content tests and backend smoke assertions also hardcoded the old 5-book / 138-scene shape.
- Cultural and visual validators were mostly data-driven, but still contained a few exact-count checks.
- `tools/score_story_writing.py` gave unknown premium book IDs a zero `book_tone` score because it had tone requirements only for the original five complete books.

## Decision Log

- Premium content will stay `access: premium`, but move to `status: complete` with `bookPath` so entitlement locking is still enforced by access, not missing content.
- Generated local visual assets will be marked `generated_reviewed` only for internal premium-demo use, with `productionApprovalStatus: not_approved`.
- Narration remains `synthetic_draft`; no professional or human-recorded claims will be made.
- Book JSON image fields remain fallback metadata where needed; runtime status truth lives in manifests.

## Outcomes & Retrospective

Completed on 2026-05-11. The catalog now has 24 complete books, 698 complete-book scenes, 24 generated-review covers, 24 character bibles, 1,396 synthetic-draft narration entries, 24 ambient loops, and layer plans for every complete scene. `scripts/agent/validate` and `scripts/agent/validate-ui` passed, including backend smoke, iOS simulator smoke, Android emulator smoke, strict visual layout QA, SwiftPM tests, Android tests, and Android assembleDebug.

Remaining blockers are intentionally external/final: external children’s editor, Korean-language, cultural, and child-safety review; commissioned final art/covers; final production character pack; commercial production licensing/legal signoff; professional or human-reviewed narration; store products; backend receipt verification; compliance review; real-device release QA.

## Context and Orientation

Source of truth lives in `shared-content/`. Native apps render catalog/book JSON and asset manifests from the shared bundle. The user specifically asked to fix two gaps:

- `Content/story`: 19 premium books metadata-only.
- `Visual/art`: all runtime scene and cover images generated draft, with no final character pack, approval, or licensing proof.

This plan can fix the repo-local metadata and draft/review coverage gaps, but cannot honestly fabricate external people review or final/licensing evidence.

## Plan of Work

1. Add a deterministic repo-local completion tool for premium books and manifest coverage.
2. Generate all missing premium story/audio/art/layer/character/review artifacts.
3. Update validators and tests to derive expected totals from the catalog.
4. Refresh reports and docs that describe the current repo state.
5. Sync iOS resources and run the agent harness end to end.

## Concrete Steps

1. Add `tools/complete_premium_content_visuals.py`.
2. Run the tool and inspect generated catalog counts/statuses.
3. Patch `tools/validate_books.py`, `tools/validate_visual_system_readiness.py`, `tools/score_art_experience.py`, `tools/score_story_writing.py`, native tests, and `scripts/agent/agent_harness.py`.
4. Refresh generated reports with existing report tools.
5. Sync shared content to iOS resources.
6. Run `scripts/agent/validate` and `scripts/agent/validate-ui` if simulator/emulator access allows.

## Validation and Acceptance

- `python3 tools/validate_books.py`
- `python3 tools/validate_assets.py`
- `python3 tools/validate_asset_status_crosswalk.py`
- `python3 tools/validate_story_quality.py`
- `python3 tools/score_story_writing.py`
- `python3 tools/validate_cultural_authenticity.py`
- `python3 tools/validate_visual_system_readiness.py`
- `python3 tools/score_art_experience.py`
- `python3 tools/validate_non_human_readiness.py`
- `python3 tools/validate_scorecard_truthfulness.py tools/output/product_score_external_validation_audit.md`
- `scripts/agent/validate`
- `scripts/agent/validate-ui` or exact reason if it cannot run.

## Idempotence and Recovery

The generation tool should be idempotent: rerunning it rewrites the deterministic premium content and upserts manifest entries by story/scene/language keys. Existing user-authored final approvals must not be overwritten by generated defaults.
