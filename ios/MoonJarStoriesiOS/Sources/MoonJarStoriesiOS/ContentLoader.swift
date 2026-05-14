import Foundation
import SwiftUI

enum ContentLoaderError: LocalizedError {
    case missingRoot
    case missingCatalog(URL)

    var errorDescription: String? {
        switch self {
        case .missingRoot:
            return "Could not find shared-content. Set MOONJAR_CONTENT_ROOT or run from the repository."
        case .missingCatalog(let url):
            return "Could not find catalog at \(url.path)."
        }
    }
}

@MainActor
final class StoryLibrary: ObservableObject {
    @Published private(set) var catalog: Catalog?
    @Published private(set) var books: [StoryBook] = []
    @Published private(set) var contentRoot: URL?
    @Published private(set) var assetResolver = AssetManifestResolver.empty
    @Published private(set) var isLoading = false
    @Published var errorMessage: String?

    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .useDefaultKeys
        return decoder
    }()

    func load() {
        guard !isLoading else { return }
        isLoading = true
        defer { isLoading = false }

        do {
            let root = try ContentRootResolver.resolve()
            let catalogURL = root.appendingPathComponent("catalog.json")
            guard FileManager.default.fileExists(atPath: catalogURL.path) else {
                throw ContentLoaderError.missingCatalog(catalogURL)
            }

            let catalog = try decoder.decode(Catalog.self, from: Data(contentsOf: catalogURL))
            var completeBooks: [StoryBook] = []
            for entry in catalog.books where entry.status == .complete {
                guard let path = entry.bookPath else { continue }
                let bookURL = root.appendingPathComponent(path)
                completeBooks.append(try decoder.decode(StoryBook.self, from: Data(contentsOf: bookURL)))
            }

            self.catalog = catalog
            self.books = completeBooks.sorted { $0.title.en < $1.title.en }
            self.contentRoot = root
            self.assetResolver = AssetManifestResolver(contentRoot: root)
            self.errorMessage = nil
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    func book(for catalogBook: CatalogBook) -> StoryBook? {
        books.first { $0.id == catalogBook.id }
    }

    func resolvedCoverAsset(for book: StoryBook?) -> String? {
        guard let book else { return nil }
        return assetResolver.coverAsset(storyId: book.id, fallback: book.coverAsset, contentRoot: contentRoot)
    }

    func resolvedSceneImageAsset(book: StoryBook, page: StoryPage) -> String? {
        assetResolver.sceneImageAsset(storyId: book.id, sceneId: page.id, fallback: page.imageAsset, contentRoot: contentRoot)
    }

    func resolvedNarrationAsset(book: StoryBook, page: StoryPage, language: ReaderLanguage) -> String? {
        let audioLanguage = language == .korean ? "ko" : "en"
        let fallback = language == .korean ? page.narrationAudio : nil
        return assetResolver.narrationAsset(storyId: book.id, sceneId: page.id, language: audioLanguage, fallback: fallback, contentRoot: contentRoot)
    }

    func resolvedPageFlipSound() -> String? {
        assetResolver.uiSound(assetType: "page_flip_sound", fallback: "audio/ui/page-flip.wav", contentRoot: contentRoot)
    }
}

enum ContentRootResolver {
    static func resolve() throws -> URL {
        let environment = ProcessInfo.processInfo.environment
        if let override = environment["MOONJAR_CONTENT_ROOT"], !override.isEmpty {
            let url = URL(fileURLWithPath: override, isDirectory: true)
            if FileManager.default.fileExists(atPath: url.appendingPathComponent("catalog.json").path) {
                return url
            }
        }

        #if SWIFT_PACKAGE
        if let resourceURL = Bundle.module.resourceURL {
            let candidate = resourceURL.appendingPathComponent("shared-content", isDirectory: true)
            if FileManager.default.fileExists(atPath: candidate.appendingPathComponent("catalog.json").path) {
                return candidate
            }
        }
        #endif

        if let bundleResourceURL = Bundle.main.resourceURL {
            let candidate = bundleResourceURL.appendingPathComponent("shared-content", isDirectory: true)
            if FileManager.default.fileExists(atPath: candidate.appendingPathComponent("catalog.json").path) {
                return candidate
            }
        }

        var current = URL(fileURLWithPath: FileManager.default.currentDirectoryPath, isDirectory: true)
        for _ in 0..<8 {
            let candidate = current.appendingPathComponent("shared-content", isDirectory: true)
            if FileManager.default.fileExists(atPath: candidate.appendingPathComponent("catalog.json").path) {
                return candidate
            }
            current.deleteLastPathComponent()
        }

        throw ContentLoaderError.missingRoot
    }
}
