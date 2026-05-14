# Moon Jar Stories Art Generation Bakeoff Report

Generated: 2026-05-11T01:56:13+00:00

## Tool Availability

No MCP image-generation server was discovered in this environment. No OpenAI or Adobe Firefly API credentials were present in environment variables, so no provider API generation was executed by this script.

| Provider | Capability | Configured | Missing Env | Default Model | Status |
| --- | --- | --- | --- | --- | --- |
| openai_image | image_generation | False | OPENAI_API_KEY | gpt-image-1 | blocked |
| adobe_firefly | image_generation | False | ADOBE_FIREFLY_API_KEY | firefly-image | blocked |
| manual_commissioned_art | manual_import | True | - | human_artist | ready |

## Approval-First Jobs

These jobs are the required approval set. Bulk regeneration of the full 138-scene launch set should stay blocked until the anchor set is reviewed. The first approved bulk pass should be The Sun and the Moon only (32 scenes).

| Job | Provider | Output | Status | Review Focus |
| --- | --- | --- | --- | --- |
| sun_moon_app_hero_style | built_in_image_gen | `assets/generated-draft/images/approval/sun-and-moon/app-hero-style.png` | generated_reviewed | Validate overall product mood before any bulk scene work. |
| sun_moon_cover_concept | built_in_image_gen | `assets/generated-draft/images/approval/sun-and-moon/cover-concept.png` | generated_reviewed | Reject if the tiger dominates like horror art or if faces/subjects are cropped. |
| sun_moon_tiger_character_sheet | built_in_image_gen | `assets/generated-draft/images/approval/sun-and-moon/tiger-character-sheet.png` | generated_reviewed | Primary approval gate for tiger tone and continuity. |
| sun_moon_child_character_sheet | built_in_image_gen | `assets/generated-draft/images/approval/sun-and-moon/child-character-sheet.png` | generated_reviewed | Approve before scenes with children are regenerated. |
| sun_moon_forest_scene | built_in_image_gen | `assets/generated-draft/images/approval/sun-and-moon/forest-scene.png` | generated_reviewed | Mysterious forest presence with mature watchful tiger tone. |
| sun_moon_house_night_scene | built_in_image_gen | `assets/generated-draft/images/approval/sun-and-moon/house-night-scene.png` | generated_reviewed | Unsettling disguised-at-door moment, child-safe. |
| sun_moon_chase_tension_scene | built_in_image_gen | `assets/generated-draft/images/approval/sun-and-moon/chase-tension-scene.png` | generated_reviewed | Threatening chase posture without gore or horror framing. |

## Current Recommendation

- Use OpenAI GPT Image models first for the seven anchor images and edit loops because they fit character-sheet, scene-draft, and cover-concept workflows.
- Evaluate Adobe Firefly as the commercial-safety-oriented comparison provider once credentials are available.
- Do not mix providers inside the same book unless the approved style packet is locked and prompts reference the same character bible.
- Commissioned/manual import remains the final production path for assets marked `commissioned_final`.
