#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
DEFAULT_AUDIT = ROOT / "tools" / "output" / "product_score_external_validation_audit.md"

REVIEWED_IMAGE_STATUSES = {"generated_reviewed", "commissioned_reviewed", "commissioned_final"}
FINAL_IMAGE_STATUS = "commissioned_final"
REVIEWED_AUDIO_STATUSES = {"synthetic_reviewed", "human_recorded_reviewed", "human_recorded_final"}
FINAL_AUDIO_STATUS = "human_recorded_final"

PRIOR_SCORE_DOCS = {
    "product-score-audit.md",
    "docs/exec-plans/active/product-score-audit.md",
    "tools/output/product_score_skeptical_audit.md",
    "tools/output/story_writing_95_report.md",
}

STALE_SCORE_MATERIAL = {
    "docs/exec-plans/active/art-animation-backend-close-to-100.md",
    "docs/exec-plans/active/art-character-animation-95.md",
    "docs/exec-plans/active/product-cultural-reader-95.md",
    "docs/exec-plans/active/product-score-audit.md",
    "docs/exec-plans/active/reader-polish-95.md",
    "tools/output/product_score_skeptical_audit.md",
    "tools/output/story_writing_95_report.md",
}

STALE_MARKERS = (
    "historical/non-evidence",
    "claims, not evidence",
    "not positive evidence",
)

INFLATION_PATTERNS = [
    r"\bdelta\s*\+",
    r"\bscore\s+deltas?\b",
    r"\bprevious\s+improvement\b",
    r"\balmost production ready\b",
    r"\bnear final\b",
    r"\bnear-final\b",
    r"\blaunch ready\b",
    r"\b95\+\b",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def complete_book_ids(catalog: dict[str, Any]) -> set[str]:
    return {entry["id"] for entry in catalog.get("books", []) if entry.get("status") == "complete"}


def current_status_counts() -> dict[str, Counter[str]]:
    catalog = load_json(CONTENT / "catalog.json")
    image_manifest = load_json(CONTENT / "assets" / "manifests" / "image_manifest.json")
    audio_manifest = load_json(CONTENT / "audio" / "manifests" / "audio_manifest.json")
    ids = complete_book_ids(catalog)
    scene_entries = [entry for entry in image_manifest.get("sceneEntries", []) if entry.get("storyId") in ids]
    cover_entries = [entry for entry in image_manifest.get("coverEntries", []) if entry.get("storyId") in ids]
    narration_entries = [entry for entry in audio_manifest.get("narrationEntries", []) if entry.get("storyId") in ids]
    return {
        "scene_images": Counter(entry.get("status", "missing") for entry in scene_entries),
        "cover_images": Counter(entry.get("status", "missing") for entry in cover_entries),
        "narration": Counter(entry.get("status", "missing") for entry in narration_entries),
    }


def deployed_backend_evidence_exists() -> bool:
    candidates = [
        ROOT / "backend" / "deployment_evidence.json",
        ROOT / "backend" / "production_deployment.json",
        ROOT / "infra",
        ROOT / "deploy",
    ]
    return any(path.exists() for path in candidates)


def receipt_backend_evidence_exists() -> bool:
    for path in [ROOT / "backend", ROOT / "infra", ROOT / "deploy"]:
        if not path.exists():
            continue
        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in {".py", ".ts", ".js", ".kt", ".swift", ".yaml", ".yml", ".json", ".md"}:
                text = file_path.read_text(encoding="utf-8", errors="ignore").lower()
                if (
                    ("app store server api" in text or "google play developer api" in text)
                    and ("receipt" in text or "purchase token" in text or "transactiontoken" in text)
                    and "stub" not in text
                ):
                    return True
    return False


def store_configuration_evidence_exists() -> bool:
    storekit_files = list((ROOT / "ios").rglob("*.storekit")) if (ROOT / "ios").exists() else []
    play_product_files = [
        path
        for path in (ROOT / "android").rglob("*")
        if path.is_file() and re.search(r"(play|billing|product|subscription).*\.(json|xml|yaml|yml)$", path.name, re.I)
    ] if (ROOT / "android").exists() else []
    production_xcconfig = ROOT / "ios" / "MoonJarStoriesiOSApp" / "Config" / "Production.xcconfig"
    has_signing = False
    if production_xcconfig.exists():
        text = production_xcconfig.read_text(encoding="utf-8", errors="ignore")
        has_signing = "DEVELOPMENT_TEAM" in text and "CODE_SIGN" in text
    android_gradle = ROOT / "android" / "MoonJarStoriesAndroid" / "build.gradle.kts"
    android_signing = False
    if android_gradle.exists():
        android_signing = "signingConfigs" in android_gradle.read_text(encoding="utf-8", errors="ignore")
    return bool(storekit_files and play_product_files and has_signing and android_signing)


def legal_review_evidence_exists() -> bool:
    return final_privacy_policy_exists() and legal_store_review_evidence_exists()


def readable_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore").lower()


def any_existing(paths: list[Path]) -> bool:
    return any(path.exists() for path in paths)


def path_or_text_evidence(paths: list[Path], required_groups: list[tuple[str, ...]] | None = None) -> bool:
    for path in paths:
        if not path.exists():
            continue
        if required_groups is None:
            return True
        text = readable_text(path)
        if all(any(token in text for token in group) for group in required_groups):
            return True
    return False


def target_parent_testing_evidence_exists() -> bool:
    paths = [
        ROOT / "docs" / "market" / "parent_testing.md",
        ROOT / "docs" / "market" / "customer_interviews.md",
        ROOT / "docs" / "parent_testing.md",
        ROOT / "docs" / "customer_interviews.md",
        ROOT / "product" / "parent_testing.json",
        ROOT / "shared-content" / "reviews" / "parent_testing.json",
        ROOT / "tools" / "output" / "parent_testing_report.md",
    ]
    return path_or_text_evidence(paths, [("parent", "customer", "family"), ("interview", "test", "session")])


def pricing_distribution_evidence_exists() -> bool:
    paths = [
        ROOT / "docs" / "market" / "pricing_validation.md",
        ROOT / "docs" / "market" / "distribution_validation.md",
        ROOT / "docs" / "pricing_validation.md",
        ROOT / "docs" / "distribution_validation.md",
        ROOT / "product" / "pricing_validation.json",
        ROOT / "tools" / "output" / "pricing_validation_report.md",
        ROOT / "tools" / "output" / "distribution_validation_report.md",
    ]
    return path_or_text_evidence(paths, [("pricing", "willingness", "conversion", "distribution", "retention")])


def market_validation_evidence_exists() -> bool:
    return target_parent_testing_evidence_exists() and pricing_distribution_evidence_exists()


def external_story_review_evidence_exists() -> bool:
    paths = [
        ROOT / "shared-content" / "reviews" / "external_story_review.json",
        ROOT / "shared-content" / "reviews" / "external_editorial_review.json",
        ROOT / "shared-content" / "reviews" / "external_korean_language_review.json",
        ROOT / "shared-content" / "reviews" / "external_child_safety_review.json",
        ROOT / "docs" / "external_story_review.md",
        ROOT / "docs" / "editorial_review_signoff.md",
        ROOT / "docs" / "korean_language_review_signoff.md",
        ROOT / "docs" / "child_safety_review_signoff.md",
    ]
    existing_text = "\n".join(readable_text(path) for path in paths if path.exists())
    if not existing_text:
        return False
    checks = [
        ("external" in existing_text or "human" in existing_text),
        ("editor" in existing_text or "editorial" in existing_text),
        ("korean" in existing_text or "language reviewer" in existing_text),
        ("cultural" in existing_text or "authenticity" in existing_text),
        ("child-safety" in existing_text or "child safety" in existing_text),
        ("approved" in existing_text or "signoff" in existing_text or "resolved" in existing_text),
    ]
    return all(checks) and "required before final" not in existing_text


def korean_human_cultural_review_exists() -> bool:
    paths = [
        ROOT / "shared-content" / "reviews" / "external_cultural_review.json",
        ROOT / "shared-content" / "reviews" / "korean_human_cultural_review.json",
        ROOT / "docs" / "korean_cultural_review_signoff.md",
        ROOT / "docs" / "cultural_authenticity_signoff.md",
    ]
    existing_text = "\n".join(readable_text(path) for path in paths if path.exists())
    if not existing_text:
        return False
    checks = [
        ("external" in existing_text or "human" in existing_text),
        "korean" in existing_text,
        ("cultural" in existing_text or "authenticity" in existing_text),
        ("approved" in existing_text or "signoff" in existing_text),
    ]
    return all(checks) and "required before final" not in existing_text


def final_privacy_policy_exists() -> bool:
    paths = [
        ROOT / "docs" / "privacy_policy.md",
        ROOT / "legal" / "privacy_policy.md",
        ROOT / "store" / "privacy_policy.md",
        ROOT / "metadata" / "privacy_policy.md",
    ]
    for path in paths:
        text = readable_text(path)
        if not text:
            continue
        if "privacy policy" in text and "draft" not in text and "todo" not in text:
            return True
    return False


def privacy_data_flow_artifacts_exist() -> bool:
    data_flow = ROOT / "shared-content" / "compliance" / "data_flow_map.json"
    labels = ROOT / "store" / "privacy_labels_draft.json"
    draft = ROOT / "docs" / "privacy_policy_draft.md"
    if not all(path.exists() for path in [data_flow, labels, draft]):
        return False
    try:
        data = load_json(data_flow)
        label_data = load_json(labels)
    except json.JSONDecodeError:
        return False
    return (
        data.get("status") == "implementation_mapped_not_legal_final"
        and label_data.get("status") == "draft_not_submitted"
        and "status: draft, not legal final" in readable_text(draft)
    )


def legal_store_review_evidence_exists() -> bool:
    paths = [
        ROOT / "docs" / "legal_compliance_signoff.md",
        ROOT / "docs" / "store_compliance_review.md",
        ROOT / "docs" / "apple_kids_category_review.md",
        ROOT / "docs" / "google_play_families_review.md",
        ROOT / "legal" / "store_compliance_signoff.md",
        ROOT / "shared-content" / "reviews" / "external_compliance_review.json",
    ]
    existing_text = "\n".join(readable_text(path) for path in paths if path.exists())
    if not existing_text:
        return False
    checks = [
        ("legal" in existing_text or "store" in existing_text or "apple" in existing_text or "google play" in existing_text),
        ("review" in existing_text or "signoff" in existing_text),
        ("approved" in existing_text or "complete" in existing_text or "passed" in existing_text),
    ]
    return all(checks) and "required before final" not in existing_text


def real_device_qa_evidence_exists() -> bool:
    artifacts = ROOT / ".agent" / "tmp" / "artifacts"
    if not artifacts.exists():
        return False
    for path in artifacts.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower() if path.suffix.lower() in {".md", ".json", ".txt"} else ""
        if "real device" in text or "physical device" in text:
            return True
    return False


def store_packaging_evidence_exists() -> bool:
    release_assets = ROOT / "store" / "release_assets_manifest.json"
    if release_assets.exists():
        try:
            payload = load_json(release_assets)
        except json.JSONDecodeError:
            payload = {}
        status = str(payload.get("status", "")).lower()
        if "missing" in status or "draft" in status:
            return False
        if not payload.get("screenshots", {}).get("storeFinalScreenshots"):
            return False
    final_metadata = [
        ROOT / "fastlane" / "metadata",
        ROOT / "metadata" / "app_store_final.json",
        ROOT / "metadata" / "google_play_final.json",
    ]
    return any(path.exists() for path in final_metadata)


def computed_caps() -> dict[str, tuple[int, str]]:
    counts = current_status_counts()
    scene_counts = counts["scene_images"]
    cover_counts = counts["cover_images"]
    narration_counts = counts["narration"]

    total_scenes = sum(scene_counts.values())
    total_covers = sum(cover_counts.values())
    total_narration = sum(narration_counts.values())
    reviewed_scenes = sum(scene_counts[status] for status in REVIEWED_IMAGE_STATUSES)
    reviewed_covers = sum(cover_counts[status] for status in REVIEWED_IMAGE_STATUSES)
    reviewed_narration = sum(narration_counts[status] for status in REVIEWED_AUDIO_STATUSES)

    caps: dict[str, tuple[int, str]] = {}

    if not target_parent_testing_evidence_exists():
        caps["Concept score"] = (80, "target parent/customer testing evidence is missing")
    elif not pricing_distribution_evidence_exists():
        caps["Concept score"] = (85, "pricing, distribution, willingness-to-pay, conversion, or retention evidence is missing")

    if not external_story_review_evidence_exists():
        caps["Content/story readiness"] = (
            85,
            "external children's editor, Korean-language, cultural, and child-safety review evidence is missing",
        )

    if not korean_human_cultural_review_exists():
        caps["Cultural authenticity"] = (80, "documented Korean human cultural reviewer signoff is missing")

    if not final_privacy_policy_exists() and not privacy_data_flow_artifacts_exist() and not legal_store_review_evidence_exists():
        caps["Compliance readiness"] = (75, "compliance evidence is code/config guardrails only")
    elif not final_privacy_policy_exists():
        caps["Compliance readiness"] = (80, "final privacy policy evidence is missing")
    elif not legal_store_review_evidence_exists():
        caps["Compliance readiness"] = (85, "legal/store compliance review evidence is missing")

    if total_scenes and scene_counts == Counter({"generated_draft": total_scenes}):
        caps["Visual/art readiness"] = (75, "all complete-scene art is generated_draft")
    elif reviewed_scenes < total_scenes or reviewed_covers < total_covers:
        caps["Visual/art readiness"] = (85, "not all complete-scene art and covers are reviewed/final")
    elif scene_counts[FINAL_IMAGE_STATUS] < total_scenes or cover_counts[FINAL_IMAGE_STATUS] < total_covers:
        caps["Visual/art readiness"] = (95, "reviewed art exists, but not all assets are final")

    if total_narration and narration_counts == Counter({"synthetic_draft": total_narration}):
        caps["Audio readiness"] = (55, "all narration is synthetic_draft")
    elif reviewed_narration == 0:
        caps["Audio readiness"] = (70, "no reviewed provider/human narration exists")
    elif narration_counts[FINAL_AUDIO_STATUS] < total_narration:
        caps["Audio readiness"] = (85, "not all narration is final mastered human/pro narration")

    if not deployed_backend_evidence_exists():
        caps["Backend readiness"] = (75, "backend evidence is OpenAPI/local stub only")
    elif not receipt_backend_evidence_exists():
        caps["Backend readiness"] = (90, "deployed backend exists, but receipt/token verification is unproven")

    production_caps: list[tuple[int, str]] = []
    if reviewed_scenes < total_scenes:
        production_caps.append((70, "final/reviewed art is missing for one or more complete scenes"))
    if reviewed_narration == 0:
        production_caps.append((72, "professional or human-reviewed narration is missing"))
    if not store_configuration_evidence_exists():
        production_caps.append((75, "real StoreKit and Google Play Billing flows are not configured"))
    if not receipt_backend_evidence_exists():
        production_caps.append((78, "receipt/token verification backend is missing"))
    if not legal_review_evidence_exists():
        production_caps.append((82, "privacy/legal/store compliance review is missing"))
    if not real_device_qa_evidence_exists():
        production_caps.append((85, "real-device QA evidence is missing"))
    if not store_packaging_evidence_exists():
        production_caps.append((90, "store packaging, signing, screenshots, and release metadata are incomplete"))
    if production_caps:
        caps["Production readiness"] = min(production_caps, key=lambda item: item[0])

    app_store_caps: list[tuple[int, str]] = []
    if not store_packaging_evidence_exists() or not store_configuration_evidence_exists() or not legal_review_evidence_exists():
        app_store_caps.append((50, "store evidence is incomplete: signing/products/policy/screenshots/disclosures are missing"))
    if not store_configuration_evidence_exists():
        app_store_caps.append((65, "real StoreKit products and restore purchase flow are not fully configured"))
    if not real_device_qa_evidence_exists() or not legal_review_evidence_exists():
        app_store_caps.append((80, "TestFlight/device QA or compliance review is missing"))
    if app_store_caps:
        caps["Store readiness"] = min(app_store_caps, key=lambda item: item[0])

    return caps


def category_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    pattern = re.compile(r"^Category:\s*(.+?)\s*\n(.*?)(?=^Category:|\Z)", re.MULTILINE | re.DOTALL)
    for match in pattern.finditer(text):
        blocks[match.group(1).strip()] = match.group(2)
    return blocks


def parse_scores(text: str) -> dict[str, int]:
    scores: dict[str, int] = {}
    for category, block in category_blocks(text).items():
        match = re.search(r"^Revised Score:\s*(\d{1,3})\b", block, re.MULTILINE)
        if not match:
            match = re.search(r"^Score:\s*(\d{1,3})\b", block, re.MULTILINE)
        if match:
            scores[category] = int(match.group(1))
    return scores


def evidence_sections(text: str) -> list[str]:
    sections: list[str] = []
    pattern = re.compile(
        r"Evidence Used:\n(.*?)(?:\nMissing External Evidence:|\nMissing Evidence:|\nFiles Inspected:|\nCommands Run:|\nScreenshots/Contact Sheets Reviewed:|\nWhy The Cap Exists:|\nWhat Would Raise It By 5 Points:|\nCategory:|\Z)",
        re.S,
    )
    sections.extend(match.group(1) for match in pattern.finditer(text))
    return sections


def no_cap_explanation_errors(text: str) -> list[str]:
    errors: list[str] = []
    for category, block in category_blocks(text).items():
        cap_match = re.search(r"^(?:Hard Cap|Cap Applied):\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
        if not cap_match:
            errors.append(f"{category} is missing a cap line.")
            continue
        cap_text = cap_match.group(1).strip().lower()
        no_cap = (
            cap_text in {"none", "none applied", "no cap"}
            or cap_text.startswith("none applied")
            or cap_text.startswith("no cap")
            or cap_text.startswith("no external-validation cap")
        )
        if no_cap and not re.search(r"Why No Cap Is Appropriate:\s*\S", block, re.IGNORECASE):
            errors.append(f"{category} has no cap but does not explain why no cap is appropriate.")
    return errors


def stale_score_material_errors() -> list[str]:
    errors: list[str] = []
    for relative in sorted(STALE_SCORE_MATERIAL):
        path = ROOT / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if not any(marker in text for marker in STALE_MARKERS):
            errors.append(f"Stale score material is not marked historical/non-evidence: {relative}")
    return errors


def main() -> int:
    audit_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_AUDIT
    errors: list[str] = []
    if not audit_path.exists():
        errors.append(f"Audit file is missing: {audit_path}")
    text = audit_path.read_text(encoding="utf-8") if audit_path.exists() else ""

    scores = parse_scores(text)
    caps = computed_caps()
    for category, (cap, reason) in caps.items():
        score = scores.get(category)
        if score is None:
            errors.append(f"Missing required score category: {category}")
            continue
        if score > cap:
            errors.append(f"{category} score {score} exceeds cap {cap}: {reason}.")

    for category in [
        "Concept score",
        "Engineering/demo readiness",
        "Content/story readiness",
        "Cultural authenticity",
        "Visual/art readiness",
        "Audio readiness",
        "Payment readiness",
        "Backend readiness",
        "Compliance readiness",
        "Store readiness",
        "Production readiness",
    ]:
        if category not in scores:
            errors.append(f"Missing required score category: {category}")

    for pattern in INFLATION_PATTERNS:
        if re.search(pattern, text, re.I):
            errors.append(f"Inflation language is not allowed in score audit: pattern {pattern!r}.")

    errors.extend(no_cap_explanation_errors(text))
    errors.extend(stale_score_material_errors())

    if scores.get("Concept score", 0) > 85 and not market_validation_evidence_exists():
        errors.append("Concept score exceeds 85 without external market/parent/pricing evidence.")
    if scores.get("Content/story readiness", 0) > 85 and not external_story_review_evidence_exists():
        errors.append("Content/story readiness exceeds 85 without external editor/Korean/cultural/child-safety review evidence.")
    if scores.get("Compliance readiness", 0) > 80 and not final_privacy_policy_exists():
        errors.append("Compliance readiness exceeds 80 without final privacy policy evidence.")
    if scores.get("Compliance readiness", 0) > 85 and not legal_store_review_evidence_exists():
        errors.append("Compliance readiness exceeds 85 without legal/store review evidence.")
    if scores.get("Cultural authenticity", 0) > 80 and not korean_human_cultural_review_exists():
        errors.append("Cultural authenticity exceeds 80 without Korean human reviewer signoff.")

    for section in evidence_sections(text):
        for prior_doc in PRIOR_SCORE_DOCS:
            if prior_doc in section:
                errors.append(f"Prior score document used as evidence: {prior_doc}")
        doc_evidence = re.findall(r"^\s*-\s*(docs/[^:\n]*|.*product-score-audit\.md).*", section, re.M)
        if doc_evidence:
            errors.append(f"Docs/old score material appears in primary evidence: {doc_evidence[:3]}")

    if "Prior score documents and progress summaries are claims, not evidence." not in text:
        errors.append("Audit must include the prior-score non-evidence guardrail sentence.")

    if errors:
        print("Scorecard truthfulness validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Scorecard truthfulness validation passed.")
    for category, (cap, reason) in sorted(caps.items()):
        print(f"{category}: cap {cap} ({reason})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
