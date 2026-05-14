# Fairy Woodcutter Authenticity Fix

## Purpose / Big Picture

Correct `선녀와 나무꾼 / The Fairy and the Woodcutter` so the book does not visually or textually flatten the folktale into a cheerful “kind choice” story. The user flagged that the generated sheet shows a happy ascent and misses the core beats: the woodcutter hides the fairy's wing robe, is warned not to reveal it until after three children, reveals it too early, and the fairy returns to the sky carrying the children.

## Progress

- [x] Confirmed `shared-content/books/fairy_woodcutter.json` repeats generic “respectful choice” copy across all 32 pages.
- [x] Confirmed the current six-panel sheet is too cheerful for the story's consequence/longing beats.
- [x] Rewrite the story JSON, page metadata, image prompts, and audio manifest text for this book.
- [x] Replace the fairy-and-woodcutter story sheet and re-import runtime panels.
- [x] Run repo validation.

## Surprises & Discoveries

- The problem is not isolated to the image. The current book text repeats the same softened beat on every page, so art-only replacement would still leave the reader experience inaccurate.

## Decision Log

- Keep the story child-safe but honest: name the robe-hiding as a wrong choice, preserve the “three children” warning, and make the sky-return and later ascent bittersweet instead of triumphant.
- Do not claim external cultural review or final production approval; this remains internal generated/demo work.

## Outcomes & Retrospective

Completed. The book now preserves the core folktale beats the user flagged: the woodcutter hides the fairy's wing robe, receives the warning not to reveal it until after three children, reveals it before the third child, the fairy returns to the sky holding one child in each arm, and the later ascent is shown as longing/consequence rather than celebration.

Implementation evidence:

- Added `tools/repair_fairy_woodcutter_authenticity.py`.
- Updated `shared-content/books/fairy_woodcutter.json` with 32 repaired bilingual pages, storyBeat metadata, vocabulary, image prompts, and child-safe moral framing.
- Updated `shared-content/audio/manifests/audio_manifest.json` narration text for this story's 64 synthetic-draft entries.
- Replaced `shared-content/assets/generated-draft/images/story-sheets/fairy-and-woodcutter.png` with a six-panel bittersweet sheet.
- Updated `tools/import_imagegen_premium_sheets.py` and `tools/validate_premium_imagegen_sheets.py` with a story-specific panel mapping so major pages do not cycle into mismatched art.
- Re-imported runtime panels and verified page 3 maps to the hidden-robe panel, page 15 maps to the one-child-in-each-arm departure panel, and pages 17-32 map to the ascent/rooster consequence panel.

Validation evidence:

- `python3 tools/repair_fairy_woodcutter_authenticity.py`: passed.
- `python3 tools/import_imagegen_premium_sheets.py`: passed.
- `python3 tools/validate_premium_imagegen_sheets.py`: passed.
- `python3 tools/validate_books.py`: passed.
- `python3 tools/validate_story_quality.py`: passed.
- `python3 tools/validate_all_story_standard.py`: passed.
- `python3 tools/validate_cultural_authenticity.py`: passed for internal demo review only.
- `scripts/agent/validate`: passed, including SwiftPM build/tests and Android Gradle test/assemble.

## Context and Orientation

- Book JSON: `shared-content/books/fairy_woodcutter.json`
- Sheet source: `shared-content/assets/generated-draft/images/story-sheets/fairy-and-woodcutter.png`
- Runtime panels: `shared-content/assets/generated-draft/images/scenes/fairy-and-woodcutter/`
- Importer: `tools/import_imagegen_premium_sheets.py`

## Plan of Work

1. Add a repeatable repair script for the book JSON and audio manifest text.
2. Generate a replacement six-panel sheet with sober, culturally faithful scenes.
3. Re-run the premium sheet importer so cover and page images update consistently.
4. Sync shared content into iOS resources if validation reports drift.
5. Run focused validators, then `scripts/agent/validate`.

## Concrete Steps

- Update story copy, `storyBeat`, vocabulary, prompts, and metadata for all 32 pages.
- Update narration manifest text for English and Korean entries for this story.
- Replace the generated sheet image.
- Regenerate imported runtime panels and reports.
- Inspect the resulting contact sheet and at least a few page assets.

## Validation and Acceptance

- `python3 tools/repair_fairy_woodcutter_authenticity.py`
- `python3 tools/import_imagegen_premium_sheets.py`
- `python3 tools/validate_books.py`
- `python3 tools/validate_story_quality.py`
- `python3 tools/validate_all_story_standard.py`
- `python3 tools/validate_premium_imagegen_sheets.py`
- `scripts/agent/validate`

Acceptance: the story and art no longer depict the key ascent/return beats as purely happy, and all repo checks pass.

## Idempotence and Recovery

The repair script should be safe to re-run. Old generated sheets can be recovered from prior `.agent/tmp/` backups if needed. Runtime panels are derived from the single story-sheet source through `tools/import_imagegen_premium_sheets.py`.
