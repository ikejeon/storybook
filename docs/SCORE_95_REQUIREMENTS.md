# Score 95 Requirements

This file defines what a 95-level score means for Moon Jar Stories. It is a rubric, not evidence that any score has been earned.

## Evidence Rules

Prior score documents and progress summaries are claims, not evidence. Scores must be based on current repo artifacts, command output, screenshots, manifest counts, and external/human review evidence.

Use this evidence order:

1. Tier 1: current source code, current manifests, current asset files, command outputs, screenshots/videos, test results, running app evidence, real store configuration, and real backend deployment/config.
2. Tier 2: schema files, generated reports based on current files, validation scripts, contact sheets, and asset status reports.
3. Tier 3: docs, plans, product summaries, old scorecards, and self-written claims.

Docs cannot raise a score unless backed by Tier 1 or Tier 2 evidence.

Repo-owned non-human readiness artifacts, such as market experiment plans, draft store metadata, data-flow maps, and deployment manifests, are useful Tier 2 support only when validators check them. They do not replace parent testing, external review, real store-console configuration, deployed backend evidence, or final production assets.

## Concept Score 95

- Clear audience and buyer are validated with user interviews or parent testing.
- Competitor/distribution analysis supports the market niche.
- Pricing is tested with target families.
- The product promise is backed by a working demo and credible content pipeline.
- Retention or willingness-to-pay evidence exists.

## Engineering/Demo Readiness 95

- iOS and Android builds pass from clean checkout.
- Reader works on simulator/emulator and has screenshot or video evidence.
- Content loads from shared data, not duplicated app code.
- Assets and audio resolve through manifests.
- Page turn, Real Book Mode, narration controls, bedtime mode, and language controls work.
- Payment and parent-gate scaffolds are test-covered as demo behavior.
- Validation passes without stale scene-count assumptions.
- Smoke tests produce agent-readable artifacts.

## Content/Story Readiness 95

- Every complete book has finished English and Korean text.
- Story beats, vocabulary, reading levels, narration scripts, and prompts are complete.
- Human children's editor review is complete.
- Human Korean-language review is complete.
- Human cultural authenticity review is complete.
- Child-safety adaptation review is complete.
- Premium catalog entries carry complete shared-content payloads and remain locked by entitlement until purchased.

## Visual/Art Readiness 95

- All complete-scene images are reviewed or final.
- All covers are reviewed or final.
- Character packs are approved for consistency across scenes.
- Human creative, cultural, and child-safety review has approved the full visual set.
- Cropping/layout checks pass across supported devices.
- Production ownership/licensing is documented.
- No complete-scene runtime art remains only `generated_draft`.

## Audio Readiness 95

- English narration is final mastered professional/human narration, or reviewed high-quality synthetic narration approved for release.
- Korean narration is final mastered professional/human narration, or reviewed high-quality synthetic narration approved by a Korean reviewer.
- Ambient, UI, and story sounds are reviewed/final and licensed.
- Audio levels are normalized and QA'd on target devices.
- Narration timing, pronunciation, pacing, and bedtime tone are approved.
- No complete-scene narration remains only `synthetic_draft`.

## Payment Readiness 95

- Real App Store Connect and Google Play Console products exist.
- StoreKit and Google Play Billing purchase flows are implemented, not prototype unlocks.
- Restore purchase flows are tested on sandbox/TestFlight/internal tracks.
- Parent gates protect purchase and restore flows.
- Subscription, lifetime, and individual-book states map to entitlement state.
- Refund, revoke, grace-period, expiration, and family-sharing decisions are tested.
- Receipt/token verification is integrated with the backend.

## Backend Readiness 95

- Catalog, entitlement, purchase sync, and asset-manifest services are deployed.
- App Store Server API and Google Play purchase token verification are implemented.
- Durable persistence, backups, and migrations are in place.
- Admin workflow supports review/import/status operations with real auth.
- Monitoring, logs, alerts, audit trails, rate limits, and operational runbooks exist.
- Security review covers secrets, admin access, and child-data minimization.
- Smoke tests prove production/staging service behavior.

## Compliance Readiness 95

- Privacy policy is final and matches actual data collection.
- COPPA, Apple Kids Category, and Google Play Families review is complete.
- Legal/store reviewer signoff is documented.
- No ads, child-facing tracking, child accounts, or child-facing external links exist.
- Parent gates are tested around adult flows.
- Accessibility and age-appropriateness QA are complete.
- Any third-party SDK/provider data flow is reviewed and disclosed.

## Store Readiness 95

- Real bundle IDs, signing, provisioning, and release configs are complete.
- App icon, launch assets, screenshots, store metadata, privacy labels, and subscription disclosures are complete.
- Store products and restore flows are configured and tested.
- TestFlight/internal testing or equivalent evidence exists.
- Compliance review is complete.
- App binaries are ready for App Store and Play submission.

## Production Readiness 95

- Final/reviewed art exists for all complete scenes and covers.
- Final/professional narration and final sound design exist.
- Real StoreKit and Google Play Billing are configured and tested.
- Receipt/token verification backend and hosted CMS/backend are operational.
- Legal/privacy/compliance signoff is complete.
- Real-device and accessibility QA are complete.
- Store packaging, signing, listings, screenshots, privacy labels, and release metadata are complete.
- No major release blockers remain.
