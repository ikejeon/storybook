# Moon Jar Stories iOS

Native SwiftUI prototype for iPadOS/iOS.

The app loads the canonical shared content from `../../shared-content` by walking up from the current working directory. During a production Xcode setup, add a build phase that copies `shared-content/` into the app bundle or points `MOONJAR_CONTENT_ROOT` to the checked-out content directory for local development.

## Local Content Root

```bash
export MOONJAR_CONTENT_ROOT=/absolute/path/to/story_book/shared-content
```

## App Responsibilities

- Render the shared book JSON
- Play Korean narration through AVFoundation
- Animate scenes natively with SwiftUI/Core Animation-friendly metadata
- Gate purchases with a parent check
- Use StoreKit 2 for production subscription and purchase flows

