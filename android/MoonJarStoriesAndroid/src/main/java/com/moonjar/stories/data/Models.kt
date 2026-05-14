package com.moonjar.stories.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class LocalizedTitle(
    val ko: String,
    val en: String,
    val romanization: String? = null
)

@Serializable
enum class BookAccess {
    @SerialName("free")
    Free,

    @SerialName("premium")
    Premium
}

@Serializable
enum class CatalogStatus {
    @SerialName("complete")
    Complete,

    @SerialName("metadata_only")
    MetadataOnly
}

@Serializable
data class Catalog(
    val schemaVersion: String,
    val libraryVersion: String,
    val monetization: Monetization,
    val books: List<CatalogBook>
)

@Serializable
data class Monetization(
    val freeBooks: Int,
    val monthlyUsd: Double,
    val annualUsd: Double,
    val lifetimeUsdRange: String,
    val individualBookUsd: Double
)

@Serializable
data class CatalogBook(
    val id: String,
    val slug: String,
    val title: LocalizedTitle,
    val access: BookAccess,
    val status: CatalogStatus,
    val ageRange: String,
    val pageTarget: Int,
    val bookPath: String? = null,
    val sensitivity: String? = null
)

@Serializable
data class StoryBook(
    val schemaVersion: String,
    val id: String,
    val slug: String,
    val title: LocalizedTitle,
    val access: BookAccess,
    val ageRange: String,
    val estimatedMinutes: Int? = null,
    val summary: String,
    val coverAsset: String? = null,
    val sensitivityNotes: List<String> = emptyList(),
    val themes: List<String>,
    val characters: List<String>,
    val pages: List<StoryPage>
)

@Serializable
data class StoryPage(
    val id: String,
    val pageNumber: Int,
    val koreanText: String,
    val englishText: String,
    val text: StoryTextVariants? = null,
    val narrationScript: String,
    val vocabulary: List<VocabularyItem>,
    val imagePrompt: String,
    val imageAsset: String? = null,
    val imageSource: String? = null,
    val audioPrompt: String,
    val narrationAudio: String? = null,
    val ambientAudio: String? = null,
    val animation: SceneAnimation,
    val storyBeat: StoryBeat? = null
)

@Serializable
data class StoryTextVariants(
    val enLittle: String? = null,
    val enStandard: String? = null,
    val koLittle: String? = null,
    val koStandard: String? = null
)

@Serializable
data class StoryBeat(
    val purpose: String? = null,
    val emotion: String? = null,
    val pageTurnHook: String? = null,
    val readAloudCue: String? = null,
    val childInteraction: String? = null
)

@Serializable
data class VocabularyItem(
    val ko: String,
    val en: String,
    val romanization: String? = null,
    val definitionEn: String? = null,
    val definitionKo: String? = null
)

@Serializable
data class SceneAnimation(
    val type: String,
    val loopDuration: Double,
    val motionSafety: String? = null,
    val layers: List<AnimationLayer>
)

@Serializable
data class AnimationLayer(
    val name: String,
    val motion: String,
    val intensity: String? = null,
    val outputFile: String? = null,
    val status: String? = null
)

@Serializable
data class AssetManifestCandidate(
    val outputFile: String? = null,
    val status: String? = null
)

@Serializable
data class AssetManifestEntry(
    val assetType: String? = null,
    val storyId: String? = null,
    val storySlug: String? = null,
    val sceneId: String? = null,
    val language: String? = null,
    val outputFile: String? = null,
    val status: String? = null,
    val candidates: List<AssetManifestCandidate> = emptyList()
)

@Serializable
data class ImageManifest(
    val sceneEntries: List<AssetManifestEntry> = emptyList(),
    val coverEntries: List<AssetManifestEntry> = emptyList(),
    val appIconConcepts: List<AssetManifestEntry> = emptyList()
)

@Serializable
data class AudioManifest(
    val narrationEntries: List<AssetManifestEntry> = emptyList(),
    val ambientEntries: List<AssetManifestEntry> = emptyList(),
    val uiSoundEntries: List<AssetManifestEntry> = emptyList()
)
