#!/usr/bin/env python3
"""Drive Android emulator UI across every catalog story and capture evidence."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "shared-content" / "catalog.json"
PACKAGE = "com.moonjar.stories"
ACTIVITY = f"{PACKAGE}/.MainActivity"


@dataclass
class UiNode:
    element: ET.Element
    parent: "UiNode | None"

    @property
    def text(self) -> str:
        return self.element.attrib.get("text", "")

    @property
    def content_desc(self) -> str:
        return self.element.attrib.get("content-desc", "")

    @property
    def clickable(self) -> bool:
        return self.element.attrib.get("clickable") == "true"

    @property
    def enabled(self) -> bool:
        return self.element.attrib.get("enabled") == "true"

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        raw = self.element.attrib.get("bounds", "[0,0][0,0]")
        match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", raw)
        if not match:
            return (0, 0, 0, 0)
        return tuple(int(part) for part in match.groups())  # type: ignore[return-value]

    def center(self) -> tuple[int, int]:
        left, top, right, bottom = self.bounds
        return ((left + right) // 2, (top + bottom) // 2)

    def clickable_ancestor(self) -> "UiNode":
        current: UiNode | None = self
        while current is not None:
            if current.clickable and current.enabled:
                return current
            current = current.parent
        return self


class AndroidQa:
    def __init__(self, serial: str, output: Path) -> None:
        self.serial = serial
        self.output = output
        self.output.mkdir(parents=True, exist_ok=True)
        self.xml_path = self.output / "window.xml"
        self._screen_size: tuple[int, int] | None = None

    def adb(
        self,
        *args: str,
        check: bool = True,
        capture: bool = True,
        timeout: float = 30,
    ) -> subprocess.CompletedProcess[str]:
        command = ["adb", "-s", self.serial, *args]
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=capture,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            if check:
                raise
            return subprocess.CompletedProcess(command, 124, "", "timeout")
        if check and completed.returncode != 0:
            raise subprocess.CalledProcessError(
                completed.returncode,
                command,
                output=completed.stdout,
                stderr=completed.stderr,
            )
        return completed

    def shell(self, *args: str, check: bool = True, timeout: float = 30) -> str:
        return self.adb("shell", *args, check=check, timeout=timeout).stdout

    def tap(self, x: int, y: int) -> None:
        self.shell("input", "tap", str(x), str(y))
        time.sleep(0.45)

    def screen_size(self) -> tuple[int, int]:
        if self._screen_size is None:
            raw = self.shell("wm", "size")
            match = re.search(r"(\d+)x(\d+)", raw)
            self._screen_size = (int(match.group(1)), int(match.group(2))) if match else (1080, 2400)
        return self._screen_size

    def tap_scaled(self, base_x: int, base_y: int) -> None:
        width, height = self.screen_size()
        self.tap(round(base_x * width / 1080), round(base_y * height / 2400))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 550) -> None:
        self.shell("input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms))
        time.sleep(0.65)

    def screenshot(self, filename: str) -> Path:
        path = self.output / filename
        with path.open("wb") as handle:
            subprocess.run(
                ["adb", "-s", self.serial, "exec-out", "screencap", "-p"],
                cwd=ROOT,
                stdout=handle,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        return path

    def dump(self, filename: str | None = None) -> list[UiNode]:
        dumped = False
        for _ in range(2):
            try:
                self.shell("uiautomator", "dump", "/sdcard/window.xml", timeout=12)
                dumped = True
                break
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                self.shell("input", "keyevent", "111", check=False, timeout=4)
                time.sleep(0.6)
        if not dumped:
            return []
        self.adb("pull", "/sdcard/window.xml", str(self.xml_path), capture=True, timeout=8)
        if filename:
            shutil.copyfile(self.xml_path, self.output / filename)
        try:
            root = ET.fromstring(self.xml_path.read_text(encoding="utf-8", errors="ignore"))
        except ET.ParseError:
            return []
        nodes: list[UiNode] = []

        def walk(element: ET.Element, parent: UiNode | None) -> None:
            node = UiNode(element=element, parent=parent)
            nodes.append(node)
            for child in element:
                walk(child, node)

        walk(root, None)
        return nodes

    def find_node(self, *, text: str | None = None, content_desc: str | None = None) -> UiNode | None:
        nodes = self.dump()
        for node in nodes:
            if text is not None and node.text == text:
                return node
            if content_desc is not None and node.content_desc == content_desc:
                return node
        return None

    def tap_node(self, node: UiNode) -> None:
        target = node.clickable_ancestor()
        self.tap(*target.center())

    def tap_text(self, text: str) -> bool:
        node = self.find_node(text=text)
        if node is None:
            return False
        self.tap_node(node)
        return True

    def tap_desc(self, content_desc: str) -> bool:
        node = self.find_node(content_desc=content_desc)
        if node is None:
            return False
        self.tap_node(node)
        return True

    def launch(self, force_stop: bool = True) -> None:
        if force_stop:
            self.shell("am", "force-stop", PACKAGE)
        self.shell("am", "start", "-n", ACTIVITY)
        self.wait_for_library(timeout=24)
        time.sleep(1.5)

    def bring_to_front(self) -> None:
        self.shell("am", "start", "-n", ACTIVITY, check=False)
        time.sleep(1.0)

    def wait_for_text(self, text: str, timeout: float = 10) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.find_node(text=text) is not None:
                return True
            time.sleep(0.4)
        return False

    def library_visible(self) -> bool:
        texts = {node.text for node in self.dump()}
        return "The Sun and the Moon" in texts and "The Gold Axe and Silver Axe" in texts

    def wait_for_library(self, timeout: float = 10) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.library_visible():
                return True
            time.sleep(0.4)
        return False

    def ensure_library(self) -> bool:
        if self.library_visible():
            return True
        self.bring_to_front()
        if self.library_visible():
            return True
        for _ in range(2):
            self.shell("input", "keyevent", "4", check=False)
            if self.wait_for_library(timeout=6):
                return True
        self.bring_to_front()
        if self.wait_for_library(timeout=6):
            return True
        return False

    def scroll_library_to_top(self) -> None:
        for _ in range(5):
            self.swipe(540, 680, 540, 2200, 260)

    def open_book_from_library(self, title_en: str, title_ko: str) -> bool:
        if not self.ensure_library():
            return False
        self.scroll_library_to_top()
        for _ in range(28):
            nodes = self.dump()
            target = None
            for node in nodes:
                if node.text in {title_en, title_ko} or node.content_desc == title_en:
                    target = node
                    break
            if target is not None:
                self.tap_node(target)
                return True
            self.swipe(540, 2120, 540, 520, 520)
        return False

    def unlock_if_needed(self) -> bool:
        nodes = self.dump()
        if any(node.text == "Read" for node in nodes):
            self.tap_text("Read")
            return True
        if not any(node.text == "Unlock" for node in nodes):
            return False
        self.tap_text("Unlock")
        if not self.wait_for_text("Premium Korean Library", timeout=8):
            return False
        self.tap_text("Continue")
        if not self.wait_for_text("7 + 5 =", timeout=8):
            return False
        edit = None
        for node in self.dump():
            if node.element.attrib.get("class") == "android.widget.EditText":
                edit = node
                break
        if edit is not None:
            self.tap_node(edit)
        else:
            self.tap(540, 1160)
        self.shell("input", "text", "12")
        time.sleep(0.3)
        self.tap_text("Continue")
        if not self.wait_for_text("Read", timeout=8):
            return False
        self.tap_text("Read")
        return True

    def reader_page_text_seen(self, expected: str) -> bool:
        return any(node.text == expected for node in self.dump())

    def return_to_library(self) -> bool:
        self.tap_scaled(106, 176)
        if self.wait_for_library(timeout=14):
            return True
        self.shell("input", "keyevent", "4", check=False)
        if self.wait_for_library(timeout=10):
            return True
        self.bring_to_front()
        for _ in range(2):
            if self.wait_for_library(timeout=6):
                return True
            self.shell("input", "keyevent", "4", check=False)
        return False

    def tap_reader_next(self) -> None:
        self.tap_scaled(887, 2072)

    def tap_reader_play(self) -> None:
        self.tap_scaled(374, 2072)


def load_catalog() -> list[dict]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    return [book for book in catalog["books"] if book["status"] == "complete"]


def write_report(output: Path, results: list[dict], serial: str) -> None:
    lines = [
        "# Android All-Story Emulator QA",
        "",
        f"- Device: `{serial}`",
        f"- Flow-passed books: {sum(1 for item in results if item['status'] == 'pass')} / {len(results)}",
        "- Evidence: real emulator launch, UIAutomator tree dumps, `adb shell input` taps, and screenshots.",
        "",
        "| # | Book | Access | Pages | Result | Notes |",
        "| ---: | --- | --- | ---: | --- | --- |",
    ]
    for index, result in enumerate(results, start=1):
        notes = "<br>".join(result["notes"]) if result["notes"] else "No tap/load blocker in automated pass."
        lines.append(
            f"| {index} | {result['title_en']} | {result['access']} | {result['pages']} | "
            f"{result['status']} | {notes} |"
        )
    lines.append("")
    lines.append("## Screenshot Files")
    for result in results:
        lines.append(
            f"- `{result['slug']}`: `{result.get('detail_screenshot', '')}`, "
            f"`{result.get('reader_screenshot', '')}`, `{result.get('reader_next_screenshot', '')}`"
        )
    (output / "android-all-story-qa-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output / "android-all-story-qa-results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True, help="ADB device serial to drive, for example emulator-5556.")
    parser.add_argument(
        "--output",
        default=str(ROOT / ".agent" / "tmp" / "artifacts" / "android-all-story-qa"),
        help="Artifact output directory.",
    )
    parser.add_argument("--only-slug", help="Run one catalog slug, useful for rerunning a missed story.")
    args = parser.parse_args()

    qa = AndroidQa(serial=args.serial, output=Path(args.output).resolve())
    books = load_catalog()
    if args.only_slug:
        books = [book for book in books if book["slug"] == args.only_slug]
        if not books:
            raise SystemExit(f"Unknown catalog slug: {args.only_slug}")
    qa.launch()
    qa.screenshot("library-start.png")

    results: list[dict] = []
    for index, book in enumerate(books, start=1):
        title = book["title"]
        title_en = title["en"]
        title_ko = title["ko"]
        pages = int(book["pageTarget"])
        slug = book["slug"]
        result = {
            "bookId": book["id"],
            "slug": slug,
            "title_en": title_en,
            "title_ko": title_ko,
            "access": book["access"],
            "pages": pages,
            "status": "pass",
            "notes": [],
        }

        if not qa.open_book_from_library(title_en, title_ko):
            result["status"] = "fail"
            result["notes"].append("Could not find/tap story tile in library.")
            results.append(result)
            print(f"{index:02d}/{len(books)} {slug}: {result['status']}", flush=True)
            qa.launch(force_stop=False)
            continue

        time.sleep(1.0)
        detail_name = f"{index:02d}-{slug}-detail.png"
        result["detail_screenshot"] = str(qa.screenshot(detail_name).relative_to(ROOT))
        qa.dump(f"{index:02d}-{slug}-detail.xml")
        detail_texts = [node.text for node in qa.dump()]
        if title_en not in detail_texts or title_ko not in detail_texts:
            result["status"] = "fail"
            result["notes"].append("Detail screen did not expose expected English/Korean title text.")

        if not qa.unlock_if_needed():
            result["status"] = "fail"
            result["notes"].append("Could not enter reader from detail screen.")
            results.append(result)
            qa.return_to_library()
            continue

        time.sleep(1.8)
        reader_name = f"{index:02d}-{slug}-reader-p1.png"
        result["reader_screenshot"] = str(qa.screenshot(reader_name).relative_to(ROOT))
        qa.tap_reader_next()
        time.sleep(2.8)
        next_name = f"{index:02d}-{slug}-reader-p2.png"
        result["reader_next_screenshot"] = str(qa.screenshot(next_name).relative_to(ROOT))

        qa.tap_reader_play()
        time.sleep(0.3)

        if not qa.return_to_library():
            result["status"] = "fail"
            result["notes"].append("Could not return to library after reader pass.")
            qa.launch(force_stop=False)

        results.append(result)
        print(f"{index:02d}/{len(books)} {slug}: {result['status']}", flush=True)

    write_report(qa.output, results, args.serial)
    failures = [item for item in results if item["status"] != "pass"]
    if failures:
        print(f"FAIL: {len(failures)} story QA failures. Report: {qa.output / 'android-all-story-qa-report.md'}")
        return 1
    print(f"PASS: all {len(results)} catalog stories opened and advanced on {args.serial}.")
    print(f"Report: {qa.output / 'android-all-story-qa-report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
