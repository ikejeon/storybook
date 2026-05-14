# Scene Animation Layer Assets ExecPlan

## Purpose / Big Picture

Make the scene animation score earn its maximum through repository evidence instead of scorecard wording. The missing proof is actual layer assets and runtime metadata for every catalog scene, not only layer plans or native overlay code.

This pass also removes the stale legacy scoring snapshot and harness dependencies on it so future scoring starts from current artifacts and command output rather than an old summary.

## Progress

- [x] Ran `scripts/agent/doctor`.
- [x] Found legacy scoring snapshot references in the docs harness and historical plans.
- [x] Found scene animation currently depends on layer plans plus native overlay treatment.
- [x] Delete the stale scorecard and remove references to it.
- [x] Materialize runtime layer assets for every complete catalog scene.
- [x] Wire native models/runtime to load layer assets where present.
- [x] Strengthen validators/scorers so max animation score requires layer assets.
- [x] Sync shared content into native bundles.
- [x] Run validation and record outcomes.

## Surprises & Discoveries

- Python Pillow is not installed, so generated layer PNGs need a dependency-free PNG writer.
- The app already has native layered treatment on iOS and Android, but it does not yet load separated runtime layer PNGs.

## Decision Log

- Treat generated runtime layer assets as `generated_reviewed`, not final commissioned production animation.
- Keep final human animation/art approval separate from repo-local animation maximum.
- Remove stale scorecard dependencies instead of archiving the file, because the user explicitly wants it gone.

## Outcomes & Retrospective

Completed on 2026-05-12.

The stale legacy scoring snapshot was deleted and harness/docs references to it were removed. Future scoring should use current source, manifests, assets, command output, smoke artifacts, tests, and external review evidence.

Scene animation now has repository evidence beyond plans:

- `tools/materialize_scene_animation_layers.py` generated 4,188 runtime layer PNG assets for 698 complete scenes.
- `shared-content/animation/layer_manifest.json` now records generated-review `outputFile` paths for all required roles: background, midground, character, foreground, effect, and particle glow.
- Every book page animation layer now references its runtime layer asset path.
- iOS and Android models accept layer `outputFile` metadata.
- iOS and Android layered scene runtime now load those generated layer assets while preserving reduced-motion behavior.
- `tools/validate_books.py`, `tools/validate_all_story_standard.py`, `tools/score_art_experience.py`, and `tools/validate_visual_system_readiness.py` now fail if materialized layer assets are missing.

Validation passed:

- `python3 tools/validate_books.py`
- `python3 tools/validate_all_story_standard.py`
- `python3 tools/score_art_experience.py`: Scene animation 100/100.
- `python3 tools/validate_visual_system_readiness.py`: Scene animation 100/100.
- `scripts/agent/validate`
- `scripts/agent/validate-ui`, including backend smoke, iOS simulator smoke, Android emulator smoke, artifact-backed reader score, and strict visual layout QA.

## Context and Orientation

- Canonical scene animation data lives in `shared-content/animation/layer_manifest.json`.
- Story page animation metadata lives in `shared-content/books/*.json`.
- iOS reader animation is in `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/Views.swift`.
- Android reader animation is in `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/ui/MoonJarApp.kt`.
- Scoring/validation gates are `tools/score_art_experience.py` and `tools/validate_visual_system_readiness.py`.

## Plan of Work

1. Remove the legacy scoring snapshot and all explicit references to it.
2. Add a deterministic layer materialization tool.
3. Generate per-role layer PNG assets for every complete scene.
4. Update book page animation layers and layer manifest entries with actual asset paths.
5. Update iOS and Android animation models and rendering to load layer assets.
6. Strengthen validators so layer files are required for max scene animation.
7. Run harness validation.

## Concrete Steps

- Delete stale scorecard file.
- Patch docs/harness references.
- Add `tools/materialize_scene_animation_layers.py`.
- Run the materializer.
- Patch native models/views.
- Patch visual scorers.
- Sync `shared-content/` into iOS resources.
- Run targeted checks and full validation.

## Validation and Acceptance

Accepted when:

- No repo file mentions the removed legacy scorecard path.
- Scene animation checks require existing layer asset files.
- Every complete scene has all required layer roles with generated-review runtime assets.
- iOS and Android source load layer assets rather than relying only on procedural overlays.
- `scripts/agent/validate` passes.

## Idempotence and Recovery

The materializer is deterministic and safe to rerun. If a layer asset or metadata path is missing, rerun `python3 tools/materialize_scene_animation_layers.py` and then sync shared content to the iOS bundle.
