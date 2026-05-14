package com.moonjar.stories.billing

import com.moonjar.stories.data.BookAccess
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class EntitlementManagerTest {
    @Test
    fun freeBooksAreReadableBeforePurchase() {
        val manager = EntitlementManager()

        assertTrue(manager.canRead(BookAccess.Free, "book.sun_moon"))
    }

    @Test
    fun premiumBooksRequireSubscriptionLifetimeOrBookUnlock() {
        val manager = EntitlementManager()

        assertFalse(manager.canRead(BookAccess.Premium, "book.simcheong"))

        manager.unlockBookForPrototype("book.simcheong")
        assertTrue(manager.canRead(BookAccess.Premium, "book.simcheong"))
        assertFalse(manager.canRead(BookAccess.Premium, "book.rabbit_turtle"))

        manager.unlockLifetimeForPrototype()
        assertTrue(manager.canRead(BookAccess.Premium, "book.rabbit_turtle"))
    }

    @Test
    fun purchaseStateTracksIndividualBookUnlocksWithoutSubscription() {
        val manager = EntitlementManager()

        manager.unlockBookForPrototype("book.simcheong")

        assertTrue(manager.purchaseState.value.unlockedBookIds.contains("book.simcheong"))
        assertTrue(manager.canRead(BookAccess.Premium, "book.simcheong"))
        assertFalse(manager.canRead(BookAccess.Premium, "book.rabbit_turtle"))
    }

    @Test
    fun productIdsIncludeIndividualPremiumBooks() {
        val manager = EntitlementManager()

        val productIds = manager.productIdsForCatalog(listOf("book.simcheong", "book.rabbit_turtle"))

        assertTrue(productIds.contains(MoonJarProductIds.Monthly))
        assertTrue(productIds.contains(MoonJarProductIds.Annual))
        assertTrue(productIds.contains(MoonJarProductIds.Lifetime))
        assertTrue(productIds.contains("com.moonjarstories.book.simcheong"))
        assertTrue(productIds.contains("com.moonjarstories.book.rabbit_turtle"))
        assertEquals(productIds.toSet().size, productIds.size)
    }
}
