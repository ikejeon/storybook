# Moon Jar Stories Voice Bakeoff Report

Generated: 2026-05-07T15:59:28+00:00

## Execution Summary

- macOS `say` baseline available: True
- No MCP voice-generation server was discovered.
- No cloud TTS credentials were present, so OpenAI, ElevenLabs, NAVER CLOVA, Google Cloud, and Azure were not actually synthesized in this pass.
- Actual local baseline samples generated: 12.
- macOS `say` remains `synthetic_draft` only and is not acceptable as final production narration.

## Professional Provider Blocker

- MCP voice tools available: False
- Cloud credentials present: False
- Blocker: No MCP voice-generation tool and no provider credentials are configured in this environment.
- Blocked providers: openai_tts, elevenlabs_tts, naver_clova_voice, google_cloud_tts, azure_speech
- English-first provider to test next: ElevenLabs and OpenAI TTS short samples before full narration generation.
- Korean provider to test next: NAVER CLOVA Voice plus ElevenLabs/Google/Azure Korean comparison.
- Final recommendation: Use human narrator import for production final narration.

## Provider Configuration

| Provider | Capability | Configured | Missing Env | Default Model | Docs |
| --- | --- | --- | --- | --- | --- |
| openai_tts | english_tts | False | OPENAI_API_KEY | gpt-4o-mini-tts | https://platform.openai.com/docs/guides/text-to-speech |
| elevenlabs_tts | english_korean_tts | False | ELEVENLABS_API_KEY | eleven_multilingual_v2 | https://elevenlabs.io/docs/api-reference/text-to-speech/convert |
| naver_clova_voice | korean_tts | False | NAVER_CLOVA_CLIENT_ID, NAVER_CLOVA_CLIENT_SECRET | clova_voice | https://api.ncloud-docs.com/docs/ai-naver-clovavoice-ttspremium |
| google_cloud_tts | korean_tts | False | GOOGLE_APPLICATION_CREDENTIALS | ko-KR neural voice | https://cloud.google.com/text-to-speech/docs/voices |
| azure_speech | korean_tts | False | AZURE_SPEECH_KEY, AZURE_SPEECH_REGION | ko-KR neural voice | https://learn.microsoft.com/azure/ai-services/speech-service/language-support?tabs=tts |
| manual_human_narrator | manual_import | True | - | human_recorded | docs/asset_production_pipeline.md |

## Qualitative Bakeoff Matrix

| Provider | English Warmth | Korean Pronunciation | Korean Story Rhythm | Bedtime Calmness | Production Use |
| --- | --- | --- | --- | --- | --- |
| openai_tts | likely strong; needs sample review | unknown until tested | controllable with instructions; needs Korean QA | promising for calm directed delivery | possible synthetic draft/reviewed after licensing and QA |
| elevenlabs_tts | likely strongest synthetic expressiveness | promising multilingual option; must test Korean rhythm | good emotional controls; risk of overacting | strong if voice settings are restrained | possible synthetic draft/reviewed after licensing and voice QA |
| naver_clova_voice | not primary English choice | likely strong Korea-native candidate | must test child-story pacing | unknown until voice selected | possible Korean synthetic draft/reviewed after licensing and QA |
| google_cloud_tts | good but usually less characterful than premium voice products | available ko-KR voices; must test warmth | stable, less expressive | acceptable baseline | good draft baseline; final depends on review |
| azure_speech | good baseline | available ko-KR voices; must test warmth | stable with SSML/style support where available | acceptable baseline | good draft baseline; final depends on review |
| manual_human_narrator | best when cast well | best when cast with native/fluent narrator | best for folktale pacing and cultural nuance | best final option | recommended final-release path |

## Actual Local Baseline Samples

Manifest: `/Users/madmax/.openclaw/workspace-coder-ike/repos/story_book/shared-content/audio/manifests/voice_bakeoff_manifest.json`

| Provider | Language | Sample | Voice | Duration | Output | Status |
| --- | --- | --- | --- | ---: | --- | --- |
| macos_grandma_en | en | en_bedtime_closing | Grandma (English (US)) | 6.671 | `audio/synthetic-draft/voice-bakeoff/macos_grandma_en/en_bedtime_closing.wav` | synthetic_draft |
| macos_grandma_en | en | en_calm_opening | Grandma (English (US)) | 7.582 | `audio/synthetic-draft/voice-bakeoff/macos_grandma_en/en_calm_opening.wav` | synthetic_draft |
| macos_grandma_en | en | en_suspense | Grandma (English (US)) | 7.071 | `audio/synthetic-draft/voice-bakeoff/macos_grandma_en/en_suspense.wav` | synthetic_draft |
| macos_grandma_ko | ko | ko_bedtime_closing | Grandma (Korean (South Korea)) | 7.519 | `audio/synthetic-draft/voice-bakeoff/macos_grandma_ko/ko_bedtime_closing.wav` | synthetic_draft |
| macos_grandma_ko | ko | ko_calm_opening | Grandma (Korean (South Korea)) | 6.734 | `audio/synthetic-draft/voice-bakeoff/macos_grandma_ko/ko_calm_opening.wav` | synthetic_draft |
| macos_grandma_ko | ko | ko_suspense | Grandma (Korean (South Korea)) | 9.47 | `audio/synthetic-draft/voice-bakeoff/macos_grandma_ko/ko_suspense.wav` | synthetic_draft |
| macos_samantha_en | en | en_bedtime_closing | Samantha | 5.067 | `audio/synthetic-draft/voice-bakeoff/macos_samantha_en/en_bedtime_closing.wav` | synthetic_draft |
| macos_samantha_en | en | en_calm_opening | Samantha | 5.656 | `audio/synthetic-draft/voice-bakeoff/macos_samantha_en/en_calm_opening.wav` | synthetic_draft |
| macos_samantha_en | en | en_suspense | Samantha | 5.159 | `audio/synthetic-draft/voice-bakeoff/macos_samantha_en/en_suspense.wav` | synthetic_draft |
| macos_yuna_ko | ko | ko_bedtime_closing | Yuna | 4.789 | `audio/synthetic-draft/voice-bakeoff/macos_yuna_ko/ko_bedtime_closing.wav` | synthetic_draft |
| macos_yuna_ko | ko | ko_calm_opening | Yuna | 4.79 | `audio/synthetic-draft/voice-bakeoff/macos_yuna_ko/ko_calm_opening.wav` | synthetic_draft |
| macos_yuna_ko | ko | ko_suspense | Yuna | 6.509 | `audio/synthetic-draft/voice-bakeoff/macos_yuna_ko/ko_suspense.wav` | synthetic_draft |

## Required Environment Variables

- OpenAI TTS: `OPENAI_API_KEY`, optional `MOONJAR_OPENAI_TTS_MODEL`, `MOONJAR_OPENAI_TTS_VOICE`.
- ElevenLabs: `ELEVENLABS_API_KEY`, `ELEVENLABS_EN_VOICE_ID`, `ELEVENLABS_KO_VOICE_ID`, optional `ELEVENLABS_MODEL_ID`.
- NAVER CLOVA Voice: `NAVER_CLOVA_CLIENT_ID`, `NAVER_CLOVA_CLIENT_SECRET`, optional `NAVER_CLOVA_VOICE`.
- Google Cloud TTS: `GOOGLE_APPLICATION_CREDENTIALS`, optional `GOOGLE_CLOUD_TTS_VOICE`.
- Azure Speech: `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, optional `AZURE_SPEECH_VOICE`.

## Current Recommendation

- Best English synthetic draft candidate to test first: ElevenLabs, with OpenAI TTS as the close second because directed delivery may be useful for calm storyteller tone.
- Best Korean synthetic draft candidate to test first: NAVER CLOVA Voice, with ElevenLabs/Google/Azure as bakeoff comparisons.
- Human narration is still recommended for final release because this is a premium kids bedtime/story product where warmth, pacing, pronunciation, and trust matter more than automation speed.
- Synthetic narration may be used for internal iteration, investor demos, and reviewed synthetic draft only after licensing and reviewer signoff.
