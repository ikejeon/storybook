#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
OUTPUT = ROOT / "tools" / "output" / "story_writing_score_report.md"

SENSORY_WORDS = {
    "warm", "cold", "steam", "smelled", "smell", "glow", "moon", "snow", "mist",
    "whisper", "whispered", "crackled", "rattled", "drifted", "shone", "soft",
    "rough", "smooth", "lantern", "shadow", "spark", "bubbled", "gold", "silver",
    "rice", "porridge", "persimmon", "hanji", "pine", "pond", "wind", "night",
}

CULTURAL_WORDS = {
    "rice cake", "rice cakes", "gotgam", "persimmon", "hanbok", "hanji", "porridge",
    "red bean", "mountain spirit", "gourd", "swallow", "cottage", "market", "pond",
    "ladle", "threshold", "moon jar", "village", "mountain", "roof", "eaves",
}

EMOTION_WORDS = {
    "brave", "afraid", "worried", "hungry", "kind", "greedy", "lonely", "proud",
    "gentle", "cunning", "watchful", "relief", "sorry", "ashamed", "hope",
    "laughed", "smiled", "trembled", "gasped", "muttered", "sighed",
    "accountability", "ache", "alarmed", "attention", "awe", "belonging",
    "bittersweet", "calm", "caution", "courage", "curious", "gratitude",
    "joy", "longing", "majestic", "peaceful", "protective", "relieved",
    "repair", "resolve", "respect", "restless", "reverent", "solemn",
    "sorrowful", "tender", "tenderness", "tension", "thankful", "trembling",
    "uneasy", "urgent", "warning", "wonder",
}

HOOK_WORDS = {
    "but", "then", "until", "before", "when", "suddenly", "outside", "door",
    "shadow", "voice", "knock", "secret", "promise", "next", "wait", "not yet",
}

ACTION_WORDS = {
    "ask", "asks", "begin", "begins", "change", "changes", "choose", "chooses",
    "come", "comes", "drop", "drops", "escape", "fall", "falls", "follow",
    "follows", "grow", "grows", "hear", "hears", "hide", "hides", "knock",
    "knocks", "learn", "learns", "listen", "listens", "open", "opens", "plan",
    "plans", "promise", "promises", "reveal", "reveals", "run", "runs", "share",
    "shares", "sing", "sings", "turn", "turns", "wait", "waits", "watch", "watches",
}

BOOK_TONE_REQUIREMENTS = {
    "book.sun_moon": ["cunning", "watchful", "hungry", "deceptive", "shadow", "door"],
    "book.gold_silver_axe": ["honest", "old iron axe", "gold", "silver", "tempt"],
    "book.heungbu_nolbu": ["kindness", "gourd", "saw", "share", "repair"],
    "book.tiger_persimmon": ["gotgam", "persimmon", "mighty persimmon", "funny", "sorry"],
    "book.red_bean_grandma": ["one warm spoonful", "clever plan", "threshold", "porridge"],
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def has_any(text: str, words: set[str] | list[str]) -> bool:
    lower = text.lower()
    return any(word in lower for word in words)


def pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def page_text(page: dict) -> str:
    story_beat = page.get("storyBeat", {})
    return " ".join(
        [
            page.get("englishText", ""),
            page.get("koreanText", ""),
            story_beat.get("purpose", ""),
            story_beat.get("emotion", ""),
            story_beat.get("pageTurnHook", ""),
            story_beat.get("readAloudCue", ""),
            story_beat.get("childInteraction", ""),
            page.get("imagePrompt", ""),
        ]
    )


def hook_is_strong(hook: str) -> bool:
    words = re.findall(r"[a-zA-Z']+", hook.lower())
    if len(words) < 5:
        return False
    if has_any(hook, HOOK_WORDS):
        return True
    if any(word in ACTION_WORDS for word in words):
        return True
    return len(words) >= 7


def score_book(book: dict) -> tuple[int, list[str], dict[str, int]]:
    pages = book["pages"]
    page_count = len(pages)
    issues: list[str] = []

    refrains = [page.get("refrain", "").strip() for page in pages if page.get("refrain", "").strip()]
    repeated_refrains = sum(count for count in Counter(refrains).values() if count >= 2)

    dialogue_pages = sum(1 for page in pages if '"' in page.get("englishText", "") or "\u201c" in page.get("englishText", ""))
    sensory_pages = sum(1 for page in pages if has_any(page_text(page), SENSORY_WORDS))
    cultural_pages = sum(1 for page in pages if has_any(page_text(page), CULTURAL_WORDS))
    emotion_pages = sum(1 for page in pages if has_any(page_text(page), EMOTION_WORDS))
    hook_pages = sum(1 for page in pages if hook_is_strong(page.get("storyBeat", {}).get("pageTurnHook", "")))
    action_pages = sum(1 for page in pages if page.get("storyBeat", {}).get("childInteraction", "").lower().startswith(("tap", "drag", "swipe", "trace", "count", "choose", "hold", "rub", "wrap", "open", "roll")))
    little_mode_pages = sum(
        1
        for page in pages
        if page.get("text", {}).get("enLittle")
        and page.get("text", {}).get("koLittle")
        and len(page["text"]["enLittle"]) < len(page.get("englishText", "")) * 0.85
    )
    vocab_definition_pages = sum(
        1
        for page in pages
        if all(item.get("definitionEn") and item.get("definitionKo") for item in page.get("vocabulary", []))
    )
    audio_direction_pages = sum(
        1
        for page in pages
        if "English-first" in page.get("audioPrompt", "")
        and "Korean optional" in page.get("audioPrompt", "")
        and len(page.get("storyBeat", {}).get("readAloudCue", "")) >= 18
    )

    tone_requirements = BOOK_TONE_REQUIREMENTS.get(book["id"], [])
    tone_text = " ".join(page_text(page) for page in pages)
    tone_hits = sum(1 for word in tone_requirements if word in tone_text.lower())

    metrics = {
        "refrains": min(100, round(100 * pct(repeated_refrains, max(3, page_count // 8)))),
        "dialogue": min(100, round(100 * pct(dialogue_pages, max(1, round(page_count * 0.35))))),
        "sensory": min(100, round(100 * pct(sensory_pages, max(1, round(page_count * 0.65))))),
        "culture": min(100, round(100 * pct(cultural_pages, max(1, round(page_count * 0.50))))),
        "emotion": min(100, round(100 * pct(emotion_pages, max(1, round(page_count * 0.50))))),
        "hooks": min(100, round(100 * pct(hook_pages, max(1, round(page_count * 0.70))))),
        "interaction": min(100, round(100 * pct(action_pages, page_count))),
        "little_mode": min(100, round(100 * pct(little_mode_pages, page_count))),
        "vocab": min(100, round(100 * pct(vocab_definition_pages, page_count))),
        "audio_direction": min(100, round(100 * pct(audio_direction_pages, page_count))),
        "book_tone": 100 if not tone_requirements else min(100, round(100 * pct(tone_hits, len(tone_requirements)))),
    }

    weights = {
        "refrains": 11,
        "dialogue": 8,
        "sensory": 10,
        "culture": 9,
        "emotion": 9,
        "hooks": 12,
        "interaction": 7,
        "little_mode": 8,
        "vocab": 7,
        "audio_direction": 7,
        "book_tone": 12,
    }
    weighted = sum(metrics[key] * weight for key, weight in weights.items()) / sum(weights.values())
    score = round(weighted)

    for key, value in metrics.items():
        if value < 95:
            issues.append(f"{key} {value}/100")
    return score, issues, metrics


def main() -> int:
    catalog = load(CATALOG)
    complete_entries = [entry for entry in catalog["books"] if entry.get("status") == "complete"]
    rows: list[str] = [
        "# Story Writing Score Report",
        "",
        "This is an internal craft scorecard for the complete demo books. It does not replace children-editor, Korean-language, cultural, or child-safety review.",
        "",
        "| Book | Score | Metrics Below 95 |",
        "| --- | ---: | --- |",
    ]
    scores: list[int] = []
    all_issues: list[str] = []
    for entry in complete_entries:
        book = load(CONTENT / entry["bookPath"])
        score, issues, metrics = score_book(book)
        scores.append(score)
        all_issues.extend(f"{book['title']['en']}: {issue}" for issue in issues)
        rows.append(f"| {book['title']['en']} | {score} | {', '.join(issues) if issues else 'none'} |")
        rows.append("")
        rows.append(f"Metrics for {book['title']['en']}:")
        rows.append("")
        for key, value in metrics.items():
            rows.append(f"- {key}: {value}")
        rows.append("")

    average = round(sum(scores) / len(scores)) if scores else 0
    rows.insert(4, f"Average score: **{average}/100**")
    rows.insert(5, "")
    OUTPUT.write_text("\n".join(rows) + "\n", encoding="utf-8")

    print(f"Story writing average score: {average}/100")
    print(f"Report: {OUTPUT.relative_to(ROOT)}")
    if average < 95 or all_issues:
        for issue in all_issues[:40]:
            print(f"- {issue}")
        if len(all_issues) > 40:
            print(f"... {len(all_issues) - 40} more issue(s)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
