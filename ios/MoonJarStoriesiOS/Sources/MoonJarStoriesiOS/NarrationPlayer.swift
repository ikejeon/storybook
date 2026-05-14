import AVFoundation
import Foundation

@MainActor
final class NarrationPlayer: NSObject, ObservableObject, AVAudioPlayerDelegate {
    @Published private(set) var isPlaying = false
    @Published private(set) var isPaused = false

    private var audioPlayer: AVAudioPlayer?
    private var soundPlayer: AVAudioPlayer?
    private var currentPlaybackKey: String?
    @Published private(set) var missingNarrationAsset: String?
    var onFinished: (() -> Void)?

    override init() {
        super.init()
        configureAudioSession()
        #if os(iOS)
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleAudioInterruption(_:)),
            name: AVAudioSession.interruptionNotification,
            object: AVAudioSession.sharedInstance()
        )
        #endif
    }

    deinit {
        NotificationCenter.default.removeObserver(self)
    }

    func playOrPause(_ page: StoryPage, language: ReaderLanguage, bedtimeMode: Bool, contentRoot: URL?, audioAssetPath: String?) {
        if isPlaying {
            pause()
            return
        }

        if isPaused, currentPlaybackKey == playbackKey(page: page, language: language) {
            resume()
            return
        }

        replay(page, language: language, bedtimeMode: bedtimeMode, contentRoot: contentRoot, audioAssetPath: audioAssetPath)
    }

    func replay(_ page: StoryPage, language: ReaderLanguage, bedtimeMode: Bool, contentRoot: URL?, audioAssetPath: String?) {
        stop()
        currentPlaybackKey = playbackKey(page: page, language: language)

        let resolvedAudioPath = audioAssetPath ?? (language == .korean ? page.narrationAudio : nil)
        if let audioURL = resolvedAudioPath.flatMap({ contentRoot?.appendingPathComponent($0) }),
           FileManager.default.fileExists(atPath: audioURL.path),
           let player = try? AVAudioPlayer(contentsOf: audioURL) {
            audioPlayer = player
            player.delegate = self
            player.volume = bedtimeMode ? 0.55 : 0.72
            player.prepareToPlay()
            player.play()
            missingNarrationAsset = nil
            isPaused = false
            isPlaying = true
            return
        }

        missingNarrationAsset = resolvedAudioPath ?? "missing manifest narration path for \(page.id) / \(language.rawValue)"
        isPlaying = false
        isPaused = false
    }

    func playPageTurn(contentRoot: URL?, soundAssetPath: String?, bedtimeMode: Bool) {
        guard let path = soundAssetPath ?? Optional("audio/ui/page-flip.wav"),
              let url = contentRoot?.appendingPathComponent(path),
              FileManager.default.fileExists(atPath: url.path),
              let player = try? AVAudioPlayer(contentsOf: url)
        else { return }

        soundPlayer = player
        player.volume = bedtimeMode ? 0.18 : 0.38
        player.prepareToPlay()
        player.play()
    }

    private func pause() {
        audioPlayer?.pause()
        isPlaying = false
        isPaused = true
    }

    private func resume() {
        audioPlayer?.play()
        isPlaying = true
        isPaused = false
    }

    func stop() {
        audioPlayer?.stop()
        audioPlayer = nil
        currentPlaybackKey = nil
        isPlaying = false
        isPaused = false
    }

    private func playbackKey(page: StoryPage, language: ReaderLanguage) -> String {
        "\(page.id)|\(language.rawValue)"
    }

    private func finishPlayback() {
        isPlaying = false
        isPaused = false
        onFinished?()
    }

    private func configureAudioSession() {
        #if os(iOS)
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio, options: [.duckOthers])
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            lastAudioSessionError = error.localizedDescription
        }
        #endif
    }

    @Published private(set) var lastAudioSessionError: String?

    #if os(iOS)
    @objc private func handleAudioInterruption(_ notification: Notification) {
        guard let value = notification.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt,
              let type = AVAudioSession.InterruptionType(rawValue: value)
        else { return }

        switch type {
        case .began:
            pause()
        case .ended:
            configureAudioSession()
        @unknown default:
            stop()
        }
    }
    #endif

    nonisolated func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        Task { @MainActor in
            finishPlayback()
        }
    }
}
