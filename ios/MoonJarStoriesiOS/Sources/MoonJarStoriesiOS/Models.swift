import Foundation

enum BookAccess: String, Codable {
    case free
    case premium
}

enum CatalogStatus: String, Codable {
    case complete
    case metadataOnly = "metadata_only"
}

struct LocalizedTitle: Codable, Hashable {
    let ko: String
    let en: String
    let romanization: String?
}

struct Catalog: Codable {
    let schemaVersion: String
    let libraryVersion: String
    let monetization: Monetization
    let books: [CatalogBook]
}

struct Monetization: Codable {
    let freeBooks: Int
    let monthlyUsd: Decimal
    let annualUsd: Decimal
    let lifetimeUsdRange: String
    let individualBookUsd: Decimal
}

struct CatalogBook: Codable, Identifiable, Hashable {
    let id: String
    let slug: String
    let title: LocalizedTitle
    let access: BookAccess
    let status: CatalogStatus
    let ageRange: String
    let pageTarget: Int
    let bookPath: String?
    let sensitivity: String?
}

struct StoryBook: Codable, Identifiable, Hashable {
    let schemaVersion: String
    let id: String
    let slug: String
    let title: LocalizedTitle
    let access: BookAccess
    let ageRange: String
    let estimatedMinutes: Int?
    let summary: String
    let coverAsset: String?
    let sensitivityNotes: [String]?
    let themes: [String]
    let characters: [String]
    let pages: [StoryPage]
}

struct StoryPage: Codable, Identifiable, Hashable {
    let id: String
    let pageNumber: Int
    let koreanText: String
    let englishText: String
    let text: StoryTextVariants?
    let narrationScript: String
    let vocabulary: [VocabularyItem]
    let imagePrompt: String
    let imageAsset: String?
    let imageSource: String?
    let audioPrompt: String
    let narrationAudio: String?
    let ambientAudio: String?
    let animation: SceneAnimation
    let storyBeat: StoryBeat?
}

struct StoryTextVariants: Codable, Hashable {
    let enLittle: String?
    let enStandard: String?
    let koLittle: String?
    let koStandard: String?
}

struct StoryBeat: Codable, Hashable {
    let purpose: String?
    let emotion: String?
    let pageTurnHook: String?
    let readAloudCue: String?
    let childInteraction: String?
}

struct VocabularyItem: Codable, Hashable {
    let ko: String
    let en: String
    let romanization: String?
    let definitionEn: String?
    let definitionKo: String?
}

struct SceneAnimation: Codable, Hashable {
    let type: String
    let loopDuration: Double
    let motionSafety: String?
    let layers: [AnimationLayer]
}

struct AnimationLayer: Codable, Hashable {
    let name: String
    let motion: String
    let intensity: String?
    let outputFile: String?
    let status: String?
}

enum ReaderLanguage: String, CaseIterable, Identifiable {
    case english = "en"
    case bilingual = "bilingual"
    case korean = "ko"

    var id: String { rawValue }

    var label: String {
        switch self {
        case .english: return "English"
        case .bilingual: return "KO/EN"
        case .korean: return "한국어"
        }
    }
}

enum ReaderTextMode: String, CaseIterable, Identifiable {
    case story
    case little

    var id: String { rawValue }

    var label: String {
        switch self {
        case .story: return "Story Mode"
        case .little: return "Little Listener"
        }
    }

    var shortLabel: String {
        switch self {
        case .story: return "Story"
        case .little: return "Little"
        }
    }
}
