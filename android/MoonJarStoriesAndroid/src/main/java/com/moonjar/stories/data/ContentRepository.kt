package com.moonjar.stories.data

import android.content.res.AssetManager
import kotlinx.serialization.json.Json

class ContentRepository(
    private val assets: AssetManager
) {
    private val json = Json {
        ignoreUnknownKeys = true
    }

    private val imageManifest: ImageManifest? by lazy {
        readJsonOrNull("shared-content/assets/manifests/image_manifest.json", ImageManifest.serializer())
    }

    private val audioManifest: AudioManifest? by lazy {
        readJsonOrNull("shared-content/audio/manifests/audio_manifest.json", AudioManifest.serializer())
    }

    fun loadCatalog(): Catalog =
        assets.open("shared-content/catalog.json").bufferedReader().use { reader ->
            json.decodeFromString(Catalog.serializer(), reader.readText())
        }

    fun loadCompleteBooks(catalog: Catalog): List<StoryBook> =
        catalog.books
            .filter { it.status == CatalogStatus.Complete }
            .mapNotNull { entry ->
                entry.bookPath?.let { path ->
                    assets.open("shared-content/$path").bufferedReader().use { reader ->
                        json.decodeFromString(StoryBook.serializer(), reader.readText())
                    }
                }
            }
            .sortedBy { it.title.en }

    fun readSharedAsset(path: String): ByteArray? =
        runCatching {
            assets.open("shared-content/$path").use { stream ->
                stream.readBytes()
            }
        }.getOrNull()

    fun sharedAssetUri(path: String): String = "asset:///shared-content/$path"

    fun resolveCoverAsset(book: StoryBook): String? =
        bestPath(imageManifest?.coverEntries?.firstOrNull { it.storyId == book.id }) ?: book.coverAsset

    fun resolveSceneAsset(book: StoryBook, page: StoryPage): String? =
        bestPath(imageManifest?.sceneEntries?.firstOrNull { it.storyId == book.id && it.sceneId == page.id }) ?: page.imageAsset

    fun resolveNarrationAsset(book: StoryBook, page: StoryPage, language: String): String? {
        val fallback = if (language == "ko") page.narrationAudio else null
        return bestPath(
            audioManifest?.narrationEntries?.firstOrNull {
                it.storyId == book.id &&
                    it.sceneId == page.id &&
                    (it.language ?: inferredNarrationLanguage(it.assetType)) == language
            }
        ) ?: fallback
    }

    fun resolvePageFlipSound(): String =
        bestPath(audioManifest?.uiSoundEntries?.firstOrNull { it.assetType == "page_flip_sound" }) ?: "audio/ui/page-flip.wav"

    private fun <T> readJsonOrNull(path: String, serializer: kotlinx.serialization.KSerializer<T>): T? =
        runCatching {
            assets.open(path).bufferedReader().use { reader ->
                json.decodeFromString(serializer, reader.readText())
            }
        }.getOrNull()

    private fun bestPath(entry: AssetManifestEntry?): String? {
        if (entry == null) return null
        val bestCandidate = entry.candidates
            .filter { candidate -> candidate.outputFile?.let { assetExists(it) } == true }
            .minByOrNull { priority(it.status) }
        if (bestCandidate?.outputFile != null) return bestCandidate.outputFile
        return entry.outputFile?.takeIf { assetExists(it) }
    }

    private fun assetExists(path: String): Boolean =
        runCatching {
            assets.open("shared-content/$path").close()
            true
        }.getOrDefault(false)

    private fun priority(status: String?): Int =
        when (status) {
            "commissioned_final", "human_recorded_final" -> 0
            "commissioned_reviewed", "generated_reviewed", "human_recorded_reviewed", "synthetic_reviewed" -> 1
            "commissioned_draft", "generated_draft", "human_recorded_draft", "synthetic_draft" -> 2
            "placeholder" -> 3
            else -> 9
        }

    private fun inferredNarrationLanguage(assetType: String?): String =
        if (assetType == "english_narration") "en" else "ko"
}
