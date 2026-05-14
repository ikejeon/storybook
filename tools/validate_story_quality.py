#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"

MIN_REFRAINS_BY_PAGE_COUNT = {
    20: 2,
    24: 2,
    26: 3,
    28: 3,
    30: 3,
    32: 3,
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def min_refrains(page_count: int) -> int:
    floor = 1
    for threshold, required in sorted(MIN_REFRAINS_BY_PAGE_COUNT.items()):
        if page_count >= threshold:
            floor = required
    return floor


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    catalog = load(CATALOG)
    complete_entries = [entry for entry in catalog["books"] if entry.get("status") == "complete"]

    for entry in complete_entries:
        book_path = CONTENT / entry["bookPath"]
        book = load(book_path)
        pages = book["pages"]
        context = f"{book_path.relative_to(ROOT)}"

        refrains = [page.get("refrain", "").strip() for page in pages if page.get("refrain", "").strip()]
        refrain_counts = Counter(refrains)
        required_refrains = min_refrains(len(pages))
        if len(refrains) < required_refrains:
            errors.append(f"{context}: expected at least {required_refrains} read-aloud refrain pages, found {len(refrains)}.")
        if refrains and max(refrain_counts.values()) < 2:
            warnings.append(f"{context}: refrains exist but no phrase repeats; repeated call-and-response may be weak.")

        for page in pages:
            page_label = f"{context} page {page['pageNumber']}"
            text = page.get("text", {})
            story_beat = page.get("storyBeat", {})
            english = page.get("englishText", "")
            korean = page.get("koreanText", "")
            en_little = text.get("enLittle", "")
            ko_little = text.get("koLittle", "")

            if text.get("enStandard") != english:
                errors.append(f"{page_label}: text.enStandard must match englishText.")
            if text.get("koStandard") != korean:
                errors.append(f"{page_label}: text.koStandard must match koreanText.")
            if not 35 <= len(english) <= 320:
                errors.append(f"{page_label}: English story text length should stay read-aloud friendly, got {len(english)} chars.")
            if not 20 <= len(korean) <= 260:
                errors.append(f"{page_label}: Korean story text length should stay read-aloud friendly, got {len(korean)} chars.")
            if len(en_little) > len(english):
                errors.append(f"{page_label}: Little Listener English should not be longer than Story Mode English.")
            if len(ko_little) > len(korean):
                errors.append(f"{page_label}: Little Listener Korean should not be longer than Story Mode Korean.")

            hook = story_beat.get("pageTurnHook", "")
            cue = story_beat.get("readAloudCue", "")
            interaction = story_beat.get("childInteraction", "")
            if len(hook.strip()) < 12:
                errors.append(f"{page_label}: pageTurnHook is too thin for picture-book pacing.")
            if len(cue.strip()) < 8:
                errors.append(f"{page_label}: readAloudCue is too thin for narrator direction.")
            if not interaction.lower().startswith(("tap", "drag", "swipe", "trace", "count", "choose", "hold", "rub", "wrap", "open", "roll")):
                warnings.append(f"{page_label}: childInteraction may be less actionable: {interaction!r}.")

            audio_prompt = page.get("audioPrompt", "")
            if "English-first" not in audio_prompt:
                errors.append(f"{page_label}: audioPrompt should preserve English-first U.S. demo direction.")
            if "Korean optional" not in audio_prompt:
                errors.append(f"{page_label}: audioPrompt should preserve optional Korean direction.")

            unsafe_story_terms = ("blood", "gore", "dead body")
            combined_story_text = f"{english} {korean} {book.get('summary', '')}".lower()
            if any(term in combined_story_text for term in unsafe_story_terms):
                errors.append(f"{page_label}: child-facing story text contains an unsafe term.")

    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        print("Moon Jar story quality validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Moon Jar story quality validation passed: {len(complete_entries)} complete books checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
