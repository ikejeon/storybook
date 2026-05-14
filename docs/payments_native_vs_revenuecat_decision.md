# Native Payments Vs RevenueCat Decision

Moon Jar Stories should keep native StoreKit 2 and Google Play Billing as the default architecture for now.

## Recommendation

Use native StoreKit 2 on iOS, Google Play Billing on Android, and a small first-party entitlement backend.

RevenueCat can be evaluated later, but should not be added to the child app until the privacy/compliance review explicitly approves the data flow.

## Comparison

| Area | Native StoreKit 2 + Google Play Billing + Own Backend | RevenueCat |
| --- | --- | --- |
| Child privacy | Strongest control over data minimization and third-party sharing. | Adds a third-party processor that must be reviewed for Kids/Families compliance. |
| Backend complexity | More engineering work: receipt validation, entitlement sync, admin support, restore behavior. | Lower engineering effort for cross-platform subscriptions and dashboards. |
| Entitlement handling | Full control over subscriptions, lifetime unlock, individual book unlocks, family-sharing policy, grace periods. | Faster entitlement abstraction; custom edge cases may depend on SDK/service behavior. |
| Restore purchases | Native restore/query flows must be built and QA’d per platform. | Built-in cross-platform restore support. |
| Grace period / expiration | Must implement and test App Store / Play state mapping in own backend. | Service helps normalize states. |
| Support/admin | Must build admin tooling for receipt lookup and entitlement correction. | Dashboard/support tooling available. |
| Kids-category risk | Lowest third-party surface if implemented carefully. | Requires privacy-policy, SDK, tracking, and data-sharing review before use. |

## Product IDs

Use placeholder constants until App Store Connect and Google Play Console products exist.

- `com.moonjarstories.subscription.monthly`
- `com.moonjarstories.subscription.annual`
- `com.moonjarstories.lifetime.korean_library`
- `com.moonjarstories.book.<book_id>`

## Required Shared Entitlement States

- `free_only`
- `subscribed_monthly`
- `subscribed_annual`
- `lifetime_unlocked`
- `individual_books_unlocked`
- `grace_period`
- `expired`
- `revoked`

## Family Sharing Decision

Prefer enabling Apple Family Sharing for subscriptions/lifetime if the final business model and StoreKit configuration allow it. For Google Play, document family-library compatibility per product type before launch.

## Go/No-Go Before Adding RevenueCat

RevenueCat may be reconsidered only after:

- Privacy/compliance reviewer approves SDK data flow.
- No child-facing identifiers or analytics are introduced.
- Parent gate remains before purchase/restore/settings flows.
- SDK is disabled from child-experience tracking or configured for strict data minimization.
- Privacy policy names the processor and collected data accurately.

## Current Decision

Do not add RevenueCat in the prototype. Keep the native payment abstractions and backend entitlement contract in place.
