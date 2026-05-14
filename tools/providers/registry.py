from __future__ import annotations

from .external_api import ExternalAPIProvider
from .macos_say import MacOSSayAudioProvider
from .placeholder import PlaceholderImageProvider, PlaceholderSoundProvider
from .provider_ready import ProviderReadyAdapter
from .vendor_specs import spec_named


def get_image_provider(name: str, **kwargs):
    if name == "placeholder":
        return PlaceholderImageProvider(**kwargs)
    if name == "openai_image":
        return ProviderReadyAdapter(spec_named("openai_image"))
    if name == "adobe_firefly":
        return ProviderReadyAdapter(spec_named("adobe_firefly"))
    if name == "manual_commissioned_art":
        return ProviderReadyAdapter(spec_named("manual_commissioned_art"))
    if name == "external_api":
        return ExternalAPIProvider("image_generation", "MOONJAR_IMAGE_API_KEY", "MOONJAR_IMAGE_MODEL")
    if name == "external_upscale":
        return ExternalAPIProvider("image_upscaling", "MOONJAR_UPSCALE_API_KEY", "MOONJAR_UPSCALE_MODEL")
    if name == "external_layer_extraction":
        return ExternalAPIProvider("image_layer_extraction", "MOONJAR_LAYER_API_KEY", "MOONJAR_LAYER_MODEL")
    raise ValueError(f"Unknown image provider: {name}")


def get_audio_provider(name: str, **kwargs):
    if name == "macos_say":
        return MacOSSayAudioProvider(**kwargs)
    if name in {"openai_tts", "elevenlabs_tts", "naver_clova_voice", "google_cloud_tts", "azure_speech", "manual_human_narrator"}:
        return ProviderReadyAdapter(spec_named(name))
    if name == "external_korean_tts":
        return ExternalAPIProvider("korean_tts", "MOONJAR_KO_TTS_API_KEY", "MOONJAR_KO_TTS_MODEL")
    if name == "external_english_tts":
        return ExternalAPIProvider("english_tts", "MOONJAR_EN_TTS_API_KEY", "MOONJAR_EN_TTS_MODEL")
    if name == "external_audio_mastering":
        return ExternalAPIProvider("audio_mastering", "MOONJAR_AUDIO_MASTERING_API_KEY", "MOONJAR_AUDIO_MASTERING_MODEL")
    raise ValueError(f"Unknown audio provider: {name}")


def get_sound_provider(name: str, **kwargs):
    if name == "placeholder":
        return PlaceholderSoundProvider()
    if name in {"manual_human_narrator", "elevenlabs_tts", "openai_tts"}:
        return ProviderReadyAdapter(spec_named(name))
    if name == "external_sfx":
        return ExternalAPIProvider("sound_effect_generation", "MOONJAR_SFX_API_KEY", "MOONJAR_SFX_MODEL")
    raise ValueError(f"Unknown sound provider: {name}")
