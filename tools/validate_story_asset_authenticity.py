#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import struct
import sys
import zlib
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any

from story_asset_semantic_expectations import (
    GENERIC_PURPOSE_RE,
    GENERIC_STORY_PATTERNS,
    PANEL_RANGES,
    STORY_EXPECTATIONS,
    expected_panel_for_page,
)

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
REPORT = ROOT / "tools" / "output" / "story_asset_authenticity_audit.md"
SNAPSHOT = ROOT / ".agent" / "tmp" / "artifacts" / "story-asset-authenticity" / "story_asset_authenticity_snapshot.json"

FINAL_IMAGE_STATUSES = {"commissioned_final"}
SHEET_IMPORTER = "built_in_image_gen_sheet_importer"
LOCAL_STORY_RENDERER = "local_story_specific_svg_renderer"
SINGLE_SCENE_IMAGEGEN = "built_in_image_gen_story_specific_scene"
ASCII_WORD_RE = re.compile(r"[A-Za-z]{3,}")
META_STORY_PHRASES = (
    "kept the scene korean and specific",
    "include key props",
    "child-safe adaptation boundaries",
    "premium korean watercolor",
)
TEMPLATE_RESIDUE_PHRASES = (
    "lantern light warmed the hanji doors while pine wind brushed the eaves",
    "등불과 솔바람, 달그림자와 한지 빛이 마음을 부드럽게 감쌌어요",
    "인물들은 스스로 다음 선택을 바라보았어요",
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(flatten(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(flatten(item) for item in value)
    if isinstance(value, str):
        return value
    return ""


def text_for_book(book: dict[str, Any]) -> str:
    pieces: list[str] = [book.get("summary", "")]
    for page in book.get("pages", []):
        pieces.append(page.get("englishText", ""))
        pieces.append(page.get("koreanText", ""))
        pieces.append(page.get("imagePrompt", ""))
        pieces.append(flatten(page.get("storyBeat", {})))
    return "\n".join(pieces)


def story_sheet_for(slug: str) -> str | None:
    relative = f"assets/generated-draft/images/story-sheets/{slug}.png"
    return relative if (CONTENT / relative).exists() else None


def file_exists(relative: str | None) -> bool:
    return isinstance(relative, str) and bool(relative) and (CONTENT / relative).exists()


def file_hash(relative: str | None) -> str | None:
    if not file_exists(relative):
        return None
    return sha256((CONTENT / str(relative)).read_bytes()).hexdigest()


def png_rgb_rows(relative: str) -> tuple[int, int, int, list[list[int]]]:
    data = (CONTENT / relative).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos = 8
    width = height = bit_depth = color_type = None
    compressed = b""
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        pos += length + 12
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(">IIBBBBB", chunk)
            if bit_depth != 8 or color_type not in {2, 6} or interlace != 0:
                raise ValueError("unsupported PNG encoding")
        elif chunk_type == b"IDAT":
            compressed += chunk
        elif chunk_type == b"IEND":
            break
    if width is None or height is None or color_type is None:
        raise ValueError("missing PNG header")
    channels = 4 if color_type == 6 else 3
    raw = zlib.decompress(compressed)
    stride = width * channels
    rows: list[list[int]] = []
    previous = [0] * stride
    cursor = 0
    for _y in range(height):
        filter_type = raw[cursor]
        cursor += 1
        encoded = list(raw[cursor : cursor + stride])
        cursor += stride
        row = [0] * stride
        for index, value in enumerate(encoded):
            left = row[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 0:
                decoded = value
            elif filter_type == 1:
                decoded = value + left
            elif filter_type == 2:
                decoded = value + up
            elif filter_type == 3:
                decoded = value + ((left + up) // 2)
            elif filter_type == 4:
                estimate = left + up - upper_left
                pa = abs(estimate - left)
                pb = abs(estimate - up)
                pc = abs(estimate - upper_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else upper_left
                decoded = value + predictor
            else:
                raise ValueError("unsupported PNG filter")
            row[index] = decoded & 255
        rows.append(row)
        previous = row
    return width, height, channels, rows


def png_region_metrics(relative: str, region: tuple[int, int, int, int]) -> dict[str, float]:
    width, height, channels, rows = png_rgb_rows(relative)
    x0, y0, x1, y1 = region
    x0 = max(0, min(width, x0))
    x1 = max(x0 + 1, min(width, x1))
    y0 = max(0, min(height, y0))
    y1 = max(y0 + 1, min(height, y1))
    total = 0
    blue = 0
    tan = 0
    greenish = 0
    for y in range(y0, y1):
        row = rows[y]
        for x in range(x0, x1):
            offset = x * channels
            red, green, blue_value = row[offset], row[offset + 1], row[offset + 2]
            total += 1
            if blue_value >= green >= red and blue_value > 120:
                blue += 1
            if red > green > blue_value and red > 150 and blue_value < 175:
                tan += 1
            if green > red * 0.95 and green > blue_value * 1.05 and 70 < green < 190:
                greenish += 1
    return {
        "blueRatio": blue / total,
        "tanRatio": tan / total,
        "greenishRatio": greenish / total,
    }


def selected_candidate(entry: dict[str, Any]) -> dict[str, Any] | None:
    output = entry.get("outputFile")
    for candidate in entry.get("candidates", []):
        if isinstance(candidate, dict) and candidate.get("outputFile") == output:
            return candidate
    return None


def production_honesty_findings(entries: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    for entry in entries:
        status = entry.get("status")
        output = entry.get("outputFile")
        if status not in FINAL_IMAGE_STATUSES and entry.get("productionApprovalStatus") == "approved":
            findings.append(f"{output}: non-final art marked production approved")
        reviewer = str(entry.get("reviewer", "")).lower()
        review_scope = str(entry.get("reviewScope", "")).lower()
        if "external" in reviewer and status not in FINAL_IMAGE_STATUSES:
            findings.append(f"{output}: generated/non-final art claims external reviewer")
        if "external signoff" in review_scope and status not in FINAL_IMAGE_STATUSES:
            findings.append(f"{output}: generated/non-final art claims external signoff scope")
        candidate = selected_candidate(entry)
        if candidate and candidate.get("productionApprovalStatus") == "approved" and candidate.get("status") not in FINAL_IMAGE_STATUSES:
            findings.append(f"{output}: selected candidate is non-final but production approved")
    return findings


def page_generic_findings(book: dict[str, Any]) -> list[str]:
    pages = book.get("pages", [])
    findings: list[str] = []
    english_texts = [str(page.get("englishText", "")) for page in pages]
    prompts = [re.sub(r"Page \d+", "Page N", str(page.get("imagePrompt", ""))) for page in pages]
    unique_texts = len(set(english_texts))
    unique_prompts = len(set(prompts))
    if pages and unique_texts < max(8, int(len(pages) * 0.8)):
        findings.append(f"story text repeats too heavily ({unique_texts}/{len(pages)} unique English pages)")
    if pages and unique_prompts < max(8, int(len(pages) * 0.6)):
        findings.append(f"image prompts repeat too heavily ({unique_prompts}/{len(pages)} unique prompt bodies)")
    for page in pages:
        page_label = f"page {page.get('pageNumber')}"
        page_text = " ".join([page.get("englishText", ""), page.get("koreanText", ""), page.get("imagePrompt", "")]).lower()
        for phrase in TEMPLATE_RESIDUE_PHRASES:
            if phrase.lower() in page_text:
                findings.append(f"{page_label}: premium template residue `{phrase}`")
                break
        for pattern in GENERIC_STORY_PATTERNS:
            if pattern in page_text:
                findings.append(f"{page_label}: generic scaffold phrase `{pattern}`")
                break
        purpose = str(page.get("storyBeat", {}).get("purpose", ""))
        if re.search(GENERIC_PURPOSE_RE, purpose, flags=re.IGNORECASE):
            findings.append(f"{page_label}: generic storyBeat purpose `{purpose}`")
    return findings[:12]


def language_integrity_findings(book: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    for page in book.get("pages", []):
        page_label = f"page {page.get('pageNumber')}"
        story_text_fields = {
            "englishText": str(page.get("englishText", "")),
            "koreanText": str(page.get("koreanText", "")),
            "narrationScript": str(page.get("narrationScript", "")),
            "text.enStandard": str(page.get("text", {}).get("enStandard", "")),
            "text.koStandard": str(page.get("text", {}).get("koStandard", "")),
        }
        for field, value in story_text_fields.items():
            lowered = value.lower()
            for phrase in META_STORY_PHRASES:
                if phrase in lowered:
                    findings.append(f"{page_label}: {field} contains generated/meta prose `{phrase}`")
        for field in ("koreanText", "narrationScript"):
            value = str(page.get(field, ""))
            match = ASCII_WORD_RE.search(value)
            if match:
                findings.append(f"{page_label}: {field} contains English/ASCII fragment `{match.group(0)}`")
        text = page.get("text", {})
        if isinstance(text, dict):
            for field in ("koLittle", "koStandard"):
                value = str(text.get(field, ""))
                match = ASCII_WORD_RE.search(value)
                if match:
                    findings.append(f"{page_label}: text.{field} contains English/ASCII fragment `{match.group(0)}`")
    return findings[:18]


def required_term_findings(slug: str, book: dict[str, Any]) -> list[str]:
    expectation = STORY_EXPECTATIONS.get(slug)
    if expectation is None:
        return [f"missing semantic expectation for {slug}"]
    haystack = text_for_book(book).lower()
    missing = [term for term in expectation.required_terms if term.lower() not in haystack]
    if missing:
        return [f"missing core term(s): {', '.join(missing)}"]
    return []


def high_risk_findings(slug: str, book: dict[str, Any]) -> list[str]:
    pages_by_number = {page.get("pageNumber"): page for page in book.get("pages", [])}
    findings: list[str] = []

    if slug == "sun-and-moon":
        joined = text_for_book(book).lower()
        for term in ("cunning", "hungry", "watchful", "deceptive", "shadow"):
            if term not in joined:
                findings.append(f"Sun/Moon tiger direction missing `{term}`")
        for page_no in (3, 4, 7, 11, 16):
            page = pages_by_number.get(page_no, {})
            prompt = str(page.get("imagePrompt", "")).lower()
            if not any(term in prompt for term in ("cunning", "dangerous", "watchful", "unsettling", "threat")):
                findings.append(f"page {page_no}: tiger prompt lacks meaningful threat language")
            positive_prompt = prompt.split("negative prompt:", 1)[0]
            if any(term in positive_prompt for term in ("friendly tiger", "cute tiger", "plush", "mascot", "pet tiger")):
                findings.append(f"page {page_no}: positive prompt cute-codes the tiger")

    if slug == "fairy-and-woodcutter":
        required_by_page = {
            3: ("hid", "wrong", "wing robe"),
            6: ("three", "children"),
            13: ("before", "third", "robe"),
            15: ("one child in each arm", "did not smile"),
            18: ("bucket", "sky"),
            28: ("rooster", "longing"),
        }
        for page_no, terms in required_by_page.items():
            page = pages_by_number.get(page_no, {})
            page_text = flatten(page).lower()
            for term in terms:
                if term.lower() not in page_text:
                    findings.append(f"page {page_no}: Fairy/Woodcutter missing `{term}`")
        for page_no in (15, 16, 18, 28):
            page = pages_by_number.get(page_no, {})
            tone_text = flatten(page.get("storyBeat", {})).lower() + " " + str(page.get("imagePrompt", "")).lower()
            if not any(term in tone_text for term in ("sorrow", "solemn", "bittersweet", "lonely", "longing", "afraid")):
                findings.append(f"page {page_no}: Fairy/Woodcutter sensitive beat lacks sober/bittersweet tone")

    return findings


def panel_mapping_findings(slug: str, book: dict[str, Any], scene_by_key: dict[tuple[str, str], dict[str, Any]]) -> list[str]:
    if slug not in PANEL_RANGES:
        return []
    findings: list[str] = []
    for page in book.get("pages", []):
        page_number = page.get("pageNumber")
        page_id = page.get("id")
        if not isinstance(page_number, int) or not isinstance(page_id, str):
            continue
        entry = scene_by_key.get((book.get("id"), page_id))
        if not entry:
            findings.append(f"page {page_number}: missing scene manifest entry")
            continue
        if entry.get("generationTool") == LOCAL_STORY_RENDERER:
            continue
        if entry.get("generationTool") != SHEET_IMPORTER:
            continue
        expected = expected_panel_for_page(slug, page_number)
        actual = entry.get("panelIndex")
        if actual != expected:
            findings.append(f"page {page_number}: panelIndex {actual!r}, expected {expected}")
    return findings[:18]


def duplicate_scene_findings(book: dict[str, Any], scenes: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    pages_by_output: dict[str, list[int]] = defaultdict(list)
    pages_by_hash: dict[str, list[int]] = defaultdict(list)
    for entry in scenes:
        page_number = entry.get("pageNumber")
        output = entry.get("outputFile")
        if isinstance(output, str) and isinstance(page_number, int):
            pages_by_output[output].append(page_number)
            digest = file_hash(output)
            if digest:
                pages_by_hash[digest].append(page_number)
    for output, pages in pages_by_output.items():
        if len(pages) > 1:
            findings.append(f"scene asset reused across pages {pages}: {output}")
    for pages in pages_by_hash.values():
        if len(pages) > 1:
            findings.append(f"selected scene art has duplicate pixels across pages {pages}")
    return findings[:12]


def cover_scene_duplicate_findings(scenes: list[dict[str, Any]], cover: dict[str, Any] | None) -> list[str]:
    if not isinstance(cover, dict):
        return []
    cover_hash = file_hash(cover.get("outputFile"))
    if not cover_hash:
        return []
    duplicate_pages = [
        entry.get("pageNumber")
        for entry in scenes
        if isinstance(entry.get("pageNumber"), int) and file_hash(entry.get("outputFile")) == cover_hash
    ]
    if duplicate_pages:
        return [f"cover art duplicates selected scene page(s) {duplicate_pages}"]
    return []


def manifest_prompt_findings(book: dict[str, Any], scenes: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    entries_by_scene = {entry.get("sceneId"): entry for entry in scenes}
    for page in book.get("pages", []):
        page_id = page.get("id")
        entry = entries_by_scene.get(page_id)
        if not isinstance(entry, dict) or entry.get("generationTool") != LOCAL_STORY_RENDERER:
            continue
        expected = page.get("imagePrompt")
        if entry.get("prompt") != expected or entry.get("rawPrompt") != expected:
            findings.append(f"page {page.get('pageNumber')}: selected manifest prompt does not match page imagePrompt")
    return findings[:18]


def visual_signature_findings(book: dict[str, Any], scenes: list[dict[str, Any]]) -> list[str]:
    if book.get("slug") != "fairy-and-woodcutter" and book.get("id") != "book.fairy_woodcutter":
        return []
    findings: list[str] = []
    scene_by_page = {
        entry.get("pageNumber"): entry
        for entry in scenes
        if isinstance(entry.get("pageNumber"), int) and isinstance(entry.get("outputFile"), str)
    }
    for page_number in (15, 18):
        entry = scene_by_page.get(page_number)
        if isinstance(entry, dict) and entry.get("generationTool") == SHEET_IMPORTER:
            expected_panel = 5 if page_number == 15 else 6
            if entry.get("panelIndex") != expected_panel:
                findings.append(f"page {page_number}: Fairy/Woodcutter rich sheet panel is {entry.get('panelIndex')!r}, expected {expected_panel}")
            continue
        if isinstance(entry, dict) and entry.get("generationTool") == SINGLE_SCENE_IMAGEGEN:
            continue
        relative = str(entry.get("outputFile")) if isinstance(entry, dict) else ""
        try:
            metrics = png_region_metrics(relative, (80, 80, 880, 540))
        except Exception as exc:
            findings.append(f"page {page_number}: could not inspect Fairy/Woodcutter visual signature ({exc})")
            continue
        if metrics["blueRatio"] < 0.45 or metrics["tanRatio"] > 0.14:
            findings.append(
                f"page {page_number}: Fairy/Woodcutter ascent/departure art reads too indoor/generic "
                f"(blueRatio={metrics['blueRatio']:.2f}, tanRatio={metrics['tanRatio']:.2f})"
            )
    entry = scene_by_page.get(16)
    if isinstance(entry, dict) and entry.get("generationTool") == SINGLE_SCENE_IMAGEGEN:
        output = str(entry.get("outputFile", ""))
        prompt = f"{entry.get('prompt', '')} {entry.get('rawPrompt', '')}".lower()
        if "story-specific-scenes/fairy-and-woodcutter/page-016.png" not in output:
            findings.append(f"page 16: Fairy/Woodcutter aftermath should use the generated empty-cottage scene, got {output!r}")
        if "empty" not in prompt or "sandals" not in prompt:
            findings.append("page 16: Fairy/Woodcutter aftermath prompt must preserve empty cottage and sandals")
        return findings
    relative = str(entry.get("outputFile")) if isinstance(entry, dict) else ""
    try:
        metrics = png_region_metrics(relative, (80, 80, 880, 540))
        lower_metrics = png_region_metrics(relative, (80, 360, 880, 540))
    except Exception as exc:
        findings.append(f"page 16: could not inspect Fairy/Woodcutter empty-cottage signature ({exc})")
    else:
        if metrics["blueRatio"] > 0.08 or metrics["tanRatio"] < 0.20 or lower_metrics["greenishRatio"] > 0.03:
            findings.append(
                "page 16: Fairy/Woodcutter aftermath art should read as empty tan cottage with no visible figures "
                f"(blueRatio={metrics['blueRatio']:.2f}, tanRatio={metrics['tanRatio']:.2f}, "
                f"lowerGreenishRatio={lower_metrics['greenishRatio']:.2f})"
            )
    return findings


def asset_findings(book: dict[str, Any], scenes: list[dict[str, Any]], cover: dict[str, Any] | None) -> list[str]:
    findings: list[str] = []
    pages = book.get("pages", [])
    if len(scenes) != len(pages):
        findings.append(f"scene asset count {len(scenes)} does not match page count {len(pages)}")
    for entry in scenes[:]:
        if not file_exists(entry.get("outputFile")):
            findings.append(f"missing scene asset {entry.get('outputFile')!r}")
        if not entry.get("characterBible"):
            findings.append(f"{entry.get('sceneId')}: missing characterBible in manifest")
    if cover is None:
        findings.append("missing cover manifest entry")
    elif not file_exists(cover.get("outputFile")):
        findings.append(f"missing cover asset {cover.get('outputFile')!r}")
    findings.extend(cover_scene_duplicate_findings(scenes, cover))
    findings.extend(production_honesty_findings(scenes + ([cover] if cover else [])))
    return findings[:18]


def fix_for(finding: str) -> str:
    if "generic" in finding or "repeat" in finding or "missing core term" in finding:
        return "repair story JSON text, storyBeat metadata, and imagePrompt fields from folktale-specific beats"
    if "panelIndex" in finding:
        return "replace modulo sheet cycling with story-specific panel range mapping and re-import runtime scenes"
    if "tiger" in finding or "threat" in finding or "cute-code" in finding:
        return "regenerate or replace tiger-facing art/prompts with child-safe antagonist direction"
    if "Fairy/Woodcutter" in finding:
        return "preserve wing-robe wrongdoing, early reveal, sorrowful departure, sky-bucket longing, and rooster ending"
    if "production" in finding or "external" in finding or "final" in finding:
        return "downgrade status/review wording to internal-demo generated-review language"
    if "missing" in finding:
        return "add or relink the missing selected asset/manifest entry"
    return "manual cultural/editorial review"


def main() -> int:
    catalog = load(CATALOG)
    manifest = load(IMAGE_MANIFEST)

    scenes_by_book: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scene_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in manifest.get("sceneEntries", []):
        if isinstance(entry, dict):
            scenes_by_book[str(entry.get("storyId"))].append(entry)
            scene_by_key[(str(entry.get("storyId")), str(entry.get("sceneId")))] = entry
    covers_by_book = {
        entry.get("storyId"): entry
        for entry in manifest.get("coverEntries", [])
        if isinstance(entry, dict)
    }

    rows = [
        "# Story Asset Authenticity Audit",
        "",
        "This audit checks semantic story/art fit. It is not a claim of commissioned final art or external human review.",
        "",
        "| Story Slug | Pages | Access | Known Folktale Core Beats | Sensitive Emotional Beats | Scene Assets | Cover Asset | Story Sheet | Mismatch Findings | Required Fixes |",
        "| --- | ---: | --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    snapshot: list[dict[str, Any]] = []
    all_findings: list[str] = []

    for catalog_entry in catalog.get("books", []):
        if catalog_entry.get("status") != "complete":
            continue
        slug = str(catalog_entry.get("slug"))
        book_path = catalog_entry.get("bookPath")
        if not isinstance(book_path, str):
            all_findings.append(f"{slug}: missing bookPath")
            continue
        book = load(CONTENT / book_path)
        scenes = sorted(scenes_by_book.get(book["id"], []), key=lambda item: int(item.get("pageNumber") or 0))
        cover = covers_by_book.get(book["id"])
        sheet = story_sheet_for(slug)
        expectation = STORY_EXPECTATIONS.get(slug)
        findings: list[str] = []
        findings.extend(asset_findings(book, scenes, cover))
        findings.extend(page_generic_findings(book))
        findings.extend(language_integrity_findings(book))
        findings.extend(required_term_findings(slug, book))
        findings.extend(high_risk_findings(slug, book))
        findings.extend(panel_mapping_findings(slug, book, scene_by_key))
        findings.extend(duplicate_scene_findings(book, scenes))
        findings.extend(manifest_prompt_findings(book, scenes))
        findings.extend(visual_signature_findings(book, scenes))
        deduped_findings = list(dict.fromkeys(findings))
        all_findings.extend(f"{slug}: {finding}" for finding in deduped_findings)
        required_fixes = list(dict.fromkeys(fix_for(finding) for finding in deduped_findings))
        cover_path = cover.get("outputFile") if isinstance(cover, dict) else None
        rows.append(
            "| "
            f"{slug} | "
            f"{len(book.get('pages', []))} | "
            f"{catalog_entry.get('access')} | "
            f"{(expectation.core_beats if expectation else 'missing expectation').replace('|', '/')} | "
            f"{(expectation.sensitive_beats if expectation else 'missing expectation').replace('|', '/')} | "
            f"{len(scenes)} | "
            f"{cover_path or 'missing'} | "
            f"{sheet or 'none'} | "
            f"{'; '.join(deduped_findings) if deduped_findings else 'pass'} | "
            f"{'; '.join(required_fixes) if required_fixes else 'none'} |"
        )
        snapshot.append(
            {
                "slug": slug,
                "pageCount": len(book.get("pages", [])),
                "access": catalog_entry.get("access"),
                "coreBeats": expectation.core_beats if expectation else None,
                "sensitiveBeats": expectation.sensitive_beats if expectation else None,
                "sceneAssetCount": len(scenes),
                "coverAssetPath": cover_path,
                "storySheetPath": sheet,
                "mismatchFindings": deduped_findings,
                "requiredFixes": required_fixes,
            }
        )

    rows.extend(
        [
            "",
            "## Result",
            "",
            "PASS" if not all_findings else "FAIL",
            "",
        ]
    )
    if all_findings:
        rows.extend(f"- {finding}" for finding in all_findings)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if all_findings:
        print(f"Story asset authenticity validation failed; see {REPORT.relative_to(ROOT)}")
        for finding in all_findings[:50]:
            print(f"- {finding}")
        if len(all_findings) > 50:
            print(f"... {len(all_findings) - 50} more")
        return 1

    print(f"Story asset authenticity validation passed: {len(snapshot)} catalog stories checked.")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    print(f"Snapshot: {SNAPSHOT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
