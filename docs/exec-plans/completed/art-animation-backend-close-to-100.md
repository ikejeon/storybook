# Art Animation Backend Close To 100 Pass

> Historical/non-evidence for current scoring: this ExecPlan is a prior repo-local work record, not positive evidence for current scores unless current manifests, source, command output, screenshots, test results, or external review artifacts independently verify the claim.

## Purpose / Big Picture

Raise the repo-local premium-demo readiness for scene art quality, character consistency, scene animation, and Backend/CMS readiness as far as repository work can honestly take them. This is not a production-release asset pass: generated draft art stays marked as generated draft, narration is explicitly out of scope, and final commissioned art/human approvals remain external blockers.

## Progress

- [x] Read `README.md`, `docs/README.md`, and ran `scripts/agent/doctor`.
- [x] Confirmed existing art scorer already reports 100/100 for repo-local premium-demo checks.
- [x] Started a combined plan for visual-system and Backend/CMS hardening.
- [x] Add durable visual review and runtime animation capability artifacts.
- [x] Add a stricter visual-system readiness validator.
- [x] Upscale the twelve low-resolution Red Bean Grandma runtime draft scenes and refresh manifest dimensions.
- [x] Upgrade the backend stub with local persistence, CMS export, review queue, and release-readiness endpoints.
- [x] Update OpenAPI and backend docs for the new local CMS behavior.
- [x] Wire new checks into `scripts/agent/test` and `tools/run_all_checks.sh`.
- [x] Run visual/backend readiness checks and backend smoke.
- [x] Run `scripts/agent/validate` and record results.

## Surprises & Discoveries

- The previous art/character/animation pass already added native layered treatments and a 100/100 repo-local scorer, but it lacks a durable cross-role visual review artifact and a stricter separate readiness validator.
- Backend/CMS readiness is the weakest code-owned item: `backend/service_stub.py` validates several payloads, but does not yet persist local review state, expose a review queue, export complete book JSON, or summarize release readiness.
- Twelve selected Red Bean Grandma runtime draft scenes were only 512x256. They were upscaled to 1024x512 and the image manifest was refreshed with dimensions for all selected image groups.

## Decision Log

- Keep final-production claims separate from premium-demo/system readiness.
- Do not change generated draft scene assets to commissioned or final statuses.
- Use local `.agent/tmp/` state for backend stub persistence so the repo gains a realistic workflow without committing mutable runtime data.
- Make admin auth optional in local development and enforce it automatically when `MOONJAR_ADMIN_TOKEN` is set.
- Add validators and reports rather than relying on prose-only score changes.

## Outcomes & Retrospective

Pending implementation and validation.
Implementation is complete for this repo-local pass. `python3 tools/validate_visual_system_readiness.py`, `python3 tools/score_backend_cms_readiness.py`, `scripts/agent/smoke backend`, and `scripts/agent/validate` all pass. Remaining blockers are external production work: commissioned final art, final character-pack approval, separated production animation assets, deployed backend/CMS UI/RBAC/audit logs, receipt verification, store setup, legal/privacy review, and narration research.

## Context and Orientation

- Existing visual scorer: `tools/score_art_experience.py`.
- Image manifest: `shared-content/assets/manifests/image_manifest.json`.
- Character bibles: `shared-content/characters/`.
- Animation layer manifest: `shared-content/animation/layer_manifest.json`.
- Backend stub: `backend/service_stub.py`.
- Backend contract: `backend/openapi.yaml`.
- Harness wiring: `scripts/agent/agent_harness.py` and `tools/run_all_checks.sh`.

## Plan of Work

1. Add visual review and animation capability artifacts that explicitly approve premium-demo readiness while preserving final-production blockers.
2. Add `tools/validate_visual_system_readiness.py` and wire it into the normal test harness.
3. Extend `backend/service_stub.py` with local state, CMS export, review queue, asset import, release readiness, and optional admin token checks.
4. Extend `backend/openapi.yaml` and backend docs for the added endpoints.
5. Add `tools/score_backend_cms_readiness.py` and wire it into the normal test harness.
6. Update the scorecard with higher repo-local scores and honest external blockers.

## Concrete Steps

- Create `shared-content/reviews/visual_art_readiness_review.json`.
- Create `shared-content/animation/runtime_animation_capabilities.json`.
- Add visual and backend/CMS validators under `tools/`.
- Patch `backend/service_stub.py`, `backend/openapi.yaml`, `backend/README.md`, `backend/cms_schema.md`, and `backend/admin_workflow.md`.
- Patch `scripts/agent/agent_harness.py`, `tools/run_all_checks.sh`, and relevant docs.
- Run:
  - `python3 tools/validate_visual_system_readiness.py`
  - `python3 tools/score_backend_cms_readiness.py`
  - `scripts/agent/smoke backend`
  - `scripts/agent/validate`

## Validation and Acceptance

Accepted when:

- Visual-system readiness validator passes the internal 95-level threshold for scene art quality, character consistency, and scene animation.
- Backend/CMS validator passes the internal 95-level threshold.
- Backend smoke covers the new CMS/review endpoints.
- `scripts/agent/validate` passes or any environment blocker is recorded exactly.
- Docs and scorecard still state that final commissioned art, approved final character packs, separated production animation assets, deployed backend/auth/CMS UI, and human approvals remain external production work.

## Idempotence and Recovery

- Validators and reports are deterministic.
- Backend state is local runtime data under `.agent/tmp/` and can be deleted safely.
- If a backend smoke run leaves a process running, use `scripts/agent/stop backend`.
- If shared-content bundle drift appears, follow the rsync command printed by `scripts/agent/check-architecture`.
