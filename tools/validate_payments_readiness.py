#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
IOS_ENTITLEMENT = ROOT / "ios" / "MoonJarStoriesiOS" / "Sources" / "MoonJarStoriesiOS" / "EntitlementStore.swift"
ANDROID_ENTITLEMENT = ROOT / "android" / "MoonJarStoriesAndroid" / "src" / "main" / "java" / "com" / "moonjar" / "stories" / "billing" / "EntitlementManager.kt"
IOS_TESTS = ROOT / "ios" / "MoonJarStoriesiOS" / "Tests" / "MoonJarStoriesiOSTests" / "EntitlementStoreTests.swift"
ANDROID_TESTS = ROOT / "android" / "MoonJarStoriesAndroid" / "src" / "test" / "java" / "com" / "moonjar" / "stories" / "billing" / "EntitlementManagerTest.kt"
RULES = ROOT / "docs" / "entitlement_rules.md"
OPENAPI = ROOT / "backend" / "openapi.yaml"
REPORT = ROOT / "tools" / "output" / "payments_readiness_report.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    catalog = json.loads((CONTENT / "catalog.json").read_text(encoding="utf-8"))
    premium_ids = [entry["id"] for entry in catalog["books"] if entry.get("access") == "premium"]
    expected_individual_products = {
        "com.moonjarstories.book." + book_id.removeprefix("book.")
        for book_id in premium_ids
    }

    ios = read(IOS_ENTITLEMENT)
    android = read(ANDROID_ENTITLEMENT)
    ios_tests = read(IOS_TESTS)
    android_tests = read(ANDROID_TESTS)
    rules = read(RULES)
    openapi = read(OPENAPI)

    required_ios_markers = [
        "static func individualBook",
        "static func all(for catalogBooks",
        "Product.products(for: MoonJarProductID.all(for: catalogBooks))",
        "Transaction.currentEntitlements",
    ]
    for marker in required_ios_markers:
        if marker not in ios:
            errors.append(f"{IOS_ENTITLEMENT.relative_to(ROOT)}: missing payment architecture marker `{marker}`.")

    required_android_markers = [
        "fun individualBook",
        "fun allForCatalog",
        "fun productIdsForCatalog",
        "restorePurchasesPlaceholder",
    ]
    for marker in required_android_markers:
        if marker not in android:
            errors.append(f"{ANDROID_ENTITLEMENT.relative_to(ROOT)}: missing payment architecture marker `{marker}`.")

    if "testProductIdsIncludeIndividualPremiumBooks" not in ios_tests:
        errors.append(f"{IOS_TESTS.relative_to(ROOT)}: missing individual-book product ID unit test.")
    if "productIdsIncludeIndividualPremiumBooks" not in android_tests:
        errors.append(f"{ANDROID_TESTS.relative_to(ROOT)}: missing individual-book product ID unit test.")

    for text, label in ((rules, RULES.relative_to(ROOT)), (openapi, OPENAPI.relative_to(ROOT))):
        for phrase in ("monthly", "annual", "lifetime", "individual"):
            if phrase not in text.lower():
                errors.append(f"{label}: entitlement/payment docs should mention `{phrase}`.")

    ios_sample_products = set(re.findall(r"com\.moonjarstories\.book\.[A-Za-z0-9_\\.-]+", ios_tests))
    android_sample_products = set(re.findall(r"com\.moonjarstories\.book\.[A-Za-z0-9_\\.-]+", android_tests))
    if not ios_sample_products:
        errors.append("iOS tests do not assert any individual-book product ID string.")
    if not android_sample_products:
        errors.append("Android tests do not assert any individual-book product ID string.")

    rows = [
        "# Payments Readiness Report",
        "",
        "This is a scaffold-readiness report. Real App Store / Google Play products, receipt/token verification, and store sandbox purchase tests are still production blockers.",
        "",
        f"- Premium catalog items needing individual product IDs: {len(premium_ids)}",
        f"- Expected individual product ID pattern: `com.moonjarstories.book.<book-slug-id>`",
        f"- Example expected IDs: {', '.join(sorted(expected_individual_products)[:5])}",
        "- iOS StoreKit 2 restore scaffold: present" if "Transaction.currentEntitlements" in ios else "- iOS StoreKit 2 restore scaffold: missing",
        "- Android billing abstraction scaffold: present" if "restorePurchasesPlaceholder" in android else "- Android billing abstraction scaffold: missing",
        "- Parent gate remains required before purchases/settings by kids-safety validation.",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")

    if errors:
        print("Moon Jar payments readiness validation failed:")
        for error in errors:
            print(f"- {error}")
        print(f"Report: {REPORT.relative_to(ROOT)}")
        return 1

    print("Moon Jar payments readiness validation passed: native StoreKit/Play Billing scaffold covers subscription, lifetime, and individual-book product IDs.")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
