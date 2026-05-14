from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    capability: str
    required_env: tuple[str, ...]
    optional_env: tuple[str, ...]
    default_model: str | None
    docs_url: str
    production_notes: str

    @property
    def configured(self) -> bool:
        return all(bool(os.environ.get(name)) for name in self.required_env)

    @property
    def missing_env(self) -> tuple[str, ...]:
        return tuple(name for name in self.required_env if not os.environ.get(name))


PROVIDER_SPECS: tuple[ProviderSpec, ...] = (
    ProviderSpec(
        name="openai_image",
        capability="image_generation",
        required_env=("OPENAI_API_KEY",),
        optional_env=("MOONJAR_OPENAI_IMAGE_MODEL", "MOONJAR_OPENAI_IMAGE_SIZE"),
        default_model="gpt-image-1",
        docs_url="https://platform.openai.com/docs/guides/image-generation",
        production_notes="Best fit for anchor images, character sheets, scene drafts, cover concepts, and edit passes.",
    ),
    ProviderSpec(
        name="adobe_firefly",
        capability="image_generation",
        required_env=("ADOBE_FIREFLY_API_KEY",),
        optional_env=("ADOBE_FIREFLY_MODEL", "ADOBE_FIREFLY_CLIENT_ID"),
        default_model="firefly-image",
        docs_url="https://developer.adobe.com/firefly-services/docs/firefly-api/guides/api/image_generation/V3/",
        production_notes="Useful commercial-safety-oriented option for image concepts and production art exploration.",
    ),
    ProviderSpec(
        name="manual_commissioned_art",
        capability="manual_import",
        required_env=(),
        optional_env=("MOONJAR_COMMISSIONED_IMPORT_ROOT",),
        default_model="human_artist",
        docs_url="docs/asset_production_pipeline.md",
        production_notes="Required path for commissioned reviewed/final production art.",
    ),
    ProviderSpec(
        name="openai_tts",
        capability="english_tts",
        required_env=("OPENAI_API_KEY",),
        optional_env=("MOONJAR_OPENAI_TTS_MODEL", "MOONJAR_OPENAI_TTS_VOICE"),
        default_model="gpt-4o-mini-tts",
        docs_url="https://platform.openai.com/docs/guides/text-to-speech",
        production_notes="Good candidate for directed English storyteller drafts; final use needs licensing and voice QA.",
    ),
    ProviderSpec(
        name="elevenlabs_tts",
        capability="english_korean_tts",
        required_env=("ELEVENLABS_API_KEY",),
        optional_env=("ELEVENLABS_EN_VOICE_ID", "ELEVENLABS_KO_VOICE_ID", "ELEVENLABS_MODEL_ID"),
        default_model="eleven_multilingual_v2",
        docs_url="https://elevenlabs.io/docs/api-reference/text-to-speech/convert",
        production_notes="Strong candidate for expressive audiobook-like English/Korean synthetic drafts.",
    ),
    ProviderSpec(
        name="naver_clova_voice",
        capability="korean_tts",
        required_env=("NAVER_CLOVA_CLIENT_ID", "NAVER_CLOVA_CLIENT_SECRET"),
        optional_env=("NAVER_CLOVA_VOICE",),
        default_model="clova_voice",
        docs_url="https://api.ncloud-docs.com/docs/ai-naver-clovavoice-ttspremium",
        production_notes="Korea-first TTS provider to evaluate for pronunciation and natural Korean rhythm.",
    ),
    ProviderSpec(
        name="google_cloud_tts",
        capability="korean_tts",
        required_env=("GOOGLE_APPLICATION_CREDENTIALS",),
        optional_env=("GOOGLE_CLOUD_TTS_VOICE", "GOOGLE_CLOUD_TTS_MODEL"),
        default_model="ko-KR neural voice",
        docs_url="https://cloud.google.com/text-to-speech/docs/voices",
        production_notes="Broad cloud TTS option; evaluate Korean warmth and child-story pacing.",
    ),
    ProviderSpec(
        name="azure_speech",
        capability="korean_tts",
        required_env=("AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"),
        optional_env=("AZURE_SPEECH_VOICE",),
        default_model="ko-KR neural voice",
        docs_url="https://learn.microsoft.com/azure/ai-services/speech-service/language-support?tabs=tts",
        production_notes="Broad cloud TTS option; evaluate pronunciation, style controls, and licensing.",
    ),
    ProviderSpec(
        name="manual_human_narrator",
        capability="manual_import",
        required_env=(),
        optional_env=("MOONJAR_HUMAN_NARRATION_IMPORT_ROOT",),
        default_model="human_recorded",
        docs_url="docs/asset_production_pipeline.md",
        production_notes="Recommended final-release path for premium bedtime storytelling.",
    ),
)


def specs_for(capability: str | None = None) -> Iterable[ProviderSpec]:
    if capability is None:
        return PROVIDER_SPECS
    return (spec for spec in PROVIDER_SPECS if capability in spec.capability)


def spec_named(name: str) -> ProviderSpec:
    for spec in PROVIDER_SPECS:
        if spec.name == name:
            return spec
    raise KeyError(f"Unknown provider spec: {name}")
