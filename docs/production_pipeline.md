# Production Pipeline

## Story Production Flow

1. Select folktale and sensitivity lane.
2. Write child-safe Korean retelling.
3. Create English translation.
4. Add vocabulary and pronunciation targets.
5. Build character bible.
6. Write page-level image prompts.
7. Write narration and ambience prompts.
8. Define animation metadata.
9. Complete cultural and sensitivity review.
10. Export approved JSON to `shared-content/books`.

## Asset Flow

1. Generate or commission cover art.
2. Generate page scene art from the character bible and page prompt.
3. Split approved art into layers where motion is needed.
4. Export platform-friendly formats.
5. Place canonical scene images in `shared-content/assets/images/scenes`.
6. Place canonical cover images in `shared-content/assets/images/covers`.
7. Update `shared-content/assets/manifests/image_manifest.json`.
8. Mark each image as `placeholder`, `generated_draft`, `generated_reviewed`, or `commissioned_final`.
9. Let platform builds copy or download the shared assets.

## Audio Flow

1. Record Korean narrator.
2. Produce page-level files.
3. Add optional ambience loops.
4. Add tap-word pronunciation clips.
5. Normalize loudness for bedtime-safe playback.
6. Place canonical narration in `shared-content/audio/narration`.
7. Update `shared-content/audio/manifests/audio_manifest.json`.
8. Mark each narration file as `placeholder`, `synthetic_draft`, `synthetic_reviewed`, or `human_recorded_final`.

## Offline Generation Rule

No image, TTS, sound-effect, or upscaling generation should run inside the child app. Generation happens only in development, CMS, or production tooling. The apps load local packaged or downloaded assets from the paths in shared content JSON.

See `docs/asset_production_pipeline.md` for the current scripts, manifests, status labels, and tool-discovery notes.

## QA

- Validate JSON with `tools/validate_books.py`.
- Confirm all complete books have 20-40 pages.
- Confirm no missing narration, image prompt, audio prompt, or animation metadata.
- Check native reader on phone and tablet sizes.
- Check reduced motion / bedtime settings.
- Check parent gate before every purchase path.
