# All Story Standard ExecPlan

## Purpose / Big Picture

Make the repo treat every catalog story as the standard unit of product coverage. A future audit, score, harness check, or review artifact should not be able to pass by looking only at a small demo subset. The app may still distinguish free and premium access, but validation must cover all 24 complete catalog books.

## Progress

- [x] Confirmed the catalog currently contains 24 complete books.
- [x] Started stale demo-subset scan across current docs, scripts, manifests, and review artifacts.
- [x] Add an executable all-story coverage validator.
- [x] Wire the validator into the agent harness and all-checks script.
- [x] Refresh current review/artifact wording so it describes all catalog stories.
- [x] Run the full harness validation and record outcomes.

## Surprises & Discoveries

- Current content coverage is broad, but several active plans and review notes still use older small-subset or subset-demo language.
- Generated outputs and historical score docs can contain stale counts; the new validator should focus on current artifacts and harness-facing docs rather than using old score material as product evidence.

## Decision Log

- Coverage means catalog-driven coverage: every `status: complete` catalog entry needs story JSON, pages, scene art, cover art, English/Korean narration, ambient audio, layer entries, character bible coverage, review artifact coverage, and ownership-ledger coverage.
- Premium books can remain entitlement-locked. The standard being enforced is coverage quality, not free access.
- The validator should fail on stale active/current language that implies only a demo subset is covered.

## Outcomes & Retrospective

Completed on 2026-05-12.

Added `tools/validate_all_story_standard.py` and wired it into `scripts/agent/agent_harness.py` plus `tools/run_all_checks.sh`. The validator now fails unless every catalog book is complete and covered by story pages, reviewed runtime scene art, cover art, English/Korean narration, ambient audio, layer plans, character bibles, cultural/visual review artifacts, and the asset ownership ledger. It also blocks current-facing stale subset language such as old five-book, old scene-count, old narration-count, or incomplete-catalog claims.

Refreshed current review/generator wording from subset-demo language to all-catalog demo language, synced canonical `shared-content/` into the iOS bundled resources, and moved completed historical ExecPlans out of `docs/exec-plans/active/`.

Validation passed:

- `python3 tools/validate_all_story_standard.py`: passed with 24 catalog books, 698 scenes, and 1,396 required narration entries covered.
- `scripts/agent/validate`: passed.
- `scripts/agent/validate-ui`: passed, including backend smoke, iOS simulator smoke, Android emulator smoke, artifact-backed reader scoring, and strict visual layout QA.

## Context and Orientation

Canonical product data lives under `shared-content/`. Native apps render shared content from that data rather than forking story text. The main harness entry points are `scripts/agent/test`, `scripts/agent/validate`, `scripts/agent/validate-ui`, and `tools/run_all_checks.sh`.

## Plan of Work

1. Add `tools/validate_all_story_standard.py`.
2. Insert it after book/story checks in the harness.
3. Update current all-story language in review artifacts and generators.
4. Regenerate affected reports where appropriate.
5. Run targeted validator, `scripts/agent/validate`, and UI validation if available.

## Concrete Steps

1. Build catalog/page expectation maps from `shared-content/catalog.json` and `shared-content/books/*.json`.
2. Compare those expectations against image, audio, layer, character, review, and ownership artifacts.
3. Scan current-facing files for stale subset phrases.
4. Patch harness scripts.
5. Refresh reports.

## Validation and Acceptance

- `python3 tools/validate_all_story_standard.py` passes.
- `scripts/agent/validate` passes.
- `scripts/agent/validate-ui` passes or any environment blocker is recorded explicitly.
- No current-facing artifact claims only an old demo-subset or stale scene-count standard.

## Idempotence and Recovery

All edits are deterministic and can be rerun. If validation fails, inspect the listed missing book/page keys and update the relevant manifest or review artifact instead of weakening the check.
