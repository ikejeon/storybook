import SwiftUI
#if os(iOS)
import UIKit
#elseif os(macOS)
import AppKit
#endif

struct RootView: View {
    @EnvironmentObject private var library: StoryLibrary
    @EnvironmentObject private var entitlements: EntitlementStore
    @AppStorage("moonjar.readerLanguage.v2") private var languageRawValue = ReaderLanguage.english.rawValue
    @AppStorage("moonjar.bedtime") private var bedtimeMode = false
    @State private var activeRoute = DemoLaunchRoute.current

    private var language: Binding<ReaderLanguage> {
        Binding(
            get: { ReaderLanguage(rawValue: languageRawValue) ?? .english },
            set: { languageRawValue = $0.rawValue }
        )
    }

    var body: some View {
        NavigationStack {
            routedRoot
                .navigationTitle(activeRoute.title)
                .toolbar {
                    if activeRoute.showsToolbar {
                        ToolbarItemGroup(placement: .primaryAction) {
                            Picker("Language", selection: language) {
                                ForEach(ReaderLanguage.allCases) { mode in
                                    Text(mode.label).tag(mode)
                                }
                            }
                            .pickerStyle(.segmented)
                            .frame(width: 260)

                            Toggle(isOn: $bedtimeMode) {
                                Label("Bedtime", systemImage: "moon.zzz.fill")
                            }
                            .toggleStyle(.button)
                        }
                    }
                }
        }
        .tint(.persimmon)
        .background(Color.moonIvory)
        .overlay {
            if library.isLoading {
                ProgressView()
                    .controlSize(.large)
            }
        }
        .alert("Content Unavailable", isPresented: Binding(get: { library.errorMessage != nil }, set: { _ in library.errorMessage = nil })) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(library.errorMessage ?? "")
        }
    }

    @ViewBuilder
    private var routedRoot: some View {
        switch activeRoute {
        case .library:
            LibraryView(language: language, bedtimeMode: $bedtimeMode)
        case .detail:
            if let book = library.books.first(where: { $0.id == "book.sun_moon" }) ?? library.books.first {
                BookDetailView(book: book, language: language, bedtimeMode: $bedtimeMode)
            } else {
                ProgressView()
            }
        case .reader:
            if let book = library.books.first(where: { $0.id == "book.sun_moon" }) ?? library.books.first {
                ReaderView(
                    book: book,
                    language: language,
                    bedtimeMode: $bedtimeMode,
                    onExit: { activeRoute = .library }
                )
            } else {
                ProgressView()
            }
        case .paywall:
            PaywallView()
        }
    }
}

enum DemoLaunchRoute {
    case library
    case detail
    case reader
    case paywall

    static var current: DemoLaunchRoute {
        let arguments = ProcessInfo.processInfo.arguments
        if arguments.contains("--demo-detail") { return .detail }
        if arguments.contains("--demo-reader") { return .reader }
        if arguments.contains("--demo-paywall") { return .paywall }
        return .library
    }

    var title: String {
        switch self {
        case .library: return "Moon Jar Stories"
        case .detail: return "Book Detail"
        case .reader: return "Reader"
        case .paywall: return "Premium Library"
        }
    }

    var showsToolbar: Bool {
        self != .paywall
    }

    static var requestedPageIndex: Int? {
        ProcessInfo.processInfo.arguments.compactMap { argument in
            guard argument.hasPrefix("--demo-page="),
                  let pageNumber = Int(argument.replacingOccurrences(of: "--demo-page=", with: ""))
            else { return nil }
            return max(pageNumber - 1, 0)
        }.first
    }

    static var requestedRealBookMode: Bool {
        ProcessInfo.processInfo.arguments.contains("--demo-real-book")
    }

    static var requestedSelfTest: String? {
        ProcessInfo.processInfo.arguments.compactMap { argument in
            guard argument.hasPrefix("--demo-self-test=") else { return nil }
            return argument.replacingOccurrences(of: "--demo-self-test=", with: "")
        }.first
    }

    static var shouldExitAfterSelfTest: Bool {
        ProcessInfo.processInfo.arguments.contains("--demo-self-test-exit")
    }
}

struct LibraryView: View {
    @EnvironmentObject private var library: StoryLibrary
    @EnvironmentObject private var entitlements: EntitlementStore
    @Binding var language: ReaderLanguage
    @Binding var bedtimeMode: Bool

    var body: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 260), spacing: 18)], spacing: 18) {
                ForEach(library.catalog?.books ?? []) { entry in
                    let book = library.book(for: entry)
                    let isUnlocked = book.map { entitlements.canRead($0) } ?? entitlements.canRead(entry)
                    NavigationLink {
                        if let book {
                            BookDetailView(book: book, language: $language, bedtimeMode: $bedtimeMode)
                        } else {
                            ComingSoonView(entry: entry)
                        }
                    } label: {
                        CatalogTile(
                            entry: entry,
                            coverAsset: library.resolvedCoverAsset(for: book),
                            contentRoot: library.contentRoot,
                            isUnlocked: isUnlocked
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(24)
        }
        .accessibilityIdentifier("library-screen")
        .background(Color.moonIvory)
    }
}

struct CatalogTile: View {
    let entry: CatalogBook
    let coverAsset: String?
    let contentRoot: URL?
    let isUnlocked: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            MoonJarCover(title: entry.title, slug: entry.slug, assetPath: coverAsset, contentRoot: contentRoot)
                .frame(maxWidth: .infinity)
                .aspectRatio(1.5, contentMode: .fit)

            VStack(alignment: .leading, spacing: 6) {
                Text(entry.title.ko)
                    .font(.title3.weight(.semibold))
                    .foregroundStyle(Color.indigoInk)
                    .lineLimit(1)
                    .minimumScaleFactor(0.82)
                Text(entry.title.en)
                    .font(.subheadline)
                    .foregroundStyle(Color.indigoInk.opacity(0.72))
                    .lineLimit(2)
                HStack(spacing: 8) {
                    Label(entry.access == .free ? "Free" : "Premium", systemImage: entry.access == .free ? "book.fill" : "lock.fill")
                    Text("\(entry.pageTarget) pages")
                }
                .font(.caption.weight(.medium))
                .foregroundStyle(isUnlocked ? Color.jadeLeaf : Color.persimmon)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(Color.white.opacity(0.82), in: RoundedRectangle(cornerRadius: ReaderMetrics.cornerMedium, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: ReaderMetrics.cornerMedium, style: .continuous)
                .stroke(Color.indigoInk.opacity(0.10), lineWidth: 1)
        )
        .shadow(color: Color.indigoInk.opacity(0.10), radius: 14, x: 0, y: 7)
    }
}

struct BookDetailView: View {
    @EnvironmentObject private var entitlements: EntitlementStore
    @EnvironmentObject private var library: StoryLibrary
    let book: StoryBook
    @Binding var language: ReaderLanguage
    @Binding var bedtimeMode: Bool
    @State private var showingPaywall = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                MoonJarCover(title: book.title, slug: book.slug, assetPath: library.resolvedCoverAsset(for: book), contentRoot: library.contentRoot)
                    .frame(maxWidth: .infinity)
                    .aspectRatio(1.5, contentMode: .fit)

                VStack(alignment: .leading, spacing: 10) {
                    Text(book.title.ko)
                        .font(.largeTitle.weight(.bold))
                        .foregroundStyle(Color.indigoInk)
                    Text(book.title.en)
                        .font(.title3)
                        .foregroundStyle(Color.indigoInk.opacity(0.72))
                    Text(book.summary)
                        .font(.body)
                        .foregroundStyle(Color.indigoInk.opacity(0.82))
                        .fixedSize(horizontal: false, vertical: true)
                }

                HStack(spacing: 12) {
                    ForEach(book.themes, id: \.self) { theme in
                        Text(theme.capitalized)
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(Color.indigoInk)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(Color.jadeLeaf.opacity(0.15), in: Capsule())
                    }
                }

                if entitlements.canRead(book) {
                    NavigationLink {
                        ReaderView(book: book, language: $language, bedtimeMode: $bedtimeMode)
                    } label: {
                        Label("Read", systemImage: "play.fill")
                            .font(.headline)
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                } else {
                    Button {
                        showingPaywall = true
                    } label: {
                        Label("Unlock", systemImage: "lock.open.fill")
                            .font(.headline)
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                }
            }
            .padding(24)
            .frame(maxWidth: 820, alignment: .leading)
        }
        .background(Color.moonIvory)
        .sheet(isPresented: $showingPaywall) {
            PaywallView()
                .environmentObject(entitlements)
        }
    }
}

struct ReaderView: View {
    @EnvironmentObject private var library: StoryLibrary
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.dismiss) private var dismiss
    let book: StoryBook
    @Binding var language: ReaderLanguage
    @Binding var bedtimeMode: Bool
    var onExit: (() -> Void)? = nil

    @StateObject private var narrator = NarrationPlayer()
    @AppStorage("moonjar.readerTextMode.v1") private var textModeRawValue = ReaderTextMode.story.rawValue
    @State private var pageIndex = 0
    @State private var autoPlay = false
    @State private var realBookMode = false
    @State private var appliedDemoPageIndex = false
    @State private var didRunDemoSelfTest = false
    @State private var animatedTurnOffset: CGFloat = 0
    @State private var pageTurnTask: Task<Void, Never>?
    @State private var layoutUsesSpreadNavigation = false
    @GestureState private var dragOffset: CGFloat = 0

    private var page: StoryPage { book.pages[pageIndex] }
    private var textMode: ReaderTextMode { ReaderTextMode(rawValue: textModeRawValue) ?? .story }
    private var effectiveReduceMotion: Bool { reduceMotion || bedtimeMode }
    private var activeTurnOffset: CGFloat {
        let raw = abs(dragOffset) > 0.5 ? dragOffset : animatedTurnOffset
        return min(max(raw, -320), 320)
    }
    private var usesSpreadNavigation: Bool { realBookMode || layoutUsesSpreadNavigation }
    private var spreadStartIndex: Int {
        pageIndex.isMultiple(of: 2) ? pageIndex : max(pageIndex - 1, 0)
    }
    private var canGoPrevious: Bool {
        usesSpreadNavigation ? spreadStartIndex > 0 : pageIndex > 0
    }
    private var canGoNext: Bool {
        usesSpreadNavigation ? spreadStartIndex + 2 < book.pages.count : pageIndex < book.pages.count - 1
    }

    var body: some View {
        GeometryReader { proxy in
            let isWide = proxy.size.width > proxy.size.height * 1.12
            Group {
                if isWide {
                    landscapeReader(size: proxy.size)
                } else {
                    portraitReader(size: proxy.size)
                }
            }
            .frame(width: proxy.size.width, height: proxy.size.height, alignment: .top)
            .onAppear {
                layoutUsesSpreadNavigation = isWide
            }
            .onChange(of: isWide) { _, newValue in
                layoutUsesSpreadNavigation = newValue
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(ReaderPalette.night.ignoresSafeArea())
        .gesture(
            DragGesture(minimumDistance: 28)
                .updating($dragOffset) { value, state, _ in
                    state = value.translation.width
                }
                .onEnded { value in
                    let projected = value.predictedEndTranslation.width
                    if value.translation.width < -70 || projected < -150 {
                        nextPage()
                    } else if value.translation.width > 70 || projected > 150 {
                        previousPage()
                    }
                }
        )
        .navigationTitle(language == .korean ? book.title.ko : book.title.en)
        .moonJarInlineNavigationTitle()
        .moonJarHideNavigationBar()
        .onChange(of: pageIndex) { _, _ in
            if autoPlay {
                narrator.replay(
                    page,
                    language: language,
                    bedtimeMode: bedtimeMode,
                    contentRoot: library.contentRoot,
                    audioAssetPath: library.resolvedNarrationAsset(book: book, page: page, language: language)
                )
            }
        }
        .onAppear {
            if DemoLaunchRoute.requestedRealBookMode {
                realBookMode = true
            }
            if !appliedDemoPageIndex,
               let requestedPageIndex = DemoLaunchRoute.requestedPageIndex,
               book.pages.indices.contains(requestedPageIndex) {
                pageIndex = requestedPageIndex
                appliedDemoPageIndex = true
            }
            runDemoSelfTestIfRequested()
            narrator.onFinished = {
                guard autoPlay, pageIndex < book.pages.count - 1 else { return }
                let delay = bedtimeMode ? 1_300_000_000 : 550_000_000
                Task { @MainActor in
                    try? await Task.sleep(nanoseconds: UInt64(delay))
                    guard autoPlay, pageIndex < book.pages.count - 1 else { return }
                    nextPage()
                }
            }
        }
        .onDisappear {
            pageTurnTask?.cancel()
            narrator.stop()
            narrator.onFinished = nil
        }
    }

    private func portraitReader(size: CGSize) -> some View {
        VStack(spacing: 14) {
            ReaderTopBar(
                book: book,
                language: $language,
                bedtimeMode: $bedtimeMode,
                compact: true,
                onBack: exitReader,
                onBookMode: { realBookMode.toggle() }
            )
            .padding(.horizontal, 26)
            .padding(.top, 22)

            PageProgressBar(pageIndex: pageIndex, pageCount: book.pages.count)
                .padding(.horizontal, max(34, size.width * 0.16))

            Group {
                if realBookMode {
                    PortraitRealBookModeCard(
                        book: book,
                        pageIndex: pageIndex,
                        language: language,
                        textMode: textMode,
                        bedtimeMode: bedtimeMode,
                        reduceMotion: effectiveReduceMotion,
                        dragOffset: activeTurnOffset,
                        contentRoot: library.contentRoot,
                        imageAsset: { page in library.resolvedSceneImageAsset(book: book, page: page) }
                    )
                    .transition(.opacity.combined(with: .scale(scale: 0.985)))
                } else {
                    PortraitStoryCard(
                        book: book,
                        page: page,
                        pageIndex: pageIndex,
                        pageCount: book.pages.count,
                        language: language,
                        textMode: textMode,
                        bedtimeMode: bedtimeMode,
                        reduceMotion: effectiveReduceMotion,
                        dragOffset: activeTurnOffset,
                        imageAssetPath: library.resolvedSceneImageAsset(book: book, page: page),
                        contentRoot: library.contentRoot,
                        onPrevious: previousPage,
                        onNext: nextPage
                    )
                    .transition(.opacity.combined(with: .scale(scale: 1.012)))
                }
            }
            .frame(maxWidth: min(size.width - 44, 980))
            .frame(height: portraitCardHeight(for: size))
            .padding(.horizontal, 22)
            .animation(effectiveReduceMotion ? nil : .spring(response: 0.38, dampingFraction: 0.86), value: realBookMode)

            RealBookModeBanner(isOn: $realBookMode)
                .frame(maxWidth: min(size.width - 92, 780))

            ReaderControlDeck(
                isPlaying: narrator.isPlaying,
                autoPlay: $autoPlay,
                textModeRawValue: $textModeRawValue,
                realBookMode: $realBookMode,
                bedtimeMode: $bedtimeMode,
                language: $language,
                canPrevious: canGoPrevious,
                canNext: canGoNext,
                onPrevious: previousPage,
                onReplay: replayNarration,
                onPlayPause: playOrPauseNarration,
                onNext: nextPage
            )

            ThumbnailStrip(
                book: book,
                pageIndex: $pageIndex,
                reduceMotion: effectiveReduceMotion,
                contentRoot: library.contentRoot,
                imageAsset: { page in library.resolvedSceneImageAsset(book: book, page: page) }
            )
            .frame(maxHeight: 94)
            .padding(.horizontal, 20)
            .padding(.bottom, 12)
        }
        .background(ReaderBackground())
    }

    private func landscapeReader(size: CGSize) -> some View {
        VStack(spacing: 16) {
            ReaderTopBar(
                book: book,
                language: $language,
                bedtimeMode: $bedtimeMode,
                compact: false,
                onBack: exitReader,
                onBookMode: { realBookMode.toggle() }
            )
            .padding(.horizontal, 40)
            .padding(.top, 24)

            OpenBookStage(
                book: book,
                pageIndex: pageIndex,
                language: language,
                textMode: textMode,
                bedtimeMode: bedtimeMode,
                reduceMotion: effectiveReduceMotion,
                dragOffset: activeTurnOffset,
                contentRoot: library.contentRoot,
                imageAsset: { page in library.resolvedSceneImageAsset(book: book, page: page) }
            )
            .frame(maxWidth: min(size.width - 116, 1320))
            .frame(height: max(430, size.height - 230))
            .padding(.horizontal, 46)

            HStack(spacing: 22) {
                ReaderControlDeck(
                    isPlaying: narrator.isPlaying,
                    autoPlay: $autoPlay,
                    textModeRawValue: $textModeRawValue,
                    realBookMode: $realBookMode,
                    bedtimeMode: $bedtimeMode,
                    language: $language,
                    canPrevious: canGoPrevious,
                    canNext: canGoNext,
                    onPrevious: previousPage,
                    onReplay: replayNarration,
                    onPlayPause: playOrPauseNarration,
                    onNext: nextPage
                )

                PageDotProgress(pageIndex: pageIndex, pageCount: book.pages.count)
                    .frame(maxWidth: 560)
            }
            .padding(.horizontal, 52)
            .padding(.bottom, 24)
        }
        .background(ReaderBackground())
    }

    private func readerSceneHeight(for size: CGSize) -> CGFloat {
        let reservedForTextAndControls: CGFloat = language == .bilingual ? 330 : 270
        let ideal = size.height - reservedForTextAndControls
        let aspectMatchedArtHeight = ((size.width - 24) / 1.5) + 86
        let maximum = size.height * (size.width > size.height ? 0.68 : 0.76)
        return max(420, min(ideal, aspectMatchedArtHeight, maximum))
    }

    private func portraitCardHeight(for size: CGSize) -> CGFloat {
        let reserve: CGFloat = size.width < 620 ? 390 : 510
        return max(560, min(size.height - reserve, size.width * 1.04))
    }

    private func replayNarration() {
        narrator.replay(
            page,
            language: language,
            bedtimeMode: bedtimeMode,
            contentRoot: library.contentRoot,
            audioAssetPath: library.resolvedNarrationAsset(book: book, page: page, language: language)
        )
    }

    private func playOrPauseNarration() {
        narrator.playOrPause(
            page,
            language: language,
            bedtimeMode: bedtimeMode,
            contentRoot: library.contentRoot,
            audioAssetPath: library.resolvedNarrationAsset(book: book, page: page, language: language)
        )
    }

    private func exitReader() {
        if let onExit {
            onExit()
        } else {
            dismiss()
        }
    }

    private func nextPage() {
        guard canGoNext else { return }
        let targetIndex = usesSpreadNavigation ? min(spreadStartIndex + 2, book.pages.count - 1) : pageIndex + 1
        turnToPage(targetIndex, direction: -1)
    }

    private func previousPage() {
        guard canGoPrevious else { return }
        let targetIndex = usesSpreadNavigation ? max(spreadStartIndex - 2, 0) : pageIndex - 1
        turnToPage(targetIndex, direction: 1)
    }

    private func turnToPage(_ targetIndex: Int, direction: CGFloat) {
        guard book.pages.indices.contains(targetIndex), targetIndex != pageIndex else { return }
        pageTurnTask?.cancel()
        narrator.stop()

        if effectiveReduceMotion {
            pageIndex = targetIndex
            narrator.playPageTurn(contentRoot: library.contentRoot, soundAssetPath: library.resolvedPageFlipSound(), bedtimeMode: bedtimeMode)
            return
        }

        animatedTurnOffset = 0
        withAnimation(.easeInOut(duration: 0.18)) {
            animatedTurnOffset = direction * 280
        }

        pageTurnTask = Task { @MainActor in
            try? await Task.sleep(nanoseconds: 180_000_000)
            guard !Task.isCancelled else { return }
            withAnimation(.interactiveSpring(response: 0.42, dampingFraction: 0.86)) {
                pageIndex = targetIndex
            }
            narrator.playPageTurn(contentRoot: library.contentRoot, soundAssetPath: library.resolvedPageFlipSound(), bedtimeMode: bedtimeMode)
            try? await Task.sleep(nanoseconds: 210_000_000)
            guard !Task.isCancelled else { return }
            withAnimation(.easeOut(duration: 0.22)) {
                animatedTurnOffset = 0
            }
        }
    }

    private func runDemoSelfTestIfRequested() {
        guard !didRunDemoSelfTest,
              let requestedSelfTest = DemoLaunchRoute.requestedSelfTest
        else { return }

        didRunDemoSelfTest = true
        Task { @MainActor in
            switch requestedSelfTest {
            case "real-book-next-back":
                try? await Task.sleep(nanoseconds: 700_000_000)
                let initialSpread = spreadLabel(for: pageIndex)
                nextPage()
                try? await Task.sleep(nanoseconds: 900_000_000)
                let afterNextSpread = spreadLabel(for: pageIndex)
                let nextAdvancedOneSpread = initialSpread != afterNextSpread && spreadStartIndex > 0
                previousPage()
                try? await Task.sleep(nanoseconds: 900_000_000)
                let afterBackSpread = spreadLabel(for: pageIndex)
                let backReturnedToInitialSpread = afterBackSpread == initialSpread
                writeDemoSelfTestResult(
                    initialSpread: initialSpread,
                    afterNextSpread: afterNextSpread,
                    afterBackSpread: afterBackSpread,
                    nextAdvancedOneSpread: nextAdvancedOneSpread,
                    backReturnedToInitialSpread: backReturnedToInitialSpread
                )
            case "reader-playback":
                try? await Task.sleep(nanoseconds: 700_000_000)
                playOrPauseNarration()
                try? await Task.sleep(nanoseconds: 1_000_000_000)
                writePlaybackSelfTestResult(isPlaying: narrator.isPlaying, pageNumber: pageIndex + 1)
            default:
                break
            }

            if DemoLaunchRoute.shouldExitAfterSelfTest {
                exitReader()
            }
        }
    }

    private func spreadLabel(for index: Int) -> String {
        let startIndex = index.isMultiple(of: 2) ? index : max(index - 1, 0)
        let leftPage = startIndex + 1
        let rightPage = min(leftPage + 1, book.pages.count)
        return leftPage == rightPage ? "\(leftPage) / \(book.pages.count)" : "\(leftPage)-\(rightPage) / \(book.pages.count)"
    }

    private func writeDemoSelfTestResult(
        initialSpread: String,
        afterNextSpread: String,
        afterBackSpread: String,
        nextAdvancedOneSpread: Bool,
        backReturnedToInitialSpread: Bool
    ) {
        let result = [
            "test": "real-book-next-back",
            "initialSpread": initialSpread,
            "afterNextSpread": afterNextSpread,
            "afterBackSpread": afterBackSpread,
            "nextAdvancedOneSpread": nextAdvancedOneSpread ? "true" : "false",
            "backReturnedToInitialSpread": backReturnedToInitialSpread ? "true" : "false",
            "timestamp": ISO8601DateFormatter().string(from: Date())
        ]

        guard let documentsURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first,
              let data = try? JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
        else { return }

        try? data.write(to: documentsURL.appendingPathComponent("reader-real-book-self-test.json"), options: .atomic)
    }

    private func writePlaybackSelfTestResult(isPlaying: Bool, pageNumber: Int) {
        let result = [
            "test": "reader-playback",
            "isPlaying": isPlaying ? "true" : "false",
            "pageNumber": "\(pageNumber)",
            "timestamp": ISO8601DateFormatter().string(from: Date())
        ]

        guard let documentsURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first,
              let data = try? JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
        else { return }

        try? data.write(to: documentsURL.appendingPathComponent("reader-playback-self-test.json"), options: .atomic)
    }

    private var pageTransition: AnyTransition {
        effectiveReduceMotion
            ? .opacity
            : .asymmetric(
                insertion: .scale(scale: 0.985).combined(with: .opacity),
                removal: .scale(scale: 1.01).combined(with: .opacity)
            )
    }
}

enum ReaderPalette {
    static let night = Color(red: 0.02, green: 0.045, blue: 0.085)
    static let deepNight = Color(red: 0.012, green: 0.025, blue: 0.050)
    static let panel = Color(red: 0.105, green: 0.125, blue: 0.165)
    static let panelStroke = Color.moonIvory.opacity(0.26)
    static let parchment = Color(red: 0.965, green: 0.905, blue: 0.770)
    static let parchmentDeep = Color(red: 0.850, green: 0.735, blue: 0.555)
    static let gold = Color.lanternGold
    static let ink = Color(red: 0.125, green: 0.105, blue: 0.090)
}

enum ReaderMetrics {
    static let cornerSmall: CGFloat = 6
    static let cornerMedium: CGFloat = 8
    static let cornerLarge: CGFloat = 18
    static let cornerBook: CGFloat = 24
    static let artAspectRatio: CGFloat = 1.5
    static let thumbnailAspectRatio: CGFloat = 1.5
    static let controlSize: CGFloat = 52
    static let safeArtInset: CGFloat = 14
}

struct ReaderBackground: View {
    var body: some View {
        ZStack {
            LinearGradient(
                colors: [ReaderPalette.deepNight, ReaderPalette.night, Color.indigoInk.opacity(0.78)],
                startPoint: .top,
                endPoint: .bottom
            )

            Canvas { context, size in
                for index in 0..<44 {
                    let seed = CGFloat(index)
                    let x = size.width * ((seed * 0.137).truncatingRemainder(dividingBy: 1))
                    let y = size.height * ((seed * 0.071 + 0.09).truncatingRemainder(dividingBy: 0.88))
                    let diameter = 1.0 + CGFloat(index % 3) * 0.8
                    let alpha = 0.08 + Double(index % 7) * 0.018
                    context.fill(
                        Path(ellipseIn: CGRect(x: x, y: y, width: diameter, height: diameter)),
                        with: .color(Color.moonIvory.opacity(alpha))
                    )
                }
            }
            .allowsHitTesting(false)

            LinearGradient(
                colors: [.clear, Color.black.opacity(0.18)],
                startPoint: .center,
                endPoint: .bottom
            )
        }
        .ignoresSafeArea()
    }
}

struct ReaderTopBar: View {
    let book: StoryBook
    @Binding var language: ReaderLanguage
    @Binding var bedtimeMode: Bool
    let compact: Bool
    let onBack: () -> Void
    var onBookMode: (() -> Void)? = nil

    var body: some View {
        HStack(spacing: compact ? 10 : 18) {
            ReaderChromeButton(title: compact ? nil : "Library", systemImage: "chevron.left", action: onBack, accessibilityID: "reader-back-button")

            if !compact {
                ReaderChromeButton(title: "Library", systemImage: "book.fill", action: onBack, accessibilityID: "reader-library-button")
            }

            Spacer(minLength: 8)

            HStack(spacing: 10) {
                MoonJarMark()
                    .frame(width: compact ? 28 : 38, height: compact ? 28 : 38)
                VStack(spacing: 1) {
                    Text("Moon Jar Stories")
                        .font(.system(size: compact ? 23 : 30, weight: .semibold, design: .serif))
                        .foregroundStyle(Color.moonIvory)
                        .lineLimit(1)
                        .minimumScaleFactor(0.72)
                    if compact {
                        Text(language == .korean ? book.title.ko : book.title.en)
                            .font(.caption.weight(.medium))
                            .foregroundStyle(Color.moonIvory.opacity(0.72))
                            .lineLimit(1)
                            .minimumScaleFactor(0.78)
                    }
                }
            }
            .accessibilityElement(children: .combine)

            Spacer(minLength: 8)

            if compact {
                ReaderChromeButton(title: nil, systemImage: "book.fill", action: { onBookMode?() ?? onBack() }, accessibilityID: "reader-real-book-top-button")
            } else {
                LanguagePill(language: $language, compact: compact)

                ReaderChromeButton(
                    title: nil,
                    systemImage: bedtimeMode ? "moon.zzz.fill" : "moon.fill",
                    action: { bedtimeMode.toggle() },
                    isActive: bedtimeMode
                )

                ReaderChromeButton(title: nil, systemImage: "speaker.wave.2.fill", action: {})
            }
        }
        .frame(minHeight: compact ? 46 : 54)
    }
}

struct MoonJarMark: View {
    var body: some View {
        ZStack {
            Image(systemName: "moon.stars.fill")
                .font(.system(size: 22, weight: .semibold))
                .foregroundStyle(ReaderPalette.night)
                .padding(7)
                .background(Color.moonIvory, in: Circle())
            Circle()
                .stroke(ReaderPalette.gold.opacity(0.75), lineWidth: 1.2)
        }
    }
}

struct ReaderChromeButton: View {
    let title: String?
    let systemImage: String
    let action: () -> Void
    var isActive = false
    var accessibilityID: String? = nil

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: systemImage)
                    .font(.system(size: 17, weight: .bold))
                if let title {
                    Text(title)
                        .font(.subheadline.weight(.semibold))
                        .lineLimit(1)
                }
            }
            .foregroundStyle(isActive ? ReaderPalette.night : Color.moonIvory)
            .padding(.horizontal, title == nil ? 14 : 18)
            .frame(height: 46)
            .background(
                Capsule()
                    .fill(isActive ? Color.moonIvory.opacity(0.88) : ReaderPalette.panel.opacity(0.72))
            )
            .overlay(
                Capsule()
                    .stroke(ReaderPalette.panelStroke, lineWidth: 1)
            )
            .shadow(color: Color.black.opacity(0.18), radius: 8, x: 0, y: 4)
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier(accessibilityID ?? "reader-chrome-\(title ?? systemImage)")
        .accessibilityLabel(title ?? systemImage)
    }
}

struct LanguagePill: View {
    @Binding var language: ReaderLanguage
    let compact: Bool

    var body: some View {
        HStack(spacing: 0) {
            ForEach(compact ? [ReaderLanguage.english, .korean] : ReaderLanguage.allCases) { option in
                Button {
                    language = option
                } label: {
                    Text(option.shortLabel)
                        .font(.caption.weight(.bold))
                        .foregroundStyle(language == option ? ReaderPalette.night : Color.moonIvory)
                        .frame(minWidth: compact ? 46 : 56)
                        .frame(height: 38)
                        .background(
                            Capsule()
                                .fill(language == option ? Color.moonIvory.opacity(0.92) : .clear)
                        )
                }
                .buttonStyle(.plain)
            }
        }
        .padding(4)
        .background(ReaderPalette.panel.opacity(0.72), in: Capsule())
        .overlay(Capsule().stroke(ReaderPalette.panelStroke, lineWidth: 1))
    }
}

struct PageProgressBar: View {
    let pageIndex: Int
    let pageCount: Int

    private var progress: CGFloat {
        guard pageCount > 1 else { return 1 }
        return CGFloat(pageIndex) / CGFloat(pageCount - 1)
    }

    var body: some View {
        VStack(spacing: 6) {
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(Color.moonIvory.opacity(0.22))
                        .frame(height: 3)
                    Capsule()
                        .fill(ReaderPalette.gold.opacity(0.92))
                        .frame(width: max(16, geometry.size.width * progress), height: 4)
                    MoonJarMark()
                        .frame(width: 29, height: 29)
                        .offset(x: min(max(0, geometry.size.width * progress - 14), geometry.size.width - 29), y: -13)
                }
                .frame(height: 30)
            }
            .frame(height: 30)

            Text("\(pageIndex + 1) / \(pageCount) pages")
                .font(.callout.weight(.medium))
                .foregroundStyle(Color.moonIvory.opacity(0.62))
        }
    }
}

struct PortraitStoryCard: View {
    let book: StoryBook
    let page: StoryPage
    let pageIndex: Int
    let pageCount: Int
    let language: ReaderLanguage
    let textMode: ReaderTextMode
    let bedtimeMode: Bool
    let reduceMotion: Bool
    let dragOffset: CGFloat
    let imageAssetPath: String?
    let contentRoot: URL?
    let onPrevious: () -> Void
    let onNext: () -> Void

    var body: some View {
        BookPageSurface(dragOffset: dragOffset, reduceMotion: reduceMotion, bedtimeMode: bedtimeMode) {
            GeometryReader { geometry in
                let textHeight = textPanelHeight(for: geometry.size)
                VStack(spacing: 0) {
                    SceneIllustrationPanel(
                        page: page,
                        imageAssetPath: imageAssetPath,
                        contentRoot: contentRoot,
                        bedtimeMode: bedtimeMode,
                        reduceMotion: reduceMotion,
                        cornerRadius: 22
                    )
                    .frame(height: max(260, geometry.size.height - textHeight))

                    ParchmentTextPanel(
                        page: page,
                        language: language,
                        textMode: textMode,
                        pageIndex: pageIndex,
                        pageCount: pageCount,
                        bedtimeMode: bedtimeMode,
                        compact: geometry.size.width < 540,
                        onPrevious: onPrevious,
                        onNext: onNext
                    )
                    .frame(height: textHeight)
                }
                .background(ReaderPalette.parchment)
                .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 24, style: .continuous)
                        .stroke(Color.moonIvory.opacity(0.35), lineWidth: 1)
                )
                .overlay(alignment: .trailing) {
                    PageDepthOverlay(side: .right, intensity: 0.74)
                        .frame(width: 26)
                        .padding(.vertical, 10)
                }
                .overlay(alignment: .bottom) {
                    Rectangle()
                        .fill(
                            LinearGradient(
                                colors: [.clear, Color.indigoInk.opacity(0.18)],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                        .frame(height: 22)
                }
                .shadow(color: Color.black.opacity(0.34), radius: 22, x: 0, y: 14)
            }
        }
    }

    private func textPanelHeight(for size: CGSize) -> CGFloat {
        let bilingualExtra: CGFloat = language == .bilingual ? 56 : 0
        let base: CGFloat = compactTextBase(for: size) + bilingualExtra
        return min(size.height * 0.42, base)
    }

    private func compactTextBase(for size: CGSize) -> CGFloat {
        size.width < 540 ? 250 : 320
    }
}

struct SceneIllustrationPanel: View {
    let page: StoryPage
    let imageAssetPath: String?
    let contentRoot: URL?
    let bedtimeMode: Bool
    let reduceMotion: Bool
    let cornerRadius: CGFloat

    @State private var animate = false

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                DemoAssetImage(assetPath: imageAssetPath, contentRoot: contentRoot, contentMode: .fill)
                    .frame(width: geometry.size.width, height: geometry.size.height)
                    .blur(radius: 26)
                    .scaleEffect(1.10)
                    .opacity(bedtimeMode ? 0.32 : 0.46)
                    .clipped()

                DemoAssetImage(assetPath: imageAssetPath, contentRoot: contentRoot, contentMode: .fit)
                    .frame(width: geometry.size.width, height: geometry.size.height)
                    .padding(ReaderMetrics.safeArtInset)
                    .scaleEffect(reduceMotion ? 1 : (animate ? 1.008 : 0.998))
                    .offset(y: reduceMotion ? 0 : (animate ? -2 : 2))
                    .background((bedtimeMode ? ReaderPalette.deepNight : ReaderPalette.parchment).opacity(0.18))

                LayeredSceneTreatment(
                    page: page,
                    contentRoot: contentRoot,
                    bedtimeMode: bedtimeMode,
                    reduceMotion: reduceMotion,
                    compact: geometry.size.width < 560
                )

                LivingSceneEffects(
                    animationType: page.animation.type,
                    loopDuration: 3.0,
                    bedtimeMode: bedtimeMode,
                    reduceMotion: reduceMotion
                )

                LinearGradient(
                    colors: bedtimeMode
                        ? [ReaderPalette.deepNight.opacity(0.26), .clear, ReaderPalette.deepNight.opacity(0.38)]
                        : [.clear, .clear, Color.black.opacity(0.12)],
                    startPoint: .top,
                    endPoint: .bottom
                )
            }
        }
        .clipShape(UnevenRoundedRectangle(topLeadingRadius: cornerRadius, bottomLeadingRadius: 0, bottomTrailingRadius: 0, topTrailingRadius: cornerRadius, style: .continuous))
        .onAppear {
            animate = false
            guard !reduceMotion else { return }
            withAnimation(.easeInOut(duration: 3.0).repeatForever(autoreverses: true)) {
                animate = true
            }
        }
    }
}

struct LayeredSceneTreatment: View {
    let page: StoryPage
    let contentRoot: URL?
    let bedtimeMode: Bool
    let reduceMotion: Bool
    var compact: Bool = false

    @State private var phase: CGFloat = 0

    private var layerNames: Set<String> {
        Set(page.animation.layers.map { $0.name.lowercased() })
    }

    private var hasCharacterLayer: Bool {
        layerNames.contains("character")
    }

    private var hasForegroundLayer: Bool {
        layerNames.contains("foreground")
    }

    private var hasEffectLayer: Bool {
        layerNames.contains("effect") || layerNames.contains("particle_glow")
    }

    private var animationKey: String {
        page.animation.type.lowercased()
    }

    private var assetLayers: [(Int, AnimationLayer)] {
        Array(page.animation.layers.enumerated()).filter { !$0.element.outputFile.orEmpty.isEmpty }
    }

    var body: some View {
        GeometryReader { geometry in
            let drift = reduceMotion ? 0 : sin(phase) * (compact ? 3 : 6)
            ZStack {
                ForEach(assetLayers, id: \.0) { index, layer in
                    DemoAssetImage(assetPath: layer.outputFile, contentRoot: contentRoot, contentMode: .fit)
                        .frame(width: geometry.size.width, height: geometry.size.height)
                        .opacity(layerOpacity(layer))
                        .scaleEffect(layerScale(layer, index: index))
                        .offset(layerOffset(layer, index: index, drift: drift))
                        .blendMode(layerBlendMode(layer))
                        .accessibilityHidden(true)
                }

                Canvas { context, size in
                    if hasCharacterLayer {
                        let focusRect = CGRect(
                            x: size.width * 0.18,
                            y: size.height * 0.14 + drift,
                            width: size.width * 0.64,
                            height: size.height * 0.66
                        )
                        context.fill(
                            Path(ellipseIn: focusRect),
                            with: .radialGradient(
                                Gradient(colors: [
                                    Color.white.opacity(bedtimeMode ? 0.045 : 0.080),
                                    Color.clear
                                ]),
                                center: CGPoint(x: focusRect.midX, y: focusRect.midY),
                                startRadius: 8,
                                endRadius: max(focusRect.width, focusRect.height) * 0.58
                            )
                        )
                    }

                    if hasForegroundLayer {
                        let top = Path(CGRect(x: 0, y: 0, width: size.width, height: size.height * 0.16))
                        context.fill(top, with: .linearGradient(
                            Gradient(colors: [
                                Color.indigoInk.opacity(bedtimeMode ? 0.20 : 0.10),
                                Color.clear
                            ]),
                            startPoint: CGPoint(x: size.width / 2, y: 0),
                            endPoint: CGPoint(x: size.width / 2, y: size.height * 0.18)
                        ))

                        let bottom = Path(CGRect(x: 0, y: size.height * 0.78, width: size.width, height: size.height * 0.22))
                        context.fill(bottom, with: .linearGradient(
                            Gradient(colors: [
                                Color.clear,
                                Color.indigoInk.opacity(bedtimeMode ? 0.28 : 0.16)
                            ]),
                            startPoint: CGPoint(x: size.width / 2, y: size.height * 0.78),
                            endPoint: CGPoint(x: size.width / 2, y: size.height)
                        ))
                    }

                    if hasEffectLayer {
                        drawSceneParticles(context: context, size: size, drift: drift)
                    }
                }
                .blendMode(bedtimeMode ? .screen : .softLight)

                if hasCharacterLayer {
                    RoundedRectangle(cornerRadius: compact ? 18 : 26, style: .continuous)
                        .stroke(
                            LinearGradient(
                                colors: [
                                    Color.white.opacity(bedtimeMode ? 0.08 : 0.16),
                                    ReaderPalette.gold.opacity(bedtimeMode ? 0.06 : 0.12),
                                    Color.clear
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: compact ? 1.0 : 1.4
                        )
                        .padding(compact ? 10 : 18)
                        .opacity(bedtimeMode ? 0.35 : 0.52)
                }
            }
            .frame(width: geometry.size.width, height: geometry.size.height)
        }
        .allowsHitTesting(false)
        .opacity(bedtimeMode ? 0.56 : 0.82)
        .onAppear {
            guard !reduceMotion else { return }
            phase = 0
            withAnimation(.easeInOut(duration: max(2.4, page.animation.loopDuration)).repeatForever(autoreverses: true)) {
                phase = .pi * 2
            }
        }
    }

    private func drawSceneParticles(context: GraphicsContext, size: CGSize, drift: CGFloat) {
        let warm = animationKey.contains("lantern") || animationKey.contains("warm") || animationKey.contains("glow")
        let cool = animationKey.contains("moon") || animationKey.contains("night") || animationKey.contains("snow")
        let count = compact ? 9 : 14
        for index in 0..<count {
            let seed = CGFloat(index + 1)
            let x = size.width * ((seed * 0.173).truncatingRemainder(dividingBy: 0.92) + 0.04)
            let yBase = size.height * ((seed * 0.119).truncatingRemainder(dividingBy: 0.72) + 0.12)
            let y = yBase + (reduceMotion ? 0 : drift * (index.isMultiple(of: 2) ? 1 : -0.55))
            let radius = CGFloat(1.6 + Double(index % 4) * 0.9)
            let color = warm ? ReaderPalette.gold : (cool ? Color.moonIvory : Color.jadeLeaf)
            context.fill(
                Path(ellipseIn: CGRect(x: x, y: y, width: radius, height: radius)),
                with: .color(color.opacity(bedtimeMode ? 0.12 : 0.20))
            )
        }
    }

    private func layerOpacity(_ layer: AnimationLayer) -> Double {
        switch layer.name.lowercased() {
        case "background": return bedtimeMode ? 0.08 : 0.12
        case "midground": return bedtimeMode ? 0.12 : 0.18
        case "character": return bedtimeMode ? 0.14 : 0.22
        case "foreground": return bedtimeMode ? 0.13 : 0.20
        case "effect": return bedtimeMode ? 0.16 : 0.24
        case "particle_glow": return bedtimeMode ? 0.18 : 0.28
        default: return bedtimeMode ? 0.10 : 0.16
        }
    }

    private func layerScale(_ layer: AnimationLayer, index: Int) -> CGFloat {
        guard !reduceMotion else { return 1.0 }
        let base = 1.0 + CGFloat(index) * 0.0015
        if layer.name.lowercased() == "foreground" { return base + 0.004 }
        if layer.name.lowercased() == "character" { return base + (sin(phase) * 0.002) }
        return base
    }

    private func layerOffset(_ layer: AnimationLayer, index: Int, drift: CGFloat) -> CGSize {
        guard !reduceMotion else { return .zero }
        let multiplier: CGFloat
        switch layer.name.lowercased() {
        case "background": multiplier = 0.18
        case "midground": multiplier = 0.34
        case "character": multiplier = 0.48
        case "foreground": multiplier = 0.62
        case "effect": multiplier = 0.76
        case "particle_glow": multiplier = 0.92
        default: multiplier = 0.32
        }
        let direction: CGFloat = index.isMultiple(of: 2) ? 1 : -1
        return CGSize(width: drift * multiplier * 0.55 * direction, height: drift * multiplier)
    }

    private func layerBlendMode(_ layer: AnimationLayer) -> BlendMode {
        switch layer.name.lowercased() {
        case "effect", "particle_glow": return bedtimeMode ? .screen : .plusLighter
        default: return bedtimeMode ? .screen : .softLight
        }
    }
}

private extension Optional where Wrapped == String {
    var orEmpty: String { self ?? "" }
}

struct ParchmentTextPanel: View {
    let page: StoryPage
    let language: ReaderLanguage
    let textMode: ReaderTextMode
    let pageIndex: Int
    let pageCount: Int
    let bedtimeMode: Bool
    let compact: Bool
    let onPrevious: () -> Void
    let onNext: () -> Void

    var body: some View {
        ZStack {
            ParchmentTexture()

            HStack(spacing: compact ? 8 : 18) {
                PageSideArrow(systemImage: "chevron.left", action: onPrevious)
                    .opacity(pageIndex == 0 ? 0.22 : 1)
                    .disabled(pageIndex == 0)

                StoryTextBlock(page: page, language: language, textMode: textMode, compact: compact)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)

                PageSideArrow(systemImage: "chevron.right", action: onNext)
                    .opacity(pageIndex >= pageCount - 1 ? 0.22 : 1)
                    .disabled(pageIndex >= pageCount - 1)
            }
            .padding(.horizontal, compact ? 14 : 24)
            .padding(.vertical, compact ? 14 : 20)

            PageCurlCorner()
                .frame(width: compact ? 92 : 122, height: compact ? 92 : 122)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomTrailing)

            Text("\(pageIndex + 1)")
                .font(.caption.weight(.bold))
                .foregroundStyle(ReaderPalette.ink.opacity(0.42))
                .padding(.horizontal, 11)
                .padding(.vertical, 5)
                .background(Color.white.opacity(0.30), in: Capsule())
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
                .padding(16)
        }
        .foregroundStyle(bedtimeMode ? Color.moonIvory.opacity(0.90) : ReaderPalette.ink)
    }
}

struct StoryTextBlock: View {
    let page: StoryPage
    let language: ReaderLanguage
    let textMode: ReaderTextMode
    let compact: Bool

    var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            VStack(alignment: .leading, spacing: compact ? 9 : 13) {
            if language == .korean || language == .bilingual {
                Text(koreanText)
                    .font(.system(size: compact ? 21 : 26, weight: .medium, design: .serif))
                    .lineSpacing(compact ? 4 : 6)
                    .foregroundStyle(ReaderPalette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .minimumScaleFactor(0.84)
            }

            if language == .bilingual {
                Divider()
                    .overlay(Color.brown.opacity(0.18))
            }

            if language == .english || language == .bilingual {
                Text(englishText)
                    .font(.system(size: language == .english ? (compact ? 20 : 24) : (compact ? 16 : 18), weight: .regular, design: .serif))
                    .lineSpacing(compact ? 3 : 5)
                    .foregroundStyle(ReaderPalette.ink.opacity(0.80))
                    .fixedSize(horizontal: false, vertical: true)
                    .minimumScaleFactor(0.82)
            }

            if !page.vocabulary.isEmpty {
                HStack(spacing: 8) {
                    ForEach(page.vocabulary.prefix(compact ? 2 : 3), id: \.self) { item in
                        VStack(alignment: .leading, spacing: 1) {
                            Text(item.en)
                                .font(.caption.weight(.semibold))
                            Text(item.ko)
                                .font(.caption2.weight(.medium))
                        }
                        .foregroundStyle(ReaderPalette.ink.opacity(0.62))
                        .lineLimit(1)
                        .minimumScaleFactor(0.78)
                        .padding(.horizontal, 9)
                        .padding(.vertical, 5)
                        .background(Color.white.opacity(0.30), in: RoundedRectangle(cornerRadius: 7, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 7, style: .continuous)
                                .stroke(Color.brown.opacity(0.08), lineWidth: 1)
                        )
                    }
                }
            }
        }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var englishText: String {
        switch textMode {
        case .little:
            return page.text?.enLittle ?? page.englishText
        case .story:
            return page.text?.enStandard ?? page.englishText
        }
    }

    private var koreanText: String {
        switch textMode {
        case .little:
            return page.text?.koLittle ?? page.koreanText
        case .story:
            return page.text?.koStandard ?? page.koreanText
        }
    }
}

struct PageSideArrow: View {
    let systemImage: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: systemImage)
                .font(.system(size: 28, weight: .semibold))
                .foregroundStyle(ReaderPalette.parchmentDeep.opacity(0.92))
                .frame(width: 46, height: 72)
        }
        .buttonStyle(.plain)
    }
}

struct PageDepthOverlay: View {
    let side: BookSide
    var intensity: Double = 1

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                ForEach(0..<7, id: \.self) { index in
                    Rectangle()
                        .fill(ReaderPalette.parchmentDeep.opacity((0.18 - Double(index) * 0.016) * intensity))
                        .frame(width: 1.2 + CGFloat(index % 2))
                        .offset(x: side == .left ? CGFloat(index) * 2.6 : -CGFloat(index) * 2.6)
                }

                LinearGradient(
                    colors: side == .left
                        ? [Color.indigoInk.opacity(0.22 * intensity), .clear]
                        : [.clear, Color.indigoInk.opacity(0.22 * intensity)],
                    startPoint: .leading,
                    endPoint: .trailing
                )

                LinearGradient(
                    colors: [.clear, Color.white.opacity(0.15 * intensity), .clear],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .frame(height: max(geometry.size.height * 0.72, 120))
                .offset(y: geometry.size.height * 0.04)
            }
            .frame(width: geometry.size.width, height: geometry.size.height)
        }
        .allowsHitTesting(false)
    }
}

struct ParchmentTexture: View {
    var body: some View {
        ZStack {
            LinearGradient(
                colors: [ReaderPalette.parchment, Color(red: 0.980, green: 0.930, blue: 0.820), ReaderPalette.parchment],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )

            Canvas { context, size in
                for index in 0..<46 {
                    let seed = CGFloat(index)
                    let x = size.width * ((seed * 0.217).truncatingRemainder(dividingBy: 1))
                    let y = size.height * ((seed * 0.381).truncatingRemainder(dividingBy: 1))
                    let rect = CGRect(x: x, y: y, width: 1.4 + CGFloat(index % 5), height: 1.0 + CGFloat(index % 3))
                    context.fill(Path(ellipseIn: rect), with: .color(Color.brown.opacity(0.018)))
                }

                for index in 0..<9 {
                    let y = size.height * (0.11 + CGFloat(index) * 0.087)
                    var path = Path()
                    path.move(to: CGPoint(x: size.width * 0.05, y: y))
                    path.addQuadCurve(
                        to: CGPoint(x: size.width * 0.95, y: y + CGFloat(index % 3) - 1),
                        control: CGPoint(x: size.width * 0.5, y: y + CGFloat(index % 2) * 4)
                    )
                    context.stroke(path, with: .color(Color.brown.opacity(0.018)), lineWidth: 0.7)
                }
            }

            VStack {
                Spacer()
                Rectangle()
                    .fill(LinearGradient(colors: [.clear, Color.brown.opacity(0.13)], startPoint: .top, endPoint: .bottom))
                    .frame(height: 46)
            }
        }
    }
}

struct PageCurlCorner: View {
    var body: some View {
        ZStack(alignment: .bottomTrailing) {
            Path { path in
                path.move(to: CGPoint(x: 0, y: 90))
                path.addQuadCurve(to: CGPoint(x: 92, y: 0), control: CGPoint(x: 56, y: 88))
                path.addLine(to: CGPoint(x: 92, y: 92))
                path.closeSubpath()
            }
            .fill(
                LinearGradient(
                    colors: [Color.white.opacity(0.76), ReaderPalette.parchment.opacity(0.96), ReaderPalette.parchmentDeep.opacity(0.68)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .shadow(color: Color.black.opacity(0.24), radius: 10, x: -5, y: -6)

            Path { path in
                path.move(to: CGPoint(x: 6, y: 86))
                path.addQuadCurve(to: CGPoint(x: 86, y: 8), control: CGPoint(x: 44, y: 76))
            }
            .stroke(Color.brown.opacity(0.22), lineWidth: 1)
        }
        .clipped()
    }
}

struct RealBookModeBanner: View {
    @Binding var isOn: Bool

    var body: some View {
        ViewThatFits(in: .horizontal) {
            bannerContent(showSubtitle: true, showPreview: true)
            bannerContent(showSubtitle: false, showPreview: false)
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 12)
        .background(ReaderPalette.panel.opacity(0.72), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .stroke(ReaderPalette.panelStroke, lineWidth: 1)
        )
    }

    private func bannerContent(showSubtitle: Bool, showPreview: Bool) -> some View {
        HStack(spacing: showPreview ? 16 : 10) {
            Image(systemName: "book.fill")
                .font(.title2.weight(.semibold))
                .foregroundStyle(ReaderPalette.gold)
                .frame(width: 38, height: 38)
                .background(ReaderPalette.panel.opacity(0.72), in: Circle())

            VStack(alignment: .leading, spacing: 3) {
                Text("Real Book Mode")
                    .font(.headline.weight(.semibold))
                    .foregroundStyle(Color.moonIvory)
                    .lineLimit(1)
                    .minimumScaleFactor(0.78)
                if showSubtitle {
                    Text("Two-page spread on tablet")
                        .font(.caption)
                        .foregroundStyle(Color.moonIvory.opacity(0.64))
                        .lineLimit(1)
                        .minimumScaleFactor(0.72)
                }
            }

            Spacer(minLength: 6)

            if showPreview {
                MiniSpreadPreview()
            }

            Toggle("", isOn: $isOn)
                .labelsHidden()
                .tint(ReaderPalette.gold)
                .accessibilityIdentifier("reader-real-book-toggle")
        }
    }
}

struct MiniSpreadPreview: View {
    var body: some View {
        HStack(spacing: 1) {
            Rectangle()
                .fill(LinearGradient(colors: [ReaderPalette.parchment, Color.lanternGold.opacity(0.48)], startPoint: .top, endPoint: .bottom))
            Rectangle()
                .fill(LinearGradient(colors: [ReaderPalette.parchment, Color.indigoInk.opacity(0.35)], startPoint: .top, endPoint: .bottom))
        }
        .frame(width: 96, height: 46)
        .clipShape(RoundedRectangle(cornerRadius: 5, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 5, style: .continuous).stroke(Color.moonIvory.opacity(0.28), lineWidth: 1))
    }
}

struct ReaderControlDeck: View {
    let isPlaying: Bool
    @Binding var autoPlay: Bool
    @Binding var textModeRawValue: String
    @Binding var realBookMode: Bool
    @Binding var bedtimeMode: Bool
    @Binding var language: ReaderLanguage
    let canPrevious: Bool
    let canNext: Bool
    let onPrevious: () -> Void
    let onReplay: () -> Void
    let onPlayPause: () -> Void
    let onNext: () -> Void

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 14) {
                ReaderRoundButton(systemImage: "backward.fill", title: "Previous", isEnabled: canPrevious, action: onPrevious, accessibilityID: "reader-previous-button")
                ReaderRoundButton(systemImage: isPlaying ? "pause.fill" : "play.fill", title: "Read", prominent: true, action: onPlayPause, accessibilityID: "reader-read-button")
                ReaderRoundButton(systemImage: "arrow.counterclockwise", title: "Replay", action: onReplay, accessibilityID: "reader-replay-button")
                ReaderRoundButton(systemImage: "textformat.size", title: textMode.shortLabel, action: toggleTextMode, isActive: textMode == .little, accessibilityID: "reader-text-button")
                ReaderRoundButton(systemImage: autoPlay ? "speaker.wave.2.fill" : "speaker.wave.1.fill", title: "Auto", action: { autoPlay.toggle() }, isActive: autoPlay, accessibilityID: "reader-autoplay-button")
                ReaderRoundButton(systemImage: bedtimeMode ? "moon.zzz.fill" : "moon.fill", title: "Bedtime", action: { bedtimeMode.toggle() }, isActive: bedtimeMode, accessibilityID: "reader-bedtime-button")
                ReaderLanguageButton(language: $language)

                if canNext {
                    ReaderRoundButton(systemImage: "forward.fill", title: "Next", action: onNext, accessibilityID: "reader-next-button")
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
        }
        .background(ReaderPalette.night.opacity(0.28), in: Capsule())
    }

    private var textMode: ReaderTextMode {
        ReaderTextMode(rawValue: textModeRawValue) ?? .story
    }

    private func toggleTextMode() {
        textModeRawValue = (textMode == .story ? ReaderTextMode.little : ReaderTextMode.story).rawValue
    }
}

struct ReaderRoundButton: View {
    let systemImage: String
    let title: String
    var prominent = false
    var isEnabled = true
    var action: () -> Void
    var isActive = false
    var accessibilityID: String? = nil

    var body: some View {
        Button(action: action) {
            VStack(spacing: 6) {
                Image(systemName: systemImage)
                    .font(.system(size: prominent ? 25 : 20, weight: .bold))
                    .frame(width: prominent ? 66 : 52, height: prominent ? 66 : 52)
                    .foregroundStyle(prominent || isActive ? ReaderPalette.night : Color.moonIvory)
                    .background(
                        Circle()
                            .fill(prominent ? ReaderPalette.gold : (isActive ? Color.moonIvory.opacity(0.88) : ReaderPalette.panel.opacity(0.74)))
                    )
                    .overlay(Circle().stroke(ReaderPalette.panelStroke, lineWidth: 1))
                    .shadow(color: prominent ? ReaderPalette.gold.opacity(0.26) : Color.black.opacity(0.16), radius: prominent ? 15 : 8, x: 0, y: 5)

                Text(title)
                    .font(.caption.weight(.medium))
                    .foregroundStyle(Color.moonIvory.opacity(isEnabled ? 0.84 : 0.38))
                    .lineLimit(1)
                    .minimumScaleFactor(0.72)
            }
        }
        .buttonStyle(.plain)
        .disabled(!isEnabled)
        .opacity(isEnabled ? 1 : 0.45)
        .accessibilityIdentifier(accessibilityID ?? "reader-\(title.lowercased())-button")
        .accessibilityLabel(title)
    }
}

struct ReaderLanguageButton: View {
    @Binding var language: ReaderLanguage

    var body: some View {
        Button {
            language = language.nextReaderLanguage
        } label: {
            VStack(spacing: 6) {
                HStack(spacing: 2) {
                    Text("가")
                        .font(.system(size: 20, weight: .bold, design: .serif))
                    Text("En")
                        .font(.system(size: 15, weight: .bold, design: .serif))
                }
                .foregroundStyle(ReaderPalette.night)
                .frame(width: 58, height: 52)
                .background(Color.moonIvory.opacity(0.92), in: Capsule())
                .overlay(Capsule().stroke(ReaderPalette.panelStroke, lineWidth: 1))

                Text(language.shortLabel)
                    .font(.caption.weight(.medium))
                    .foregroundStyle(Color.moonIvory.opacity(0.84))
            }
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("reader-language-button")
        .accessibilityLabel("Language")
    }
}

struct ThumbnailStrip: View {
    let book: StoryBook
    @Binding var pageIndex: Int
    let reduceMotion: Bool
    let contentRoot: URL?
    let imageAsset: (StoryPage) -> String?

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                ForEach(Array(book.pages.enumerated()), id: \.element.id) { index, page in
                    Button {
                        withAnimation(reduceMotion ? nil : .spring(response: 0.34, dampingFraction: 0.86)) {
                            pageIndex = index
                        }
                    } label: {
                        VStack(spacing: 4) {
                            ArtThumbnail(assetPath: imageAsset(page), contentRoot: contentRoot, isSelected: pageIndex == index)
                                .frame(width: 80, height: 58)
                            Text("\(index + 1)")
                                .font(.caption2.weight(.bold))
                                .foregroundStyle(pageIndex == index ? ReaderPalette.night : Color.moonIvory.opacity(0.76))
                        }
                        .padding(5)
                        .background(pageIndex == index ? Color.moonIvory : ReaderPalette.panel.opacity(0.54), in: RoundedRectangle(cornerRadius: 9, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 9, style: .continuous)
                                .stroke(pageIndex == index ? ReaderPalette.gold : ReaderPalette.panelStroke, lineWidth: pageIndex == index ? 2 : 1)
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 6)
            .padding(.vertical, 4)
        }
    }
}

struct ArtThumbnail: View {
    let assetPath: String?
    let contentRoot: URL?
    let isSelected: Bool

    var body: some View {
        ZStack {
            ParchmentTexture()
            DemoAssetImage(assetPath: assetPath, contentRoot: contentRoot, contentMode: .fit)
                .padding(4)
        }
        .aspectRatio(ReaderMetrics.thumbnailAspectRatio, contentMode: .fit)
        .clipShape(RoundedRectangle(cornerRadius: ReaderMetrics.cornerSmall, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: ReaderMetrics.cornerSmall, style: .continuous)
                .stroke(isSelected ? ReaderPalette.gold.opacity(0.92) : Color.moonIvory.opacity(0.18), lineWidth: isSelected ? 2 : 1)
        )
        .shadow(color: Color.black.opacity(isSelected ? 0.24 : 0.12), radius: isSelected ? 8 : 4, x: 0, y: 3)
    }
}

struct PortraitRealBookModeCard: View {
    let book: StoryBook
    let pageIndex: Int
    let language: ReaderLanguage
    let textMode: ReaderTextMode
    let bedtimeMode: Bool
    let reduceMotion: Bool
    let dragOffset: CGFloat
    let contentRoot: URL?
    let imageAsset: (StoryPage) -> String?

    var body: some View {
        GeometryReader { geometry in
            let spreadHeight = min(geometry.size.height - 92, geometry.size.width * 0.64)

            ZStack {
                RoundedRectangle(cornerRadius: 26, style: .continuous)
                    .fill(
                        LinearGradient(
                            colors: [
                                ReaderPalette.deepNight.opacity(0.95),
                                ReaderPalette.night.opacity(0.90),
                                Color.indigoInk.opacity(0.82)
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )

                Canvas { context, size in
                    for index in 0..<26 {
                        let seed = CGFloat(index)
                        let x = size.width * ((seed * 0.271).truncatingRemainder(dividingBy: 1))
                        let y = size.height * ((seed * 0.193 + 0.11).truncatingRemainder(dividingBy: 0.82))
                        let diameter = 1.2 + CGFloat(index % 3) * 0.7
                        context.fill(
                            Path(ellipseIn: CGRect(x: x, y: y, width: diameter, height: diameter)),
                            with: .color(Color.moonIvory.opacity(0.12))
                        )
                    }
                }
                .allowsHitTesting(false)

                VStack(spacing: 18) {
                    HStack {
                        Label("Real Book Mode", systemImage: "book.pages.fill")
                            .font(.headline.weight(.semibold))
                            .foregroundStyle(Color.moonIvory)
                        Spacer()
                        Text("\(visiblePageLabel)")
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(Color.moonIvory.opacity(0.72))
                    }
                    .padding(.horizontal, 22)
                    .padding(.top, 18)

                    OpenBookStage(
                        book: book,
                        pageIndex: pageIndex,
                        language: language,
                        textMode: textMode,
                        bedtimeMode: bedtimeMode,
                        reduceMotion: reduceMotion,
                        dragOffset: dragOffset,
                        contentRoot: contentRoot,
                        imageAsset: imageAsset
                    )
                    .frame(height: max(360, spreadHeight))
                    .padding(.horizontal, 18)

                    PageDotProgress(pageIndex: pageIndex, pageCount: book.pages.count)
                        .scaleEffect(0.88)
                        .padding(.bottom, 14)
                }
            }
            .clipShape(RoundedRectangle(cornerRadius: 26, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 26, style: .continuous)
                    .stroke(ReaderPalette.panelStroke, lineWidth: 1)
            )
            .shadow(color: Color.black.opacity(0.38), radius: 22, x: 0, y: 14)
        }
    }

    private var visiblePageLabel: String {
        let leftPage = pageIndex.isMultiple(of: 2) ? pageIndex + 1 : pageIndex
        let rightPage = min(leftPage + 1, book.pages.count)
        return leftPage == rightPage ? "\(leftPage) / \(book.pages.count)" : "\(leftPage)-\(rightPage) / \(book.pages.count)"
    }
}

struct OpenBookStage: View {
    let book: StoryBook
    let pageIndex: Int
    let language: ReaderLanguage
    let textMode: ReaderTextMode
    let bedtimeMode: Bool
    let reduceMotion: Bool
    let dragOffset: CGFloat
    let contentRoot: URL?
    let imageAsset: (StoryPage) -> String?

    private var leftIndex: Int {
        pageIndex.isMultiple(of: 2) ? pageIndex : max(pageIndex - 1, 0)
    }

    private var rightIndex: Int? {
        let index = leftIndex + 1
        return index < book.pages.count ? index : nil
    }

    var body: some View {
        GeometryReader { geometry in
            let pageWidth = (geometry.size.width - 22) / 2
            let progress = min(abs(dragOffset) / 260, 1)
            let direction: CGFloat = dragOffset < 0 ? -1 : 1

            ZStack {
                BookBoardBacking(progress: progress)

                HStack(spacing: 0) {
                    OpenBookPage(
                        page: book.pages[leftIndex],
                        side: .left,
                        language: language,
                        textMode: textMode,
                        bedtimeMode: bedtimeMode,
                        reduceMotion: reduceMotion,
                        imageAssetPath: imageAsset(book.pages[leftIndex]),
                        contentRoot: contentRoot
                    )
                    .frame(width: pageWidth)

                    BookSpine()
                        .frame(width: 22)

                    if let rightIndex {
                        OpenBookPage(
                            page: book.pages[rightIndex],
                            side: .right,
                            language: language,
                            textMode: textMode,
                            bedtimeMode: bedtimeMode,
                            reduceMotion: reduceMotion,
                            imageAssetPath: imageAsset(book.pages[rightIndex]),
                            contentRoot: contentRoot
                        )
                        .frame(width: pageWidth)
                    } else {
                        BlankBookPage(side: .right)
                            .frame(width: pageWidth)
                    }
                }
                .frame(width: geometry.size.width, height: geometry.size.height)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .stroke(Color.moonIvory.opacity(0.20), lineWidth: 1)
                )
                .shadow(color: Color.black.opacity(0.38), radius: 24, x: 0, y: 16)
                .overlay(alignment: .leading) {
                    BookPageStackEdges(side: .left)
                        .frame(width: 18)
                        .offset(x: -12)
                }
                .overlay(alignment: .trailing) {
                    BookPageStackEdges(side: .right)
                        .frame(width: 18)
                        .offset(x: 12)
                }
                .overlay(alignment: .top) {
                    PageTopBottomDepth(edge: .top)
                        .frame(height: 16)
                        .offset(y: -8)
                }
                .overlay(alignment: .bottom) {
                    PageTopBottomDepth(edge: .bottom)
                        .frame(height: 18)
                        .offset(y: 8)
                }
                .rotation3DEffect(
                    .degrees(reduceMotion ? 0 : Double(dragOffset / 76)),
                    axis: (x: 0, y: 1, z: 0),
                    anchor: dragOffset < 0 ? .trailing : .leading,
                    perspective: 0.78
                )

                if !reduceMotion {
                    TurningBookPagePreview(
                        page: book.pages[direction < 0 ? (rightIndex ?? leftIndex) : leftIndex],
                        side: direction < 0 ? .right : .left,
                        language: language,
                        textMode: textMode,
                        bedtimeMode: bedtimeMode,
                        reduceMotion: reduceMotion,
                        imageAssetPath: imageAsset(book.pages[direction < 0 ? (rightIndex ?? leftIndex) : leftIndex]),
                        contentRoot: contentRoot,
                        progress: progress,
                        direction: direction,
                        pageWidth: pageWidth
                    )
                    .opacity(progress > 0.025 ? 0.96 : 0)

                    PageTurnSheet(progress: progress, direction: dragOffset > 0 ? 1 : -1)
                        .opacity(progress > 0.03 ? 0.86 : 0)
                } else {
                    EmptyView()
                }
            }
        }
    }
}

struct BookBoardBacking: View {
    let progress: CGFloat

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(Color.black.opacity(0.30))
                .offset(y: 18)
                .blur(radius: 14)

            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [
                            Color.indigoInk.opacity(0.82),
                            ReaderPalette.deepNight.opacity(0.92),
                            Color.indigoInk.opacity(0.72)
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .padding(.horizontal, -14)
                .padding(.vertical, -12)
                .overlay(
                    RoundedRectangle(cornerRadius: 20, style: .continuous)
                        .stroke(Color.moonIvory.opacity(0.18), lineWidth: 1)
                        .padding(.horizontal, -14)
                        .padding(.vertical, -12)
                )

            VStack(spacing: 0) {
                Rectangle()
                    .fill(Color.moonIvory.opacity(0.08 + 0.05 * progress))
                    .frame(height: 2)
                Spacer()
                Rectangle()
                    .fill(Color.black.opacity(0.24 + 0.10 * progress))
                    .frame(height: 3)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, -8)
        }
        .allowsHitTesting(false)
    }
}

enum PageDepthEdge {
    case top
    case bottom
}

struct PageTopBottomDepth: View {
    let edge: PageDepthEdge

    var body: some View {
        LinearGradient(
            colors: edge == .top
                ? [Color.black.opacity(0.16), ReaderPalette.parchmentDeep.opacity(0.20), .clear]
                : [.clear, ReaderPalette.parchmentDeep.opacity(0.26), Color.black.opacity(0.18)],
            startPoint: .top,
            endPoint: .bottom
        )
        .overlay {
            Canvas { context, size in
                for index in 0..<5 {
                    let y = size.height * (0.20 + CGFloat(index) * 0.14)
                    var path = Path()
                    path.move(to: CGPoint(x: size.width * 0.04, y: y))
                    path.addLine(to: CGPoint(x: size.width * 0.96, y: y + CGFloat(index % 2)))
                    context.stroke(path, with: .color(Color.brown.opacity(0.05)), lineWidth: 0.6)
                }
            }
        }
        .allowsHitTesting(false)
    }
}

struct TurningBookPagePreview: View {
    let page: StoryPage
    let side: BookSide
    let language: ReaderLanguage
    let textMode: ReaderTextMode
    let bedtimeMode: Bool
    let reduceMotion: Bool
    let imageAssetPath: String?
    let contentRoot: URL?
    let progress: CGFloat
    let direction: CGFloat
    let pageWidth: CGFloat

    var body: some View {
        GeometryReader { geometry in
            let centerX = direction < 0
                ? geometry.size.width / 2 + 11 + pageWidth / 2
                : geometry.size.width / 2 - 11 - pageWidth / 2
            let lift = min(max(progress, 0), 1)

            OpenBookPage(
                page: page,
                side: side,
                language: language,
                textMode: textMode,
                bedtimeMode: bedtimeMode,
                reduceMotion: reduceMotion,
                imageAssetPath: imageAssetPath,
                contentRoot: contentRoot
            )
            .frame(width: pageWidth, height: geometry.size.height)
            .overlay(
                LinearGradient(
                    colors: direction < 0
                        ? [Color.black.opacity(0.24 * lift), Color.white.opacity(0.22 * lift), ReaderPalette.parchmentDeep.opacity(0.34 * lift)]
                        : [ReaderPalette.parchmentDeep.opacity(0.34 * lift), Color.white.opacity(0.22 * lift), Color.black.opacity(0.24 * lift)],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            .shadow(color: Color.black.opacity(0.30 * lift), radius: 18 + 10 * lift, x: direction < 0 ? -14 * lift : 14 * lift, y: 10)
            .overlay(alignment: direction < 0 ? .leading : .trailing) {
                PageDepthOverlay(side: direction < 0 ? .left : .right, intensity: 0.90)
                    .frame(width: 18)
                    .opacity(lift)
            }
            .rotation3DEffect(
                .degrees(Double(direction < 0 ? -78 * lift : 78 * lift)),
                axis: (x: 0, y: 1, z: 0),
                anchor: direction < 0 ? .leading : .trailing,
                perspective: 0.78
            )
            .scaleEffect(x: 1 - lift * 0.08, y: 1, anchor: direction < 0 ? .leading : .trailing)
            .position(x: centerX + direction * pageWidth * 0.18 * lift, y: geometry.size.height / 2)
        }
        .allowsHitTesting(false)
    }
}

enum BookSide {
    case left
    case right
}

struct OpenBookPage: View {
    let page: StoryPage
    let side: BookSide
    let language: ReaderLanguage
    let textMode: ReaderTextMode
    let bedtimeMode: Bool
    let reduceMotion: Bool
    let imageAssetPath: String?
    let contentRoot: URL?

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                ParchmentTexture()

                DemoAssetImage(assetPath: imageAssetPath, contentRoot: contentRoot, contentMode: .fit)
                    .frame(width: geometry.size.width * 0.92, height: geometry.size.height * 0.58)
                    .offset(y: geometry.size.height * 0.19)
                    .opacity(bedtimeMode ? 0.18 : 0.25)
                    .clipped()

                VStack(alignment: side == .left ? .leading : .trailing, spacing: 14) {
                    OpenBookText(page: page, language: language, textMode: textMode, compact: geometry.size.width < 520)
                        .frame(maxWidth: geometry.size.width * 0.74, alignment: side == .left ? .leading : .trailing)
                        .padding(.top, max(28, geometry.size.height * 0.07))
                        .padding(.horizontal, max(28, geometry.size.width * 0.08))

                    Spacer(minLength: 4)

                    DemoAssetImage(assetPath: imageAssetPath, contentRoot: contentRoot, contentMode: .fit)
                        .frame(width: max(120, geometry.size.width - 52), height: max(170, geometry.size.height * 0.52))
                        .opacity(bedtimeMode ? 0.76 : 0.94)
                        .padding(.horizontal, 20)
                        .padding(.bottom, max(16, geometry.size.height * 0.04))
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)

                LivingSceneEffects(
                    animationType: page.animation.type,
                    loopDuration: 3.0,
                    bedtimeMode: bedtimeMode,
                    reduceMotion: reduceMotion
                )
                .opacity(0.28)

                LayeredSceneTreatment(
                    page: page,
                    contentRoot: contentRoot,
                    bedtimeMode: bedtimeMode,
                    reduceMotion: reduceMotion,
                    compact: geometry.size.width < 520
                )
                .opacity(0.48)

                LinearGradient(
                    colors: side == .left
                        ? [Color.clear, Color.black.opacity(0.19)]
                        : [Color.black.opacity(0.18), Color.clear],
                    startPoint: .leading,
                    endPoint: .trailing
                )

                Image(systemName: side == .left ? "sparkle" : "cloud.moon.fill")
                    .font(.system(size: 22, weight: .semibold))
                    .foregroundStyle(ReaderPalette.gold.opacity(0.44))
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: side == .left ? .topLeading : .topTrailing)
                    .padding(28)

                BookFolioMark(pageNumber: page.pageNumber, side: side)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: side == .left ? .bottomLeading : .bottomTrailing)
                    .padding(.horizontal, 26)
                    .padding(.bottom, 18)

                PageDepthOverlay(side: side, intensity: 0.52)
                    .frame(width: 18)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: side == .left ? .leading : .trailing)
            }
            .clipShape(
                UnevenRoundedRectangle(
                    topLeadingRadius: side == .left ? 10 : 2,
                    bottomLeadingRadius: side == .left ? 10 : 2,
                    bottomTrailingRadius: side == .right ? 10 : 2,
                    topTrailingRadius: side == .right ? 10 : 2,
                    style: .continuous
                )
            )
        }
    }
}

struct BookFolioMark: View {
    let pageNumber: Int
    let side: BookSide

    var body: some View {
        HStack(spacing: 6) {
            if side == .right {
                Rectangle()
                    .fill(ReaderPalette.ink.opacity(0.22))
                    .frame(width: 24, height: 1)
            }
            Text("\(pageNumber)")
                .font(.caption.weight(.semibold))
                .foregroundStyle(ReaderPalette.ink.opacity(0.44))
                .monospacedDigit()
            if side == .left {
                Rectangle()
                    .fill(ReaderPalette.ink.opacity(0.22))
                    .frame(width: 24, height: 1)
            }
        }
        .padding(.horizontal, 9)
        .padding(.vertical, 5)
        .background(Color.white.opacity(0.20), in: Capsule())
    }
}

struct OpenBookText: View {
    let page: StoryPage
    let language: ReaderLanguage
    let textMode: ReaderTextMode
    let compact: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Image(systemName: "sparkle")
                .font(.system(size: compact ? 16 : 20, weight: .semibold))
                .foregroundStyle(ReaderPalette.gold.opacity(0.62))

            if language == .korean || language == .bilingual {
                Text(koreanText)
                    .font(.system(size: compact ? 22 : 30, weight: .medium, design: .serif))
                    .lineSpacing(compact ? 5 : 8)
                    .foregroundStyle(ReaderPalette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .minimumScaleFactor(0.82)
            }

            if language == .english || language == .bilingual {
                Text(englishText)
                    .font(.system(size: language == .english ? (compact ? 19 : 22) : (compact ? 14 : 17), weight: .regular, design: .serif))
                    .lineSpacing(4)
                    .foregroundStyle(ReaderPalette.ink.opacity(0.74))
                    .fixedSize(horizontal: false, vertical: true)
                    .minimumScaleFactor(0.82)
            }
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 14)
        .background(
            LinearGradient(
                colors: [ReaderPalette.parchment.opacity(0.40), ReaderPalette.parchment.opacity(0.10)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            ),
            in: RoundedRectangle(cornerRadius: 8, style: .continuous)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .stroke(Color.brown.opacity(0.08), lineWidth: 1)
        )
    }

    private var englishText: String {
        switch textMode {
        case .little:
            return page.text?.enLittle ?? page.englishText
        case .story:
            return page.text?.enStandard ?? page.englishText
        }
    }

    private var koreanText: String {
        switch textMode {
        case .little:
            return page.text?.koLittle ?? page.koreanText
        case .story:
            return page.text?.koStandard ?? page.koreanText
        }
    }
}

struct BookPageStackEdges: View {
    let side: BookSide

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                ForEach(0..<5, id: \.self) { index in
                    RoundedRectangle(cornerRadius: 2, style: .continuous)
                        .fill(ReaderPalette.parchmentDeep.opacity(0.34 - Double(index) * 0.038))
                        .frame(width: 3)
                        .offset(x: side == .left ? CGFloat(index) * 3 : -CGFloat(index) * 3)
                }
                LinearGradient(
                    colors: side == .left
                        ? [Color.black.opacity(0.22), .clear]
                        : [.clear, Color.black.opacity(0.22)],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            }
            .frame(width: geometry.size.width, height: geometry.size.height)
        }
        .allowsHitTesting(false)
    }
}

struct BlankBookPage: View {
    let side: BookSide

    var body: some View {
        ZStack {
            ParchmentTexture()
            LinearGradient(
                colors: side == .left ? [.clear, Color.black.opacity(0.14)] : [Color.black.opacity(0.14), .clear],
                startPoint: .leading,
                endPoint: .trailing
            )
        }
    }
}

struct BookSpine: View {
    var body: some View {
        LinearGradient(
            colors: [Color.black.opacity(0.34), ReaderPalette.parchmentDeep.opacity(0.48), Color.black.opacity(0.28)],
            startPoint: .leading,
            endPoint: .trailing
        )
        .overlay(Rectangle().fill(Color.white.opacity(0.10)).frame(width: 1), alignment: .center)
    }
}

struct PageTurnSheet: View {
    let progress: CGFloat
    let direction: CGFloat

    var body: some View {
        GeometryReader { geometry in
            let width = geometry.size.width * (0.28 + 0.18 * progress)
            let height = geometry.size.height * (0.82 + 0.12 * progress)
            let trailingX = direction < 0 ? geometry.size.width - width - 12 : 12
            let curlPath = Path { path in
                path.move(to: CGPoint(x: trailingX + width * (direction < 0 ? 0.18 : 0.82), y: 0))
                path.addQuadCurve(
                    to: CGPoint(x: trailingX + width * (direction < 0 ? 0.88 : 0.12), y: height),
                    control: CGPoint(x: trailingX + width * (direction < 0 ? 0.05 : 0.95), y: height * 0.50)
                )
                path.addQuadCurve(
                    to: CGPoint(x: trailingX + width * (direction < 0 ? 0.98 : 0.02), y: height * 0.08),
                    control: CGPoint(x: trailingX + width * 0.52, y: height * 0.78)
                )
                path.closeSubpath()
            }

            ZStack {
                curlPath
                    .fill(
                        LinearGradient(
                            colors: [
                                Color.white.opacity(0.70),
                                ReaderPalette.parchment.opacity(0.96),
                                ReaderPalette.parchmentDeep.opacity(0.82),
                                Color.black.opacity(0.24)
                            ],
                            startPoint: direction < 0 ? .leading : .trailing,
                            endPoint: direction < 0 ? .trailing : .leading
                        )
                    )

                curlPath
                    .stroke(Color.white.opacity(0.42), lineWidth: 1.2)

                curlPath
                    .fill(
                        LinearGradient(
                            colors: [Color.clear, Color.black.opacity(0.16 * progress)],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                    .blendMode(.multiply)

                Path { path in
                    let edgeX = trailingX + width * (direction < 0 ? 0.86 : 0.14)
                    path.move(to: CGPoint(x: edgeX, y: height * 0.08))
                    path.addQuadCurve(
                        to: CGPoint(x: edgeX + direction * width * 0.08, y: height * 0.88),
                        control: CGPoint(x: edgeX - direction * width * 0.16, y: height * 0.48)
                    )
                }
                .stroke(Color.black.opacity(0.18 + progress * 0.18), lineWidth: 3)

                ForEach(0..<5, id: \.self) { index in
                    Path { path in
                        let startY = height * (0.14 + CGFloat(index) * 0.14)
                        let startX = trailingX + width * (direction < 0 ? 0.30 : 0.70)
                        path.move(to: CGPoint(x: startX, y: startY))
                        path.addQuadCurve(
                            to: CGPoint(x: startX + direction * width * 0.44, y: startY + height * 0.10),
                            control: CGPoint(x: startX + direction * width * 0.18, y: startY + height * 0.04)
                        )
                    }
                    .stroke(Color.brown.opacity(0.035), lineWidth: 0.8)
                }

                ForEach(0..<4, id: \.self) { index in
                    Path { path in
                        let x = trailingX + width * (direction < 0 ? 0.76 : 0.24) + direction * CGFloat(index) * 5
                        path.move(to: CGPoint(x: x, y: height * 0.10))
                        path.addQuadCurve(
                            to: CGPoint(x: x + direction * width * 0.05, y: height * 0.91),
                            control: CGPoint(x: x - direction * width * 0.10, y: height * 0.52)
                        )
                    }
                    .stroke(Color.white.opacity(0.11 - Double(index) * 0.015), lineWidth: 1)
                }
            }
            .shadow(color: Color.black.opacity(0.34), radius: 16, x: direction < 0 ? -9 : 9, y: 9)
            .overlay(
                LinearGradient(
                    colors: [Color.clear, Color.black.opacity(0.16 * progress)],
                    startPoint: .top,
                    endPoint: .bottom
                )
            )
            .offset(y: geometry.size.height * 0.04)
        }
        .allowsHitTesting(false)
    }
}

struct PageDotProgress: View {
    let pageIndex: Int
    let pageCount: Int

    var body: some View {
        HStack(spacing: 10) {
            ForEach(0..<pageCount, id: \.self) { index in
                Circle()
                    .fill(index == pageIndex ? ReaderPalette.gold : Color.moonIvory.opacity(0.32))
                    .frame(width: index == pageIndex ? 11 : 9, height: index == pageIndex ? 11 : 9)
            }
            Text("\(pageIndex + 1) / \(pageCount)")
                .font(.headline.weight(.semibold))
                .foregroundStyle(Color.moonIvory)
                .padding(.horizontal, 18)
                .padding(.vertical, 10)
                .background(ReaderPalette.panel.opacity(0.78), in: Capsule())
                .overlay(Capsule().stroke(ReaderPalette.panelStroke, lineWidth: 1))
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 10)
        .background(ReaderPalette.panel.opacity(0.58), in: Capsule())
    }
}

struct BookPageSurface<Content: View>: View {
    let dragOffset: CGFloat
    let reduceMotion: Bool
    let bedtimeMode: Bool
    @ViewBuilder let content: Content

    private var progress: CGFloat {
        min(abs(dragOffset) / 280, 1)
    }

    private var turnDirection: CGFloat {
        dragOffset < 0 ? -1 : 1
    }

    var body: some View {
        content
            .clipShape(RoundedRectangle(cornerRadius: 6, style: .continuous))
            .overlay(alignment: .leading) {
                Rectangle()
                    .fill(
                        LinearGradient(
                            colors: [
                                Color.indigoInk.opacity(bedtimeMode ? 0.40 : 0.28),
                                .clear
                            ],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .frame(width: 18)
                    .opacity(reduceMotion ? 0.35 : 0.55)
            }
            .overlay(alignment: .trailing) {
                Rectangle()
                    .fill(
                        LinearGradient(
                            colors: [
                                .clear,
                                Color.indigoInk.opacity(0.32 + progress * 0.30)
                            ],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .frame(width: 38)
                    .opacity(reduceMotion ? 0.18 : 0.58)
            }
            .overlay {
                if !reduceMotion && progress > 0.02 {
                    LinearGradient(
                        colors: [
                            Color.white.opacity(0.12 * progress),
                            Color.indigoInk.opacity(0.34 * progress)
                        ],
                        startPoint: turnDirection < 0 ? .trailing : .leading,
                        endPoint: turnDirection < 0 ? .leading : .trailing
                    )
                }
            }
            .overlay {
                if !reduceMotion && progress > 0.035 {
                    PageTurnSheet(progress: progress, direction: turnDirection)
                        .opacity(0.72)
                }
            }
            .rotation3DEffect(
                .degrees(reduceMotion ? 0 : Double(turnDirection * progress * 16)),
                axis: (x: 0, y: 1, z: 0),
                anchor: turnDirection < 0 ? .trailing : .leading,
                perspective: 0.62
            )
            .offset(x: reduceMotion ? 0 : dragOffset * 0.06)
            .shadow(color: Color.indigoInk.opacity(bedtimeMode ? 0.34 : 0.22), radius: reduceMotion ? 0 : 16 + progress * 16, x: 0, y: 8)
            .padding(.horizontal, 12)
            .padding(.top, 12)
    }
}

struct PageText: View {
    let page: StoryPage
    let language: ReaderLanguage
    let bedtimeMode: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            if language == .korean || language == .bilingual {
                Text(page.koreanText)
                    .font(.title3.weight(.semibold))
                    .foregroundStyle(bedtimeMode ? Color.moonIvory : Color.indigoInk)
                    .fixedSize(horizontal: false, vertical: true)
            }
            if language == .english || language == .bilingual {
                Text(page.englishText)
                    .font(.body)
                    .foregroundStyle(bedtimeMode ? Color.moonIvory.opacity(0.72) : Color.indigoInk.opacity(0.72))
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}

struct AnimatedSceneView: View {
    let page: StoryPage
    let imageAssetPath: String?
    let bedtimeMode: Bool
    let contentRoot: URL?
    let reduceMotion: Bool
    let sceneHeight: CGFloat

    @State private var animate = false

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                DemoAssetImage(assetPath: imageAssetPath, contentRoot: contentRoot, contentMode: .fill)
                    .frame(width: geometry.size.width, height: geometry.size.height)
                    .blur(radius: 22)
                    .scaleEffect(1.08)
                    .opacity(bedtimeMode ? 0.34 : 0.48)
                    .clipped()

                DemoAssetImage(assetPath: imageAssetPath, contentRoot: contentRoot, contentMode: .fit)
                    .frame(
                        width: max(geometry.size.width - 28, 280),
                        height: max(geometry.size.height - 22, 260)
                    )
                    .background((bedtimeMode ? Color.indigoInk : Color.moonIvory).opacity(0.42))
                    .clipShape(RoundedRectangle(cornerRadius: 6, style: .continuous))
                    .scaleEffect(reduceMotion ? 1 : (animate ? 1.006 : 1.0))
                    .offset(x: reduceMotion ? 0 : (animate ? -1.5 : 1.5), y: 0)
                    .shadow(color: Color.indigoInk.opacity(bedtimeMode ? 0.20 : 0.14), radius: 14, x: 0, y: 7)

                LinearGradient(
                    colors: bedtimeMode
                        ? [Color.indigoInk.opacity(0.34), Color.indigoInk.opacity(0.08)]
                        : [.clear, Color.indigoInk.opacity(0.10)],
                    startPoint: .top,
                    endPoint: .bottom
                )

                LivingSceneEffects(
                    animationType: page.animation.type,
                    loopDuration: page.animation.loopDuration,
                    bedtimeMode: bedtimeMode,
                    reduceMotion: reduceMotion
                )

                if imageAssetPath == nil {
                    Text(page.animation.type.replacingOccurrences(of: "_", with: " ").capitalized)
                        .font(.caption.weight(.bold))
                        .foregroundStyle(Color.indigoInk.opacity(0.58))
                        .padding(.horizontal, 12)
                        .padding(.vertical, 7)
                        .background(.white.opacity(0.55), in: Capsule())

                    Text(page.imagePrompt)
                        .font(.title2.weight(.semibold))
                        .multilineTextAlignment(.center)
                        .foregroundStyle(Color.indigoInk)
                        .lineLimit(5)
                        .padding(.horizontal, 32)
                        .minimumScaleFactor(0.74)
                }
            }
        }
        .frame(maxWidth: .infinity)
        .frame(height: sceneHeight)
        .clipped()
        .contentShape(Rectangle())
        .onAppear {
            animate = false
            guard !reduceMotion else { return }
            withAnimation(.easeInOut(duration: max(page.animation.loopDuration, 2.4)).repeatForever(autoreverses: true)) {
                animate = true
            }
        }
    }

    private var sceneAccent: Color {
        if page.animation.type.lowercased().contains("moon") { return .jadeLeaf }
        if page.animation.type.lowercased().contains("sun") { return .persimmon }
        if page.animation.type.lowercased().contains("snow") { return .lotusPink }
        return .lanternGold
    }
}

struct RealBookSpreadView: View {
    let book: StoryBook
    let pageIndex: Int
    let bedtimeMode: Bool
    let contentRoot: URL?
    let reduceMotion: Bool
    let sceneHeight: CGFloat
    let imageAsset: (StoryPage) -> String?

    private var leftIndex: Int {
        pageIndex.isMultiple(of: 2) ? pageIndex : max(pageIndex - 1, 0)
    }

    private var rightIndex: Int? {
        let index = leftIndex + 1
        return index < book.pages.count ? index : nil
    }

    var body: some View {
        HStack(spacing: 0) {
            SpreadPage(page: book.pages[leftIndex], imageAssetPath: imageAsset(book.pages[leftIndex]), bedtimeMode: bedtimeMode, contentRoot: contentRoot, reduceMotion: reduceMotion)
                .overlay(alignment: .trailing) {
                    Rectangle()
                        .fill(LinearGradient(colors: [.clear, Color.indigoInk.opacity(0.26)], startPoint: .leading, endPoint: .trailing))
                        .frame(width: 26)
                }

            Rectangle()
                .fill(LinearGradient(colors: [Color.indigoInk.opacity(0.38), Color.indigoInk.opacity(0.12), Color.indigoInk.opacity(0.38)], startPoint: .leading, endPoint: .trailing))
                .frame(width: 18)

            if let rightIndex {
                SpreadPage(page: book.pages[rightIndex], imageAssetPath: imageAsset(book.pages[rightIndex]), bedtimeMode: bedtimeMode, contentRoot: contentRoot, reduceMotion: reduceMotion)
                    .overlay(alignment: .leading) {
                        Rectangle()
                            .fill(LinearGradient(colors: [Color.indigoInk.opacity(0.22), .clear], startPoint: .leading, endPoint: .trailing))
                            .frame(width: 26)
                    }
            } else {
                Color.moonIvory
            }
        }
        .background(Color.moonIvory)
        .frame(maxWidth: .infinity)
        .frame(height: sceneHeight)
    }
}

struct SpreadPage: View {
    let page: StoryPage
    let imageAssetPath: String?
    let bedtimeMode: Bool
    let contentRoot: URL?
    let reduceMotion: Bool

    var body: some View {
        ZStack {
            DemoAssetImage(assetPath: imageAssetPath, contentRoot: contentRoot, contentMode: .fit)
                .padding(12)
            LivingSceneEffects(animationType: page.animation.type, loopDuration: page.animation.loopDuration, bedtimeMode: bedtimeMode, reduceMotion: reduceMotion)
            LinearGradient(colors: [.clear, Color.indigoInk.opacity(bedtimeMode ? 0.34 : 0.16)], startPoint: .top, endPoint: .bottom)
            VStack {
                Spacer()
                Text(page.koreanText)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(bedtimeMode ? Color.moonIvory : Color.indigoInk)
                    .lineLimit(3)
                    .padding(10)
                    .background((bedtimeMode ? Color.indigoInk : Color.moonIvory).opacity(0.72), in: RoundedRectangle(cornerRadius: 6, style: .continuous))
                    .padding(12)
            }
        }
        .clipped()
    }
}

struct LivingSceneEffects: View {
    let animationType: String
    let loopDuration: Double
    let bedtimeMode: Bool
    let reduceMotion: Bool

    var body: some View {
        if reduceMotion {
            sceneCanvas(phase: 0)
                .opacity(0.14)
                .allowsHitTesting(false)
        } else {
            TimelineView(.animation) { timeline in
                let duration = max(loopDuration, 2.4)
                let phase = timeline.date.timeIntervalSinceReferenceDate.truncatingRemainder(dividingBy: duration) / duration
                sceneCanvas(phase: phase)
            }
            .opacity(0.42)
            .allowsHitTesting(false)
        }
    }

    private func sceneCanvas(phase: Double) -> some View {
        Canvas { context, size in
            let intensity = bedtimeMode ? 0.45 : 1.0
            let lower = animationType.lowercased()

            drawSoftSceneBreath(context: context, size: size, phase: phase, intensity: intensity)

            if lower.contains("moon") || lower.contains("night") || lower.contains("bedtime") {
                drawMoonGlow(context: context, size: size, phase: phase, intensity: intensity)
            }
            if lower.contains("lantern") || lower.contains("warm") {
                drawLanternFlicker(context: context, size: size, phase: phase, intensity: intensity)
            }
            if lower.contains("cloud") || lower.contains("drift") || lower.contains("sky") {
                drawCloudDrift(context: context, size: size, phase: phase, intensity: intensity)
            }
            if lower.contains("water") || lower.contains("ripple") || lower.contains("pond") || lower.contains("river") {
                drawWaterRipple(context: context, size: size, phase: phase, intensity: intensity)
            }
            if lower.contains("tiger") || lower.contains("blink") || lower.contains("tail") {
                drawBlinkAndTail(context: context, size: size, phase: phase, intensity: intensity)
            }
            if lower.contains("spark") || lower.contains("magic") || lower.contains("glow") || lower.contains("dokkaebi") || lower.contains("spirit") {
                drawSparkles(context: context, size: size, phase: phase, intensity: intensity)
            }
            if lower.contains("fire") || lower.contains("star") || lower.contains("night") {
                drawFireflies(context: context, size: size, phase: phase, intensity: intensity)
            }
        }
    }

    private func drawSoftSceneBreath(context: GraphicsContext, size: CGSize, phase: Double, intensity: Double) {
        let pulse = 0.5 + 0.5 * sin(phase * .pi * 2)
        let alpha = 0.035 + 0.035 * pulse
        context.fill(
            Path(CGRect(origin: .zero, size: size)),
            with: .linearGradient(
                Gradient(colors: [
                    Color.moonIvory.opacity(alpha * intensity),
                    Color.clear,
                    Color.indigoInk.opacity(0.025 * intensity)
                ]),
                startPoint: CGPoint(x: size.width * 0.5, y: 0),
                endPoint: CGPoint(x: size.width * 0.5, y: size.height)
            )
        )
    }

    private func drawMoonGlow(context: GraphicsContext, size: CGSize, phase: Double, intensity: Double) {
        let pulse = 0.55 + 0.45 * sin(phase * .pi * 2)
        let rect = CGRect(x: size.width * 0.66, y: size.height * 0.10, width: 120 + pulse * 28, height: 120 + pulse * 28)
        context.fill(Path(ellipseIn: rect), with: .color(Color.moonIvory.opacity(0.18 * intensity)))
        context.stroke(Path(ellipseIn: rect.insetBy(dx: -16, dy: -16)), with: .color(Color.jadeLeaf.opacity(0.12 * intensity)), lineWidth: 2)
    }

    private func drawLanternFlicker(context: GraphicsContext, size: CGSize, phase: Double, intensity: Double) {
        let flicker = 0.6 + 0.4 * sin(phase * .pi * 10)
        context.fill(
            Path(CGRect(origin: .zero, size: size)),
            with: .color(Color.lanternGold.opacity(0.035 * flicker * intensity))
        )
    }

    private func drawCloudDrift(context: GraphicsContext, size: CGSize, phase: Double, intensity: Double) {
        for index in 0..<3 {
            let x = (size.width * (0.12 + CGFloat(index) * 0.30) + CGFloat(phase) * 42).truncatingRemainder(dividingBy: size.width + 90) - 45
            let y = size.height * (0.14 + CGFloat(index) * 0.08)
            let rect = CGRect(x: x, y: y, width: 120, height: 34)
            context.fill(Path(roundedRect: rect, cornerRadius: 18), with: .color(Color.moonIvory.opacity(0.12 * intensity)))
        }
    }

    private func drawWaterRipple(context: GraphicsContext, size: CGSize, phase: Double, intensity: Double) {
        for index in 0..<3 {
            let radius = CGFloat(40 + index * 24) + CGFloat(phase) * 28
            let rect = CGRect(x: size.width * 0.50 - radius, y: size.height * 0.68 - radius * 0.32, width: radius * 2, height: radius * 0.64)
            context.stroke(Path(ellipseIn: rect), with: .color(Color.jadeLeaf.opacity(0.18 * intensity * (1 - Double(index) * 0.18))), lineWidth: 2)
        }
    }

    private func drawBlinkAndTail(context: GraphicsContext, size: CGSize, phase: Double, intensity: Double) {
        let blink = phase > 0.82 ? 0.18 : 1.0
        let eyeY = size.height * 0.32
        let eyeRect = CGRect(x: size.width * 0.72, y: eyeY, width: 12, height: 8 * blink)
        context.fill(Path(ellipseIn: eyeRect), with: .color(Color.indigoInk.opacity(0.22 * intensity)))
        var tail = Path()
        let sway = CGFloat(sin(phase * .pi * 2)) * 18
        tail.move(to: CGPoint(x: size.width * 0.72, y: size.height * 0.62))
        tail.addCurve(to: CGPoint(x: size.width * 0.86, y: size.height * 0.66), control1: CGPoint(x: size.width * 0.78 + sway, y: size.height * 0.56), control2: CGPoint(x: size.width * 0.82 - sway, y: size.height * 0.72))
        context.stroke(tail, with: .color(Color.persimmon.opacity(0.18 * intensity)), lineWidth: 7)
    }

    private func drawSparkles(context: GraphicsContext, size: CGSize, phase: Double, intensity: Double) {
        for index in 0..<10 {
            let seed = Double(index)
            let x = size.width * CGFloat(0.16 + 0.072 * seed)
            let y = size.height * CGFloat(0.18 + 0.18 * ((seed * 1.7).truncatingRemainder(dividingBy: 3)) / 3)
            let alpha = 0.06 + 0.16 * (0.5 + 0.5 * sin((phase + seed * 0.13) * .pi * 2))
            let rect = CGRect(x: x, y: y, width: 4 + CGFloat(index % 3), height: 4 + CGFloat(index % 3))
            context.fill(Path(ellipseIn: rect), with: .color(Color.lanternGold.opacity(alpha * intensity)))
        }
    }

    private func drawFireflies(context: GraphicsContext, size: CGSize, phase: Double, intensity: Double) {
        for index in 0..<8 {
            let seed = CGFloat(index)
            let x = size.width * (0.12 + seed * 0.10) + CGFloat(sin(phase * .pi * 2 + Double(seed))) * 9
            let y = size.height * (0.44 + CGFloat(index % 4) * 0.08) + CGFloat(cos(phase * .pi * 2 + Double(seed))) * 7
            context.fill(Path(ellipseIn: CGRect(x: x, y: y, width: 5, height: 5)), with: .color(Color.lanternGold.opacity(0.20 * intensity)))
        }
    }
}

struct MoonJarCover: View {
    let title: LocalizedTitle
    let slug: String
    var assetPath: String? = nil
    var contentRoot: URL? = nil

    var body: some View {
        ZStack {
            ParchmentTexture()

            DemoAssetImage(assetPath: assetPath, contentRoot: contentRoot, contentMode: .fit)
                .padding(assetPath == nil ? 0 : 18)

            LinearGradient(
                colors: assetPath == nil
                    ? [Color.indigoInk, Color.jadeLeaf.opacity(0.82), Color.persimmon.opacity(0.68)]
                    : [Color.clear, Color.indigoInk.opacity(0.08)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )

            if assetPath == nil {
                Circle()
                    .stroke(Color.moonIvory.opacity(0.88), lineWidth: 12)
                    .frame(width: 110, height: 110)
                    .offset(y: -2)
            }
        }
        .aspectRatio(ReaderMetrics.artAspectRatio, contentMode: .fit)
        .background(ReaderPalette.parchment, in: RoundedRectangle(cornerRadius: ReaderMetrics.cornerMedium, style: .continuous))
        .clipShape(RoundedRectangle(cornerRadius: ReaderMetrics.cornerMedium, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: ReaderMetrics.cornerMedium, style: .continuous)
                .stroke(Color.indigoInk.opacity(0.12), lineWidth: 1)
        )
        .accessibilityLabel("\(title.ko), \(title.en)")
    }
}

struct ComingSoonView: View {
    let entry: CatalogBook

    var body: some View {
        VStack(spacing: 18) {
            MoonJarCover(title: entry.title, slug: entry.slug)
                .frame(maxWidth: .infinity)
                .frame(height: 300)
                .clipped()
            Text(entry.title.ko)
                .font(.largeTitle.weight(.bold))
            Text(entry.sensitivity ?? "Premium story metadata is ready for production scripting.")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding(24)
        .frame(maxWidth: 680)
        .background(Color.moonIvory)
    }
}

struct PaywallView: View {
    @EnvironmentObject private var entitlements: EntitlementStore
    @Environment(\.dismiss) private var dismiss
    @State private var showParentGate = false
    @State private var pendingParentGateAction = ParentGateAction.purchase

    var body: some View {
        VStack(spacing: 20) {
            MoonJarCover(title: LocalizedTitle(ko: "달항아리 이야기", en: "Moon Jar Stories", romanization: nil), slug: "moon-jar")
                .frame(maxWidth: .infinity)
                .frame(height: 220)
                .clipped()

            Text("Premium Korean Library")
                .font(.title.weight(.bold))
                .foregroundStyle(Color.indigoInk)

            VStack(spacing: 10) {
                PlanRow(title: "Monthly", price: "$4.99")
                PlanRow(title: "Annual", price: "$39.99")
                PlanRow(title: "Lifetime", price: "$79.99-$99.99")
            }

            Button {
                pendingParentGateAction = .purchase
                showParentGate = true
            } label: {
                Label("Continue", systemImage: "lock.open.fill")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)

            Button("Restore") {
                pendingParentGateAction = .restore
                showParentGate = true
            }
            .buttonStyle(.borderless)
        }
        .padding(24)
        .frame(maxWidth: 900, maxHeight: .infinity, alignment: .top)
        .presentationDetents([.medium, .large])
        .sheet(isPresented: $showParentGate) {
            ParentGateView {
                showParentGate = false
                switch pendingParentGateAction {
                case .purchase:
                    entitlements.unlockForPrototype()
                    dismiss()
                case .restore:
                    Task { await entitlements.restore() }
                }
            }
        }
    }
}

private enum ParentGateAction {
    case purchase
    case restore
}

struct DemoAssetImage: View {
    let assetPath: String?
    let contentRoot: URL?
    var contentMode: ContentMode = .fill

    var body: some View {
        if let image = loadImage() {
            image
                .resizable()
                .aspectRatio(contentMode: contentMode)
        } else {
            LinearGradient(
                colors: [Color.ivoryWarm, Color.jadeLeaf.opacity(0.52), Color.persimmon.opacity(0.42)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        }
    }

    private func loadImage() -> Image? {
        guard let assetPath, let contentRoot else { return nil }
        let url = contentRoot.appendingPathComponent(assetPath)
        guard let data = try? Data(contentsOf: url) else { return nil }

        #if os(iOS)
        guard let platformImage = UIImage(data: data) else { return nil }
        return Image(uiImage: platformImage)
        #elseif os(macOS)
        guard let platformImage = NSImage(data: data) else { return nil }
        return Image(nsImage: platformImage)
        #else
        return nil
        #endif
    }
}

struct PlanRow: View {
    let title: String
    let price: String

    var body: some View {
        HStack {
            Text(title)
                .fontWeight(.semibold)
            Spacer()
            Text(price)
                .foregroundStyle(Color.indigoInk.opacity(0.72))
        }
        .padding(14)
        .background(.white.opacity(0.75), in: RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}

struct ParentGateView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var answer = ""
    let onPass: () -> Void

    var body: some View {
        VStack(spacing: 18) {
            Text("Parent Check")
                .font(.title2.weight(.bold))
            Text("7 + 5 =")
                .font(.largeTitle.weight(.semibold))
            TextField("Answer", text: $answer)
                .moonJarParentGateTextField()
                .frame(width: 180)
            HStack {
                Button("Cancel") { dismiss() }
                Button("Continue") {
                    if answer.trimmingCharacters(in: .whitespacesAndNewlines) == "12" {
                        onPass()
                    }
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(24)
    }
}

extension Color {
    static let indigoInk = Color(red: 0.12, green: 0.16, blue: 0.32)
    static let moonIvory = Color(red: 0.98, green: 0.95, blue: 0.87)
    static let ivoryWarm = Color(red: 0.96, green: 0.91, blue: 0.78)
    static let persimmon = Color(red: 0.82, green: 0.31, blue: 0.18)
    static let jadeLeaf = Color(red: 0.19, green: 0.50, blue: 0.42)
    static let lotusPink = Color(red: 0.86, green: 0.48, blue: 0.58)
    static let lanternGold = Color(red: 0.93, green: 0.66, blue: 0.24)
}

private extension View {
    @ViewBuilder
    func moonJarInlineNavigationTitle() -> some View {
        #if os(iOS)
        self.navigationBarTitleDisplayMode(.inline)
        #else
        self
        #endif
    }

    @ViewBuilder
    func moonJarHideNavigationBar() -> some View {
        #if os(iOS)
        self.toolbar(.hidden, for: .navigationBar)
        #else
        self
        #endif
    }

    @ViewBuilder
    func moonJarParentGateTextField() -> some View {
        #if os(iOS)
        self
            .keyboardType(.numberPad)
            .textFieldStyle(.roundedBorder)
            .multilineTextAlignment(.center)
        #else
        self
            .textFieldStyle(.roundedBorder)
        #endif
    }
}

private extension ReaderLanguage {
    var shortLabel: String {
        switch self {
        case .english: return "EN"
        case .bilingual: return "KO/EN"
        case .korean: return "한국어"
        }
    }

    var nextReaderLanguage: ReaderLanguage {
        switch self {
        case .english: return .bilingual
        case .bilingual: return .korean
        case .korean: return .english
        }
    }
}
