from __future__ import annotations

import shutil
from pathlib import Path

from .base import ProviderResult


class ManualImportProvider:
    name = "manual_import"

    def import_image(self, source_file: Path, output_file: Path, status: str = "commissioned_draft") -> ProviderResult:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, output_file)
        return ProviderResult(
            output_file=output_file,
            status=status,
            provider=self.name,
            model="commissioned_asset",
            generation_status="imported",
        )

    def import_audio(self, source_file: Path, output_file: Path, status: str = "human_recorded_draft") -> ProviderResult:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, output_file)
        return ProviderResult(
            output_file=output_file,
            status=status,
            provider=self.name,
            model="human_recorded_asset",
            generation_status="imported",
        )
