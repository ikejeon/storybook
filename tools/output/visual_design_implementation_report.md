# Moon Jar Stories Visual Design Implementation Report

Generated: 2026-05-07

## Summary

This pass focused on visual quality and reading experience polish rather than architecture. The app now treats story art as a fit-first picture-book asset, uses stable 3:2 containers for covers/cards/thumbnails, defaults the demo reader language storage back to English, improves spread navigation behavior, adds shared Moon Jar design tokens, and adds an approval-first provider workflow for art and voice.

## 2026-05-07 Reader Experience Polish Pass

- Reader UX, Real Book Mode, and Page flip now have a mechanical score gate at `tools/score_reader_experience.py`.
- The score report lives at `tools/output/reader_experience_score_report.md`.
- iOS Real Book Mode now shows a turning-page preview over the two-page spread, with 3D rotation, paper gradient, shadow, page thickness, and curl/fold overlay.
- iOS single-page/portrait mode now uses the same page-turn sheet cue during drag or button/autoplay turns.
- iOS page-turn sound timing was tightened so it fires after the page turn is committed, including the reduced-motion path.
- Android button/autoplay page turns now animate through multiple offset steps instead of popping to the next page.
- Android portrait and Real Book spread surfaces now show a Compose canvas curl overlay with paper gradient, crease, depth, and shadow cues during drag/button turns.
- Android drag threshold and clamping were tuned for a more deliberate book-like turn.
- Android phone controls now use a two-row deck instead of a horizontally clipped row, so Previous/Play/Replay/Next and Auto/Story/Book controls stay visible on narrow screens.
- These changes bring the three local implementation criteria to the premium-demo target; this still does not mean final production art, professional narration, or a physics-perfect page-curl engine exists.

## Voice And Narration Direction

- Default reader language storage was moved to `moonjar.readerLanguage.v2`, so the demo starts English-first instead of inheriting an older Korean simulator setting.
- English synthetic-draft narration exists for all 138 complete-book scenes with local macOS voices; it remains draft-only and is not production-quality narration.
- Korean narration remains optional and synthetic draft.
- Current narration is still not final or human-recorded.
- No MCP or callable production voice tool was available. Research notes:
  - OpenAI audio speech supports text-to-speech models including `gpt-4o-mini-tts`: https://platform.openai.com/docs/guides/text-to-speech
  - ElevenLabs TTS is positioned for audiobook-style emotional delivery, with voice settings for stability, similarity, style exaggeration, and speed: https://elevenlabs.io/docs/capabilities/text-to-speech
  - Resemble AI provides API-based TTS with voice UUIDs, text input, and WAV output options: https://docs.app.resemble.ai/docs/text_to_speech/
- Voice provider bakeoff report: `tools/output/voice_bakeoff_report.md`

## iOS Layout Changes

- Book cards now use stable 3:2 image frames with fit rendering, hanji-style matte backgrounds, borders, and shadows.
- Cover/detail artwork now uses `.scaledToFit` through `DemoAssetImage(..., contentMode: .fit)` instead of accidental fill/crop behavior.
- Reader scene images use fit rendering with safe padding; blurred fill is only used as decorative atmosphere behind the primary art.
- Thumbnail strip now uses fixed 3:2 cells through `ArtThumbnail`, with fit rendering, consistent selection styling, and no jumpy cell sizes.
- Real Book Mode now ties spread navigation to actual tablet/landscape layout, so a visible spread advances by spread.
- Real Book Mode pages now include page-stack edge strips and a more integrated parchment/art composition instead of a generic two-panel card.
- Page-turn sound now fires when the page turn completes, not at drag start.
- Living-scene overlays now explicitly invoke moon glow, water ripple, tiger blink/tail approximation, lantern flicker, cloud drift, sparkles, and fireflies when animation metadata matches.

## Android Layout Changes

- Reader no longer sits under the generic app top bar; it has a dark indigo storybook chrome row.
- Android reader now uses English-first narration selection unless Korean mode is selected.
- Android cards/covers use fit-based 3:2 artwork instead of `ContentScale.Crop`.
- Android portrait reader uses a large illustration area above a parchment text panel with a page-curl cue.
- Android spread mode now advances by spread when the layout is wide or Real Book Mode is enabled.
- Android Real Book Mode now renders two parchment pages with center gutter, page text, fit-rendered art, and a drag-following turn overlay.
- Android Real Book Mode now includes page-stack edge strips and a closer composition match to the iOS spread.

## Image Cropping And Alignment

- UI-level accidental cropping was removed from:
  - library cards
  - book detail covers
  - reader scene art
  - page thumbnails
  - Android covers
  - Android reader scenes
- `scaledToFill` / crop behavior is now limited to blurred decorative backgrounds, not primary illustrations.
- Validation now parses PNG dimensions and checks image assets remain inside the supported fit-safe aspect-ratio range.
- Important honest note: some generated-draft assets themselves are poorly composed, especially a few covers with subjects cut off inside the source image. The UI now shows the full bitmap, but those source assets still need regeneration/review.

## iPad Reader Status

- Landscape/tablet layout is treated as a real book spread by default.
- Real Book Mode has a visible center gutter, parchment surface, page shadows, spread navigation, and fit-rendered artwork.
- Current implementation is still an approximation, not a native physics-accurate page curl.
- The portrait simulator screenshot shows the tablet-style Real Book Mode card, not a rotated landscape device.

## Phone Reader Status

- Portrait reader uses a single-page vertical layout.
- Illustration is shown large on top with fit rendering.
- Parchment text panel sits below the art with a bottom-corner page curl cue.
- Controls and thumbnails remain below the reader card.

## Page Flip Status

- Drag follows the finger through `dragOffset` / gesture state.
- Turns require a threshold.
- Cancelled drags return via gesture reset.
- Button navigation also triggers the turn offset animation.
- iOS and Android both show a visible curl/fold sheet during the turn.
- iOS Real Book Mode shows a turning page preview over the spread.
- Page edge shadow, page thickness illusion, and gutter shadow exist.
- Page-stack edge strips now make the spread feel more like an actual book block on both platforms.
- Reduced-motion path skips the 3D turn.
- Still not final: this remains a premium approximation, not a true UIKit page-curl implementation.

## Typography And Text

- English remains the default demo reading/narration mode.
- Bilingual mode is now labeled `KO/EN` and renders Korean first with English beneath it.
- Korean typography is larger in bilingual/Korean reader views.
- English-only mode remains large and readable for the English-first demo requirement.

## Design Tokens

Shared token file:

`shared-content/design/moonjar_design_tokens.json`

Included:

- Moon ivory
- Deep indigo
- Persimmon orange
- Jade green
- Lotus pink
- Warm hanji beige
- Soft ink black
- Lantern gold
- Gold highlight
- Page edge shadow
- corner radius scale
- shadow scale
- text size scale
- spacing scale
- book/page dimensions
- thumbnail aspect ratios
- control sizes
- bedtime mode adjustments

## Screenshot-Ready Views

- `build/screenshots/visual-pass-ios-library.png`
- `build/screenshots/visual-pass-ios-reader-page-3.png`
- `build/screenshots/visual-pass-ios-real-book.png`
- `.agent/tmp/artifacts/ios-smoke-real-book-page3.png`
- `.agent/tmp/artifacts/ios-smoke-reader-playback.png`
- `.agent/tmp/artifacts/android-smoke-launch.png`

## Asset Status Honesty

- Scene art: generated draft, not final.
- Covers: generated draft, not final.
- App icon: one generated draft concept, two placeholder concepts.
- English narration: synthetic draft regenerated with macOS `Grandma (English (US))`.
- Korean narration: synthetic draft.
- Page-turn/UI/ambient/story SFX sounds: synthetic draft after this pass, not final.
- Layered animation files: not present; current animation is native overlay effects over single scene images.

## New Tool Reports

- Art review checklist: `tools/output/art_review_checklist.md`
- Art generation bakeoff report: `tools/output/art_generation_bakeoff_report.md`
- Approval job manifest: `shared-content/assets/manifests/art_approval_jobs.json`
- Voice bakeoff report: `tools/output/voice_bakeoff_report.md`
- Payments decision: `docs/payments_native_vs_revenuecat_decision.md`

## Remaining Design Gaps

- Regenerate/review cover art with no subjects cut off inside the source image.
- Replace synthetic narration with professional provider output or human-recorded narration.
- Add true landscape simulator/real-device screenshot QA.
- Implement a true native page curl if required for final polish.
- Tune Real Book Mode page composition further so art and text feel more organically integrated.
- Replace placeholder UI, page-turn, and ambient sounds.
