# Xcode App Target Scaffold

The Swift package in `ios/MoonJarStoriesiOS` remains the runnable prototype target used by `swift build` and simulator packaging. This folder documents the production Xcode app target shape that should wrap the package sources before App Store submission.

Expected target:

- Target name: `MoonJarStories`
- Bundle identifier placeholders:
  - Debug: `com.moonjarstories.app.debug`
  - Staging: `com.moonjarstories.app.staging`
  - Production: `com.moonjarstories.app`
- Deployment target: iOS/iPadOS 17+
- SwiftUI app entry: reuse `MoonJarStoriesApp.swift`
- Resources: package `shared-content` plus downloadable asset bundles later
- App icon: `MoonJarStories/Assets.xcassets/AppIcon.appiconset`
- Launch screen: `MoonJarStories/Base.lproj/LaunchScreen.storyboard`

Audio behavior:

- Narration uses `AVAudioSession` category `.playback` with `.spokenAudio` mode so bedtime narration works even if the ringer switch is silent.
- Page changes stop old narration before the next page starts.
- Autoplay advances only after narration completion.
- Interruption handling pauses playback and reconfigures the audio session when interruption ends.

Build configurations:

- Debug: local packaged shared-content, mock StoreKit, verbose validation.
- Staging: staging backend/catalog, StoreKit sandbox product IDs, TestFlight review assets.
- Production: production backend/catalog, real product IDs, reviewed/final assets only.
