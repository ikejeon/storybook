from __future__ import annotations

from pathlib import Path

from .base import ProviderResult
from .vendor_specs import ProviderSpec


class ProviderNotConfigured(RuntimeError):
    pass


class ProviderReadyAdapter:
    """Provider adapter shell for offline/dev-time production pipelines.

    These adapters intentionally fail closed when credentials are missing.
    They make provider selection explicit without letting the child app depend
    on live generation services.
    """

    def __init__(self, spec: ProviderSpec):
        self.spec = spec
        self.name = spec.name

    def require_config(self) -> None:
        if not self.spec.configured:
            missing = ", ".join(self.spec.missing_env)
            raise ProviderNotConfigured(f"{self.spec.name} is not configured. Missing: {missing}")

    def generate_image(self, prompt: str, output_file: Path, *, seed: int | None = None) -> ProviderResult:
        self.require_config()
        raise NotImplementedError(
            f"Connect {self.spec.name} image API here. Docs: {self.spec.docs_url}. "
            "Generation must run offline/dev-time and write output_file."
        )

    def upscale_image(self, source_file: Path, output_file: Path) -> ProviderResult:
        self.require_config()
        raise NotImplementedError(
            f"Connect {self.spec.name} upscaling API here if supported. Source: {source_file}."
        )

    def extract_layers(self, source_file: Path, output_dir: Path, layer_plan: dict) -> ProviderResult:
        self.require_config()
        raise NotImplementedError(
            f"Connect {self.spec.name} layer extraction/matting API here if supported. Source: {source_file}."
        )

    def synthesize_korean(self, text: str, output_file: Path) -> ProviderResult:
        self.require_config()
        raise NotImplementedError(
            f"Connect {self.spec.name} Korean TTS API here. Docs: {self.spec.docs_url}."
        )

    def synthesize_english(self, text: str, output_file: Path) -> ProviderResult:
        self.require_config()
        raise NotImplementedError(
            f"Connect {self.spec.name} English TTS API here. Docs: {self.spec.docs_url}."
        )

    def normalize(self, source_file: Path, output_file: Path | None = None) -> ProviderResult:
        self.require_config()
        raise NotImplementedError(f"Connect {self.spec.name} normalization/mastering API here.")

    def generate_or_import(self, description: str, output_file: Path, *, source_file: Path | None = None) -> ProviderResult:
        self.require_config()
        raise NotImplementedError(f"Connect {self.spec.name} sound-effect generation/import API here.")
