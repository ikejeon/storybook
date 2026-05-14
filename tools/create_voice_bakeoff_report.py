#!/usr/bin/env python3
from __future__ import annotations

import shutil
import json
from collections import Counter
from pathlib import Path

from asset_pipeline_common import AUDIO, utc_now
from providers.vendor_specs import PROVIDER_SPECS

REPORT = Path("tools/output/voice_bakeoff_report.md")
SAMPLE_MANIFEST = AUDIO / "manifests" / "voice_bakeoff_manifest.json"


def row_for(spec) -> dict:
    return {
        "provider": spec.name,
        "capability": spec.capability,
        "configured": spec.configured,
        "missing": ", ".join(spec.missing_env) if spec.missing_env else "-",
        "model": spec.default_model or "-",
        "docs": spec.docs_url,
        "notes": spec.production_notes,
    }


def qualitative_scores(provider: str) -> dict[str, str]:
    scores = {
        "openai_tts": {
            "englishWarmth": "likely strong; needs sample review",
            "koreanPronunciation": "unknown until tested",
            "rhythm": "controllable with instructions; needs Korean QA",
            "bedtime": "promising for calm directed delivery",
            "productionUse": "possible synthetic draft/reviewed after licensing and QA",
        },
        "elevenlabs_tts": {
            "englishWarmth": "likely strongest synthetic expressiveness",
            "koreanPronunciation": "promising multilingual option; must test Korean rhythm",
            "rhythm": "good emotional controls; risk of overacting",
            "bedtime": "strong if voice settings are restrained",
            "productionUse": "possible synthetic draft/reviewed after licensing and voice QA",
        },
        "naver_clova_voice": {
            "englishWarmth": "not primary English choice",
            "koreanPronunciation": "likely strong Korea-native candidate",
            "rhythm": "must test child-story pacing",
            "bedtime": "unknown until voice selected",
            "productionUse": "possible Korean synthetic draft/reviewed after licensing and QA",
        },
        "google_cloud_tts": {
            "englishWarmth": "good but usually less characterful than premium voice products",
            "koreanPronunciation": "available ko-KR voices; must test warmth",
            "rhythm": "stable, less expressive",
            "bedtime": "acceptable baseline",
            "productionUse": "good draft baseline; final depends on review",
        },
        "azure_speech": {
            "englishWarmth": "good baseline",
            "koreanPronunciation": "available ko-KR voices; must test warmth",
            "rhythm": "stable with SSML/style support where available",
            "bedtime": "acceptable baseline",
            "productionUse": "good draft baseline; final depends on review",
        },
        "manual_human_narrator": {
            "englishWarmth": "best when cast well",
            "koreanPronunciation": "best when cast with native/fluent narrator",
            "rhythm": "best for folktale pacing and cultural nuance",
            "bedtime": "best final option",
            "productionUse": "recommended final-release path",
        },
    }
    return scores.get(
        provider,
        {
            "englishWarmth": "not evaluated",
            "koreanPronunciation": "not evaluated",
            "rhythm": "not evaluated",
            "bedtime": "not evaluated",
            "productionUse": "not evaluated",
        },
    )


def main() -> int:
    rows = [row_for(spec) for spec in PROVIDER_SPECS if "tts" in spec.capability or spec.name == "manual_human_narrator"]
    macos_say_available = shutil.which("say") is not None and shutil.which("afconvert") is not None
    sample_manifest = json.loads(SAMPLE_MANIFEST.read_text(encoding="utf-8")) if SAMPLE_MANIFEST.exists() else {"entries": []}
    sample_entries = sample_manifest.get("entries", [])
    sample_counts = Counter(entry.get("provider", "unknown") for entry in sample_entries)
    professional_status = sample_manifest.get("professionalProviderStatus", {})

    lines = [
        "# Moon Jar Stories Voice Bakeoff Report",
        "",
        f"Generated: {utc_now()}",
        "",
        "## Execution Summary",
        "",
        f"- macOS `say` baseline available: {macos_say_available}",
        "- No MCP voice-generation server was discovered.",
        "- No cloud TTS credentials were present, so OpenAI, ElevenLabs, NAVER CLOVA, Google Cloud, and Azure were not actually synthesized in this pass.",
        f"- Actual local baseline samples generated: {sum(sample_counts.values())}.",
        "- macOS `say` remains `synthetic_draft` only and is not acceptable as final production narration.",
        "",
    ]
    if professional_status:
        lines.extend(
            [
                "## Professional Provider Blocker",
                "",
                f"- MCP voice tools available: {professional_status.get('mcpVoiceToolsAvailable')}",
                f"- Cloud credentials present: {professional_status.get('cloudCredentialsPresent')}",
                f"- Blocker: {professional_status.get('blocker')}",
                f"- Blocked providers: {', '.join(professional_status.get('blockedProviders', []))}",
                f"- English-first provider to test next: {professional_status.get('recommendedEnglishFirstTest')}",
                f"- Korean provider to test next: {professional_status.get('recommendedKoreanFirstTest')}",
                f"- Final recommendation: {professional_status.get('finalRecommendation')}",
                "",
            ]
        )

    lines.extend([
        "## Provider Configuration",
        "",
        "| Provider | Capability | Configured | Missing Env | Default Model | Docs |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for row in rows:
        lines.append(
            f"| {row['provider']} | {row['capability']} | {row['configured']} | {row['missing']} | {row['model']} | {row['docs']} |"
        )

    lines.extend(
        [
            "",
            "## Qualitative Bakeoff Matrix",
            "",
            "| Provider | English Warmth | Korean Pronunciation | Korean Story Rhythm | Bedtime Calmness | Production Use |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        scores = qualitative_scores(row["provider"])
        lines.append(
            f"| {row['provider']} | {scores['englishWarmth']} | {scores['koreanPronunciation']} | {scores['rhythm']} | {scores['bedtime']} | {scores['productionUse']} |"
        )

    lines.extend(
        [
            "",
            "## Actual Local Baseline Samples",
            "",
            f"Manifest: `{SAMPLE_MANIFEST}`" if SAMPLE_MANIFEST.exists() else "Manifest: not generated yet.",
            "",
            "| Provider | Language | Sample | Voice | Duration | Output | Status |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for entry in sorted(sample_entries, key=lambda item: (item.get("provider", ""), item.get("sampleId", ""))):
        lines.append(
            f"| {entry.get('provider')} | {entry.get('language')} | {entry.get('sampleId')} | "
            f"{entry.get('voice') or '-'} | {entry.get('duration') or 0} | `{entry.get('outputFile')}` | {entry.get('status')} |"
        )

    lines.extend(
        [
            "",
            "## Required Environment Variables",
            "",
            "- OpenAI TTS: `OPENAI_API_KEY`, optional `MOONJAR_OPENAI_TTS_MODEL`, `MOONJAR_OPENAI_TTS_VOICE`.",
            "- ElevenLabs: `ELEVENLABS_API_KEY`, `ELEVENLABS_EN_VOICE_ID`, `ELEVENLABS_KO_VOICE_ID`, optional `ELEVENLABS_MODEL_ID`.",
            "- NAVER CLOVA Voice: `NAVER_CLOVA_CLIENT_ID`, `NAVER_CLOVA_CLIENT_SECRET`, optional `NAVER_CLOVA_VOICE`.",
            "- Google Cloud TTS: `GOOGLE_APPLICATION_CREDENTIALS`, optional `GOOGLE_CLOUD_TTS_VOICE`.",
            "- Azure Speech: `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, optional `AZURE_SPEECH_VOICE`.",
            "",
            "## Current Recommendation",
            "",
            "- Best English synthetic draft candidate to test first: ElevenLabs, with OpenAI TTS as the close second because directed delivery may be useful for calm storyteller tone.",
            "- Best Korean synthetic draft candidate to test first: NAVER CLOVA Voice, with ElevenLabs/Google/Azure as bakeoff comparisons.",
            "- Human narration is still recommended for final release because this is a premium kids bedtime/story product where warmth, pacing, pronunciation, and trust matter more than automation speed.",
            "- Synthetic narration may be used for internal iteration, investor demos, and reviewed synthetic draft only after licensing and reviewer signoff.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
