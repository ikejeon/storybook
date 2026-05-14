# Non-Human Readiness Closeout

## Purpose / Big Picture

Finish the repository-owned gaps identified by the external-validation score audit while keeping the scorecard honest. This pass should not pretend that missing people, store accounts, deployed production infrastructure, or final commissioned assets already exist. It should convert every feasible non-human blocker into current artifacts, configuration, validators, and harness output.

## Progress

- [x] Read `README.md`.
- [x] Read `docs/README.md`.
- [x] Read the harness engineering ExecPlan.
- [x] Ran `scripts/agent/doctor`.
- [x] Add market, pricing, distribution, privacy, store, and launch-readiness artifacts that are useful without claiming external validation.
- [x] Add or tighten validators so those artifacts stay current and cannot be hand-wavy.
- [x] Wire new checks into the agent harness.
- [x] Run `scripts/agent/validate` and any practical smoke checks.
- [x] Update scoring/audit notes with the new evidence and remaining true blockers.

## Surprises & Discoveries

- The harness already runs a scorecard truthfulness validator and keeps external validation caps explicit.
- The prior audit correctly found no real parent/customer evidence, no final privacy policy, no legal/store signoff, no store products, no deployed backend, and no final art/audio.
- The first `scripts/agent/validate` run failed because the new canonical compliance data-flow file had not been synced into the iOS bundled shared-content copy. Running the documented `rsync` fixed it, and validation passed afterward.

## Decision Log

- Treat docs as supporting artifacts only when paired with machine-readable files or validators.
- Use explicit `draft`, `planned`, `not_configured`, and `blocked` statuses where real store/backend/account evidence is absent.
- Do not raise production scores by creating plans.
- Add validation coverage for market/distribution planning, privacy/data-flow mapping, store packaging metadata, accessibility QA checklists, and external blocker accounting.

## Outcomes & Retrospective

Completed on 2026-05-11.

Added repo-owned non-human readiness artifacts:

- `product/market-validation/market_validation_plan.json`
- `product/market-validation/source_backed_positioning.md`
- `product/release_readiness_ledger.json`
- `shared-content/compliance/data_flow_map.json`
- `docs/privacy_policy_draft.md`
- `store/privacy_labels_draft.json`
- `store/accessibility_qa_checklist.json`
- `store/product_configuration_manifest.json`
- `store/app_store_metadata_draft.json`
- `store/google_play_metadata_draft.json`
- `store/release_assets_manifest.json`
- `backend/deployment_readiness_manifest.json`
- `backend/receipt_verification_contract.json`

Added `tools/validate_non_human_readiness.py`, wired it into `scripts/agent/test`, `tools/run_all_checks.sh`, and `.github/workflows/agent-harness.yml`, and synced the new compliance artifact into the iOS shared-content bundle.

Validation results:

- `python3 tools/validate_non_human_readiness.py`: passed.
- `python3 tools/validate_scorecard_truthfulness.py tools/output/product_score_external_validation_audit.md`: passed.
- `scripts/agent/validate`: passed after syncing iOS bundled shared-content.
- `scripts/agent/validate-ui`: passed, including backend smoke, iOS simulator smoke, Android emulator smoke, artifact-backed reader scoring, and strict visual layout QA.
- `tools/run_all_checks.sh --with-smoke`: passed, including backend/iOS/Android smoke, native builds/tests, strict layout, and generated-draft readiness.

Remaining blockers are still real: parent/customer demand evidence, external editorial/Korean/cultural/legal/store review, final art/audio, real store-console product setup, deployed backend with receipt/token verification, and real-device/accessibility/store-submission QA.

## Context and Orientation

- Current score audit: `tools/output/product_score_external_validation_audit.md`.
- Score guardrail: `tools/validate_scorecard_truthfulness.py`.
- Harness: `scripts/agent/agent_harness.py`.
- Compliance flags: `shared-content/compliance/app_behavior_flags.json`.
- Payments scaffold: `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/EntitlementStore.swift` and `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/billing/EntitlementManager.kt`.
- Backend stub: `backend/service_stub.py`.

## Plan of Work

1. Add machine-readable market/pricing/distribution readiness artifacts and a validator.
2. Add machine-readable privacy/data-flow and store-readiness artifacts and a validator.
3. Add a release blocker ledger that distinguishes completed repo-owned work from blocked external work.
4. Wire the new validators into `scripts/agent/test`.
5. Run the harness and update this plan with exact results.

## Concrete Steps

- Create files under `product/market-validation/`, `shared-content/compliance/`, and `store/`.
- Add `tools/validate_non_human_readiness.py`.
- Update docs index and harness wiring.
- Run:
  - `python3 tools/validate_non_human_readiness.py`
  - `scripts/agent/validate`
  - practical smoke commands when simulator/emulator/backend are available

## Validation and Acceptance

Accepted when:

- Every repo-owned non-human gap has a current artifact or a clear external blocker.
- New artifacts are checked by a validator.
- The normal agent harness passes.
- The score audit still refuses to count plans as external/human proof.

## Idempotence and Recovery

The new artifacts should be deterministic, small, and safe to update. Generated smoke and validation artifacts remain under `.agent/tmp/`. If a validator fails, fix the source artifact rather than loosening the rule.
