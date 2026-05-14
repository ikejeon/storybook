import Foundation
import StoreKit

enum EntitlementState: Equatable {
    case freeOnly
    case subscribed
    case lifetime
}

enum MoonJarProductID {
    static let monthly = "com.moonjarstories.subscription.monthly"
    static let annual = "com.moonjarstories.subscription.annual"
    static let lifetime = "com.moonjarstories.lifetime.korean_library"
    static let bookPrefix = "com.moonjarstories.book."

    static let subscriptions = [monthly, annual]
    static let all = [monthly, annual, lifetime]

    static func individualBook(_ bookId: String) -> String {
        bookPrefix + bookId.replacingOccurrences(of: "book.", with: "")
    }

    static func all(for catalogBooks: [CatalogBook]) -> [String] {
        let individualBooks = catalogBooks
            .filter { $0.access == .premium }
            .map { individualBook($0.id) }
        return all + individualBooks
    }
}

struct PurchaseState: Codable, Equatable {
    var subscriptionExpiresAt: Date?
    var isInGracePeriod: Bool = false
    var hasLifetimeUnlock: Bool = false
    var unlockedBookIds: Set<String> = []

    var hasActiveSubscription: Bool {
        guard let subscriptionExpiresAt else { return false }
        return subscriptionExpiresAt > Date() || isInGracePeriod
    }
}

@MainActor
final class EntitlementStore: ObservableObject {
    @Published private(set) var state: EntitlementState = .freeOnly
    @Published private(set) var products: [Product] = []
    @Published private(set) var purchaseState = PurchaseState()
    @Published var lastStoreMessage: String?

    func loadProducts(catalogBooks: [CatalogBook] = []) async {
        do {
            products = try await Product.products(for: MoonJarProductID.all(for: catalogBooks))
        } catch {
            lastStoreMessage = "Store products are unavailable in this prototype."
        }
    }

    func canRead(_ book: StoryBook) -> Bool {
        book.access == .free || state == .subscribed || state == .lifetime || purchaseState.unlockedBookIds.contains(book.id)
    }

    func canRead(_ catalogBook: CatalogBook) -> Bool {
        catalogBook.access == .free || state == .subscribed || state == .lifetime || purchaseState.unlockedBookIds.contains(catalogBook.id)
    }

    func unlockForPrototype() {
        state = .subscribed
        purchaseState.subscriptionExpiresAt = Calendar.current.date(byAdding: .month, value: 1, to: Date())
        lastStoreMessage = "Prototype subscription unlocked."
    }

    func unlockLifetimeForPrototype() {
        purchaseState.hasLifetimeUnlock = true
        state = .lifetime
        lastStoreMessage = "Prototype lifetime library unlocked."
    }

    func unlockBookForPrototype(_ bookId: String) {
        purchaseState.unlockedBookIds.insert(bookId)
        lastStoreMessage = "Prototype book unlocked."
    }

    func restore() async {
        var hasPremium = false
        var hasLifetime = false
        var unlockedBooks: Set<String> = []
        for await result in Transaction.currentEntitlements {
            guard case .verified(let transaction) = result else { continue }
            if MoonJarProductID.subscriptions.contains(transaction.productID) {
                hasPremium = true
                purchaseState.subscriptionExpiresAt = transaction.expirationDate
            } else if transaction.productID == MoonJarProductID.lifetime {
                hasLifetime = true
            } else if transaction.productID.hasPrefix(MoonJarProductID.bookPrefix) {
                unlockedBooks.insert(String(transaction.productID.dropFirst(MoonJarProductID.bookPrefix.count)))
            }
        }
        purchaseState.hasLifetimeUnlock = hasLifetime
        purchaseState.unlockedBookIds = unlockedBooks
        state = hasLifetime ? .lifetime : (hasPremium ? .subscribed : .freeOnly)
    }
}
