# Entitlement Rules

The app keeps payments mocked until real store products and backend verification are available.

Product IDs:

- Monthly: `com.moonjarstories.subscription.monthly`
- Annual: `com.moonjarstories.subscription.annual`
- Lifetime Korean Library: `com.moonjarstories.lifetime.korean_library`
- Individual book prefix: `com.moonjarstories.book.`

Rules:

- Five launch books are free.
- Nineteen premium books have complete shared-content payloads but remain locked by entitlement until a qualifying purchase or subscription is present.
- Active monthly or annual subscription unlocks all books in the Korean Library catalog.
- Lifetime unlock grants permanent access to the Korean Library SKU.
- Individual book purchase unlocks only that book.
- Grace period keeps subscription access while the store reports the account is still recoverable.
- Expired subscription falls back to free books plus individual/lifetime purchases.
- Family sharing is a store configuration and product-policy decision. Do not promise it until App Store and Play Console products are configured.
- The child app should never ask for payment directly without a parent gate.
