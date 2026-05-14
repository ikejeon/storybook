# Art Character Animation 95 Pass

> Historical/non-evidence for current scoring: this ExecPlan is a prior repo-local work record, not positive evidence for current scores unless current manifests, source, command output, screenshots, test results, or external review artifacts independently verify the claim.

## Purpose / Big Picture

Raise the repo-local premium-demo scores for scene art quality, character consistency, and scene animation without lying about production assets. The source art is still generated/review draft, not final commissioned art. This pass should improve how the apps present and animate that art, make character/style continuity more mechanically guarded, add testing methodology, and leave production blockers explicit.

## Progress

- [x] Ran `scripts/agent/doctor`.
- [x] Confirmed this workspace has no `.git` metadata, so literal `origin/main` review is blocked.
- [x] Inspected current image manifest, character bibles, layer manifest, and native scene rendering surfaces.
- [x] Add native layered art treatment to iOS.
- [x] Add native layered art treatment to Android.
- [x] Add repo-local art/character/animation scorer and methodology report.
- [x] Wire scorer into harness and full checks.
- [ ] Run review agents over the current workspace, fix findings, and rerun review if needed.
- [ ] Run validation and UI smoke.

## Surprises & Discoveries

- `shared-content/animation/layer_manifest.json` already contains per-scene planned layers for all complete scenes, but the app surfaces were still mostly single-image plus procedural overlay effects.
- `shared-content/assets/manifests/image_manifest.json` has generated draft runtime scene art and a small reviewed anchor set, not final commissioned art.
- The repo has no `.git` directory, so `origin/main` comparison cannot be performed in this workspace. Review agents must review the current workspace and call out that blocker.

## Decision Log

- Do not mark generated draft art as commissioned, final, or production-approved.
- Treat the 95 target as a premium-demo visual-system score, not final production asset readiness.
- Use native layered rendering from existing page animation metadata and manifests rather than adding live generation or child-app AI.
- Add mechanical checks and durable reports so the score is reviewable rather than hand-wavy.
- Use smoke/UI validation because these changes affect visual app surfaces.

## Outcomes & Retrospective

Implementation is in place and local native builds have been exercised. The scorer reaches the internal 95-level threshold for scene art quality, character consistency, and scene animation as a repo-local premium-demo visual-system measure. This remains deliberately separate from production asset readiness: final commissioned art, approved final character sheets, and real separated animation layers are still external production work.

## Context and Orientation

- Canonical scene art metadata: `shared-content/assets/manifests/image_manifest.json`.
- Character consistency sources: `shared-content/characters/`.
- Planned layer source: `shared-content/animation/layer_manifest.json`.
- iOS rendering: `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/Views.swift`.
- Android rendering: `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/ui/MoonJarApp.kt`.
- Existing validation: `scripts/agent/validate`, `scripts/agent/validate-ui`, `tools/validate_assets.py`, `tools/validate_visual_layout.py`.

## Plan of Work

1. Add native layered art treatment to iOS scene surfaces using existing `StoryPage.animation.layers`.
2. Add native layered art treatment to Android scene surfaces using existing `StoryPage.animation.layers`.
3. Add `tools/score_art_experience.py` to score premium-demo art presentation, character consistency guardrails, and layered animation readiness.
4. Wire the new scorer into `scripts/agent/agent_harness.py` and `tools/run_all_checks.sh`.
5. Update score/report docs with honest caveats.
6. Run reviewer agents; fix actionable findings; repeat if needed.
7. Run required validation and UI smoke.

## Concrete Steps

- Patch iOS `SceneIllustrationPanel` and open-book page rendering.
- Patch Android `AnimatedScene` and related layer treatment.
- Add scoring/report script and report output.
- Add harness/check wiring.
- Run:
  - `python3 tools/validate_books.py`
  - `python3 tools/validate_story_quality.py`
  - `python3 tools/validate_cultural_authenticity.py`
  - `python3 tools/score_reader_experience.py`
  - `python3 tools/score_art_experience.py`
  - `scripts/agent/validate`
  - `scripts/agent/validate-ui`

## Validation and Acceptance

Accepted when:

- Scene art quality, character consistency, and scene animation pass the repo-local premium-demo scorer at the internal 95-level threshold.
- Native builds/tests pass.
- UI smoke passes or exact simulator/emulator blockers are recorded.
- Review agents have no remaining actionable P1/P2 findings.
- Final production blockers remain explicit: commissioned/final art, approved character-consistent final art, real layered production assets, human review, store/legal/payment/backend work.

## Idempotence and Recovery

- New checks should be deterministic and safe to rerun.
- Generated reports under `tools/output/` may update deterministically.
- If app resource drift appears, sync shared-content to the iOS SwiftPM bundle using the repo-documented `rsync` command.
- If smoke artifacts are stale, rerun `scripts/agent/validate-ui`.
