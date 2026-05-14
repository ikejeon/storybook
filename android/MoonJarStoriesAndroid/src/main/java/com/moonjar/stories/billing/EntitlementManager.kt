package com.moonjar.stories.billing

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

enum class EntitlementState {
    FreeOnly,
    Subscribed,
    Lifetime
}

object MoonJarProductIds {
    const val Monthly = "com.moonjarstories.subscription.monthly"
    const val Annual = "com.moonjarstories.subscription.annual"
    const val Lifetime = "com.moonjarstories.lifetime.korean_library"
    const val BookPrefix = "com.moonjarstories.book."
    val All = listOf(Monthly, Annual, Lifetime)

    fun individualBook(bookId: String): String =
        BookPrefix + bookId.removePrefix("book.")

    fun allForCatalog(premiumBookIds: Iterable<String>): List<String> =
        All + premiumBookIds.map(::individualBook)
}

data class PurchaseState(
    val subscriptionExpiresAtMillis: Long? = null,
    val isInGracePeriod: Boolean = false,
    val hasLifetimeUnlock: Boolean = false,
    val unlockedBookIds: Set<String> = emptySet()
)

class EntitlementManager {
    private val _state = MutableStateFlow(EntitlementState.FreeOnly)
    val state: StateFlow<EntitlementState> = _state
    private val _purchaseState = MutableStateFlow(PurchaseState())
    val purchaseState: StateFlow<PurchaseState> = _purchaseState

    val productIds = MoonJarProductIds.All

    fun productIdsForCatalog(premiumBookIds: Iterable<String>): List<String> =
        MoonJarProductIds.allForCatalog(premiumBookIds)

    fun unlockForPrototype() {
        _purchaseState.value = _purchaseState.value.copy(
            subscriptionExpiresAtMillis = System.currentTimeMillis() + 30L * 24L * 60L * 60L * 1000L
        )
        _state.value = EntitlementState.Subscribed
    }

    fun unlockLifetimeForPrototype() {
        _purchaseState.value = _purchaseState.value.copy(hasLifetimeUnlock = true)
        _state.value = EntitlementState.Lifetime
    }

    fun unlockBookForPrototype(bookId: String) {
        _purchaseState.value = _purchaseState.value.copy(
            unlockedBookIds = _purchaseState.value.unlockedBookIds + bookId
        )
    }

    fun canRead(access: com.moonjar.stories.data.BookAccess, bookId: String): Boolean =
        access == com.moonjar.stories.data.BookAccess.Free ||
            _state.value == EntitlementState.Subscribed ||
            _state.value == EntitlementState.Lifetime ||
            _purchaseState.value.unlockedBookIds.contains(bookId)

    fun restorePurchasesPlaceholder() {
        _state.value = if (_purchaseState.value.hasLifetimeUnlock) EntitlementState.Lifetime else EntitlementState.FreeOnly
    }
}
