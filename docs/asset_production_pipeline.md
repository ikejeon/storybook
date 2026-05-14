# Moon Jar Stories Asset Production Pipeline

Asset generation is an offline/dev-time process. The child app must never call image, TTS, sound-effect, or upscaling generators at runtime. Native apps load only local packaged assets or assets downloaded through a controlled content delivery path.

## Tool Discovery

Current environment:

| Capability | Available now | Notes |
| --- | --- | --- |
| MCP image generation | No | No generation MCP tools are exposed in this thread. |
| Built-in image generation | Yes | Used for generated-draft storyboard sheets and cropped scene drafts. Not available to the child app at runtime. |
| Cloud image generation API | No | No image-provider API keys are configured. |
| TTS narration | Yes | macOS `say` is available with Korean voices. |
| Sound effect generation | No | Existing placeholder WAVs are kept. |
| Image upscaling | No | `sips` can resize/convert, but it is not AI upscaling. |
| Audio normalization | Yes | `tools/generate_production_audio.py` applies simple WAV peak normalization. |
| File management | Yes | Local filesystem and Python scripts. |

## Status Labels

Images:

- `placeholder`
- `generated_draft`
- `generated_reviewed`
- `commissioned_draft`
- `commissioned_reviewed`
- `commissioned_final`
- `rejected`

Audio:

- `placeholder`
- `synthetic_draft`
- `synthetic_reviewed`
- `human_recorded_draft`
- `human_recorded_reviewed`
- `human_recorded_final`
- `rejected`

Validation fails if placeholder or synthetic assets are marked as production-ready final assets.

## Character Consistency

Production character bibles live in:

```text
shared-content/characters/
```

The index is:

```text
shared-content/characters/index.json
```

Each complete book has:

- character sheet prompt
- main character descriptions
- outfit and color rules
- style rules
- forbidden visual elements
- scene-to-scene continuity notes
- prompt prefix for scene generation

Scene image prompts should always include the matching character bible path.

## Image Pipeline

Prompt export:

```bash
python3 tools/generate_image_prompts.py
```

Image staging / manifest:

```bash
python3 tools/generate_production_images.py --stage-placeholders
```

Current output folders:

```text
shared-content/assets/placeholders/
shared-content/assets/generated-draft/
shared-content/assets/reviewed/
shared-content/assets/final/
shared-content/assets/manifests/
```

Manifest:

```text
shared-content/assets/manifests/image_manifest.json
```

Current generated-draft art was produced offline. The free stories use imported generated-review raster scenes. The 19 premium stories use built-in image generation six-panel story sheets stored in `shared-content/assets/generated-draft/images/story-sheets/`, then `tools/import_imagegen_premium_sheets.py` crops/imports those panels into runtime cover and scene PNGs. These premium runtime assets are `generated_reviewed` for internal demo use, but they are not commissioned/final production art.

Refresh premium story-sheet imports and guard against drift:

```bash
python3 tools/import_imagegen_premium_sheets.py
python3 tools/validate_premium_imagegen_sheets.py
```

Future provider adapters or commissioned art imports should write real outputs into the status-specific folders and update manifest candidates to `generated_draft`, `generated_reviewed`, `commissioned_draft`, `commissioned_reviewed`, then `commissioned_final` only after review.

### Sun and Moon Tiger Anchor Gate

The tiger direction for `해님 달님 / The Sun and the Moon` has been revised. The tiger is a deceptive antagonist: cunning, hungry, watchful, and dangerous through eyes, posture, shadow, framing, and lighting, while still child-safe. He should not be cute, plush-like, goofy, pet-like, or friendly.

Before bulk-regenerating all 20 Sun and Moon scenes, generate 3-5 anchor images for approval:

```text
shared-content/assets/manifests/sun_moon_tiger_anchor_plan.json
```

Anchor pages:

- Page 3: mysterious forest presence
- Page 4: deceptive and watchful
- Page 7: disguised/pretending at the house, unsettling
- Page 11: threatening chase posture, child-safe
- Page 16: defeated/resolved without graphic punishment

Bulk generation for Sun and Moon should remain blocked until those anchors are reviewed for antagonist tone, cultural fit, child safety, and continuity.

## Layered Animation Plan

Layer manifest:

```bash
python3 tools/build_layer_manifest.py
```

Output:

```text
shared-content/animation/layer_manifest.json
```

Each scene currently uses one full-scene image. The manifest defines future production layers:

- background
- midground
- character
- foreground
- effect
- particle/glow

Native apps can keep using single images until layered image assets exist.

## Audio Pipeline

Prompt export:

```bash
python3 tools/generate_audio_prompts.py
```

Generate English synthetic-draft narration for the default demo experience:

```bash
python3 tools/generate_audio.py --provider macos_say --languages en --english-voice Samantha --rate 145
```

Generate optional Korean synthetic-draft narration:

```bash
python3 tools/generate_audio.py --provider macos_say --languages ko --voice "Grandma (Korean (South Korea))" --rate 155
```

Narration output:

```text
shared-content/audio/synthetic-draft/narration/
```

Manifest:

```text
shared-content/audio/manifests/audio_manifest.json
```

The current narration is useful for timing and demos, but production release should replace it with reviewed synthetic narration or human-recorded narration. Final production audio should use `human_recorded_final`.

## Validation

Run:

```bash
python3 tools/validate_books.py
```

Validation checks:

- all complete books load
- scene image files exist
- narration audio files exist
- image/audio prompts exist
- animation types are registered in the layer manifest
- cover images exist
- character bibles exist
- image/audio manifests are valid
- placeholder assets are not marked as reviewed/final
- premium catalog books remain locked in mock entitlement mode

## Manual Steps Remaining

- Connect a real image generator or commission final art.
- Review generated drafts for cultural accuracy, safety, composition, and continuity.
- Split final art into animation layers where needed.
- Record or approve final English narration, and final Korean narration if Korean audio remains in the launch scope.
- Create real ambient loops and UI sounds.
- Perform loudness, accessibility, device, and app-store compliance QA.
