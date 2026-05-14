#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
REPORT = ROOT / "tools" / "output" / "premium_template_residue_repair_report.md"

EN_FILLER = "Lantern light warmed the hanji doors while pine wind brushed the eaves."
KO_ATMOSPHERE_RE = re.compile(r"\s*등불과 솔바람, 달그림자와 한지 빛이 마음을 부드럽게 감쌌어요\.")
KO_CHOICE_RE = re.compile(r"\s*그 마음에는 [^.。]*? 담겼고, 인물들은 스스로 다음 선택을 바라보았어요\.")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_en(value: str) -> str:
    value = value.replace(" " + EN_FILLER, "")
    value = value.replace(EN_FILLER, "")
    return re.sub(r"\s{2,}", " ", value).strip()


def clean_ko(value: str) -> str:
    value = KO_ATMOSPHERE_RE.sub("", value)
    value = KO_CHOICE_RE.sub("", value)
    return re.sub(r"\s{2,}", " ", value).strip()


def clean_page(page: dict[str, Any]) -> int:
    changed = 0
    for field in ("englishText",):
        before = str(page.get(field, ""))
        after = clean_en(before)
        if after != before:
            page[field] = after
            changed += 1
    for field in ("koreanText", "narrationScript"):
        before = str(page.get(field, ""))
        after = clean_ko(before)
        if after != before:
            page[field] = after
            changed += 1
    text = page.get("text")
    if isinstance(text, dict):
        for field in ("enStandard",):
            before = str(text.get(field, ""))
            after = clean_en(before)
            if after != before:
                text[field] = after
                changed += 1
        for field in ("koStandard",):
            before = str(text.get(field, ""))
            after = clean_ko(before)
            if after != before:
                text[field] = after
                changed += 1
    return changed


def main() -> int:
    catalog = load(CATALOG)
    rows = [
        "# Premium Template Residue Repair Report",
        "",
        "Removed repeated generated-template atmosphere sentences from premium story text and narration. This is a text cleanup, not human editorial signoff.",
        "",
        "| Story | Pages touched | Fields changed |",
        "| --- | ---: | ---: |",
    ]
    total_pages = 0
    total_fields = 0
    for entry in catalog.get("books", []):
        if entry.get("status") != "complete" or entry.get("access") != "premium":
            continue
        book_path = entry.get("bookPath")
        if not isinstance(book_path, str):
            continue
        path = CONTENT / book_path
        book = load(path)
        pages_touched = 0
        fields_changed = 0
        for page in book.get("pages", []):
            changed = clean_page(page)
            if changed:
                pages_touched += 1
                fields_changed += changed
        if fields_changed:
            write_json(path, book)
        total_pages += pages_touched
        total_fields += fields_changed
        rows.append(f"| {book.get('slug')} | {pages_touched} | {fields_changed} |")

    rows.extend(
        [
            "",
            "## Totals",
            "",
            f"- Pages touched: {total_pages}",
            f"- Fields changed: {total_fields}",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Removed premium template residue from {total_pages} pages ({total_fields} fields).")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
