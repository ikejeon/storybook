import XCTest

final class SharedContentTests: XCTestCase {
    func testCompleteCatalogCountsMatchExpandedLaunchSet() throws {
        let contentRoot = try locateSharedContentRoot()
        let catalog = try loadJSON(contentRoot.appendingPathComponent("catalog.json"))
        let books = try XCTUnwrap(catalog["books"] as? [[String: Any]])

        XCTAssertEqual(books.count, 24)
        let completeBooks = books.filter { $0["status"] as? String == "complete" }
        XCTAssertEqual(completeBooks.count, books.count)

        var totalScenes = 0
        var sceneCounts: [String: Int] = [:]
        for entry in completeBooks {
            let id = try XCTUnwrap(entry["id"] as? String)
            let bookPath = try XCTUnwrap(entry["bookPath"] as? String)
            let book = try loadJSON(contentRoot.appendingPathComponent(bookPath))
            let pages = try XCTUnwrap(book["pages"] as? [[String: Any]])
            sceneCounts[id] = pages.count
            totalScenes += pages.count
        }

        XCTAssertEqual(sceneCounts["book.sun_moon"], 32)
        XCTAssertEqual(sceneCounts["book.gold_silver_axe"], 24)
        XCTAssertEqual(sceneCounts["book.tiger_persimmon"], 24)
        XCTAssertEqual(sceneCounts["book.heungbu_nolbu"], 32)
        XCTAssertEqual(sceneCounts["book.red_bean_grandma"], 26)
        XCTAssertEqual(totalScenes, books.compactMap { $0["pageTarget"] as? Int }.reduce(0, +))
    }

    func testAssetManifestsCoverAllCompleteScenesAndLanguageTracks() throws {
        let contentRoot = try locateSharedContentRoot()
        let imageManifest = try loadJSON(contentRoot.appendingPathComponent("assets/manifests/image_manifest.json"))
        let audioManifest = try loadJSON(contentRoot.appendingPathComponent("audio/manifests/audio_manifest.json"))

        let sceneEntries = try XCTUnwrap(imageManifest["sceneEntries"] as? [[String: Any]])
        let narrationEntries = try XCTUnwrap(audioManifest["narrationEntries"] as? [[String: Any]])
        let catalog = try loadJSON(contentRoot.appendingPathComponent("catalog.json"))
        let books = try XCTUnwrap(catalog["books"] as? [[String: Any]])
        let completeBooks = books.filter { $0["status"] as? String == "complete" }
        let completeIds = Set(completeBooks.compactMap { $0["id"] as? String })
        let expectedScenes = completeBooks.compactMap { $0["pageTarget"] as? Int }.reduce(0, +)
        let completeSceneEntries = sceneEntries.filter { entry in
            guard let storyId = entry["storyId"] as? String else { return false }
            return completeIds.contains(storyId)
        }
        let completeNarrationEntries = narrationEntries.filter { entry in
            guard let storyId = entry["storyId"] as? String else { return false }
            return completeIds.contains(storyId)
        }

        XCTAssertEqual(completeSceneEntries.count, expectedScenes)
        XCTAssertEqual(completeNarrationEntries.count, expectedScenes * 2)
        XCTAssertEqual(sceneEntries.filter { $0["storyId"] as? String == "book.sun_moon" }.count, 32)
        XCTAssertEqual(narrationEntries.filter { $0["storyId"] as? String == "book.sun_moon" }.count, 64)
        XCTAssertTrue(narrationEntries.contains { $0["language"] as? String == "en" })
        XCTAssertTrue(narrationEntries.contains { $0["language"] as? String == "ko" })
    }

    func testAssetResolverPriorityInputsAreGeneratedDraftAndExist() throws {
        let contentRoot = try locateSharedContentRoot()
        let imageManifest = try loadJSON(contentRoot.appendingPathComponent("assets/manifests/image_manifest.json"))
        let sceneEntries = try XCTUnwrap(imageManifest["sceneEntries"] as? [[String: Any]])

        for entry in sceneEntries {
            let outputFile = try XCTUnwrap(entry["outputFile"] as? String)
            XCTAssertTrue(FileManager.default.fileExists(atPath: contentRoot.appendingPathComponent(outputFile).path), outputFile)
            XCTAssertNotEqual(entry["status"] as? String, "placeholder", outputFile)

            let candidates = try XCTUnwrap(entry["candidates"] as? [[String: Any]])
            let bestCandidate = try XCTUnwrap(candidates.min { priority($0["status"] as? String) < priority($1["status"] as? String) })
            XCTAssertEqual(bestCandidate["outputFile"] as? String, outputFile)
            XCTAssertLessThanOrEqual(priority(entry["status"] as? String), priority("generated_draft"))
        }
    }

    func testNarrationTracksAreEnglishFirstWithKoreanOptional() throws {
        let contentRoot = try locateSharedContentRoot()
        let catalog = try loadJSON(contentRoot.appendingPathComponent("catalog.json"))
        let audioManifest = try loadJSON(contentRoot.appendingPathComponent("audio/manifests/audio_manifest.json"))
        let narrationEntries = try XCTUnwrap(audioManifest["narrationEntries"] as? [[String: Any]])
        let books = try XCTUnwrap(catalog["books"] as? [[String: Any]])
        let completeBooks = books.filter { $0["status"] as? String == "complete" }

        var expectedKeys = Set<String>()
        for entry in completeBooks {
            let bookId = try XCTUnwrap(entry["id"] as? String)
            let bookPath = try XCTUnwrap(entry["bookPath"] as? String)
            let book = try loadJSON(contentRoot.appendingPathComponent(bookPath))
            let pages = try XCTUnwrap(book["pages"] as? [[String: Any]])
            for page in pages {
                let sceneId = try XCTUnwrap(page["id"] as? String)
                expectedKeys.insert("\(bookId)|\(sceneId)|en")
                expectedKeys.insert("\(bookId)|\(sceneId)|ko")
            }
        }

        let actualKeys = Set(narrationEntries.compactMap { entry -> String? in
            guard let storyId = entry["storyId"] as? String,
                  let sceneId = entry["sceneId"] as? String,
                  let language = entry["language"] as? String,
                  let outputFile = entry["outputFile"] as? String
            else { return nil }
            XCTAssertTrue(FileManager.default.fileExists(atPath: contentRoot.appendingPathComponent(outputFile).path), outputFile)
            XCTAssertEqual(entry["status"] as? String, "synthetic_draft")
            return "\(storyId)|\(sceneId)|\(language)"
        })
        XCTAssertTrue(expectedKeys.isSubset(of: actualKeys))
    }

    func testPremiumCatalogEntriesRemainLockedWithContentPayloads() throws {
        let contentRoot = try locateSharedContentRoot()
        let catalog = try loadJSON(contentRoot.appendingPathComponent("catalog.json"))
        let books = try XCTUnwrap(catalog["books"] as? [[String: Any]])
        let premiumBooks = books.filter { $0["access"] as? String == "premium" }

        XCTAssertFalse(premiumBooks.isEmpty)
        XCTAssertTrue(premiumBooks.allSatisfy { $0["status"] as? String == "complete" })
        XCTAssertTrue(premiumBooks.allSatisfy { ($0["bookPath"] as? String)?.isEmpty == false })
    }

    func testBookSchemaMatchesValidatorContract() throws {
        let contentRoot = try locateSharedContentRoot()
        let schema = try loadJSON(contentRoot.appendingPathComponent("schemas/book.schema.json"))
        let required = Set(try XCTUnwrap(schema["required"] as? [String]))
        XCTAssertTrue(required.isSuperset(of: ["coverAsset", "coverAssetStatus", "characterBible", "narrationAudioStatus"]))

        let properties = try XCTUnwrap(schema["properties"] as? [String: Any])
        let pages = try XCTUnwrap(properties["pages"] as? [String: Any])
        let pageItems = try XCTUnwrap(pages["items"] as? [String: Any])
        let pageRequired = Set(try XCTUnwrap(pageItems["required"] as? [String]))
        XCTAssertTrue(pageRequired.isSuperset(of: ["text", "storyBeat", "imagePrompt", "audioPrompt", "animation"]))
    }

    private func locateSharedContentRoot() throws -> URL {
        let fileManager = FileManager.default
        var current = URL(fileURLWithPath: fileManager.currentDirectoryPath, isDirectory: true)
        for _ in 0..<8 {
            let candidate = current.appendingPathComponent("../../shared-content", isDirectory: true).standardizedFileURL
            if fileManager.fileExists(atPath: candidate.appendingPathComponent("catalog.json").path) {
                return candidate
            }
            let sibling = current.appendingPathComponent("shared-content", isDirectory: true)
            if fileManager.fileExists(atPath: sibling.appendingPathComponent("catalog.json").path) {
                return sibling
            }
            current.deleteLastPathComponent()
        }
        throw XCTSkip("shared-content/catalog.json was not found from \(fileManager.currentDirectoryPath)")
    }

    private func loadJSON(_ url: URL) throws -> [String: Any] {
        let data = try Data(contentsOf: url)
        let value = try JSONSerialization.jsonObject(with: data)
        return try XCTUnwrap(value as? [String: Any])
    }

    private func priority(_ status: String?) -> Int {
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
}
