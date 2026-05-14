# Reader Polish 95 Pass

> Historical/non-evidence for current scoring: this ExecPlan is a prior repo-local work record, not positive evidence for current scores unless current manifests, source, command output, screenshots, test results, or external review artifacts independently verify the claim.

## Purpose / Big Picture

Bring Reader UX, Real Book Mode, and Page flip to a conservative 95-level demo experience without changing narration quality or claiming final production readiness. The work should make the native readers feel more like a premium living picture book: tactile pages, clearer book-object depth, better reading comfort, and stronger turn feedback on iOS and Android.

## Progress

- [x] Ran `scripts/agent/doctor`.
- [x] Inspected iOS `Views.swift` reader surfaces and Android `MoonJarApp.kt` reader surfaces.
- [x] Improve iOS portrait reader, Real Book Mode, and page-turn visuals.
- [x] Improve Android portrait reader, Real Book Mode, and page-turn visuals.
- [x] Update scoring/report checks if the new product details should be guarded.
- [x] Run required validation, including UI validation or exact simulator/emulator blocker.

## Surprises & Discoveries

- Existing repo-local scorer already reports Reader UX, Real Book Mode, and Page flip at 100/100, but the user's requested conservative score asks for actual experience polish rather than just score text.
- Voice quality is explicitly out of scope; narration controls may remain, but no voice asset/provider work should happen in this pass.
- The best repo-local lift is code-native tactile polish because final art/audio assets are still external blockers.

## Decision Log

- Keep shared story/content unchanged unless UI validation reveals a content-layout problem.
- Avoid new dependencies; use native SwiftUI and Compose drawing primitives.
- Preserve existing smoke hooks because they are part of the repo's app-feedback loop.
- Improve both platforms for parity: portrait reading comfort, Real Book Mode object depth, and page-turn/curl cues.
- Add scorer checks for the new tactile page depth, folio marks, book-object backing, and curl depth primitives so future changes cannot silently drop them.

## Outcomes & Retrospective

Completed on 2026-05-09. Reader UX, Real Book Mode, and Page flip were improved without touching voice assets or narration quality. iOS gained tactile page depth, richer parchment grain, folio marks, book-board backing, top/bottom page thickness, and more detailed curl/crease handling. Android gained parity page depth, folio marks, vocabulary chips, book-object backing, and richer curl grain/rib details.

Validation passed:

- `python3 tools/validate_books.py`
- `python3 tools/validate_story_quality.py`
- `python3 tools/validate_cultural_authenticity.py`
- `python3 tools/score_reader_experience.py`
- `scripts/agent/validate`
- `scripts/agent/validate-ui`

Artifact-backed reader scoring passed with Reader UX, Real Book Mode, and Page flip at 100/100. This supports a conservative 95 product score for those areas, while final production feel still depends on final art and final sound/voice assets.

## Context and Orientation

- iOS reader implementation: `ios/MoonJarStoriesiOS/Sources/MoonJarStoriesiOS/Views.swift`.
- Android reader implementation: `android/MoonJarStoriesAndroid/src/main/java/com/moonjar/stories/ui/MoonJarApp.kt`.
- Reader score gate: `tools/score_reader_experience.py`.
- UI/smoke validation command: `scripts/agent/validate-ui`.
- Product truth remains: final art, final narration, final sound design, store setup, backend/CMS, and legal/privacy review are production blockers.

## Plan of Work

1. Add tactile page details to the portrait reader: page thickness, safer text panel hierarchy, vocabulary/interaction affordance polish, and stronger but restrained paper texture.
2. Upgrade Real Book Mode as a book object: cloth cover/board shadow, page stack, gutter depth, folio/page numbers, and better spread lighting.
3. Improve page flip: stronger curl sheet, crease/ribbing, under-page shadow, drag threshold feedback, and reduced-motion-safe fallback.
4. Mirror the meaningful details in Android Compose.
5. Tighten scorer checks for the new details so future regressions are caught.
6. Run validation.

## Concrete Steps

- Patch iOS `Views.swift`.
- Patch Android `MoonJarApp.kt`.
- Patch `tools/score_reader_experience.py` only if new details are practical to guard mechanically.
- Run content/story/cultural/reader validators and `scripts/agent/validate`.
- Run `scripts/agent/validate-ui` for this UI change, or record the exact simulator/emulator blocker.

## Validation and Acceptance

Accepted when:

- Reader score remains at least 95.
- Native build/tests pass through `scripts/agent/validate`.
- UI validation passes, or the exact unavailable simulator/emulator/device blocker is documented.
- Product caveats remain honest: no claim of final art, professional voice, final sound, production backend, or store readiness.

## Idempotence and Recovery

- Changes are code-only except generated reports from validators.
- Re-running validators should be safe and deterministic.
- If iOS bundled shared-content drift appears, rerun the documented `rsync` command from the cultural/reader ExecPlan.
- If smoke artifacts become stale, rerun `scripts/agent/smoke ios` and `scripts/agent/smoke android`.
