# Compliance And Kids Safety

Moon Jar Stories is designed as a child-facing, parent-purchased reading app. This checklist maps policy risk directly to app behavior and validation.

Sources checked on May 4, 2026:

- Apple App Store Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- Google Play Families Policy: https://support.google.com/googleplay/android-developer/answer/9893335
- FTC COPPA resources and rule: https://www.ftc.gov/business-guidance/privacy-security/children and https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa

## Apple Kids Category Checklist

- Child-facing experience contains no ads.
- Child-facing experience contains no third-party tracking.
- Purchases, subscriptions, restore purchase, external links, account actions, and grown-up settings are behind a parent gate.
- Privacy policy must disclose exactly what is collected, why, and whether anything leaves the device.
- No child account creation in the reader.
- No external web links in the child reader.
- No behavioral analytics SDK in child-facing screens.

## Google Play Families Checklist

- App content is appropriate for ages 3-8.
- No ads or ad SDKs.
- No third-party tracking in the child experience.
- Store listing must accurately disclose in-app purchases and subscriptions.
- Any external link, purchase, or adult-targeted setting needs a parent gate.
- No collection of precise location, contacts, microphone recordings, photos, or child identity.

## COPPA Data Minimization Checklist

- Do not collect child name, email, persistent child profile, voice recordings, precise location, contacts, or behavioral tracking.
- Parent/grandparent voice recording is a future adult-controlled feature and must require explicit parental consent, local-first storage choices, deletion, and a privacy review before implementation.
- Reading progress should remain local unless a parent signs into a non-child account and opts into sync.
- Purchase state can be stored as anonymous entitlement state tied to store receipts, not child identity.

## No Ads / No Tracking

Current repo behavior:

- `shared-content/compliance/app_behavior_flags.json` sets ads and third-party tracking to false.
- No ad SDK is configured in Android Gradle.
- No analytics SDK is configured in iOS Swift package or Android Gradle.

## Parent Gate

Current prototype behavior:

- iOS paywall continues through `ParentGateView`.
- Android locked-book flow shows a mock paywall, then `ParentGateDialog`.
- Future external links and account management must use the same parent gate pattern.

## Subscription Disclosure

Production paywalls must show:

- Price.
- Billing period.
- What unlocks.
- Renewal behavior.
- Trial behavior, if any.
- Restore purchase action.
- Terms and privacy links behind parent gate.

## Data Collected Vs Not Collected

| Data | Current State | Notes |
| --- | --- | --- |
| Child name/email | Not collected | Do not add child accounts. |
| Reading progress | Device-local only | Can sync later only through parent account and privacy review. |
| Purchase entitlement | Mock local state now | Production backend verifies store receipts/tokens. |
| Audio recordings | Not collected | Future grandparent voice mode needs consent/deletion design. |
| Analytics | Not collected | Avoid child-facing third-party analytics. |
| Ads | Not present | Keep zero ads. |
| External links | Not in reader | Parent gate required for any future external link. |

## Validation Rule

`tools/validate_assets.py` fails if future config enables ads, third-party tracking, child accounts, child-facing external links, or child data collection.
