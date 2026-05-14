#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
BOOKS = CONTENT / "books"
CHARACTERS = CONTENT / "characters"
ASSETS = CONTENT / "assets"
AUDIO = CONTENT / "audio"

IMAGE_STATUSES = {
    "placeholder",
    "generated_draft",
    "generated_reviewed",
    "commissioned_draft",
    "commissioned_reviewed",
    "commissioned_final",
    "rejected",
}

AUDIO_STATUSES = {
    "placeholder",
    "synthetic_draft",
    "synthetic_reviewed",
    "human_recorded_draft",
    "human_recorded_reviewed",
    "human_recorded_final",
    "rejected",
}

IMAGE_ASSET_PRIORITY = [
    "commissioned_final",
    "commissioned_reviewed",
    "generated_reviewed",
    "commissioned_draft",
    "generated_draft",
    "placeholder",
]

AUDIO_ASSET_PRIORITY = [
    "human_recorded_final",
    "human_recorded_reviewed",
    "synthetic_reviewed",
    "human_recorded_draft",
    "synthetic_draft",
    "placeholder",
]

REVIEW_FIELDS = [
    "reviewer",
    "reviewDate",
    "rejectionReason",
    "notes",
    "culturalReviewStatus",
    "childSafetyReviewStatus",
    "productionApprovalStatus",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_catalog() -> dict[str, Any]:
    return load_json(CATALOG)


def complete_books() -> list[tuple[dict[str, Any], Path, dict[str, Any]]]:
    catalog = load_catalog()
    result: list[tuple[dict[str, Any], Path, dict[str, Any]]] = []
    for entry in catalog.get("books", []):
        if entry.get("status") != "complete":
            continue
        book_path = CONTENT / entry["bookPath"]
        result.append((entry, book_path, load_json(book_path)))
    return result


def load_character_index() -> dict[str, str]:
    index_path = CHARACTERS / "index.json"
    if not index_path.exists():
        return {}
    index = load_json(index_path)
    return {
        item["bookId"]: item["characterBible"]
        for item in index.get("books", [])
        if item.get("bookId") and item.get("characterBible")
    }


def page_asset_name(page_number: int, extension: str) -> str:
    return f"page-{page_number:03d}.{extension.lstrip('.')}"


def content_path(relative_path: str) -> Path:
    return CONTENT / relative_path


def existing_or_none(relative_path: str | None) -> Path | None:
    if not relative_path:
        return None
    path = content_path(relative_path)
    return path if path.exists() else None
