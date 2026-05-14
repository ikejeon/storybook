import Foundation

struct AssetManifestEntry: Codable, Hashable {
    let assetType: String?
    let storyId: String?
    let storySlug: String?
    let sceneId: String?
    let language: String?
    let outputFile: String?
    let status: String?
    let candidates: [AssetManifestCandidate]?
}

struct AssetManifestCandidate: Codable, Hashable {
    let outputFile: String?
    let status: String?
}

private struct ImageManifest: Codable {
    let sceneEntries: [AssetManifestEntry]
    let coverEntries: [AssetManifestEntry]
    let appIconConcepts: [AssetManifestEntry]?
}

private struct AudioManifest: Codable {
    let narrationEntries: [AssetManifestEntry]
    let ambientEntries: [AssetManifestEntry]
    let uiSoundEntries: [AssetManifestEntry]
}

struct AssetManifestResolver {
    static let empty = AssetManifestResolver()

    private var sceneImages: [String: AssetManifestEntry] = [:]
    private var coverImages: [String: AssetManifestEntry] = [:]
    private var narrationAudio: [String: AssetManifestEntry] = [:]
    private var uiSounds: [String: AssetManifestEntry] = [:]

    init(contentRoot: URL? = nil) {
        guard let contentRoot else { return }
        let decoder = JSONDecoder()

        let imageURL = contentRoot.appendingPathComponent("assets/manifests/image_manifest.json")
        if let data = try? Data(contentsOf: imageURL),
           let manifest = try? decoder.decode(ImageManifest.self, from: data) {
            sceneImages = Dictionary(uniqueKeysWithValues: manifest.sceneEntries.compactMap { entry in
                guard let storyId = entry.storyId, let sceneId = entry.sceneId else { return nil }
                return (Self.key(storyId: storyId, sceneId: sceneId), entry)
            })
            coverImages = Dictionary(uniqueKeysWithValues: manifest.coverEntries.compactMap { entry in
                guard let storyId = entry.storyId else { return nil }
                return (storyId, entry)
            })
        }

        let audioURL = contentRoot.appendingPathComponent("audio/manifests/audio_manifest.json")
        if let data = try? Data(contentsOf: audioURL),
           let manifest = try? decoder.decode(AudioManifest.self, from: data) {
            narrationAudio = Dictionary(uniqueKeysWithValues: manifest.narrationEntries.compactMap { entry in
                guard let storyId = entry.storyId, let sceneId = entry.sceneId else { return nil }
                let language = entry.language ?? Self.inferredLanguage(for: entry.assetType)
                return (Self.key(storyId: storyId, sceneId: sceneId, language: language), entry)
            })
            uiSounds = Dictionary(uniqueKeysWithValues: manifest.uiSoundEntries.compactMap { entry in
                guard let assetType = entry.assetType else { return nil }
                return (assetType, entry)
            })
        }
    }

    func coverAsset(storyId: String, fallback: String?, contentRoot: URL?) -> String? {
        bestPath(for: coverImages[storyId], contentRoot: contentRoot) ?? fallback
    }

    func sceneImageAsset(storyId: String, sceneId: String, fallback: String?, contentRoot: URL?) -> String? {
        bestPath(for: sceneImages[Self.key(storyId: storyId, sceneId: sceneId)], contentRoot: contentRoot) ?? fallback
    }

    func narrationAsset(storyId: String, sceneId: String, language: String, fallback: String?, contentRoot: URL?) -> String? {
        bestPath(for: narrationAudio[Self.key(storyId: storyId, sceneId: sceneId, language: language)], contentRoot: contentRoot) ?? fallback
    }

    func uiSound(assetType: String, fallback: String?, contentRoot: URL?) -> String? {
        bestPath(for: uiSounds[assetType], contentRoot: contentRoot) ?? fallback
    }

    private func bestPath(for entry: AssetManifestEntry?, contentRoot: URL?) -> String? {
        guard let entry else { return nil }
        if let candidates = entry.candidates {
            let existing = candidates.compactMap { candidate -> (Int, String)? in
                guard let path = candidate.outputFile,
                      let contentRoot,
                      FileManager.default.fileExists(atPath: contentRoot.appendingPathComponent(path).path)
                else { return nil }
                return (Self.priority(for: candidate.status), path)
            }
            if let best = existing.sorted(by: { $0.0 < $1.0 }).first {
                return best.1
            }
        }
        guard let path = entry.outputFile else { return nil }
        if let contentRoot, FileManager.default.fileExists(atPath: contentRoot.appendingPathComponent(path).path) {
            return path
        }
        return nil
    }

    private static func priority(for status: String?) -> Int {
        switch status {
        case "commissioned_final", "human_recorded_final":
            return 0
        case "commissioned_reviewed", "generated_reviewed", "human_recorded_reviewed", "synthetic_reviewed":
            return 1
        case "commissioned_draft", "generated_draft", "human_recorded_draft", "synthetic_draft":
            return 2
        case "placeholder":
            return 3
        default:
            return 9
        }
    }

    private static func key(storyId: String, sceneId: String) -> String {
        "\(storyId)|\(sceneId)"
    }

    private static func key(storyId: String, sceneId: String, language: String) -> String {
        "\(storyId)|\(sceneId)|\(language)"
    }

    private static func inferredLanguage(for assetType: String?) -> String {
        assetType == "english_narration" ? "en" : "ko"
    }
}
