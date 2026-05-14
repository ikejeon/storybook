package com.moonjar.stories.ui

import android.graphics.BitmapFactory
import android.provider.Settings
import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.Book
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.LockOpen
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Replay
import androidx.compose.material.icons.filled.Translate
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TextField
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.moonjar.stories.billing.AudioEngine
import com.moonjar.stories.billing.EntitlementManager
import com.moonjar.stories.billing.EntitlementState
import com.moonjar.stories.billing.PurchaseState
import com.moonjar.stories.data.BookAccess
import com.moonjar.stories.data.Catalog
import com.moonjar.stories.data.CatalogBook
import com.moonjar.stories.data.CatalogStatus
import com.moonjar.stories.data.ContentRepository
import com.moonjar.stories.data.LocalizedTitle
import com.moonjar.stories.data.StoryBook
import com.moonjar.stories.data.StoryPage
import java.io.File
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.json.JSONObject

private enum class ReaderLanguage(val label: String, val compactLabel: String) {
    English("English", "EN"),
    Bilingual("KO/EN", "KO/EN"),
    Korean("한국어", "KO")
}

private enum class ReaderTextMode(val label: String) {
    Story("Story"),
    Little("Little")
}

private sealed interface Screen {
    data object Library : Screen
    data class Detail(val bookId: String) : Screen
    data class Reader(val bookId: String) : Screen
}

private fun canReadCatalogEntry(
    access: BookAccess,
    bookId: String,
    entitlement: EntitlementState,
    purchaseState: PurchaseState
): Boolean =
    access == BookAccess.Free ||
        entitlement == EntitlementState.Subscribed ||
        entitlement == EntitlementState.Lifetime ||
        purchaseState.unlockedBookIds.contains(bookId)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MoonJarApp(
    repository: ContentRepository,
    demoSelfTest: String? = null,
    demoSelfTestToken: String? = null,
    selfTestOutputDir: File? = null
) {
    val entitlementManager = remember { EntitlementManager() }
    val entitlement by entitlementManager.state.collectAsState()
    var catalog by remember { mutableStateOf<Catalog?>(null) }
    var books by remember { mutableStateOf<List<StoryBook>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }
    var screen by remember { mutableStateOf<Screen>(Screen.Library) }
    var language by remember { mutableStateOf(ReaderLanguage.English) }
    var bedtimeMode by remember { mutableStateOf(false) }
    val purchaseState by entitlementManager.purchaseState.collectAsState()
    val topBarCompact = LocalConfiguration.current.screenWidthDp < 600

    LaunchedEffect(repository) {
        runCatching {
            val loadedCatalog = repository.loadCatalog()
            catalog = loadedCatalog
            books = repository.loadCompleteBooks(loadedCatalog)
        }.onFailure {
            error = it.message ?: "Content could not be loaded."
        }
    }

    LaunchedEffect(catalog, books, demoSelfTest, demoSelfTestToken) {
        if (demoSelfTest == "reader-contract" && catalog != null && books.isNotEmpty() && selfTestOutputDir != null) {
            val sunMoon = books.firstOrNull { it.id == "book.sun_moon" } ?: books.first()
            language = ReaderLanguage.English
            screen = Screen.Reader(sunMoon.id)
        }
    }

    BackHandler(enabled = screen !is Screen.Library) {
        screen = Screen.Library
    }

    Scaffold(
        topBar = {
            if (screen !is Screen.Reader) {
                TopAppBar(
                    title = {
                        if (!topBarCompact) {
                            Text("Moon Jar Stories", maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = MoonIvory,
                        titleContentColor = IndigoInk
                    ),
                    actions = {
                        LanguageChooser(language = language, compact = topBarCompact, onChange = { language = it })
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.padding(horizontal = if (topBarCompact) 8.dp else 12.dp)
                        ) {
                            Text(
                                if (topBarCompact) "Bed" else "Bedtime",
                                style = MaterialTheme.typography.labelMedium,
                                maxLines = 1
                            )
                            Switch(checked = bedtimeMode, onCheckedChange = { bedtimeMode = it })
                        }
                    }
                )
            }
        },
        containerColor = if (screen is Screen.Reader || bedtimeMode) IndigoInk else MoonIvory
    ) { padding ->
        AnimatedContent(
            targetState = screen,
            label = "screen",
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) { target ->
            when (target) {
                Screen.Library -> LibraryScreen(
                    catalog = catalog,
                    books = books,
                    repository = repository,
                    entitlement = entitlement,
                    purchaseState = purchaseState,
                    onOpen = { screen = Screen.Detail(it.id) }
                )

                is Screen.Detail -> {
                    val catalogEntry = catalog?.books?.firstOrNull { it.id == target.bookId }
                    val book = books.firstOrNull { it.id == target.bookId }
                    if (book != null) {
                        BookDetailScreen(
                            book = book,
                            repository = repository,
                            entitlement = entitlement,
                            purchaseState = purchaseState,
                            onRead = { screen = Screen.Reader(book.id) },
                            onUnlock = { entitlementManager.unlockForPrototype() }
                        )
                    } else if (catalogEntry != null) {
                        ComingSoonScreen(entry = catalogEntry)
                    }
                }

                is Screen.Reader -> {
                    val book = books.firstOrNull { it.id == target.bookId }
                    if (book != null) {
                        ReaderScreen(
                            book = book,
                            repository = repository,
                            language = language,
                            bedtimeMode = bedtimeMode,
                            onExit = { screen = Screen.Library },
                            demoSelfTest = demoSelfTest,
                            demoSelfTestToken = demoSelfTestToken,
                            selfTestOutputDir = selfTestOutputDir,
                            catalogBookCount = catalog?.books?.size ?: 0,
                            completeBookCount = books.size,
                            premiumLockedForSelfTest = catalog
                                ?.books
                                ?.firstOrNull { it.access == BookAccess.Premium }
                                ?.let { !entitlementManager.canRead(it.access, it.id) } ?: true
                        )
                    }
                }
            }
        }
    }

    error?.let {
        AlertDialog(
            onDismissRequest = { error = null },
            confirmButton = { TextButton(onClick = { error = null }) { Text("OK") } },
            title = { Text("Content Unavailable") },
            text = { Text(it) }
        )
    }
}

@Composable
private fun LanguageChooser(language: ReaderLanguage, compact: Boolean = false, onChange: (ReaderLanguage) -> Unit) {
    Row(horizontalArrangement = Arrangement.spacedBy(if (compact) 4.dp else 6.dp)) {
        ReaderLanguage.entries.forEach { mode ->
            FilterChip(
                selected = mode == language,
                onClick = { onChange(mode) },
                label = { Text(if (compact) mode.compactLabel else mode.label, maxLines = 1) },
                leadingIcon = {
                    if (mode == language && !compact) {
                        Icon(Icons.Default.Translate, contentDescription = null, modifier = Modifier.size(16.dp))
                    }
                }
            )
        }
    }
}

@Composable
private fun LibraryScreen(
    catalog: Catalog?,
    books: List<StoryBook>,
    repository: ContentRepository,
    entitlement: EntitlementState,
    purchaseState: PurchaseState,
    onOpen: (CatalogBook) -> Unit
) {
    LazyVerticalGrid(
        columns = GridCells.Adaptive(minSize = 250.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        horizontalArrangement = Arrangement.spacedBy(16.dp),
        modifier = Modifier
            .fillMaxSize()
            .background(MoonIvory)
            .padding(20.dp)
    ) {
        items(catalog?.books.orEmpty(), key = { it.id }) { entry ->
                    val unlocked = canReadCatalogEntry(entry.access, entry.id, entitlement, purchaseState)
                    val book = books.firstOrNull { it.id == entry.id }
            CatalogTile(
                entry = entry,
                coverAsset = book?.let { repository.resolveCoverAsset(it) },
                repository = repository,
                unlocked = unlocked,
                onClick = { onOpen(entry) }
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun CatalogTile(
    entry: CatalogBook,
    coverAsset: String?,
    repository: ContentRepository,
    unlocked: Boolean,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White.copy(alpha = 0.78f)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            MoonJarCover(
                title = entry.title,
                assetPath = coverAsset,
                repository = repository,
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(1.5f)
            )
            Text(entry.title.ko, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = IndigoInk)
            Text(
                entry.title.en,
                style = MaterialTheme.typography.bodyMedium,
                color = IndigoInk.copy(alpha = 0.74f),
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = if (unlocked) Icons.Default.Book else Icons.Default.Lock,
                    contentDescription = null,
                    tint = if (unlocked) JadeLeaf else Persimmon,
                    modifier = Modifier.size(18.dp)
                )
                Text(
                    text = if (entry.access == BookAccess.Free) "Free" else "Premium",
                    style = MaterialTheme.typography.labelLarge,
                    color = if (unlocked) JadeLeaf else Persimmon
                )
                Text("${entry.pageTarget} pages", style = MaterialTheme.typography.labelMedium, color = IndigoInk.copy(alpha = 0.62f))
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun BookDetailScreen(
    book: StoryBook,
    repository: ContentRepository,
    entitlement: EntitlementState,
    purchaseState: PurchaseState,
    onRead: () -> Unit,
    onUnlock: () -> Unit
) {
    var showParentGate by remember { mutableStateOf(false) }
    var showPaywall by remember { mutableStateOf(false) }
    val unlocked = canReadCatalogEntry(book.access, book.id, entitlement, purchaseState)

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MoonIvory)
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp)
    ) {
        MoonJarCover(
            title = book.title,
            assetPath = repository.resolveCoverAsset(book),
            repository = repository,
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(1.5f)
        )
        Text(book.title.ko, style = MaterialTheme.typography.displaySmall, fontWeight = FontWeight.Bold, color = IndigoInk)
        Text(book.title.en, style = MaterialTheme.typography.titleLarge, color = IndigoInk.copy(alpha = 0.72f))
        Text(book.summary, style = MaterialTheme.typography.bodyLarge, color = IndigoInk.copy(alpha = 0.82f))
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            book.themes.forEach { theme ->
                AssistChip(onClick = {}, label = { Text(theme.replaceFirstChar { it.titlecase() }) })
            }
        }
        Button(onClick = { if (unlocked) onRead() else showPaywall = true }, modifier = Modifier.fillMaxWidth()) {
            Icon(if (unlocked) Icons.Default.PlayArrow else Icons.Default.LockOpen, contentDescription = null)
            Spacer(Modifier.size(8.dp))
            Text(if (unlocked) "Read" else "Unlock")
        }
    }

    if (showPaywall) {
        PaywallDialog(
            onDismiss = { showPaywall = false },
            onContinue = {
                showPaywall = false
                showParentGate = true
            }
        )
    }

    if (showParentGate) {
        ParentGateDialog(
            onDismiss = { showParentGate = false },
            onPass = {
                showParentGate = false
                onUnlock()
            }
        )
    }
}

@Composable
private fun ComingSoonScreen(entry: CatalogBook) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MoonIvory)
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        MoonJarCover(title = entry.title, modifier = Modifier.fillMaxWidth().aspectRatio(1.5f))
        Text(entry.title.ko, style = MaterialTheme.typography.displaySmall, fontWeight = FontWeight.Bold, color = IndigoInk)
        Text(entry.sensitivity.orEmpty(), textAlign = TextAlign.Center, color = IndigoInk.copy(alpha = 0.72f))
    }
}

@Composable
private fun ReaderScreen(
    book: StoryBook,
    repository: ContentRepository,
    language: ReaderLanguage,
    bedtimeMode: Boolean,
    onExit: () -> Unit,
    demoSelfTest: String? = null,
    demoSelfTestToken: String? = null,
    selfTestOutputDir: File? = null,
    catalogBookCount: Int = 0,
    completeBookCount: Int = 0,
    premiumLockedForSelfTest: Boolean = true
) {
    var pageIndex by remember(book.id) { mutableIntStateOf(0) }
    var playing by remember { mutableStateOf(false) }
    var autoPlay by remember { mutableStateOf(false) }
    var realBookMode by remember { mutableStateOf(false) }
    var textMode by remember { mutableStateOf(ReaderTextMode.Story) }
    var dragOffset by remember { mutableFloatStateOf(0f) }
    var buttonTurnOffset by remember { mutableFloatStateOf(0f) }
    var turnInProgress by remember { mutableStateOf(false) }
    val page = book.pages[pageIndex]
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val systemReducedMotion = remember {
        Settings.Global.getFloat(context.contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f
    }
    val reduceSceneMotion = bedtimeMode || systemReducedMotion
    val audioEngine = remember(book.id) { AudioEngine(context) }
    val narrationLanguage = if (language == ReaderLanguage.Korean) "ko" else "en"
    val narrationPath = repository.resolveNarrationAsset(book, page, narrationLanguage)
    val narrationUri = narrationPath?.let { repository.sharedAssetUri(it) }
    val pageTurnUri = repository.sharedAssetUri(repository.resolvePageFlipSound())
    val configuration = LocalConfiguration.current
    val phonePortrait = configuration.screenWidthDp < 600 && configuration.screenHeightDp >= configuration.screenWidthDp
    val supportsRealBookMode = !phonePortrait
    val wideLayout = supportsRealBookMode && configuration.screenWidthDp > configuration.screenHeightDp * 1.12f
    val spreadMode = supportsRealBookMode && (realBookMode || wideLayout)
    val visualTurnOffset = if (kotlin.math.abs(dragOffset) > 0.5f) dragOffset else buttonTurnOffset
    fun spreadStart(): Int = if (pageIndex % 2 == 0) pageIndex else (pageIndex - 1).coerceAtLeast(0)

    fun turnToPage(target: Int, direction: Float) {
        if (turnInProgress || target == pageIndex || target !in book.pages.indices) return
        audioEngine.stop()
        playing = false

        if (reduceSceneMotion) {
            pageIndex = target
            audioEngine.playSound(pageTurnUri, bedtimeMode)
            return
        }

        scope.launch {
            turnInProgress = true
            val maxTurn = 300f
            buttonTurnOffset = direction * maxTurn
            pageIndex = target
            audioEngine.playSound(pageTurnUri, bedtimeMode)
            repeat(12) { step ->
                buttonTurnOffset = direction * maxTurn * (1f - ((step + 1) / 12f))
                delay(16)
            }
            buttonTurnOffset = 0f
            turnInProgress = false
        }
    }

    fun goToNextPage() {
        val target = if (spreadMode) (spreadStart() + 2).coerceAtMost(book.pages.lastIndex) else pageIndex + 1
        if (target != pageIndex && pageIndex < book.pages.lastIndex) {
            turnToPage(target, -1f)
        }
    }

    fun goToPreviousPage() {
        val target = if (spreadMode) (spreadStart() - 2).coerceAtLeast(0) else pageIndex - 1
        if (target != pageIndex && pageIndex > 0) {
            turnToPage(target, 1f)
        }
    }

    fun goToNextSpreadForSelfTest() {
        val target = (spreadStart() + 2).coerceAtMost(book.pages.lastIndex)
        if (target != pageIndex && pageIndex < book.pages.lastIndex) {
            turnToPage(target, -1f)
        }
    }

    fun writeReaderSelfTest(
        initialPage: Int,
        afterNextPage: Int,
        afterPreviousPage: Int,
        realBookModeToggled: Boolean,
        beforeSpreadNextPage: Int,
        afterSpreadNextPage: Int,
        playbackStarted: Boolean
    ) {
        val firstPage = book.pages.first()
        val englishNarration = repository.resolveNarrationAsset(book, firstPage, "en")
        val koreanNarration = repository.resolveNarrationAsset(book, firstPage, "ko")
        val sceneAsset = repository.resolveSceneAsset(book, firstPage)
        val result = JSONObject()
            .put("test", "android-reader-contract")
            .put("token", demoSelfTestToken ?: "")
            .put("catalogBooks", catalogBookCount)
            .put("completeBooks", completeBookCount)
            .put("openedBookId", book.id)
            .put("sceneCount", book.pages.size)
            .put("englishFirst", language == ReaderLanguage.English)
            .put("freeBookReadable", book.access == BookAccess.Free)
            .put("premiumBookLocked", premiumLockedForSelfTest)
            .put("sceneAssetResolved", sceneAsset != null)
            .put("englishNarrationResolved", englishNarration != null)
            .put("koreanNarrationResolved", koreanNarration != null)
            .put("initialPageIndex", initialPage)
            .put("afterNextPageIndex", afterNextPage)
            .put("afterPreviousPageIndex", afterPreviousPage)
            .put("beforeSpreadNextPageIndex", beforeSpreadNextPage)
            .put("afterSpreadNextPageIndex", afterSpreadNextPage)
            .put("nextAdvanced", afterNextPage == initialPage + 1)
            .put("previousReturned", afterPreviousPage == initialPage)
            .put("phonePortrait", phonePortrait)
            .put("realBookSupported", supportsRealBookMode)
            .put("realBookModeToggled", realBookModeToggled)
            .put("spreadNextAdvanced", if (supportsRealBookMode) afterSpreadNextPage >= beforeSpreadNextPage + 2 else true)
            .put("singlePageFallbackKept", if (supportsRealBookMode) true else afterSpreadNextPage == beforeSpreadNextPage + 1)
            .put("playbackStarted", playbackStarted)
            .put("timestamp", System.currentTimeMillis())
        selfTestOutputDir?.resolve("moonjar-android-self-test.json")?.writeText(result.toString(2))
    }

    DisposableEffect(audioEngine) {
        onDispose { audioEngine.release() }
    }

    LaunchedEffect(supportsRealBookMode) {
        if (!supportsRealBookMode && realBookMode) {
            realBookMode = false
        }
    }

    LaunchedEffect(demoSelfTest, demoSelfTestToken, book.id) {
        if (demoSelfTest != "reader-contract" || selfTestOutputDir == null) return@LaunchedEffect
        delay(450)
        val initialPage = pageIndex
        goToNextPage()
        delay(if (reduceSceneMotion) 120 else 620)
        val afterNextPage = pageIndex
        goToPreviousPage()
        delay(if (reduceSceneMotion) 120 else 620)
        val afterPreviousPage = pageIndex

        realBookMode = true
        delay(160)
        val beforeSpreadNextPage = pageIndex
        if (supportsRealBookMode) {
            goToNextSpreadForSelfTest()
        } else {
            goToNextPage()
        }
        delay(if (reduceSceneMotion) 120 else 620)
        val afterSpreadNextPage = pageIndex

        val firstNarration = repository.resolveNarrationAsset(book, book.pages.first(), "en")
        val playbackStarted = firstNarration != null
        if (firstNarration != null) {
            audioEngine.replay(repository.sharedAssetUri(firstNarration), bedtimeMode)
            playing = true
        }

        writeReaderSelfTest(
            initialPage = initialPage,
            afterNextPage = afterNextPage,
            afterPreviousPage = afterPreviousPage,
            realBookModeToggled = realBookMode,
            beforeSpreadNextPage = beforeSpreadNextPage,
            afterSpreadNextPage = afterSpreadNextPage,
            playbackStarted = playbackStarted
        )
    }

    LaunchedEffect(page.id) {
        audioEngine.stop()
        playing = false
        if (autoPlay && narrationUri != null) {
            audioEngine.replay(narrationUri, bedtimeMode) {
                if (autoPlay && pageIndex < book.pages.lastIndex) {
                    goToNextPage()
                }
            }
            playing = true
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(if (bedtimeMode) DeepIndigo else DeepIndigo)
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        ReaderChromeRow(
            title = book.title.en,
            language = language,
            bedtimeMode = bedtimeMode,
            pageIndex = pageIndex,
            pageCount = book.pages.size,
            compactLayout = phonePortrait,
            onExit = onExit
        )
        BookPageSurface(
            dragOffset = visualTurnOffset,
            reducedMotion = reduceSceneMotion,
            bedtimeMode = bedtimeMode,
            modifier = Modifier
                .weight(1f)
                .pointerInput(pageIndex, book.id) {
                    detectHorizontalDragGestures(
                        onDragEnd = {
                            when {
                                dragOffset < -92f -> goToNextPage()
                                dragOffset > 92f -> goToPreviousPage()
                            }
                            dragOffset = 0f
                        },
                        onDragCancel = { dragOffset = 0f },
                        onHorizontalDrag = { change, dragAmount ->
                            change.consume()
                            dragOffset = (dragOffset + dragAmount).coerceIn(-320f, 320f)
                        }
                    )
            }
        ) {
            if (spreadMode) {
                RealBookSpread(
                    book = book,
                    pageIndex = pageIndex,
                    repository = repository,
                    language = language,
                    textMode = textMode,
                    bedtimeMode = bedtimeMode,
                    reducedMotion = reduceSceneMotion,
                    dragOffset = visualTurnOffset
                )
            } else {
                PortraitReaderPage(
                    page = page,
                    pageIndex = pageIndex,
                    pageCount = book.pages.size,
                    language = language,
                    textMode = textMode,
                    repository = repository,
                    imageAsset = repository.resolveSceneAsset(book, page),
                    bedtimeMode = bedtimeMode,
                    reducedMotion = reduceSceneMotion,
                    onPrevious = ::goToPreviousPage,
                    onNext = ::goToNextPage
                )
            }
        }
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color.Transparent)
                .padding(horizontal = 4.dp, vertical = 4.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(28.dp))
                    .background(IndigoInk.copy(alpha = 0.62f))
                    .border(1.dp, MoonIvory.copy(alpha = 0.20f), RoundedCornerShape(28.dp))
                    .padding(horizontal = 12.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceEvenly,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    IconButton(onClick = {
                        if (pageIndex > 0) {
                            goToPreviousPage()
                        }
                    }, enabled = pageIndex > 0) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = MoonIvory)
                    }
                    IconButton(
                        onClick = {
                            if (narrationUri != null) {
                                audioEngine.playOrPause(narrationUri, bedtimeMode) {
                                    playing = false
                                    if (autoPlay && pageIndex < book.pages.lastIndex) {
                                        goToNextPage()
                                    }
                                }
                                playing = !playing
                            }
                        }
                    ) {
                        Icon(if (playing) Icons.Default.Pause else Icons.Default.PlayArrow, contentDescription = "Play", tint = LanternGold)
                    }
                    IconButton(
                        onClick = {
                            if (narrationUri != null) {
                                audioEngine.replay(narrationUri, bedtimeMode)
                                playing = true
                            }
                        }
                    ) {
                        Icon(Icons.Default.Replay, contentDescription = "Replay", tint = MoonIvory)
                    }
                    Text("${page.pageNumber} / ${book.pages.size}", color = MoonIvory.copy(alpha = 0.86f))
                    IconButton(onClick = {
                        goToNextPage()
                    }, enabled = pageIndex < book.pages.lastIndex) {
                        Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = "Next", tint = MoonIvory)
                    }
                }
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    FilterChip(
                        selected = autoPlay,
                        onClick = { autoPlay = !autoPlay },
                        label = { Text("Auto") }
                    )
                    FilterChip(
                        selected = textMode == ReaderTextMode.Little,
                        onClick = { textMode = if (textMode == ReaderTextMode.Story) ReaderTextMode.Little else ReaderTextMode.Story },
                        label = { Text(textMode.label) }
                    )
                    if (supportsRealBookMode) {
                        FilterChip(
                            selected = spreadMode,
                            onClick = { realBookMode = !realBookMode },
                            label = { Text("Book") }
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun ReaderChromeRow(
    title: String,
    language: ReaderLanguage,
    bedtimeMode: Boolean,
    pageIndex: Int,
    pageCount: Int,
    compactLayout: Boolean,
    onExit: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(58.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        IconButton(
            onClick = onExit,
            modifier = Modifier
                .clip(CircleShape)
                .background(IndigoInk.copy(alpha = 0.70f))
                .border(1.dp, MoonIvory.copy(alpha = 0.22f), CircleShape)
        ) {
            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Library", tint = MoonIvory)
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.weight(1f)) {
            Text(
                if (compactLayout) "Moon Jar" else "Moon Jar Stories",
                style = if (compactLayout) MaterialTheme.typography.titleMedium else MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.SemiBold,
                color = MoonIvory,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            Text(title, style = MaterialTheme.typography.labelMedium, color = MoonIvory.copy(alpha = 0.68f), maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        Text(
            "${pageIndex + 1} / $pageCount",
            style = MaterialTheme.typography.labelLarge,
            color = MoonIvory.copy(alpha = 0.74f),
            modifier = Modifier
                .clip(RoundedCornerShape(22.dp))
                .background(IndigoInk.copy(alpha = 0.68f))
                .border(1.dp, MoonIvory.copy(alpha = 0.18f), RoundedCornerShape(22.dp))
                .padding(horizontal = 12.dp, vertical = 8.dp)
        )
        Text(
            language.label,
            style = MaterialTheme.typography.labelLarge,
            color = if (bedtimeMode) LanternGold else MoonIvory,
            modifier = Modifier
                .clip(RoundedCornerShape(22.dp))
                .background(IndigoInk.copy(alpha = 0.68f))
                .border(1.dp, MoonIvory.copy(alpha = 0.18f), RoundedCornerShape(22.dp))
                .padding(horizontal = 12.dp, vertical = 8.dp)
        )
    }
}

@Composable
private fun PortraitReaderPage(
    page: StoryPage,
    pageIndex: Int,
    pageCount: Int,
    language: ReaderLanguage,
    textMode: ReaderTextMode,
    repository: ContentRepository,
    imageAsset: String?,
    bedtimeMode: Boolean,
    reducedMotion: Boolean,
    onPrevious: () -> Unit,
    onNext: () -> Unit
) {
    val imageWeight = if (language == ReaderLanguage.Bilingual) 0.36f else 0.54f
    val textWeight = 1f - imageWeight
    val textBottomInset = if (language == ReaderLanguage.Bilingual) 18.dp else 34.dp

    Box(modifier = Modifier.fillMaxSize()) {
        Column(modifier = Modifier.fillMaxSize()) {
            AnimatedScene(
                page = page,
                imageAsset = imageAsset,
                repository = repository,
                bedtimeMode = bedtimeMode,
                reducedMotion = reducedMotion,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(imageWeight)
            )
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(textWeight)
                    .background(IvoryWarm)
                    .padding(horizontal = 18.dp, vertical = 16.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxSize()) {
                    IconButton(onClick = onPrevious, enabled = pageIndex > 0) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Previous", tint = IndigoInk.copy(alpha = if (pageIndex > 0) 0.70f else 0.24f))
                    }
                    PageText(
                        page = page,
                        language = language,
                        textMode = textMode,
                        bedtimeMode = false,
                        compactLayout = true,
                        bottomInset = textBottomInset,
                        modifier = Modifier.weight(1f)
                    )
                    IconButton(onClick = onNext, enabled = pageIndex < pageCount - 1) {
                        Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = "Next", tint = IndigoInk.copy(alpha = if (pageIndex < pageCount - 1) 0.70f else 0.24f))
                    }
                }
                FolioMark(
                    pageNumber = pageIndex + 1,
                    side = 1,
                    modifier = Modifier.align(Alignment.BottomStart)
                )
                PageCurlCue(
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .size(76.dp)
                )
            }
        }
        PageDepthOverlay(
            side = 1,
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .fillMaxHeight()
                .width(24.dp)
        )
    }
}

@Composable
private fun BookPageSurface(
    dragOffset: Float,
    reducedMotion: Boolean,
    bedtimeMode: Boolean,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    val progress = (kotlin.math.abs(dragOffset) / 320f).coerceIn(0f, 1f)
    val direction = if (dragOffset < 0f) -1f else 1f

    Box(
        modifier = modifier
            .padding(horizontal = 12.dp, vertical = 12.dp)
            .graphicsLayer {
                rotationY = if (reducedMotion) 0f else direction * progress * 10f
                cameraDistance = 22f * density
                shadowElevation = if (reducedMotion) 0f else 18f + progress * 24f
                translationX = if (reducedMotion) 0f else dragOffset * 0.06f
                clip = true
            }
            .clip(RoundedCornerShape(6.dp))
            .background(if (bedtimeMode) IndigoInk else MoonIvory)
    ) {
        content()
        Box(
            modifier = Modifier
                .align(Alignment.CenterStart)
                .fillMaxSize()
                .background(
                    Brush.horizontalGradient(
                        listOf(IndigoInk.copy(alpha = if (bedtimeMode) 0.34f else 0.20f), Color.Transparent),
                        startX = 0f,
                        endX = 80f
                    )
                )
        )
        Box(
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .fillMaxSize()
                .background(
                    Brush.horizontalGradient(
                        listOf(Color.Transparent, IndigoInk.copy(alpha = 0.18f + progress * 0.26f)),
                        startX = 0f,
                        endX = Float.POSITIVE_INFINITY
                    )
                )
        )
        if (!reducedMotion && progress > 0.03f) {
            PageTurnCurlOverlay(
                progress = progress,
                direction = direction,
                modifier = Modifier.matchParentSize()
            )
        }
    }
}

@Composable
private fun PageDepthOverlay(side: Int, modifier: Modifier = Modifier, intensity: Float = 1f) {
    Canvas(modifier = modifier) {
        repeat(7) { index ->
            val x = if (side < 0) index * 3f else size.width - index * 3f
            drawLine(
                color = IvoryWarm.copy(alpha = (0.22f - index * 0.022f).coerceAtLeast(0.04f) * intensity),
                start = Offset(x, size.height * 0.02f),
                end = Offset(x, size.height * 0.98f),
                strokeWidth = (1.1f + (index % 2) * 0.8f)
            )
        }
        drawRect(
            brush = Brush.horizontalGradient(
                if (side < 0) listOf(IndigoInk.copy(alpha = 0.22f * intensity), Color.Transparent)
                else listOf(Color.Transparent, IndigoInk.copy(alpha = 0.22f * intensity))
            )
        )
        drawRect(
            brush = Brush.verticalGradient(
                listOf(Color.Transparent, Color.White.copy(alpha = 0.10f * intensity), Color.Transparent)
            )
        )
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun PageText(
    page: StoryPage,
    language: ReaderLanguage,
    textMode: ReaderTextMode,
    bedtimeMode: Boolean,
    modifier: Modifier = Modifier,
    compactLayout: Boolean = false,
    bottomInset: androidx.compose.ui.unit.Dp = 0.dp
) {
    val primaryText = if (bedtimeMode) MoonIvory else IndigoInk
    val secondaryText = if (bedtimeMode) MoonIvory.copy(alpha = 0.74f) else IndigoInk.copy(alpha = 0.72f)
    val englishText = if (textMode == ReaderTextMode.Little) page.text?.enLittle ?: page.englishText else page.text?.enStandard ?: page.englishText
    val koreanText = if (textMode == ReaderTextMode.Little) page.text?.koLittle ?: page.koreanText else page.text?.koStandard ?: page.koreanText
    val compactBilingual = compactLayout && language == ReaderLanguage.Bilingual
    val koreanStyle = if (compactLayout) {
        if (compactBilingual) {
            MaterialTheme.typography.titleMedium.copy(fontSize = 14.sp, lineHeight = 18.sp)
        } else {
            MaterialTheme.typography.titleMedium.copy(fontSize = 19.sp, lineHeight = 25.sp)
        }
    } else {
        MaterialTheme.typography.titleLarge
    }
    val englishStyle = if (compactLayout) {
        if (compactBilingual) {
            MaterialTheme.typography.bodyMedium.copy(fontSize = 13.sp, lineHeight = 18.sp)
        } else {
            MaterialTheme.typography.bodyMedium.copy(fontSize = 17.sp, lineHeight = 24.sp)
        }
    } else {
        MaterialTheme.typography.bodyLarge
    }
    val itemSpacing = if (compactBilingual) 4.dp else 8.dp
    Column(
        modifier = modifier.verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(itemSpacing)
    ) {
        if (language == ReaderLanguage.Korean || language == ReaderLanguage.Bilingual) {
            Text(koreanText, style = koreanStyle, fontWeight = FontWeight.SemiBold, color = primaryText)
        }
        if (language == ReaderLanguage.English || language == ReaderLanguage.Bilingual) {
            Text(englishText, style = englishStyle, color = secondaryText)
        }
        if (page.vocabulary.isNotEmpty() && !compactBilingual) {
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                page.vocabulary.take(3).forEach { item ->
                    Column(
                        modifier = Modifier
                            .clip(RoundedCornerShape(7.dp))
                            .background((if (bedtimeMode) MoonIvory else Color.White).copy(alpha = if (bedtimeMode) 0.12f else 0.34f))
                            .border(1.dp, IndigoInk.copy(alpha = if (bedtimeMode) 0.08f else 0.10f), RoundedCornerShape(7.dp))
                            .padding(horizontal = 9.dp, vertical = 5.dp)
                    ) {
                        Text(item.en, style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.SemiBold, color = secondaryText, maxLines = 1)
                        Text(item.ko, style = MaterialTheme.typography.labelSmall, color = secondaryText.copy(alpha = 0.82f), maxLines = 1)
                    }
                }
            }
        }
        if (bottomInset > 0.dp) {
            Spacer(Modifier.height(bottomInset))
        }
    }
}

@Composable
private fun FolioMark(pageNumber: Int, side: Int, modifier: Modifier = Modifier) {
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(18.dp))
            .background(Color.White.copy(alpha = 0.20f))
            .padding(horizontal = 9.dp, vertical = 5.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        if (side > 0) {
            Box(modifier = Modifier.width(22.dp).height(1.dp).background(IndigoInk.copy(alpha = 0.22f)))
        }
        Text("$pageNumber", style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.SemiBold, color = IndigoInk.copy(alpha = 0.48f))
        if (side < 0) {
            Box(modifier = Modifier.width(22.dp).height(1.dp).background(IndigoInk.copy(alpha = 0.22f)))
        }
    }
}


@Composable
private fun PageCurlCue(modifier: Modifier = Modifier) {
    Canvas(modifier = modifier) {
        val paper = androidx.compose.ui.graphics.Path().apply {
            moveTo(size.width, size.height)
            lineTo(size.width, size.height * 0.12f)
            quadraticTo(size.width * 0.54f, size.height * 0.74f, size.width * 0.10f, size.height)
            close()
        }
        drawPath(
            path = paper,
            brush = Brush.linearGradient(
                listOf(MoonIvory.copy(alpha = 0.92f), IvoryWarm, IndigoInk.copy(alpha = 0.16f)),
                start = Offset(size.width * 0.22f, size.height * 0.30f),
                end = Offset(size.width, size.height)
            )
        )
        drawPath(
            path = paper,
            color = IndigoInk.copy(alpha = 0.12f),
            style = androidx.compose.ui.graphics.drawscope.Stroke(width = 1.2.dp.toPx())
        )
    }
}

@Composable
private fun PageTurnCurlOverlay(
    progress: Float,
    direction: Float,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier) {
        val lift = progress.coerceIn(0f, 1f)
        val curlWidth = size.width * (0.18f + 0.20f * lift)
        val x0 = if (direction < 0f) size.width - curlWidth - 10f else 10f
        val outer = if (direction < 0f) x0 + curlWidth else x0
        val inner = if (direction < 0f) x0 + curlWidth * 0.18f else x0 + curlWidth * 0.82f
        val path = androidx.compose.ui.graphics.Path().apply {
            moveTo(inner, size.height * 0.04f)
            quadraticTo(
                if (direction < 0f) x0 - curlWidth * 0.04f else x0 + curlWidth * 1.04f,
                size.height * 0.50f,
                if (direction < 0f) x0 + curlWidth * 0.88f else x0 + curlWidth * 0.12f,
                size.height * 0.94f
            )
            quadraticTo(
                if (direction < 0f) x0 + curlWidth * 0.58f else x0 + curlWidth * 0.42f,
                size.height * 0.72f,
                outer,
                size.height * 0.10f
            )
            close()
        }
        drawPath(
            path = path,
            brush = Brush.linearGradient(
                colors = if (direction < 0f) {
                    listOf(Color.White.copy(alpha = 0.68f), IvoryWarm.copy(alpha = 0.94f), IndigoInk.copy(alpha = 0.26f))
                } else {
                    listOf(IndigoInk.copy(alpha = 0.26f), IvoryWarm.copy(alpha = 0.94f), Color.White.copy(alpha = 0.68f))
                },
                start = Offset(x0, 0f),
                end = Offset(x0 + curlWidth, size.height)
            )
        )
        drawPath(
            path = path,
            color = Color.White.copy(alpha = 0.22f),
            style = androidx.compose.ui.graphics.drawscope.Stroke(width = 1.2.dp.toPx())
        )
        val creaseX = if (direction < 0f) x0 + curlWidth * 0.82f else x0 + curlWidth * 0.18f
        val crease = androidx.compose.ui.graphics.Path().apply {
            moveTo(creaseX, size.height * 0.08f)
            quadraticTo(
                creaseX - direction * curlWidth * 0.16f,
                size.height * 0.50f,
                creaseX + direction * curlWidth * 0.06f,
                size.height * 0.90f
            )
        }
        drawPath(
            path = crease,
            color = IndigoInk.copy(alpha = 0.18f + 0.22f * lift),
            style = androidx.compose.ui.graphics.drawscope.Stroke(width = 3.dp.toPx())
        )
        repeat(5) { index ->
            val y = size.height * (0.16f + index * 0.13f)
            val startX = x0 + curlWidth * if (direction < 0f) 0.30f else 0.70f
            val endX = startX + direction * curlWidth * 0.44f
            val grain = androidx.compose.ui.graphics.Path().apply {
                moveTo(startX, y)
                quadraticTo(startX + direction * curlWidth * 0.18f, y + size.height * 0.035f, endX, y + size.height * 0.09f)
            }
            drawPath(
                path = grain,
                color = IndigoInk.copy(alpha = 0.035f),
                style = androidx.compose.ui.graphics.drawscope.Stroke(width = 0.8.dp.toPx())
            )
        }
        repeat(4) { index ->
            val x = creaseX + direction * index * 5f
            val rib = androidx.compose.ui.graphics.Path().apply {
                moveTo(x, size.height * 0.11f)
                quadraticTo(x - direction * curlWidth * 0.09f, size.height * 0.52f, x + direction * curlWidth * 0.04f, size.height * 0.88f)
            }
            drawPath(
                path = rib,
                color = Color.White.copy(alpha = 0.10f - index * 0.014f),
                style = androidx.compose.ui.graphics.drawscope.Stroke(width = 1.dp.toPx())
            )
        }
    }
}

@Composable
private fun RealBookSpread(
    book: StoryBook,
    pageIndex: Int,
    repository: ContentRepository,
    language: ReaderLanguage,
    textMode: ReaderTextMode,
    bedtimeMode: Boolean,
    reducedMotion: Boolean,
    dragOffset: Float
) {
    val leftIndex = if (pageIndex % 2 == 0) pageIndex else (pageIndex - 1).coerceAtLeast(0)
    val rightIndex = leftIndex + 1

    val turnProgress = (kotlin.math.abs(dragOffset) / 320f).coerceIn(0f, 1f)
    val direction = if (dragOffset < 0f) -1f else 1f

    Box(
        modifier = Modifier
            .fillMaxSize()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, MoonIvory.copy(alpha = 0.28f), RoundedCornerShape(12.dp))
    ) {
        BookObjectBacking(progress = turnProgress, modifier = Modifier.matchParentSize())
        Row(modifier = Modifier.fillMaxSize()) {
            BookSpreadPage(
                page = book.pages[leftIndex],
                imageAsset = repository.resolveSceneAsset(book, book.pages[leftIndex]),
                repository = repository,
                language = language,
                textMode = textMode,
                bedtimeMode = bedtimeMode,
                reducedMotion = reducedMotion,
                side = -1,
                modifier = Modifier.weight(1f).fillMaxSize()
            )
            Box(
                modifier = Modifier
                    .fillMaxHeight()
                    .width(22.dp)
                    .background(
                        Brush.horizontalGradient(
                            listOf(IndigoInk.copy(alpha = 0.30f), IvoryWarm.copy(alpha = 0.86f), IndigoInk.copy(alpha = 0.26f))
                        )
                    )
            )
            if (rightIndex < book.pages.size) {
                BookSpreadPage(
                    page = book.pages[rightIndex],
                    imageAsset = repository.resolveSceneAsset(book, book.pages[rightIndex]),
                    repository = repository,
                    language = language,
                    textMode = textMode,
                    bedtimeMode = bedtimeMode,
                    reducedMotion = reducedMotion,
                    side = 1,
                    modifier = Modifier.weight(1f).fillMaxSize()
                )
            } else {
                Box(modifier = Modifier.weight(1f).fillMaxSize().background(IvoryWarm))
            }
        }
        BookPageStackEdges(
            modifier = Modifier
                .align(Alignment.CenterStart)
                .fillMaxHeight()
                .width(16.dp),
            side = -1
        )
        BookPageStackEdges(
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .fillMaxHeight()
                .width(16.dp),
            side = 1
        )
        if (!reducedMotion && turnProgress > 0.03f) {
            Box(
                modifier = Modifier
                    .align(if (dragOffset < 0f) Alignment.CenterEnd else Alignment.CenterStart)
                    .fillMaxHeight(0.92f)
                    .width((120 + 120 * turnProgress).dp)
                    .background(
                        Brush.horizontalGradient(
                            if (dragOffset < 0f) listOf(Color.Transparent, MoonIvory.copy(alpha = 0.72f), IndigoInk.copy(alpha = 0.22f))
                            else listOf(IndigoInk.copy(alpha = 0.22f), MoonIvory.copy(alpha = 0.72f), Color.Transparent)
                        )
                    )
                    .graphicsLayer {
                        alpha = 0.78f
                        rotationY = if (dragOffset < 0f) -18f * turnProgress else 18f * turnProgress
                        cameraDistance = 18f * density
                    }
            )
            PageTurnCurlOverlay(
                progress = turnProgress,
                direction = direction,
                modifier = Modifier
                    .align(if (direction < 0f) Alignment.CenterEnd else Alignment.CenterStart)
                    .fillMaxHeight(0.94f)
                    .fillMaxWidth(0.46f)
            )
        }
    }
}

@Composable
private fun BookObjectBacking(progress: Float, modifier: Modifier = Modifier) {
    Canvas(modifier = modifier.background(IndigoInk.copy(alpha = 0.92f))) {
        drawRect(
            brush = Brush.linearGradient(
                listOf(IndigoInk.copy(alpha = 0.90f), DeepIndigo.copy(alpha = 0.96f), IndigoInk.copy(alpha = 0.78f)),
                start = Offset.Zero,
                end = Offset(size.width, size.height)
            )
        )
        drawRoundRect(
            color = Color.Black.copy(alpha = 0.20f + progress * 0.10f),
            topLeft = Offset(size.width * 0.02f, size.height * 0.94f),
            size = Size(size.width * 0.96f, size.height * 0.035f),
            cornerRadius = androidx.compose.ui.geometry.CornerRadius(18f, 18f)
        )
        drawLine(
            color = MoonIvory.copy(alpha = 0.12f + progress * 0.05f),
            start = Offset(size.width * 0.04f, size.height * 0.025f),
            end = Offset(size.width * 0.96f, size.height * 0.025f),
            strokeWidth = 2f
        )
        repeat(10) { index ->
            val y = size.height * (0.08f + index * 0.082f)
            drawLine(
                color = MoonIvory.copy(alpha = 0.018f),
                start = Offset(size.width * 0.03f, y),
                end = Offset(size.width * 0.97f, y + if (index % 2 == 0) 1f else -1f),
                strokeWidth = 0.8f
            )
        }
    }
}

@Composable
private fun BookSpreadPage(
    page: StoryPage,
    imageAsset: String?,
    repository: ContentRepository,
    language: ReaderLanguage,
    textMode: ReaderTextMode,
    bedtimeMode: Boolean,
    reducedMotion: Boolean,
    side: Int,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier.background(IvoryWarm)
    ) {
        val sceneImage = remember(imageAsset) {
            imageAsset
                ?.let { repository.readSharedAsset(it) }
                ?.let { bytes -> BitmapFactory.decodeByteArray(bytes, 0, bytes.size) }
                ?.asImageBitmap()
        }
        if (sceneImage != null) {
            Image(
                bitmap = sceneImage,
                contentDescription = page.imagePrompt,
                contentScale = ContentScale.Fit,
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth(0.92f)
                    .fillMaxHeight(0.58f)
                    .padding(bottom = 14.dp)
                    .graphicsLayer { alpha = if (bedtimeMode) 0.18f else 0.25f }
            )
        }
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 22.dp, vertical = 18.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            horizontalAlignment = if (side < 0) Alignment.Start else Alignment.End
        ) {
            PageText(
                page = page,
                language = language,
                textMode = textMode,
                bedtimeMode = false,
                modifier = Modifier
                    .fillMaxWidth(0.78f)
                    .clip(RoundedCornerShape(8.dp))
                    .background(IvoryWarm.copy(alpha = 0.34f))
                    .border(1.dp, IndigoInk.copy(alpha = 0.08f), RoundedCornerShape(8.dp))
                    .padding(horizontal = 16.dp, vertical = 14.dp)
            )
            Spacer(Modifier.weight(1f))
            AnimatedScene(
                page = page,
                imageAsset = imageAsset,
                repository = repository,
                bedtimeMode = bedtimeMode,
                reducedMotion = reducedMotion,
                modifier = Modifier
                    .fillMaxWidth()
                    .fillMaxHeight(0.54f)
                    .clip(RoundedCornerShape(8.dp))
                    .border(1.dp, IndigoInk.copy(alpha = 0.10f), RoundedCornerShape(8.dp))
            )
        }
        Box(
            modifier = Modifier
                .align(if (side < 0) Alignment.CenterEnd else Alignment.CenterStart)
                .fillMaxHeight()
                .width(24.dp)
                .background(
                    Brush.horizontalGradient(
                        if (side < 0) listOf(Color.Transparent, IndigoInk.copy(alpha = 0.16f))
                        else listOf(IndigoInk.copy(alpha = 0.14f), Color.Transparent)
                    )
                )
        )
        FolioMark(
            pageNumber = page.pageNumber,
            side = side,
            modifier = Modifier
                .align(if (side < 0) Alignment.BottomStart else Alignment.BottomEnd)
                .padding(horizontal = 22.dp, vertical = 16.dp)
        )
        PageDepthOverlay(
            side = side,
            intensity = 0.58f,
            modifier = Modifier
                .align(if (side < 0) Alignment.CenterStart else Alignment.CenterEnd)
                .fillMaxHeight()
                .width(18.dp)
        )
    }
}

@Composable
private fun BookPageStackEdges(modifier: Modifier = Modifier, side: Int) {
    Box(modifier = modifier) {
        repeat(5) { index ->
            Box(
                modifier = Modifier
                    .align(if (side < 0) Alignment.CenterStart else Alignment.CenterEnd)
                    .width(3.dp)
                    .fillMaxHeight()
                    .padding(vertical = 6.dp)
                    .graphicsLayer {
                        translationX = if (side < 0) index * 3f else -index * 3f
                        alpha = 0.42f - index * 0.05f
                    }
                    .background(IvoryWarm.copy(alpha = 0.86f))
            )
        }
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    Brush.horizontalGradient(
                        if (side < 0) listOf(IndigoInk.copy(alpha = 0.22f), Color.Transparent)
                        else listOf(Color.Transparent, IndigoInk.copy(alpha = 0.22f))
                    )
                )
        )
    }
}

@Composable
private fun AnimatedScene(
    page: StoryPage,
    imageAsset: String?,
    repository: ContentRepository,
    bedtimeMode: Boolean,
    reducedMotion: Boolean,
    modifier: Modifier = Modifier
) {
    val shift = if (reducedMotion) {
        0f
    } else {
        val transition = rememberInfiniteTransition(label = "scene")
        val animatedShift by transition.animateFloat(
            initialValue = -18f,
            targetValue = 18f,
            animationSpec = infiniteRepeatable(
                animation = tween(durationMillis = (page.animation.loopDuration * 1000).toInt().coerceAtLeast(2400)),
                repeatMode = RepeatMode.Reverse
            ),
            label = "sceneShift"
        )
        animatedShift
    }
    val accent = when {
        page.animation.type.contains("moon", ignoreCase = true) -> JadeLeaf
        page.animation.type.contains("sun", ignoreCase = true) -> Persimmon
        page.animation.type.contains("snow", ignoreCase = true) -> LotusPink
        else -> LanternGold
    }
    val motionShift = shift

    Box(
        modifier = modifier
            .fillMaxWidth()
            .background(if (bedtimeMode) IndigoInk else IvoryWarm),
        contentAlignment = Alignment.Center
    ) {
        val sceneImage = remember(imageAsset) {
            imageAsset
                ?.let { repository.readSharedAsset(it) }
                ?.let { bytes -> BitmapFactory.decodeByteArray(bytes, 0, bytes.size) }
                ?.asImageBitmap()
        }

        if (sceneImage != null) {
            Image(
                bitmap = sceneImage,
                contentDescription = page.imagePrompt,
                contentScale = ContentScale.Fit,
                modifier = Modifier
                    .fillMaxSize()
                    .padding(10.dp)
            )
        } else {
            Canvas(modifier = Modifier.fillMaxSize()) {
                drawRect(
                    brush = Brush.linearGradient(
                        colors = if (bedtimeMode) listOf(IndigoInk, JadeLeaf) else listOf(IvoryWarm, accent.copy(alpha = 0.55f)),
                        start = Offset.Zero,
                        end = Offset(size.width, size.height)
                    )
                )
                drawCircle(
                    color = MoonIvory.copy(alpha = if (bedtimeMode) 0.18f else 0.34f),
                    radius = size.minDimension * 0.18f,
                    center = Offset(size.width * 0.68f + motionShift, size.height * 0.28f)
                )
                rotate(degrees = motionShift / 8f, pivot = Offset(size.width * 0.5f, size.height * 0.68f)) {
                    drawOval(
                        color = Persimmon.copy(alpha = 0.18f),
                        topLeft = Offset(size.width * 0.12f, size.height * 0.58f),
                        size = Size(size.width * 0.76f, size.height * 0.24f)
                    )
                }
            }
        }

        LayeredSceneTreatment(
            page = page,
            repository = repository,
            bedtimeMode = bedtimeMode,
            reducedMotion = reducedMotion,
            modifier = Modifier.matchParentSize()
        )

        Canvas(modifier = Modifier.fillMaxSize()) {
            val lower = page.animation.type.lowercase()
            val motion = if (reducedMotion) 0f else motionShift
            drawRect(
                brush = Brush.linearGradient(
                    colors = if (bedtimeMode) listOf(IndigoInk.copy(alpha = 0.28f), IndigoInk.copy(alpha = 0.04f)) else listOf(Color.Transparent, IndigoInk.copy(alpha = 0.08f)),
                    start = Offset.Zero,
                    end = Offset(size.width, size.height)
                )
            )
            if (lower.contains("moon") || lower.contains("night") || lower.contains("sky") || lower.contains("bedtime")) {
                drawRect(color = MoonIvory.copy(alpha = if (bedtimeMode) 0.025f else 0.045f))
            }
            if (lower.contains("lantern") || lower.contains("warm")) {
                drawRect(color = LanternGold.copy(alpha = if (bedtimeMode) 0.025f else 0.04f))
            }
            if (lower.contains("cloud") || lower.contains("drift") || lower.contains("sky")) {
                repeat(3) { index ->
                    val x = ((size.width * (0.12f + index * 0.28f)) + motionShift * 1.8f) % (size.width + 120f) - 60f
                    val y = size.height * (0.12f + index * 0.08f)
                    drawRoundRect(
                        color = MoonIvory.copy(alpha = if (bedtimeMode) 0.08f else 0.14f),
                        topLeft = Offset(x, y),
                        size = Size(126f, 34f),
                        cornerRadius = androidx.compose.ui.geometry.CornerRadius(18f, 18f)
                    )
                }
            }
            if (lower.contains("water") || lower.contains("ripple") || lower.contains("pond")) {
                repeat(3) { index ->
                    drawOval(
                        color = JadeLeaf.copy(alpha = if (bedtimeMode) 0.18f else 0.32f),
                        topLeft = Offset(size.width * 0.50f - 68f - index * 18f, size.height * 0.66f - 16f - index * 3f),
                        size = Size(136f + index * 36f, 34f + index * 9f),
                        style = androidx.compose.ui.graphics.drawscope.Stroke(width = 2.dp.toPx())
                    )
                }
            }
            if (lower.contains("tail") || lower.contains("blink") || lower.contains("comic") || lower.contains("tiger")) {
                drawRect(color = Persimmon.copy(alpha = if (bedtimeMode) 0.018f else 0.028f))
            }
            if (lower.contains("spark") || lower.contains("magic") || lower.contains("glow") || lower.contains("dokkaebi") || lower.contains("spirit") || lower.contains("star") || lower.contains("night")) {
                repeat(12) { index ->
                    val wave = kotlin.math.sin((motionShift / 18f) + index)
                    val x = size.width * (0.12f + index * 0.07f)
                    val y = size.height * (0.20f + (index % 4) * 0.09f) + wave * 8f
                    drawCircle(
                        color = LanternGold.copy(alpha = if (bedtimeMode) 0.10f else 0.20f),
                        radius = 2.5f + (index % 3),
                        center = Offset(x, y)
                    )
                }
            }
        }
        if (sceneImage == null) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp),
                modifier = Modifier.padding(28.dp)
            ) {
                Text(
                    page.animation.type.replace("_", " ").replaceFirstChar { it.titlecase() },
                    style = MaterialTheme.typography.labelLarge,
                    color = IndigoInk.copy(alpha = 0.64f),
                    modifier = Modifier
                        .clip(CircleShape)
                        .background(Color.White.copy(alpha = 0.55f))
                        .padding(horizontal = 12.dp, vertical = 7.dp)
                )
                Text(
                    page.imagePrompt,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.SemiBold,
                    textAlign = TextAlign.Center,
                    color = IndigoInk,
                    maxLines = 5,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}

@Composable
private fun LayeredSceneTreatment(
    page: StoryPage,
    repository: ContentRepository,
    bedtimeMode: Boolean,
    reducedMotion: Boolean,
    modifier: Modifier = Modifier
) {
    val phase = if (reducedMotion) {
        0f
    } else {
        val transition = rememberInfiniteTransition(label = "layered-scene")
        val animatedPhase by transition.animateFloat(
            initialValue = 0f,
            targetValue = 6.28318f,
            animationSpec = infiniteRepeatable(
                animation = tween(durationMillis = (page.animation.loopDuration * 1000).toInt().coerceAtLeast(2400)),
                repeatMode = RepeatMode.Reverse
            ),
            label = "layeredScenePhase"
        )
        animatedPhase
    }
    val layerNames = page.animation.layers.map { it.name.lowercase() }.toSet()
    val hasCharacterLayer = "character" in layerNames
    val hasForegroundLayer = "foreground" in layerNames
    val hasEffectLayer = "effect" in layerNames || "particle_glow" in layerNames
    val animationKey = page.animation.type.lowercase()
    val drift = if (reducedMotion) 0f else kotlin.math.sin(phase) * 7f

    Box(modifier = modifier) {
        page.animation.layers.forEachIndexed { index, layer ->
            val outputFile = layer.outputFile
            val layerBitmap = remember(outputFile) {
                outputFile
                    ?.let { repository.readSharedAsset(it) }
                    ?.let { bytes -> BitmapFactory.decodeByteArray(bytes, 0, bytes.size) }
                    ?.asImageBitmap()
            }
            if (layerBitmap != null) {
                Image(
                    bitmap = layerBitmap,
                    contentDescription = null,
                    contentScale = ContentScale.Fit,
                    modifier = Modifier
                        .matchParentSize()
                        .graphicsLayer {
                            alpha = layerAssetAlpha(layer.name, bedtimeMode)
                            val multiplier = layerMotionMultiplier(layer.name)
                            translationX = drift * multiplier * 0.45f * if (index % 2 == 0) 1f else -1f
                            translationY = drift * multiplier
                            scaleX = 1f + (index * 0.0015f)
                            scaleY = 1f + (index * 0.0015f)
                        }
                )
            }
        }

        Canvas(modifier = Modifier.matchParentSize()) {
            if (hasCharacterLayer) {
                drawOval(
                    color = Color.White.copy(alpha = if (bedtimeMode) 0.035f else 0.070f),
                    topLeft = Offset(size.width * 0.18f, size.height * 0.14f + drift),
                    size = Size(size.width * 0.64f, size.height * 0.66f)
                )
                drawRoundRect(
                    color = LanternGold.copy(alpha = if (bedtimeMode) 0.035f else 0.070f),
                    topLeft = Offset(size.width * 0.07f, size.height * 0.07f),
                    size = Size(size.width * 0.86f, size.height * 0.82f),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(28f, 28f),
                    style = androidx.compose.ui.graphics.drawscope.Stroke(width = 1.4.dp.toPx())
                )
            }

            if (hasForegroundLayer) {
                drawRect(
                    brush = Brush.verticalGradient(
                        listOf(
                            IndigoInk.copy(alpha = if (bedtimeMode) 0.20f else 0.10f),
                            Color.Transparent,
                            IndigoInk.copy(alpha = if (bedtimeMode) 0.28f else 0.15f)
                        )
                    )
                )
            }

            if (hasEffectLayer) {
                val warm = animationKey.contains("lantern") || animationKey.contains("warm") || animationKey.contains("glow")
                val cool = animationKey.contains("moon") || animationKey.contains("night") || animationKey.contains("snow")
                val color = when {
                    warm -> LanternGold
                    cool -> MoonIvory
                    else -> JadeLeaf
                }
                repeat(14) { index ->
                    val seed = index + 1f
                    val x = size.width * (((seed * 0.173f) % 0.92f) + 0.04f)
                    val yBase = size.height * (((seed * 0.119f) % 0.72f) + 0.12f)
                    val y = yBase + drift * if (index % 2 == 0) 1f else -0.55f
                    drawCircle(
                        color = color.copy(alpha = if (bedtimeMode) 0.10f else 0.18f),
                        radius = 1.7f + (index % 4) * 0.9f,
                        center = Offset(x, y)
                    )
                }
            }
        }
    }
}

private fun layerAssetAlpha(name: String, bedtimeMode: Boolean): Float =
    when (name.lowercase()) {
        "background" -> if (bedtimeMode) 0.08f else 0.12f
        "midground" -> if (bedtimeMode) 0.12f else 0.18f
        "character" -> if (bedtimeMode) 0.14f else 0.22f
        "foreground" -> if (bedtimeMode) 0.13f else 0.20f
        "effect" -> if (bedtimeMode) 0.16f else 0.24f
        "particle_glow" -> if (bedtimeMode) 0.18f else 0.28f
        else -> if (bedtimeMode) 0.10f else 0.16f
    }

private fun layerMotionMultiplier(name: String): Float =
    when (name.lowercase()) {
        "background" -> 0.18f
        "midground" -> 0.34f
        "character" -> 0.48f
        "foreground" -> 0.62f
        "effect" -> 0.76f
        "particle_glow" -> 0.92f
        else -> 0.32f
    }

@Composable
private fun PaywallDialog(onDismiss: () -> Unit, onContinue: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Premium Korean Library") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Monthly $4.99")
                Text("Annual $39.99")
                Text("Lifetime Korean Library $79.99-$99.99")
                Text("Purchases require a parent check in this prototype.")
            }
        },
        confirmButton = {
            Button(onClick = onContinue) {
                Text("Continue")
            }
        },
        dismissButton = {
            OutlinedButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}

@Composable
private fun MoonJarCover(
    title: LocalizedTitle,
    assetPath: String? = null,
    repository: ContentRepository? = null,
    modifier: Modifier = Modifier
) {
    val coverImage = remember(assetPath, repository) {
        if (assetPath != null && repository != null) {
            repository.readSharedAsset(assetPath)
                ?.let { bytes -> BitmapFactory.decodeByteArray(bytes, 0, bytes.size) }
                ?.asImageBitmap()
        } else {
            null
        }
    }

    Box(
        modifier = modifier
            .aspectRatio(1.5f)
            .clip(RoundedCornerShape(8.dp))
            .background(
                Brush.linearGradient(
                    colors = listOf(IndigoInk, JadeLeaf, Persimmon)
                )
            )
            .padding(18.dp),
        contentAlignment = Alignment.Center
    ) {
        if (coverImage != null) {
            Image(
                bitmap = coverImage,
                contentDescription = title.en,
                contentScale = ContentScale.Fit,
                modifier = Modifier
                    .fillMaxSize()
                    .clip(RoundedCornerShape(6.dp))
                    .background(IvoryWarm)
                    .padding(4.dp)
            )
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Brush.verticalGradient(listOf(Color.Transparent, IndigoInk.copy(alpha = 0.08f))))
            )
        } else {
            Canvas(modifier = Modifier.size(118.dp)) {
                drawCircle(color = MoonIvory.copy(alpha = 0.86f), style = androidx.compose.ui.graphics.drawscope.Stroke(width = 12.dp.toPx()))
            }
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Bottom,
                modifier = Modifier.fillMaxSize()
            ) {
                Spacer(Modifier.weight(1f))
                Text(title.ko, style = MaterialTheme.typography.titleLarge, color = MoonIvory, fontWeight = FontWeight.Bold, textAlign = TextAlign.Center)
                Text(title.en, style = MaterialTheme.typography.bodySmall, color = MoonIvory.copy(alpha = 0.84f), textAlign = TextAlign.Center, maxLines = 2)
            }
        }
    }
}

@Composable
private fun ParentGateDialog(onDismiss: () -> Unit, onPass: () -> Unit) {
    var answer by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Parent Check") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                Text("7 + 5 =", style = MaterialTheme.typography.headlineLarge)
                TextField(value = answer, onValueChange = { answer = it }, singleLine = true)
            }
        },
        confirmButton = {
            Button(onClick = { if (answer.trim() == "12") onPass() }) {
                Text("Continue")
            }
        },
        dismissButton = {
            OutlinedButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
