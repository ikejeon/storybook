# Moon Jar Stories Documentation Map

This directory contains the authoritative repo guidance for product, engineering, safety, plans, and production operations.

## Core Engineering Docs

| Doc | Purpose |
| --- | --- |
| `README.md` | This documentation map. |
| `ARCHITECTURE.md` | Current system map, boundaries, and dependency direction rules. |
| `HARNESS.md` | Agent command harness, checks, artifacts, and local workflow. |
| `PLANS.md` | ExecPlan format and expectations. |
| `RELIABILITY.md` | Startup, tests, builds, logging, smoke checks, and recovery. |
| `SECURITY.md` | Secrets, kids safety, dependency hygiene, and agent boundaries. |
| `SCORE_95_REQUIREMENTS.md` | Evidence-based requirements for honestly reaching 95-level scores. |
| `PRODUCT_SENSE.md` | User-visible product principles and taste guidance. |

## Product / Content / Compliance Docs

| Doc | Purpose |
| --- | --- |
| `product_plan.md` | Product scope and commercial direction. |
| `design_system.md` | Visual identity and design system details. |
| `asset_production_pipeline.md` | Offline art/audio production workflow. |
| `production_pipeline.md` | Broader content production pipeline. |
| `entitlement_rules.md` | Subscription and unlock rules. |
| `payments_native_vs_revenuecat_decision.md` | Payment architecture decision. |
| `app_store_safety.md` | App Store safety notes. |
| `compliance_kids_safety.md` | Kids privacy and compliance checklist. |
| `privacy_policy_draft.md` | Draft privacy policy aligned to current app behavior; not legal final. |

## Product / Store / Backend Artifacts

| Path | Purpose |
| --- | --- |
| `../product/market-validation/market_validation_plan.json` | Machine-readable market, pricing, and distribution experiment plan; not external demand evidence. |
| `../product/market-validation/source_backed_positioning.md` | Public source-backed competitor/distribution notes for planning. |
| `../product/release_readiness_ledger.json` | Repo-owned artifacts and remaining external blockers by score category. |
| `../store/product_configuration_manifest.json` | Planned product IDs and store-evidence status. |
| `../store/app_store_metadata_draft.json` | Draft App Store listing metadata; not submitted. |
| `../store/google_play_metadata_draft.json` | Draft Google Play listing metadata; not submitted. |
| `../store/privacy_labels_draft.json` | Draft privacy/data-safety label mapping. |
| `../backend/deployment_readiness_manifest.json` | Backend deployment preparation; not deployed evidence. |
| `../backend/receipt_verification_contract.json` | Receipt/token verification contract; not integrated with store APIs. |

## Planning Areas

- Active plans: `exec-plans/active/`
- Completed plans: `exec-plans/completed/`
- Tech debt tracker: `exec-plans/tech-debt-tracker.md`
- Future design docs: `design-docs/index.md`
- Generated docs/reports: `generated/`
- External references/sources: `references/`

## Authoritative Data

`shared-content/` is the authoritative source for catalog, story JSON, schemas, character bibles, design tokens, assets, audio manifests, and compliance flags. Native apps should not duplicate story text or asset metadata in app code.

## Freshness Rule

If you change architecture, commands, app startup, validation, asset status, payments, compliance, or story/content shape, update the relevant doc and run:

```bash
scripts/agent/lint
```
