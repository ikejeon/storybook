# Entitlement API Spec

Moon Jar Stories should keep platform purchase systems native while resolving access through a shared entitlement backend.

## Goals

- App Store purchases use StoreKit 2.
- Google Play purchases use Google Play Billing.
- The backend validates platform receipts/tokens server-side.
- Child reader screens never call third-party analytics or advertising SDKs.
- Apps can read free books offline without an account.

## Product IDs

| Product | Apple Product ID | Google Play Product ID | Access |
| --- | --- | --- | --- |
| Monthly | `com.moonjarstories.subscription.monthly` | `com.moonjarstories.subscription.monthly` | All premium books while active |
| Annual | `com.moonjarstories.subscription.annual` | `com.moonjarstories.subscription.annual` | All premium books while active |
| Lifetime | `com.moonjarstories.lifetime.korean_library` | `com.moonjarstories.lifetime.korean_library` | Current Korean folktale library |
| Individual Book | `com.moonjarstories.book.{book_id}` | `com.moonjarstories.book.{book_id}` | One book |

## Entitlement Model

```json
{
  "familyId": "fam_123",
  "platform": "ios",
  "status": "active",
  "entitlements": [
    {
      "type": "subscription",
      "productId": "com.moonjarstories.subscription.annual",
      "expiresAt": "2027-05-01T00:00:00Z"
    }
  ],
  "bookUnlocks": ["book.sun_moon"],
  "updatedAt": "2026-05-02T00:00:00Z"
}
```

## Endpoints

### `POST /v1/purchases/sync`

Validates App Store transactions or Google Play purchase tokens server-side and returns the current purchase state. This matches `backend/openapi.yaml`.

Request:

```json
{
  "anonymousUserId": "anon_install_or_family_safe_id",
  "platform": "ios",
  "transactions": [
    {
      "transactionToken": "200000000000000",
      "productId": "com.moonjarstories.subscription.annual",
      "purchaseDate": "2026-05-07T00:00:00Z"
    }
  ]
}
```

Response:

```json
{
  "anonymousUserId": "anon_install_or_family_safe_id",
  "subscriptionExpiresAt": "2027-05-01T00:00:00Z",
  "isInGracePeriod": false,
  "hasLifetimeUnlock": false,
  "unlockedBookIds": []
}
```

### `POST /v1/entitlements/check`

Returns a compact entitlement decision for one book.

Request:

```json
{
  "anonymousUserId": "anon_install_or_family_safe_id",
  "platform": "ios",
  "bookId": "book.sun_moon"
}
```

Response:

```json
{
  "canRead": true,
  "reason": "free_book",
  "expiresAt": null
}
```

### Restore Purchases

Restore remains native-store-first:

- iOS queries StoreKit 2 `Transaction.currentEntitlements`.
- Android queries Google Play Billing purchases.
- Apps then call `POST /v1/purchases/sync` with the restored transaction tokens.

## Offline Rules

- Free books: always available after download.
- Active subscription: cache premium entitlement for 14 days.
- Expired subscription: keep downloaded premium books visible but locked until verification refreshes.
- Lifetime: cache indefinitely after validation, with periodic background refresh.
