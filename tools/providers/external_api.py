from __future__ import annotations

import os
from pathlib import Path

from .base import ProviderResult


class ExternalAPIProvider:
    """Provider-ready adapter shell for future cloud generators.

    This class intentionally does not guess at vendor payloads. It centralizes
    the required environment and failure mode so production integration can be
    added without touching the child apps or content schema.
    """

    name = "external_api"

    def __init__(self, capability: str, key_env: str, model_env: str):
        self.capability = capability
        self.key_env = key_env
        self.model_env = model_env
        self.api_key = os.environ.get(key_env)
        self.model = os.environ.get(model_env)

    def _require_config(self) -> None:
        missing = [name for name, value in ((self.key_env, self.api_key), (self.model_env, self.model)) if not value]
        if missing:
            raise RuntimeError(f"{self.capability} provider is not configured. Missing: {', '.join(missing)}")

    def generate_image(self, prompt: str, output_file: Path, *, seed: int | None = None) -> ProviderResult:
        self._require_config()
        raise NotImplementedError("Connect the selected image API here, then write output_file and return ProviderResult.")

    def upscale_image(self, source_file: Path, output_file: Path) -> ProviderResult:
        self._require_config()
        raise NotImplementedError("Connect the selected image upscaler API here.")

    def extract_layers(self, source_file: Path, output_dir: Path, layer_plan: dict) -> ProviderResult:
        self._require_config()
        raise NotImplementedError("Connect a matting/layer extraction API here when available.")

    def synthesize_korean(self, text: str, output_file: Path) -> ProviderResult:
        self._require_config()
        raise NotImplementedError("Connect the selected Korean TTS API here.")

    def synthesize_english(self, text: str, output_file: Path) -> ProviderResult:
        self._require_config()
        raise NotImplementedError("Connect the selected English TTS API here.")

    def normalize(self, source_file: Path, output_file: Path | None = None) -> ProviderResult:
        self._require_config()
        raise NotImplementedError("Connect external mastering/normalization here.")

    def generate_or_import(self, description: str, output_file: Path, *, source_file: Path | None = None) -> ProviderResult:
        self._require_config()
        raise NotImplementedError("Connect sound-effect generation/import here.")
