import XCTest
@testable import MoonJarStoriesiOS

@MainActor
final class EntitlementStoreTests: XCTestCase {
    func testFreeBooksAreReadableBeforePurchase() {
        let store = EntitlementStore()
        let book = makeBook(id: "book.sun_moon", access: .free)

        XCTAssertTrue(store.canRead(book))
    }

    func testPremiumBooksRequireSubscriptionLifetimeOrBookUnlock() {
        let store = EntitlementStore()
        let premiumBook = makeBook(id: "book.simcheong", access: .premium)
        let otherPremiumBook = makeBook(id: "book.rabbit_turtle", access: .premium)

        XCTAssertFalse(store.canRead(premiumBook))

        store.unlockBookForPrototype(premiumBook.id)
        XCTAssertTrue(store.canRead(premiumBook))
        XCTAssertFalse(store.canRead(otherPremiumBook))

        store.unlockLifetimeForPrototype()
        XCTAssertTrue(store.canRead(otherPremiumBook))
    }

    func testCatalogEntriesHonorIndividualBookUnlocks() {
        let store = EntitlementStore()
        let premiumEntry = CatalogBook(
            id: "book.simcheong",
            slug: "simcheong",
            title: LocalizedTitle(ko: "심청전", en: "Simcheong", romanization: nil),
            access: .premium,
            status: .metadataOnly,
            ageRange: "6-8",
            pageTarget: 32,
            bookPath: nil,
            sensitivity: nil
        )

        XCTAssertFalse(store.canRead(premiumEntry))
        store.unlockBookForPrototype(premiumEntry.id)
        XCTAssertTrue(store.canRead(premiumEntry))
    }

    func testProductIdsIncludeIndividualPremiumBooks() {
        let freeEntry = makeCatalogEntry(id: "book.sun_moon", access: .free)
        let premiumEntry = makeCatalogEntry(id: "book.simcheong", access: .premium)

        let productIds = MoonJarProductID.all(for: [freeEntry, premiumEntry])

        XCTAssertTrue(productIds.contains(MoonJarProductID.monthly))
        XCTAssertTrue(productIds.contains(MoonJarProductID.annual))
        XCTAssertTrue(productIds.contains(MoonJarProductID.lifetime))
        XCTAssertTrue(productIds.contains("com.moonjarstories.book.simcheong"))
        XCTAssertFalse(productIds.contains("com.moonjarstories.book.sun_moon"))
    }

    private func makeBook(id: String, access: BookAccess) -> StoryBook {
        StoryBook(
            schemaVersion: "1.0.0",
            id: id,
            slug: id.replacingOccurrences(of: "book.", with: ""),
            title: LocalizedTitle(ko: "테스트", en: "Test", romanization: nil),
            access: access,
            ageRange: "3-8",
            estimatedMinutes: 1,
            summary: "Test book",
            coverAsset: nil,
            sensitivityNotes: nil,
            themes: [],
            characters: [],
            pages: []
        )
    }

    private func makeCatalogEntry(id: String, access: BookAccess) -> CatalogBook {
        CatalogBook(
            id: id,
            slug: id.replacingOccurrences(of: "book.", with: ""),
            title: LocalizedTitle(ko: "테스트", en: "Test", romanization: nil),
            access: access,
            status: access == .free ? .complete : .metadataOnly,
            ageRange: "3-8",
            pageTarget: 24,
            bookPath: access == .free ? "books/test.json" : nil,
            sensitivity: nil
        )
    }
}
