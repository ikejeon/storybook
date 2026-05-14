# Product Score External-Validation Audit

Generated: 2026-05-11

Prior score documents and progress summaries are claims, not evidence. Scores must be based on current repo artifacts, command output, screenshots, manifest counts, and external/human review evidence.

This audit reflects the current 24-book shared-content state after the content/visual closeout. Repo-local engineering, manifests, generated reports, and smoke artifacts are allowed evidence. Old scorecards, prior deltas, and optimistic summaries are not positive evidence.

## Revised Scorecard

| Category | Current Score | Cap Applied | Revised Score | Confidence |
| --- | ---: | --- | ---: | --- |
| Concept score | 86 | 80 | 80 | Medium |
| Engineering/demo readiness | 94 | No external-validation cap | 94 | High |
| Content/story readiness | 86 | 85 | 85 | Medium |
| Cultural authenticity | 80 | 80 | 80 | Medium |
| Visual/art readiness | 85 | 95 | 85 | Medium |
| Audio readiness | 45 | 55 | 45 | High |
| Payment readiness | 58 | 75 | 58 | High |
| Backend readiness | 69 | 75 | 69 | High |
| Compliance readiness | 78 | 80 | 78 | High |
| Store readiness | 38 | 50 | 38 | High |
| Production readiness | 60 | 72 | 60 | High |

Category: Concept score
Current Score: 86
Cap Applied: 80 because target parent/customer testing evidence is missing.
Revised Score: 80
Confidence: Medium
Evidence Used:
- `shared-content/catalog.json` contains 24 complete catalog entries.
- Current iOS and Android source exposes library, detail, reader, locked premium, and parent-gated purchase surfaces.
- Current backend, iOS, and Android smoke artifacts show the concept is demoable.
Missing External Evidence:
- No target parent/customer interviews, willingness-to-pay signal, retention signal, conversion signal, or distribution proof.
Why The Cap Exists:
- A repo can prove a coherent demo, but it cannot prove demand without external market evidence.
What Would Raise It By 5 Points:
- Add parent/customer interview evidence plus a small pricing or willingness-to-pay test.
What Would Raise It To 95:
- Document target-family testing, pricing or willingness-to-pay evidence, retention or repeated-use signal, conversion intent, and a distribution plan.

Category: Engineering/demo readiness
Current Score: 94
Cap Applied: No external-validation cap.
Why No Cap Is Appropriate: This category is limited to repo-local engineering proof: builds, tests, shared-content loading, manifest resolution, reader behavior, payment scaffolding, backend stub behavior, and simulator/emulator artifacts. Market, legal, editorial, art, audio, and store validation are scored elsewhere.
Revised Score: 94
Confidence: High
Evidence Used:
- `scripts/agent/validate` passed in the current workspace.
- `scripts/agent/validate-ui` passed with backend smoke, iOS simulator smoke, Android emulator smoke, artifact-backed reader scoring, and strict visual layout QA.
- SwiftPM build/tests, Android Gradle tests, and Android debug assemble passed.
Missing External Evidence:
- Real-device release QA is scored under production/store readiness.
Why The Cap Exists:
- No external-validation cap is applied because this category does not claim market, legal, production asset, or store readiness.
What Would Raise It By 5 Points:
- Add CI-backed repeatable smoke evidence and reduce risk in the largest reader files.
What Would Raise It To 95:
- Keep current build/test/smoke evidence green in one audit window and complete minor maintainability cleanup.

Category: Content/story readiness
Current Score: 86
Cap Applied: 85 because external children's editor, Korean-language, cultural, and child-safety review evidence is missing.
Revised Score: 85
Confidence: Medium
Evidence Used:
- `shared-content/catalog.json` contains 24 complete books.
- `shared-content/books/*.json` contains 698 total pages with English/Korean text, text-level variants, storyBeat metadata, vocabulary, image prompts, audio prompts, narration scripts, and animation metadata.
- `python3 tools/validate_books.py`, `python3 tools/validate_story_quality.py`, and `python3 tools/score_story_writing.py` passed.
Missing External Evidence:
- No external children's editor signoff, Korean-language reviewer signoff, cultural authenticity approval, or child-safety adaptation review.
Why The Cap Exists:
- Internal structure and validation are strong, but production story readiness depends on external human review.
What Would Raise It By 5 Points:
- Obtain and resolve comments from an external children's editor and Korean-language reviewer.
What Would Raise It To 95:
- Complete human editorial, Korean-language, cultural authenticity, and child-safety approvals with changes applied to current story files.

Category: Cultural authenticity
Current Score: 80
Cap Applied: 80 because documented Korean human cultural reviewer signoff is missing.
Revised Score: 80
Confidence: Medium
Evidence Used:
- `shared-content/reviews/cultural_authenticity_review.json` covers all 24 complete books as internal premium-demo review.
- `python3 tools/validate_cultural_authenticity.py` passed.
Missing External Evidence:
- No Korean human cultural reviewer signoff, Korean parent read-aloud testing, or resolved external cultural comments.
Why The Cap Exists:
- Internal cultural metadata is useful but cannot replace Korean human cultural review.
What Would Raise It By 5 Points:
- Add attributable Korean human cultural review evidence and resolve required changes.
What Would Raise It To 95:
- Document Korean cultural reviewer approval, Korean-language approval, parent/read-aloud feedback, and final art/audio cultural checks.

Category: Visual/art readiness
Current Score: 85
Cap Applied: 95 because all complete-scene art and covers are reviewed, but not final.
Revised Score: 85
Confidence: Medium
Evidence Used:
- `shared-content/assets/manifests/image_manifest.json` shows 698 complete-scene entries and 24 covers with status `generated_reviewed`.
- `shared-content/characters/index.json` contains 24 character-bible entries.
- `shared-content/assets/manifests/asset_ownership_ledger.json` documents repo-local asset source and explicitly keeps legal production approval blocked.
- `python3 tools/validate_visual_system_readiness.py`, `python3 tools/score_art_experience.py`, and strict visual layout QA passed.
Missing External Evidence:
- No commissioned final scene art, commissioned final covers, final approved character pack, external creative/cultural/child-safety art approval, or commercial production licensing/legal signoff.
Why The Cap Exists:
- Generated-review art supports a stronger demo, but final production visual readiness still requires final assets and approvals.
What Would Raise It By 5 Points:
- Replace a meaningful subset with commissioned/reviewed production art and resolve continuity/cropping defects.
What Would Raise It To 95:
- All 698 scene images and 24 covers are final approved, character consistency is approved, and ownership/licensing is production-cleared.

Category: Audio readiness
Current Score: 45
Cap Applied: 55 because all narration is `synthetic_draft`.
Revised Score: 45
Confidence: High
Evidence Used:
- `shared-content/audio/manifests/audio_manifest.json` shows 1,396 complete-book narration entries with status `synthetic_draft`.
- `python3 tools/validate_assets.py` and generated-draft readiness passed.
Missing External Evidence:
- No professional narrator files, reviewed provider narration, human-recorded narration, Korean pronunciation review, or mastered final audio QA.
Why The Cap Exists:
- Draft synthetic narration proves coverage, not production audio quality.
What Would Raise It By 5 Points:
- Produce reviewed English and Korean provider samples and document human review for warmth, pronunciation, pacing, and child suitability.
What Would Raise It To 95:
- Final mastered narration and sound design are approved, licensed, normalized, and QA'd on target devices.

Category: Payment readiness
Current Score: 58
Cap Applied: 75 because real StoreKit and Google Play Billing product configuration is absent.
Revised Score: 58
Confidence: High
Evidence Used:
- Current iOS and Android entitlement tests passed.
- `python3 tools/validate_payments_readiness.py` passed for scaffold readiness.
Missing External Evidence:
- No App Store Connect products, Google Play Console products, sandbox purchase/restore transcripts, or backend receipt/token verification.
Why The Cap Exists:
- Payment scaffolding is not configured store purchasing.
What Would Raise It By 5 Points:
- Add real StoreKit configuration and Android purchase/restore implementation with sandbox evidence.
What Would Raise It To 95:
- Real products, purchase/restore flows, parent gates, and backend verification all pass store testing.

Category: Backend readiness
Current Score: 69
Cap Applied: 75 because backend evidence is OpenAPI/local stub only.
Revised Score: 69
Confidence: High
Evidence Used:
- `backend/service_stub.py` and `backend/openapi.yaml` provide local catalog, entitlement, purchase sync, review queue, CMS export, and readiness contracts.
- Backend smoke passed.
Missing External Evidence:
- No deployed backend URL/config, durable production database, production auth/RBAC, monitoring, or receipt/token verification service.
Why The Cap Exists:
- A local stub and contract are not a deployed production backend.
What Would Raise It By 5 Points:
- Deploy the entitlement/catalog/purchase-sync service with durable storage and auth evidence.
What Would Raise It To 95:
- Deployed backend, receipt/token verification, monitoring, security, admin workflow, and production operations are proven.

Category: Compliance readiness
Current Score: 78
Cap Applied: 80 because final privacy policy evidence is missing.
Revised Score: 78
Confidence: High
Evidence Used:
- `shared-content/compliance/app_behavior_flags.json` and data-flow artifacts are present.
- `python3 tools/validate_kids_safety.py` and `python3 tools/validate_non_human_readiness.py` passed.
Missing External Evidence:
- No final privacy policy, legal/privacy signoff, Apple Kids Category review, Google Play Families review, or real-device accessibility QA.
Why The Cap Exists:
- Repo guardrails and drafts cannot replace final legal/store compliance review.
What Would Raise It By 5 Points:
- Add final privacy policy evidence and complete data-flow/privacy label review.
What Would Raise It To 95:
- Legal/privacy/store signoff is complete and app behavior matches disclosures.

Category: Store readiness
Current Score: 38
Cap Applied: 50 because store evidence is incomplete: signing/products/policy/screenshots/disclosures are missing.
Revised Score: 38
Confidence: High
Evidence Used:
- Current store/product metadata artifacts are drafts only.
- Android debug assemble passed; iOS SwiftPM host build passed.
Missing External Evidence:
- No real bundle IDs/signing evidence, configured store products, final store screenshots, submitted metadata, TestFlight/internal track evidence, or compliance review.
Why The Cap Exists:
- Debug/demo builds are not store submission readiness.
What Would Raise It By 5 Points:
- Add real signing config, final icon/launch assets, store screenshots, privacy policy, and product configuration evidence.
What Would Raise It To 95:
- The app is ready for App Store and Play submission with packaging, signing, metadata, screenshots, products, disclosures, and QA complete.

Category: Production readiness
Current Score: 60
Cap Applied: 72 because professional or human-reviewed narration is missing.
Revised Score: 60
Confidence: High
Evidence Used:
- `python3 tools/validate_production_readiness.py --level generated-draft` passed.
- `python3 tools/validate_production_readiness.py --level release-candidate` failed with final asset/audio/backend/store/compliance/signing blockers.
- `scripts/agent/validate` and `scripts/agent/validate-ui` passed for demo readiness.
Missing External Evidence:
- 698 scene images are not `commissioned_final`.
- 24 covers are not `commissioned_final`.
- 1,396 narration files are not `human_recorded_final`.
- Deployed backend receipt/token verification, real store products, legal/privacy review, human review signoff, signing, and store listing evidence are missing.
Why The Cap Exists:
- Production readiness depends on final assets/audio, backend, payments, compliance, store packaging, and real-device QA.
What Would Raise It By 5 Points:
- Import final/reviewed production art for a release subset and add reviewed provider narration samples.
What Would Raise It To 95:
- Final/reviewed art, final narration/sound, real payments, receipt verification backend, hosted CMS/backend, legal/privacy signoff, real-device/accessibility QA, and store packaging are complete.
