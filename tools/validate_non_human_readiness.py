#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
REPORT = ROOT / "tools" / "output" / "non_human_readiness_report.md"

MARKET_PLAN = ROOT / "product" / "market-validation" / "market_validation_plan.json"
POSITIONING = ROOT / "product" / "market-validation" / "source_backed_positioning.md"
READINESS_LEDGER = ROOT / "product" / "release_readiness_ledger.json"
DATA_FLOW = CONTENT / "compliance" / "data_flow_map.json"
BEHAVIOR_FLAGS = CONTENT / "compliance" / "app_behavior_flags.json"
PRIVACY_DRAFT = ROOT / "docs" / "privacy_policy_draft.md"
PRIVACY_LABELS = ROOT / "store" / "privacy_labels_draft.json"
ACCESSIBILITY_QA = ROOT / "store" / "accessibility_qa_checklist.json"
PRODUCT_CONFIG = ROOT / "store" / "product_configuration_manifest.json"
APP_STORE_METADATA = ROOT / "store" / "app_store_metadata_draft.json"
GOOGLE_PLAY_METADATA = ROOT / "store" / "google_play_metadata_draft.json"
RELEASE_ASSETS = ROOT / "store" / "release_assets_manifest.json"
BACKEND_DEPLOYMENT = ROOT / "backend" / "deployment_readiness_manifest.json"
RECEIPT_CONTRACT = ROOT / "backend" / "receipt_verification_contract.json"
IOS_ENTITLEMENT = ROOT / "ios" / "MoonJarStoriesiOS" / "Sources" / "MoonJarStoriesiOS" / "EntitlementStore.swift"
ANDROID_ENTITLEMENT = ROOT / "android" / "MoonJarStoriesAndroid" / "src" / "main" / "java" / "com" / "moonjar" / "stories" / "billing" / "EntitlementManager.kt"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def require_file(errors: list[str], path: Path) -> bool:
    if not path.exists():
        errors.append(f"Missing required non-human readiness artifact: {rel(path)}")
        return False
    return True


def status_contains(value: object, tokens: list[str]) -> bool:
    text = str(value).lower()
    return any(token in text for token in tokens)


def catalog_product_ids() -> set[str]:
    catalog = load_json(CONTENT / "catalog.json")
    ids = {"com.moonjarstories.subscription.monthly", "com.moonjarstories.subscription.annual", "com.moonjarstories.lifetime.korean_library"}
    for entry in catalog.get("books", []):
        if entry.get("access") == "premium":
            ids.add("com.moonjarstories.book." + entry["id"].removeprefix("book."))
    return ids


def validate_market(errors: list[str], report: list[str]) -> None:
    plan = load_json(MARKET_PLAN)
    source_text = POSITIONING.read_text(encoding="utf-8")
    evidence = plan.get("evidenceStatus", {})
    if plan.get("status") != "repo_ready_no_external_demand_evidence":
        errors.append(f"{rel(MARKET_PLAN)} must stay honest with status repo_ready_no_external_demand_evidence.")
    for key in ["targetParentTesting", "pricingValidation", "willingnessToPaySignal", "retentionSignal", "conversionSignal"]:
        value = evidence.get(key)
        if value not in {"missing_external", "planned_not_run"}:
            errors.append(f"{rel(MARKET_PLAN)} must not claim completed external demand evidence for {key}.")
    if len(plan.get("pricingHypotheses", [])) < 4:
        errors.append(f"{rel(MARKET_PLAN)} should cover monthly, annual, lifetime, and individual-book pricing hypotheses.")
    if len(plan.get("distributionExperiments", [])) < 4:
        errors.append(f"{rel(MARKET_PLAN)} should define App Store, Play Store, and owned/community distribution experiments.")
    if "not parent testing" not in source_text.lower() or "does not prove demand" not in source_text.lower():
        errors.append(f"{rel(POSITIONING)} must clearly state that source-backed research is not demand proof.")
    urls = re.findall(r"https://[^\s)]+", source_text)
    if len(urls) < 8:
        errors.append(f"{rel(POSITIONING)} should include enough public source links for competitor, distribution, and compliance planning.")
    report.append("- Market/pricing/distribution planning artifacts are present, with external demand evidence still marked missing.")


def validate_compliance(errors: list[str], report: list[str]) -> None:
    flags = load_json(BEHAVIOR_FLAGS)
    data_flow = load_json(DATA_FLOW)
    labels = load_json(PRIVACY_LABELS)
    policy_text = PRIVACY_DRAFT.read_text(encoding="utf-8").lower()
    accessibility = load_json(ACCESSIBILITY_QA)
    for key in [
        "adsEnabled",
        "thirdPartyTrackingEnabled",
        "childAccountsEnabled",
        "childFacingExternalLinksEnabled",
        "childDataCollectionEnabled",
        "liveImageGenerationInChildApp",
        "liveTtsGenerationInChildApp",
    ]:
        if flags.get(key) is not False:
            errors.append(f"{rel(BEHAVIOR_FLAGS)} must keep {key}=false.")
    if data_flow.get("status") != "implementation_mapped_not_legal_final":
        errors.append(f"{rel(DATA_FLOW)} must be marked implementation_mapped_not_legal_final.")
    if data_flow.get("childDataCollectionEnabled") is not False or data_flow.get("thirdPartyTrackingEnabled") is not False:
        errors.append(f"{rel(DATA_FLOW)} must keep child data collection and third-party tracking disabled.")
    flows = {flow.get("id"): flow for flow in data_flow.get("flows", [])}
    for flow_id in ["local_reading_progress", "purchase_entitlement_state", "child_voice_recording"]:
        if flow_id not in flows:
            errors.append(f"{rel(DATA_FLOW)} missing flow {flow_id}.")
    if flows.get("child_voice_recording", {}).get("releaseStatus") != "prohibited_in_current_child_app":
        errors.append(f"{rel(DATA_FLOW)} must keep child voice recording prohibited in the current child app.")
    if "status: draft, not legal final" not in policy_text:
        errors.append(f"{rel(PRIVACY_DRAFT)} must identify itself as draft and not legal final.")
    if labels.get("status") != "draft_not_submitted":
        errors.append(f"{rel(PRIVACY_LABELS)} must be draft_not_submitted.")
    if "not_submitted" not in str(labels).lower():
        errors.append(f"{rel(PRIVACY_LABELS)} must not claim submitted store labels.")
    if accessibility.get("status") != "static_checks_ready_real_device_qa_missing":
        errors.append(f"{rel(ACCESSIBILITY_QA)} must keep real-device accessibility QA missing until proven.")
    report.append("- Privacy/data-flow, draft privacy labels, and accessibility checklist are present without claiming legal/store completion.")


def validate_store_and_payments(errors: list[str], report: list[str]) -> None:
    product_config = load_json(PRODUCT_CONFIG)
    expected_ids = catalog_product_ids()
    ios_text = IOS_ENTITLEMENT.read_text(encoding="utf-8")
    android_text = ANDROID_ENTITLEMENT.read_text(encoding="utf-8")
    if product_config.get("status") != "planned_not_configured_in_store_consoles":
        errors.append(f"{rel(PRODUCT_CONFIG)} must not claim real store-console configuration.")
    base_ids = {item.get("productId") for item in product_config.get("baseProducts", [])}
    for product_id in ["com.moonjarstories.subscription.monthly", "com.moonjarstories.subscription.annual", "com.moonjarstories.lifetime.korean_library"]:
        if product_id not in base_ids:
            errors.append(f"{rel(PRODUCT_CONFIG)} missing base product {product_id}.")
        if product_id not in ios_text or product_id not in android_text:
            errors.append(f"Native source is missing planned product id {product_id}.")
    if product_config.get("individualBookProductPattern") != "com.moonjarstories.book.<book_id_without_book_prefix>":
        errors.append(f"{rel(PRODUCT_CONFIG)} has unexpected individual-book product pattern.")
    for item in product_config.get("baseProducts", []):
        if item.get("storeConfigured") is not False or item.get("sandboxTested") is not False:
            errors.append(f"{rel(PRODUCT_CONFIG)} cannot mark products configured/tested without external store evidence.")
    app_store = load_json(APP_STORE_METADATA)
    google_play = load_json(GOOGLE_PLAY_METADATA)
    release_assets = load_json(RELEASE_ASSETS)
    for path, payload in [(APP_STORE_METADATA, app_store), (GOOGLE_PLAY_METADATA, google_play)]:
        if payload.get("status") != "draft_not_submitted":
            errors.append(f"{rel(path)} must remain draft_not_submitted.")
        if payload.get("submissionStatus") != "blocked":
            errors.append(f"{rel(path)} must keep submissionStatus blocked until real store evidence exists.")
    if release_assets.get("status") != "draft_assets_present_final_store_assets_missing":
        errors.append(f"{rel(RELEASE_ASSETS)} must keep final store assets missing until they exist.")
    if release_assets.get("screenshots", {}).get("storeFinalScreenshots") != []:
        errors.append(f"{rel(RELEASE_ASSETS)} must not list final store screenshots until exported.")
    if len(expected_ids) < 20:
        errors.append("Expected catalog product ID set should include base products plus all premium books.")
    report.append(f"- Store/payment manifests align with {len(expected_ids)} planned product IDs and keep real store evidence missing.")


def validate_backend(errors: list[str], report: list[str]) -> None:
    deployment = load_json(BACKEND_DEPLOYMENT)
    receipt = load_json(RECEIPT_CONTRACT)
    if deployment.get("status") != "contract_ready_not_deployed":
        errors.append(f"{rel(BACKEND_DEPLOYMENT)} must be contract_ready_not_deployed until staging/production URLs exist.")
    evidence = deployment.get("deploymentEvidence", {})
    if evidence.get("stagingUrl") is not None or evidence.get("productionUrl") is not None:
        errors.append(f"{rel(BACKEND_DEPLOYMENT)} cannot claim deployed URLs without real evidence.")
    if receipt.get("status") != "contract_only_not_integrated_with_store_apis":
        errors.append(f"{rel(RECEIPT_CONTRACT)} must stay contract_only_not_integrated_with_store_apis until real API integration exists.")
    for platform in receipt.get("platforms", []):
        if platform.get("implemented") is not False:
            errors.append(f"{rel(RECEIPT_CONTRACT)} cannot mark {platform.get('platform')} receipt verification implemented.")
    report.append("- Backend deployment and receipt-verification contracts are present while deployed service evidence remains missing.")


def validate_ledger(errors: list[str], report: list[str]) -> None:
    ledger = load_json(READINESS_LEDGER)
    if ledger.get("status") != "repo_owned_non_human_artifacts_added_external_blockers_remain":
        errors.append(f"{rel(READINESS_LEDGER)} must keep external blockers explicit.")
    categories = {item.get("category"): item for item in ledger.get("criteria", [])}
    for category in [
        "Concept score",
        "Content/story readiness",
        "Visual/art readiness",
        "Audio readiness",
        "Payment readiness",
        "Backend readiness",
        "Compliance readiness",
        "Store readiness",
    ]:
        item = categories.get(category)
        if not item:
            errors.append(f"{rel(READINESS_LEDGER)} missing category {category}.")
            continue
        if not item.get("repoOwnedArtifacts") or not item.get("remainingBlockers"):
            errors.append(f"{rel(READINESS_LEDGER)} category {category} must list artifacts and remaining blockers.")
    report.append("- Release readiness ledger separates repo-owned artifacts from remaining external blockers.")


def main() -> int:
    errors: list[str] = []
    required = [
        MARKET_PLAN,
        POSITIONING,
        READINESS_LEDGER,
        DATA_FLOW,
        BEHAVIOR_FLAGS,
        PRIVACY_DRAFT,
        PRIVACY_LABELS,
        ACCESSIBILITY_QA,
        PRODUCT_CONFIG,
        APP_STORE_METADATA,
        GOOGLE_PLAY_METADATA,
        RELEASE_ASSETS,
        BACKEND_DEPLOYMENT,
        RECEIPT_CONTRACT,
    ]
    if not all(require_file(errors, path) for path in required):
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    report: list[str] = [
        "# Non-Human Readiness Report",
        "",
        "This report validates repo-owned readiness artifacts that do not require real people, real store consoles, or a deployed production backend. It does not count as external validation.",
        "",
    ]
    validate_market(errors, report)
    validate_compliance(errors, report)
    validate_store_and_payments(errors, report)
    validate_backend(errors, report)
    validate_ledger(errors, report)

    report.extend(
        [
            "",
            "## Remaining True Blockers",
            "",
            "- Parent/customer testing, pricing validation, retention/conversion, and willingness-to-pay evidence.",
            "- External editorial, Korean-language, cultural, child-safety, legal, and store review.",
            "- Final/reviewed art, final mastered narration, and final sound design.",
            "- Real App Store Connect and Google Play Console products plus sandbox/internal-track purchase evidence.",
            "- Deployed backend, durable database, production auth/RBAC, monitoring, backups, and receipt/token verification.",
            "- Real-device accessibility and store packaging QA.",
            "",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(report), encoding="utf-8")

    if errors:
        print("Moon Jar non-human readiness validation failed:")
        for error in errors:
            print(f"- {error}")
        print(f"Report: {rel(REPORT)}")
        return 1

    print("Moon Jar non-human readiness validation passed: repo-owned market/store/privacy/backend artifacts are present and honest.")
    print(f"Report: {rel(REPORT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
