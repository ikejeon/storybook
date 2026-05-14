# Moon Jar Stories Privacy Policy Draft

Status: draft, not legal final, not store-submission evidence.

This draft exists so engineering, product, and store metadata can stay aligned with the current app behavior. It must be reviewed and finalized before app submission.

## Summary

Moon Jar Stories is designed as a children and family reading app. The child-facing experience does not include ads, third-party tracking, child accounts, child-facing external links, live image generation, or live text-to-speech generation.

## Data We Expect To Use

| Data | Current Use | Notes |
| --- | --- | --- |
| Local reading progress | Stored on device to resume a book. | Not linked to child identity. |
| Purchase entitlement state | Used to unlock subscriptions, lifetime access, or individual books. | Production will require Apple/Google store transaction validation and backend entitlement sync. |
| Parent contact/waitlist information | Not part of the child app. | May be collected only through adult-controlled marketing or research flows. |
| Crash diagnostics | Not currently configured. | If added, provider/data flow must be reviewed and disclosed. |
| Voice recordings | Not collected by the current app. | Future family recording features require separate parental consent, storage, deletion, and review. |

## Child-Facing Restrictions

- No ads.
- No third-party tracking.
- No child accounts.
- No child-facing external links.
- No live image or audio generation in the child app.
- Purchases, restore purchases, external links, and settings remain parent-gated.

## Required Before Submission

- Legal/privacy review.
- Final policy text with company/contact details.
- Store privacy labels that match the data-flow map.
- Parent-gate QA evidence.
- Accessibility QA evidence.
- Confirmation that production backend, payment, analytics, diagnostics, and support tools match this policy.
