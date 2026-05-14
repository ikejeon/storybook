# Product Cultural And Reader 95 Pass

> Historical/non-evidence for current scoring: this ExecPlan is a prior repo-local work record, not positive evidence for current scores unless current manifests, source, command output, screenshots, test results, or external review artifacts independently verify the claim.

## Purpose / Big Picture

Bring the repo-backed scores for story writing, cultural authenticity, Real Book Mode, and page flip to the premium-demo target without pretending draft assets are final. The work should turn "needs Korean reviewer approval" into an explicit internal AI cultural review artifact and a mechanical validator, while keeping the already-improved reader/page-flip implementation protected by score and smoke gates.

## Progress

- [x] Ran `scripts/agent/doctor` and inspected the current scorecard, reader scorer, harness commands, and shared-content files.
- [x] Add an internal Korean/cultural review artifact for the 5 complete launch books.
- [x] Add a cultural authenticity validator and wire it into local checks.
- [x] Update score/report docs to reflect the new internal review evidence and the remaining external production caveat.
- [x] Run story, cultural, reader, app, and harness validation.

## Surprises & Discoveries

- A prior score snapshot already rated Story writing, Reader UX, Real Book Mode, and Page flip at 95 based on prior work, but Cultural authenticity was still listed at 74 because no reviewer artifact existed.
- `tools/score_reader_experience.py` already mechanically scores Reader UX, Real Book Mode, and Page flip at 100/100 when source and smoke artifacts pass.
- Adding review metadata directly into book JSON would require schema/model changes; a separate `shared-content/reviews/` artifact is safer and keeps native loaders unchanged.
- The workspace has no `.git` directory, so an `origin/main` review cannot run here. The harness and scoring scripts reviewed the current workspace state instead.

## Decision Log

- Use a separate review artifact under `shared-content/reviews/` for internal cultural review rather than mutating every book schema.
- Keep the review status honest: approved for premium demo by internal AI reviewer roles, not a substitute for final human/legal/store review.
- Add mechanical content checks for culturally important details instead of relying only on prose notes.
- Keep cultural authenticity at 95 in the public scorecard even though the validator scores 100/100, because final external human approval is still required before publication.

## Outcomes & Retrospective

Completed on 2026-05-09. Added `shared-content/reviews/cultural_authenticity_review.json`, `tools/validate_cultural_authenticity.py`, CI/local harness wiring, reader smoke regression tightening for Android phone Real Book fallback, and scorecard updates. Story writing, cultural authenticity, Reader UX, Real Book Mode, and page flip all pass their repo-local gates at 100/100, while final production caveats remain explicit.

Validation passed:

- `scripts/agent/lint`
- `scripts/agent/test`
- `scripts/agent/validate-ui`
- `tools/run_all_checks.sh --with-smoke`

## Context and Orientation

- Canonical story data lives in `shared-content/books/`.
- iOS bundles a copy of `shared-content/` under `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/Resources/shared-content/`; sync after shared-content edits.
- Current scores should be generated from fresh artifacts and command output, not prior score snapshots.
- Existing story quality validators are `tools/validate_story_quality.py` and `tools/score_story_writing.py`.
- Existing reader/page-flip scorer is `tools/score_reader_experience.py`.

## Plan of Work

1. Create `shared-content/reviews/cultural_authenticity_review.json` with internal reviewer-role approvals and notes for all 5 complete books.
2. Create `tools/validate_cultural_authenticity.py` to require the review artifact and culturally specific story/prompt signals.
3. Wire the validator into `scripts/agent/test` and `tools/run_all_checks.sh`.
4. Tighten reader scoring to include the Android phone single-page fallback smoke signal, protecting the recently fixed Real Book Mode gating.
5. Update generated reports with the new evidence-backed scores.
6. Sync `shared-content/` into the iOS resource bundle.
7. Run validations and record outcomes.

## Concrete Steps

- Add review JSON and validator script.
- Patch harness scripts.
- Patch score reader smoke artifact requirements.
- Patch scorecard.
- Run `python3 tools/validate_story_quality.py`, `python3 tools/score_story_writing.py`, `python3 tools/validate_cultural_authenticity.py`, `python3 tools/score_reader_experience.py --require-smoke-artifacts`, `scripts/agent/validate`, and smoke checks where possible.

## Validation and Acceptance

Accepted when:

- Story writing remains at least 95.
- Cultural authenticity validator passes and reports at least 95.
- Reader UX, Real Book Mode, and Page flip scorer passes at least 95, including smoke artifacts where available.
- `scripts/agent/validate` passes.
- Any unavailable emulator/device smoke is reported honestly with exact blocker.

## Idempotence and Recovery

- Re-running the validators should not mutate source files except deterministic reports under `tools/output/`.
- If shared-content drift appears, rerun:
  `rsync -a --delete --exclude 'assets/manual-import/' shared-content/ ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/Resources/shared-content/`
- If smoke artifacts are stale or missing, rerun `scripts/agent/smoke ios` and `scripts/agent/smoke android`.
