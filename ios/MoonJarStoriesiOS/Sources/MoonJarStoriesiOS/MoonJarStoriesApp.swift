import SwiftUI

@main
struct MoonJarStoriesApp: App {
    @StateObject private var library = StoryLibrary()
    @StateObject private var entitlements = EntitlementStore()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(library)
                .environmentObject(entitlements)
                .task {
                    library.load()
                    await entitlements.loadProducts()
                }
        }
    }
}

