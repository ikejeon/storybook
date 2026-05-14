# Entitlement Service Stub

Product IDs:

- iOS monthly: `com.moonjarstories.subscription.monthly`
- iOS annual: `com.moonjarstories.subscription.annual`
- iOS lifetime: `com.moonjarstories.lifetime.korean_library`
- iOS individual book prefix: `com.moonjarstories.book.`
- Android monthly: `com.moonjarstories.subscription.monthly`
- Android annual: `com.moonjarstories.subscription.annual`
- Android lifetime: `com.moonjarstories.lifetime.korean_library`
- Android individual book prefix: `com.moonjarstories.book.`

Rules:

- Free books always unlock.
- Active monthly/annual subscription unlocks all current library books.
- Grace period keeps subscribed access until platform expiration data says otherwise.
- Lifetime unlock grants the Korean Library SKU only, not future unrelated products unless product copy says so.
- Individual book purchase unlocks that book permanently.
- Family sharing is a product decision per store configuration; the backend records entitlements by verified store account/install purchase evidence, not by child identity.
