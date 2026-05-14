package com.moonjar.stories.data

import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

class SharedContentContractTest {
    private val json = Json { ignoreUnknownKeys = true }

    @Test
    fun completeCatalogCountsMatchExpandedLaunchSet() {
        val root = locateSharedContentRoot()
        val catalog = json.decodeFromString<Catalog>(root.resolve("catalog.json").readText())
        val completeEntries = catalog.books.filter { it.status == CatalogStatus.Complete }

        assertEquals(24, catalog.books.size)
        assertEquals(catalog.books.size, completeEntries.size)

        val counts = completeEntries.associate { entry ->
            val bookPath = requireNotNull(entry.bookPath)
            val book = json.decodeFromString<StoryBook>(root.resolve(bookPath).readText())
            entry.id to book.pages.size
        }

        assertEquals(32, counts["book.sun_moon"])
        assertEquals(24, counts["book.gold_silver_axe"])
        assertEquals(24, counts["book.tiger_persimmon"])
        assertEquals(32, counts["book.heungbu_nolbu"])
        assertEquals(26, counts["book.red_bean_grandma"])
        assertEquals(catalog.books.sumOf { it.pageTarget }, counts.values.sum())
    }

    @Test
    fun assetManifestsCoverAllSceneAndNarrationTracks() {
        val root = locateSharedContentRoot()
        val imageManifest = json.decodeFromString<ImageManifest>(
            root.resolve("assets/manifests/image_manifest.json").readText()
        )
        val audioManifest = json.decodeFromString<AudioManifest>(
            root.resolve("audio/manifests/audio_manifest.json").readText()
        )

        val catalog = json.decodeFromString<Catalog>(root.resolve("catalog.json").readText())
        val completeIds = catalog.books.filter { it.status == CatalogStatus.Complete }.map { it.id }.toSet()
        val expectedScenes = catalog.books.filter { it.status == CatalogStatus.Complete }.sumOf { it.pageTarget }
        val completeSceneEntries = imageManifest.sceneEntries.filter { it.storyId in completeIds }
        val completeNarrationEntries = audioManifest.narrationEntries.filter { it.storyId in completeIds }

        assertEquals(expectedScenes, completeSceneEntries.size)
        assertEquals(expectedScenes * 2, completeNarrationEntries.size)
        assertEquals(32, imageManifest.sceneEntries.count { it.storyId == "book.sun_moon" })
        assertEquals(64, audioManifest.narrationEntries.count { it.storyId == "book.sun_moon" })
        assertTrue(audioManifest.narrationEntries.any { it.language == "en" })
        assertTrue(audioManifest.narrationEntries.any { it.language == "ko" })
    }

    @Test
    fun assetResolverPriorityInputsAreGeneratedDraftAndExist() {
        val root = locateSharedContentRoot()
        val imageManifest = json.decodeFromString<ImageManifest>(
            root.resolve("assets/manifests/image_manifest.json").readText()
        )

        imageManifest.sceneEntries.forEach { entry ->
            val outputFile = requireNotNull(entry.outputFile)
            assertTrue(root.resolve(outputFile).isFile, outputFile)
            assertTrue(entry.status != "placeholder", outputFile)
            val bestCandidate = entry.candidates.minByOrNull { priority(it.status) }
                ?: error("missing candidate for $outputFile")
            assertEquals(outputFile, bestCandidate.outputFile)
            assertTrue(priority(entry.status) <= priority("generated_draft"), outputFile)
        }
    }

    @Test
    fun narrationTracksAreEnglishFirstWithKoreanOptional() {
        val root = locateSharedContentRoot()
        val catalog = json.decodeFromString<Catalog>(root.resolve("catalog.json").readText())
        val audioManifest = json.decodeFromString<AudioManifest>(
            root.resolve("audio/manifests/audio_manifest.json").readText()
        )

        val expectedKeys = catalog.books
            .filter { it.status == CatalogStatus.Complete }
            .flatMap { entry ->
                val book = json.decodeFromString<StoryBook>(root.resolve(requireNotNull(entry.bookPath)).readText())
                book.pages.flatMap { page ->
                    listOf("${entry.id}|${page.id}|en", "${entry.id}|${page.id}|ko")
                }
            }
            .toSet()

        val actualKeys = audioManifest.narrationEntries.mapNotNull { entry ->
            val storyId = entry.storyId ?: return@mapNotNull null
            val sceneId = entry.sceneId ?: return@mapNotNull null
            val language = entry.language ?: return@mapNotNull null
            val outputFile = entry.outputFile ?: return@mapNotNull null
            assertTrue(root.resolve(outputFile).isFile, outputFile)
            assertEquals("synthetic_draft", entry.status)
            "$storyId|$sceneId|$language"
        }.toSet()

        assertTrue(actualKeys.containsAll(expectedKeys))
    }

    @Test
    fun premiumCatalogEntriesRemainLockedWithContentPayloads() {
        val root = locateSharedContentRoot()
        val catalog = json.decodeFromString<Catalog>(root.resolve("catalog.json").readText())
        val premiumBooks = catalog.books.filter { it.access == BookAccess.Premium }

        assertTrue(premiumBooks.isNotEmpty())
        assertTrue(premiumBooks.all { it.status == CatalogStatus.Complete })
        assertTrue(premiumBooks.all { it.bookPath?.isNotBlank() == true })
    }

    @Test
    fun bookSchemaMatchesValidatorContract() {
        val root = locateSharedContentRoot()
        val schema = json.parseToJsonElement(root.resolve("schemas/book.schema.json").readText()).jsonObject
        val required = schema.requiredSet()
        assertTrue(required.containsAll(listOf("coverAsset", "coverAssetStatus", "characterBible", "narrationAudioStatus")))

        val pageItems = schema
            .jsonObject("properties")
            .jsonObject("pages")
            .jsonObject("items")
        val pageRequired = pageItems.requiredSet()
        assertTrue(pageRequired.containsAll(listOf("text", "storyBeat", "imagePrompt", "audioPrompt", "animation")))
    }

    private fun locateSharedContentRoot(): File {
        val workingDirectory = requireNotNull(System.getProperty("user.dir")) { "user.dir is unavailable" }
        val candidates = generateSequence(File(workingDirectory).canonicalFile) { parent ->
            parent.parentFile
        }.flatMap { current ->
            sequenceOf(
                current.resolve("shared-content"),
                current.resolve("../shared-content"),
                current.resolve("../../shared-content")
            )
        }
        return candidates.firstOrNull { it.resolve("catalog.json").isFile }
            ?: error("shared-content/catalog.json was not found from ${System.getProperty("user.dir")}")
    }

    private fun priority(status: String?): Int =
        when (status) {
            "commissioned_final", "human_recorded_final" -> 0
            "commissioned_reviewed", "generated_reviewed", "human_recorded_reviewed", "synthetic_reviewed" -> 1
            "commissioned_draft", "generated_draft", "human_recorded_draft", "synthetic_draft" -> 2
            "placeholder" -> 3
            else -> 9
        }

    private fun JsonObject.jsonObject(key: String): JsonObject =
        requireNotNull(this[key] as? JsonObject) { "missing object: $key" }

    private fun JsonObject.requiredSet(): Set<String> =
        requireNotNull(this["required"] as? JsonArray) { "missing required array" }
            .jsonArray
            .map { it.jsonPrimitive.content }
            .toSet()
}
