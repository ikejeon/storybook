# Premium Product Push Report

Generated: 2026-05-07

## What Moved Forward

- The Sun and Moon approval anchors are now `generated_reviewed` for generated-draft bulk regeneration.
- The tiger direction uses `tiger-character-sheet-v2.png` as the approved draft antagonist reference.
- Bulk Sun and Moon draft regeneration is now unblocked in the art manifests, but final approval remains blocked.
- Local voice bakeoff samples were regenerated and normalized to a consistent draft peak level.
- Voice provider status is explicit: no MCP voice tool and no cloud provider credentials are configured.
- Page-turn sound and procedural ambient/SFX drafts were refreshed.
- iOS page turning now clamps drag offset and uses predicted drag velocity for more natural release thresholds.
- iOS page curl overlay now has stronger paper fold, edge shadow, paper grain lines, and depth cues.
- Android button/autoplay navigation now uses the same visual turn offset path as swipe navigation, so button turns feel less like hard cuts.

## Still Not Final

- No scene art is commissioned final.
- No narration is human-recorded final.
- No professional cloud TTS samples were generated because credentials are absent.
- No final page-turn/UI/ambient sounds are present.
- No true native page curl has been implemented.
- No production store screenshots/app icon have been final-reviewed.

## Key Paths

- Anchor contact sheet: `build/screenshots/sun-moon-anchor-review-contact-sheet.png`
- Anchor approval report: `tools/output/sun_moon_anchor_approval_report.md`
- Image manifest: `shared-content/assets/manifests/image_manifest.json`
- Tiger anchor plan: `shared-content/assets/manifests/sun_moon_tiger_anchor_plan.json`
- Voice bakeoff manifest: `shared-content/audio/manifests/voice_bakeoff_manifest.json`
- Voice bakeoff report: `tools/output/voice_bakeoff_report.md`

## Next Production Move

Add credentials for at least one English voice provider and one Korean voice provider, then generate short voice samples before any full narration pass:

- English: ElevenLabs and OpenAI TTS
- Korean: NAVER CLOVA Voice plus ElevenLabs/Google/Azure comparison

For art, regenerate the Sun and Moon scene set from the approved anchors, keep status as `generated_draft`, then run human creative/cultural/child-safety review before any final promotion.
