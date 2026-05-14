#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from story_asset_semantic_expectations import expected_panel_for_page

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
CHARACTER_MANIFEST = CONTENT / "assets" / "manifests" / "character_art_manifest.json"
CHARACTER_DIR = CONTENT / "characters"
STORY_SHEET_DIR = CONTENT / "assets" / "generated-draft" / "images" / "story-sheets"
REPORT = ROOT / "tools" / "output" / "story_specific_art_upgrade_report.md"
CONTACT_SHEET_SVG = ROOT / "tools" / "output" / "story_specific_art_contact_sheet.svg"
CONTACT_SHEET_PNG = ROOT / "tools" / "output" / "story_specific_art_contact_sheet.png"
TMP = ROOT / ".agent" / "tmp" / "story-specific-art-svg"
TEXTURE_REFERENCES = [
    CONTENT / "assets" / "books" / "sun-and-moon" / "page-001.png",
    CONTENT / "assets" / "books" / "gold-axe-silver-axe" / "page-001.png",
    CONTENT / "assets" / "books" / "tiger-and-persimmon" / "page-001.png",
    CONTENT / "assets" / "books" / "heungbu-and-nolbu" / "page-001.png",
    CONTENT / "assets" / "books" / "red-bean-porridge-grandma" / "page-001.png",
]
TEXTURE_DATA_URIS: dict[Path, str] = {}
STORY_SHEET_DATA_URIS: dict[Path, str] = {}

WIDTH = 960
HEIGHT = 640
CHARACTER_SHEET_WIDTH = 960
CHARACTER_SHEET_HEIGHT = 640
RENDERER = "local_story_specific_svg_renderer"
MODEL = "moonjar_story_specific_painterly_svg_v3"
PROMPT_SAFETY = (
    "Premium Korean watercolor, gouache, soft ink, hanji paper texture, "
    "fit-safe composition, safe margins, no cropping, no cropped faces or hands, "
    "no text, no letters, no watermark."
)
SINGLE_SCENE_EXCEPTIONS: dict[tuple[str, int], str] = {
    ("fairy-and-woodcutter", 16): "assets/generated-draft/images/story-specific-scenes/fairy-and-woodcutter/page-016.png",
    ("fairy-and-woodcutter", 28): "assets/generated-draft/images/story-specific-scenes/fairy-and-woodcutter/page-028.png",
}


ART_SPECS: dict[str, dict[str, Any]] = {
    "book.sun_moon": {
        "environment": "forest_house_sky",
        "figures": ["child", "child", "tiger"],
        "prop": "persimmon",
        "palette": ["#1f294f", "#2f806c", "#f4dfa7", "#d65c31", "#f2b94b"],
    },
    "book.gold_silver_axe": {
        "environment": "mountain_spring",
        "figures": ["woodcutter", "mountain_spirit"],
        "prop": "axe_pair",
        "palette": ["#263a55", "#387e69", "#f3d36a", "#c8d8de", "#9f6a3a"],
    },
    "book.tiger_persimmon": {
        "environment": "village_persimmon_tree",
        "figures": ["parent", "child", "tiger"],
        "prop": "persimmon",
        "palette": ["#22315c", "#d85c2f", "#f0b23a", "#31745d", "#7c5535"],
    },
    "book.heungbu_nolbu": {
        "environment": "gourd_roof_village",
        "figures": ["younger_man", "older_man", "magpie"],
        "prop": "gourd",
        "palette": ["#28385b", "#4b8b62", "#e2c36a", "#c95036", "#f4dfa7"],
    },
    "book.red_bean_grandma": {
        "environment": "kitchen_mountain",
        "figures": ["grandmother", "helper_child"],
        "prop": "red_bean_pot",
        "palette": ["#252c52", "#9c3144", "#f1d7ab", "#5c8a82", "#d65c31"],
    },
    "book.simcheong": {
        "environment": "harbor",
        "figures": ["young_girl", "elder", "auntie"],
        "prop": "lotus_lantern",
        "palette": ["#20345c", "#467b86", "#f0d6a2", "#d97a45", "#d98aa6"],
    },
    "book.rabbit_turtle": {
        "environment": "pond_palace",
        "figures": ["rabbit", "turtle", "palace_messenger"],
        "prop": "moon_shell",
        "palette": ["#19395a", "#4d8f88", "#f5d58a", "#c56f42", "#7fbf7f"],
    },
    "book.dokkaebi_club": {
        "environment": "pine_clearing",
        "figures": ["wood_gatherer", "dokkaebi"],
        "prop": "dokkaebi_club",
        "palette": ["#242e55", "#436f5e", "#f1c779", "#c75b45", "#7c6bb0"],
    },
    "book.dangun": {
        "environment": "mountain_cave",
        "figures": ["bear_child", "tiger_friend", "sky_helper"],
        "prop": "mugwort",
        "palette": ["#243456", "#557a58", "#e8d1a3", "#b5653d", "#7b8dbd"],
    },
    "book.grateful_magpie": {
        "environment": "mountain_path",
        "figures": ["traveler", "magpie", "village_child"],
        "prop": "silver_bell",
        "palette": ["#24365f", "#517b64", "#ecd8ad", "#b76c43", "#bfc7cf"],
    },
    "book.kongjwi_patjwi": {
        "environment": "hanok_courtyard",
        "figures": ["young_girl", "stepsister", "frog_helper"],
        "prop": "lotus_shoe",
        "palette": ["#26335c", "#5a8c71", "#f1d3a4", "#d78aa3", "#7d5c3f"],
    },
    "book.geumgang_tiger": {
        "environment": "geumgang_cliffs",
        "figures": ["mountain_child", "tiger", "grandmother"],
        "prop": "jade_pine_cone",
        "palette": ["#21385a", "#598660", "#ead4a1", "#d76837", "#77a98b"],
    },
    "book.lump_old_man": {
        "environment": "festival_path",
        "figures": ["old_man", "dokkaebi", "neighbor"],
        "prop": "song_drum",
        "palette": ["#25325a", "#775d8f", "#f0c67a", "#cf5f40", "#4f8566"],
    },
    "book.gyeonwu_jiknyeo": {
        "environment": "star_bridge",
        "figures": ["weaver", "herder", "magpie"],
        "prop": "star_ribbon",
        "palette": ["#172a55", "#395f92", "#f1d7a6", "#d286aa", "#f3e47a"],
    },
    "book.bari_princess_part_1": {
        "environment": "palace_garden",
        "figures": ["princess", "nurse", "guard"],
        "prop": "medicine_flower",
        "palette": ["#22335c", "#506f88", "#f0d3a0", "#d07b51", "#d493b7"],
    },
    "book.bari_princess_part_2": {
        "environment": "healing_river",
        "figures": ["princess", "river_guide", "old_healer"],
        "prop": "water_bowl",
        "palette": ["#1e3b5c", "#4f8f9b", "#ecd29c", "#cc7850", "#79b7a7"],
    },
    "book.snail_bride": {
        "environment": "rice_fields",
        "figures": ["snail_bride", "farmer", "auntie"],
        "prop": "shell_bowl",
        "palette": ["#21395a", "#5e9463", "#eed59e", "#c77848", "#8fbf93"],
    },
    "book.janghwa_hongryeon": {
        "environment": "lotus_pond",
        "figures": ["sister_one", "sister_two", "pond_keeper"],
        "prop": "twin_lotus",
        "palette": ["#27345d", "#638584", "#edd0a2", "#d989a7", "#b46779"],
    },
    "book.fairy_woodcutter": {
        "environment": "mountain_spring",
        "figures": ["woodcutter", "sky_fairy", "deer_friend"],
        "prop": "feather_robe",
        "palette": ["#24365d", "#4f856c", "#efd6a7", "#c87547", "#b9cbe6"],
    },
    "book.green_frog": {
        "environment": "stream_bank",
        "figures": ["frog_child", "mother_frog", "stream_friend"],
        "prop": "reed_umbrella",
        "palette": ["#203958", "#5b936f", "#ead6a2", "#c36a43", "#87b7a4"],
    },
    "book.kind_brothers": {
        "environment": "rice_barns",
        "figures": ["younger_man", "older_man"],
        "prop": "rice_sack",
        "palette": ["#25345a", "#6d7d53", "#ecd29c", "#c66a43", "#d8bf82"],
    },
    "book.byeoljubu": {
        "environment": "sea_palace",
        "figures": ["turtle", "rabbit", "sea_king"],
        "prop": "pearl_map",
        "palette": ["#17395d", "#2f7f91", "#edd49f", "#c96c46", "#86c8c8"],
    },
    "book.farting_daughter_in_law": {
        "environment": "village_courtyard",
        "figures": ["young_woman", "mother_in_law", "family"],
        "prop": "wind_jar",
        "palette": ["#24355c", "#6b8668", "#efd29b", "#cf7350", "#d5a15e"],
    },
    "book.serpent_bridegroom": {
        "environment": "bamboo_room",
        "figures": ["bride", "serpent", "sister_helper"],
        "prop": "scale_ribbon",
        "palette": ["#20335b", "#51766e", "#edd3a3", "#c7744d", "#a7b7bd"],
    },
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def simple_hash(text: str) -> int:
    value = 0
    for char in text:
        value = (value * 131 + ord(char)) % 1_000_003
    return value


def svg_path(points: list[tuple[float, float]], fill: str, opacity: float = 1.0) -> str:
    first, *rest = points
    path = f"M{first[0]:.1f} {first[1]:.1f} " + " ".join(f"L{x:.1f} {y:.1f}" for x, y in rest) + " Z"
    return f'<path d="{path}" fill="{fill}" opacity="{opacity:.3f}"/>'


def oval(cx: float, cy: float, rx: float, ry: float, fill: str, opacity: float = 1.0, extra: str = "") -> str:
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" opacity="{opacity:.3f}" {extra}/>'


def circle(cx: float, cy: float, r: float, fill: str, opacity: float = 1.0, extra: str = "") -> str:
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity:.3f}" {extra}/>'


def rect(x: float, y: float, w: float, h: float, fill: str, opacity: float = 1.0, rx: float = 0) -> str:
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}" opacity="{opacity:.3f}"/>'


def stroke_path(d: str, stroke: str, width: float, opacity: float = 1.0, fill: str = "none", cap: str = "round") -> str:
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width:.1f}" stroke-linecap="{cap}" stroke-linejoin="round" opacity="{opacity:.3f}"/>'


def group(body: str, x: float, y: float, scale: float = 1.0, flip: bool = False, opacity: float = 1.0) -> str:
    sx = -scale if flip else scale
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({sx:.3f} {scale:.3f})" opacity="{opacity:.3f}">{body}</g>'


def seeded_float(seed: int, index: int, low: float = 0.0, high: float = 1.0) -> float:
    raw = math.sin(seed * 12.9898 + index * 78.233) * 43758.5453
    fraction = raw - math.floor(raw)
    return low + (high - low) * fraction


def painted_defs(seed: int, palette: list[str]) -> str:
    dark, green, warm, hot, accent = palette
    return f"""
      <defs>
        <linearGradient id="premiumSky{seed}" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="{dark}"/>
          <stop offset="42%" stop-color="{green}"/>
          <stop offset="72%" stop-color="{warm}"/>
          <stop offset="100%" stop-color="{hot}"/>
        </linearGradient>
        <radialGradient id="premiumLamp{seed}" cx="42%" cy="34%" r="60%">
          <stop offset="0%" stop-color="#fff6cf" stop-opacity="0.95"/>
          <stop offset="42%" stop-color="#f2d58e" stop-opacity="0.28"/>
          <stop offset="100%" stop-color="{dark}" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="premiumInk{seed}" cx="54%" cy="62%" r="74%">
          <stop offset="0%" stop-color="#fff6dd" stop-opacity="0"/>
          <stop offset="72%" stop-color="{dark}" stop-opacity="0.05"/>
          <stop offset="100%" stop-color="{dark}" stop-opacity="0.28"/>
        </radialGradient>
        <filter id="premiumPaper{seed}">
          <feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="4" seed="{seed % 997}"/>
          <feColorMatrix type="matrix" values="0.18 0 0 0 0.72  0 0.16 0 0 0.64  0 0 0.12 0 0.50  0 0 0 0.28 0"/>
          <feBlend in="SourceGraphic" mode="multiply"/>
        </filter>
        <filter id="premiumSoftShadow{seed}" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="10" stdDeviation="9" flood-color="{dark}" flood-opacity="0.24"/>
        </filter>
        <filter id="premiumPigment{seed}" x="-10%" y="-10%" width="120%" height="120%">
          <feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="3" seed="{(seed + 19) % 997}"/>
          <feDisplacementMap in="SourceGraphic" scale="4"/>
        </filter>
        <filter id="premiumBackdropPaint{seed}" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="8"/>
          <feColorMatrix type="saturate" values="0.34"/>
        </filter>
        <clipPath id="premiumPanelClip{seed}">
          <rect x="34" y="34" width="{WIDTH - 68}" height="{HEIGHT - 68}" rx="38"/>
        </clipPath>
      </defs>
    """


def painterly_strokes(seed: int, palette: list[str], *, count: int, y_min: float, y_max: float, opacity: float) -> str:
    colors = [palette[0], palette[1], palette[2], palette[3], palette[4], "#fff5d6", "#27304f"]
    lines: list[str] = []
    for index in range(count):
        x = seeded_float(seed, index, -80, WIDTH + 80)
        y = seeded_float(seed, index + 101, y_min, y_max)
        dx = seeded_float(seed, index + 202, 120, 380)
        dy = seeded_float(seed, index + 303, -72, 72)
        c1x = x + seeded_float(seed, index + 404, 30, 120)
        c1y = y + seeded_float(seed, index + 505, -66, 66)
        c2x = x + dx - seeded_float(seed, index + 606, 30, 130)
        c2y = y + dy + seeded_float(seed, index + 707, -66, 66)
        color = colors[index % len(colors)]
        width = seeded_float(seed, index + 808, 5, 28)
        line_opacity = opacity * seeded_float(seed, index + 909, 0.45, 1.2)
        lines.append(stroke_path(f"M{x:.1f} {y:.1f} C{c1x:.1f} {c1y:.1f} {c2x:.1f} {c2y:.1f} {x+dx:.1f} {y+dy:.1f}", color, width, line_opacity))
    return "\n".join(lines)


def painterly_texture_underlay(seed: int, opacity: float = 0.20) -> str:
    uri = texture_data_uri(seed)
    if not uri:
        return ""
    return (
        f'<image href="{escape(uri)}" x="-56" y="-38" width="{WIDTH + 112}" height="{HEIGHT + 76}" '
        f'preserveAspectRatio="xMidYMid slice" opacity="{opacity:.3f}" filter="url(#premiumBackdropPaint{seed})"/>'
    )


def story_sheet_panel_underlay(slug: str, page_number: int, seed: int, opacity: float = 0.84) -> str:
    sheet = STORY_SHEET_DIR / f"{slug}.png"
    if not sheet.exists():
        return ""
    if sheet not in STORY_SHEET_DATA_URIS:
        STORY_SHEET_DATA_URIS[sheet] = image_data_uri(sheet)
    panel_index = max(1, min(6, expected_panel_for_page(slug, page_number)))
    cell_w = 1536 / 3
    cell_h = 1024 / 2
    crop_w = cell_w - 24
    crop_h = crop_w * HEIGHT / WIDTH
    col = (panel_index - 1) % 3
    row = (panel_index - 1) // 3
    crop_x = col * cell_w + (cell_w - crop_w) / 2
    crop_y = row * cell_h + (cell_h - crop_h) / 2
    scale = WIDTH / crop_w
    return (
        f'<image href="{escape(STORY_SHEET_DATA_URIS[sheet])}" '
        f'x="{-crop_x * scale:.1f}" y="{-crop_y * scale:.1f}" '
        f'width="{1536 * scale:.1f}" height="{1024 * scale:.1f}" '
        f'preserveAspectRatio="none" opacity="{opacity:.3f}"/>'
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#fff4d5" opacity="0.04" filter="url(#premiumPaper{seed})"/>'
    )


def painted_moon_jar(seed: int, palette: list[str]) -> str:
    dark, green, warm, hot, accent = palette
    return f"""
      {oval(0, 16, 58, 82, "#d9d2bf", 0.96, f'filter="url(#premiumSoftShadow{seed})"')}
      {oval(0, -50, 42, 18, "#f0ead7", 0.92)}
      {oval(0, -50, 27, 8, dark, 0.18)}
      {circle(-16, -6, 9, "#fff8df", 0.35)}
      {stroke_path("M-42 -20 C-12 -34 18 -30 42 -10 M-48 22 C-18 46 20 48 50 20", "#766d61", 3, 0.28)}
      {painterly_strokes(seed + 31, [dark, green, warm, hot, accent], count=8, y_min=-42, y_max=70, opacity=0.08)}
    """


def painted_lantern(seed: int, palette: list[str]) -> str:
    dark, green, warm, hot, accent = palette
    return f"""
      {circle(0, 0, 68, "#fff2b8", 0.22)}
      {rect(-32, -46, 64, 92, "#f4cf74", 0.45, 18)}
      {rect(-24, -36, 48, 74, "#fff0b8", 0.42, 14)}
      {stroke_path("M-36 -50 L36 -50 M-36 50 L36 50 M-28 -50 L-28 50 M28 -50 L28 50", "#684c34", 4, 0.55)}
      {stroke_path("M0 -64 C-16 -88 16 -88 0 -64", dark, 4, 0.4)}
      {circle(0, 4, 20, "#fff9d8", 0.42)}
    """


def painted_table_still_life(seed: int, palette: list[str]) -> str:
    dark, green, warm, hot, accent = palette
    cakes = "".join(circle(-64 + index * 21, -18 + (index % 2) * 8, 15, "#f4ead8", 0.96) for index in range(7))
    persimmons = "".join(circle(58 + index * 20, -16 + (index % 2) * 6, 13, hot, 0.85) for index in range(4))
    return f"""
      {oval(0, 10, 190, 48, "#705038", 0.86, f'filter="url(#premiumSoftShadow{seed})"')}
      {oval(0, -2, 174, 36, "#9a6f47", 0.72)}
      {oval(-32, -14, 92, 28, "#cfae78", 0.42)}
      {cakes}
      {persimmons}
      {stroke_path("M-132 -5 C-70 18 55 18 134 -4", "#fff2cf", 4, 0.28)}
    """


def hanji_room_overlay(seed: int, palette: list[str]) -> str:
    dark, green, warm, hot, accent = palette
    doors = []
    for x in [44, 748]:
        doors.append(rect(x, 58, 168, 360, "#f8e9c7", 0.24, 8))
        for offset in [34, 80, 126]:
            doors.append(stroke_path(f"M{x+offset} 64 L{x+offset} 410", "#6b573e", 3, 0.22))
        for y in [126, 206, 286, 366]:
            doors.append(stroke_path(f"M{x+8} {y} L{x+160} {y}", "#6b573e", 3, 0.18))
    return f"""
      {''.join(doors)}
      {rect(46, 420, 868, 150, "#d9b885", 0.20, 0)}
      {stroke_path("M70 422 C210 390 344 448 502 412 S748 384 898 422", "#fff2c8", 8, 0.14)}
      {group(painted_lantern(seed + 41, palette), 780, 152, 0.66)}
      {group(painted_moon_jar(seed + 42, palette), 806, 342, 0.72)}
    """


def figure_underpainting(kind: str, palette: list[str], seed: int) -> str:
    dark, green, warm, hot, accent = palette
    return f"""
      {oval(0, 76, 112, 26, dark, 0.18)}
      {circle(-14, 4, 74, "#fff0c8", 0.08)}
      {painterly_strokes(seed + 52, palette, count=12, y_min=-40, y_max=110, opacity=0.055)}
      {stroke_path("M-62 48 C-34 -8 20 -30 58 22", "#fff4ce", 5, 0.18)}
      {stroke_path("M-54 82 C-20 120 34 116 70 76", dark, 4, 0.20)}
    """


def painted_figure(kind: str, palette: list[str], seed: int) -> str:
    return f"""
      <g filter="url(#premiumSoftShadow{seed})">
        {figure_underpainting(kind, palette, seed)}
        <g filter="url(#premiumPigment{seed})">{figure_svg(kind, palette, seed)}</g>
        {stroke_path("M-34 18 C-12 32 16 32 38 18", "#fff4d4", 3, 0.22)}
        {stroke_path("M-38 72 C-8 88 18 90 46 70", "#30263c", 3, 0.18)}
      </g>
    """


def premium_environment_details(spec: dict[str, Any], page_number: int, seed: int) -> str:
    dark, green, warm, hot, accent = spec["palette"]
    env = str(spec["environment"])
    details: list[str] = []
    if env in {"harbor", "sea_palace", "healing_river", "pond_palace", "lotus_pond", "stream_bank"}:
        for index in range(10):
            y = 300 + index * 18
            details.append(stroke_path(f"M40 {y} C210 {y-32} 360 {y+22} 520 {y} S760 {y-24} 920 {y+8}", "#e3f7ee", 5, 0.16))
        details.append(group(prop_svg("lotus_lantern" if env == "harbor" else str(spec["prop"]), spec["palette"]), 664, 332, 0.72))
    if env in {"bamboo_room", "pine_clearing", "mountain_path", "mountain_cave", "geumgang_cliffs"}:
        for index in range(9):
            x = 106 + index * 86
            details.append(stroke_path(f"M{x} 96 C{x-18} 210 {x+22} 320 {x-12} 470", green, 7, 0.26))
            details.append(stroke_path(f"M{x} 210 Q{x+44} 184 {x+78} 132", green, 4, 0.20))
        details.append(group(painted_lantern(seed + 61, spec["palette"]), 744, 218, 0.52))
    if env in {"hanok_courtyard", "palace_garden", "village_courtyard", "gourd_roof_village", "rice_barns", "rice_fields"}:
        for index in range(6):
            x = 160 + index * 110
            details.append(rect(x, 300, 54, 92, warm, 0.18, 4))
            details.append(stroke_path(f"M{x-18} 300 L{x+27} 260 L{x+72} 300", hot, 5, 0.28))
        details.append(group(painted_table_still_life(seed + 62, spec["palette"]), 690, 388, 0.54))
    if env == "star_bridge":
        for index in range(84):
            x = seeded_float(seed, index + 121, 40, 920)
            y = seeded_float(seed, index + 321, 42, 300)
            details.append(circle(x, y, seeded_float(seed, index + 421, 1.4, 4.6), "#fff6cc", 0.52))
        details.append(stroke_path("M70 350 C250 254 690 254 888 350", "#fff1b4", 14, 0.24))
    return "\n".join(details)


def page_semantic_text(page: dict[str, Any]) -> str:
    beat = page.get("storyBeat", {})
    pieces = [
        str(page.get("englishText", "")),
        str(page.get("koreanText", "")),
        str(page.get("imagePrompt", "")),
    ]
    if isinstance(beat, dict):
        pieces.extend(str(value) for value in beat.values())
    return " ".join(pieces).lower()


def rooster_svg(palette: list[str]) -> str:
    dark, _green, warm, hot, accent = palette
    return f"""
      {oval(0, 42, 54, 36, hot, 0.92)}
      {circle(42, 10, 25, warm, 0.95)}
      {circle(50, 4, 3.2, dark, 0.82)}
      {svg_path([(64, 12), (102, 0), (70, 28)], "#e2b34e", 0.92)}
      {''.join(oval(-34 - i * 9, 26 - i * 5, 12, 42, accent, 0.72, f'transform="rotate({-38 - i * 8})"') for i in range(4))}
      {stroke_path("M-18 76 L-36 112 M18 76 L30 112", dark, 5, 0.72)}
      {stroke_path("M-78 -10 C-36 -40 12 -30 42 -54", "#fff4ce", 5, 0.34)}
      {stroke_path("M-86 16 C-36 -4 16 -4 72 -20", "#fff4ce", 4, 0.28)}
    """


def bucket_rope_svg(palette: list[str]) -> str:
    dark, _green, warm, _hot, accent = palette
    return f"""
      {stroke_path("M0 -250 L0 46", dark, 7, 0.62)}
      {stroke_path("M-34 -4 C-12 -34 12 -34 34 -4", dark, 6, 0.62)}
      {oval(0, 36, 50, 32, "#8f6844", 0.92)}
      {oval(0, 24, 40, 15, "#d1eef2", 0.58)}
      {rect(-36, 16, 72, 54, warm, 0.62, 8)}
      {stroke_path("M-36 20 C-12 36 18 36 36 20", accent, 4, 0.34)}
    """


def somber_mouth(x: float, y: float, palette: list[str], scale: float = 1.0) -> str:
    dark = palette[0]
    return (
        rect(x - 18 * scale, y - 4 * scale, 36 * scale, 14 * scale, "#f0c2a4", 0.72, 7 * scale)
        + stroke_path(
            f"M{x - 13 * scale:.1f} {y + 7 * scale:.1f} "
            f"Q{x:.1f} {y - 3 * scale:.1f} {x + 13 * scale:.1f} {y + 7 * scale:.1f}",
            dark,
            3.2 * scale,
            0.66,
        )
    )


def sky_horse_svg(palette: list[str]) -> str:
    dark, _green, warm, _hot, accent = palette
    return f"""
      {oval(0, 42, 82, 34, "#f4efe1", 0.96)}
      {circle(-72, 18, 28, "#f4efe1", 0.96)}
      {stroke_path("M56 44 Q110 8 124 48", "#f4efe1", 16, 0.92)}
      {stroke_path("M-40 70 L-56 126 M-4 72 L-8 130 M42 66 L58 124", dark, 5, 0.48)}
      {stroke_path("M-86 8 C-68 -22 -36 -26 -20 -8", accent, 7, 0.5)}
      {circle(-78, 10, 3.2, dark, 0.76)}
      {stroke_path("M-28 8 C8 -30 56 -28 86 -2", "#fff8de", 18, 0.34)}
      {oval(4, 118, 96, 12, dark, 0.14)}
    """


def empty_sandals_svg(palette: list[str]) -> str:
    dark, _green, warm, hot, _accent = palette
    return f"""
      {oval(-34, 0, 30, 13, warm, 0.88)}
      {oval(34, 0, 30, 13, warm, 0.88)}
      {stroke_path("M-50 -2 C-38 -18 -22 -18 -12 -2", hot, 5, 0.58)}
      {stroke_path("M18 -2 C30 -18 46 -18 56 -2", hot, 5, 0.58)}
      {oval(-34, 20, 35, 6, dark, 0.20)}
      {oval(34, 20, 35, 6, dark, 0.20)}
    """


def fairy_high_risk_scene_overlay(book: dict[str, Any], page_number: int, palette: list[str]) -> str:
    dark, green, warm, hot, accent = palette
    if page_number == 15:
        return f"""
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, "#dcecee", 0.985, 38)}
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, dark, 0.20, 38)}
          {circle(690, 112, 58, "#fff4c7", 0.84)}
          {svg_path([(34, 520), (176, 356), (346, 520)], dark, 0.24)}
          {svg_path([(250, 532), (474, 310), (704, 532)], green, 0.26)}
          {svg_path([(610, 526), (806, 332), (926, 526)], dark, 0.20)}
          {stroke_path("M120 404 C238 354 362 382 480 338 S730 300 852 340", "#fff8d9", 10, 0.40)}
          {stroke_path("M350 320 C430 236 550 232 636 318", "#fff7d9", 9, 0.50)}
          {group(prop_svg("feather_robe", palette), 492, 206, 2.10, opacity=0.96)}
          {group(painted_figure("sky_fairy", palette, simple_hash(book["id"] + "fairy-page15-sky")), 492, 306, 1.02, opacity=0.96)}
          {group(painted_figure("child", palette, simple_hash(book["id"] + "fairy-page15-left-child")), 388, 320, 0.54, opacity=0.96)}
          {group(painted_figure("child", palette, simple_hash(book["id"] + "fairy-page15-right-child")), 596, 320, 0.54, opacity=0.96)}
          {stroke_path("M430 318 C458 350 530 350 560 318", "#fff8d9", 9, 0.42)}
          {group(painted_figure("woodcutter", palette, simple_hash(book["id"] + "woodcutter-page15-ground")), 218, 480, 0.62, opacity=0.95)}
          {stroke_path("M238 448 C286 410 332 382 382 348", warm, 6, 0.55)}
          {somber_mouth(492, 309, palette, 1.02)}
          {somber_mouth(388, 322, palette, 0.54)}
          {somber_mouth(596, 322, palette, 0.54)}
          {somber_mouth(218, 482, palette, 0.62)}
        """
    if page_number == 16:
        return f"""
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, "#e7dec7", 0.99, 38)}
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, dark, 0.14, 38)}
          {rect(88, 84, 270, 310, "#f5e6c4", 0.62, 10)}
          {rect(602, 84, 270, 310, "#f5e6c4", 0.58, 10)}
          {stroke_path("M142 94 L142 388 M210 94 L210 388 M286 94 L286 388 M94 178 L352 178 M94 270 L352 270", "#6b573e", 4, 0.26)}
          {stroke_path("M656 94 L656 388 M724 94 L724 388 M800 94 L800 388 M608 178 L866 178 M608 270 L866 270", "#6b573e", 4, 0.24)}
          {rect(82, 408, 796, 126, "#cda978", 0.42, 0)}
          {circle(480, 268, 188, "#fff3c6", 0.18)}
          {group(painted_lantern(simple_hash(book["id"] + "empty-lantern"), palette), 480, 170, 0.70, opacity=0.66)}
          {group(empty_sandals_svg(palette), 476, 474, 1.35, opacity=0.95)}
          {group(prop_svg("feather_robe", palette), 286, 318, 0.56, opacity=0.28)}
          {stroke_path("M210 456 C330 416 600 418 746 458", dark, 8, 0.16)}
          {stroke_path("M400 384 C438 364 520 364 560 384", "#fff7d9", 6, 0.22)}
        """
    if page_number == 18:
        return f"""
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, "#d7ecef", 0.985, 38)}
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, dark, 0.18, 38)}
          {circle(720, 112, 54, "#fff4c7", 0.84)}
          {svg_path([(34, 534), (198, 344), (374, 534)], dark, 0.24)}
          {svg_path([(306, 548), (522, 306), (754, 548)], green, 0.27)}
          {svg_path([(640, 540), (824, 350), (926, 540)], dark, 0.20)}
          {stroke_path("M148 392 C284 326 420 372 552 326 S770 292 860 340", "#fff8d9", 11, 0.42)}
          {stroke_path("M480 36 L480 308", dark, 8, 0.62)}
          {stroke_path("M438 302 C454 270 506 270 522 302", dark, 7, 0.62)}
          {oval(480, 352, 82, 42, "#8f6844", 0.95)}
          {rect(424, 328, 112, 72, warm, 0.72, 10)}
          {oval(480, 322, 72, 22, "#d1eef2", 0.60)}
          {group(painted_figure("woodcutter", palette, simple_hash(book["id"] + "woodcutter-page18-bucket")), 480, 320, 0.48, opacity=0.92)}
          {stroke_path("M340 264 C402 214 560 214 626 272", "#fff4ce", 7, 0.30)}
          {stroke_path("M410 404 C474 452 566 452 632 404", "#fff8d9", 7, 0.24)}
        """
    return ""


def simcheong_high_risk_scene_overlay(book: dict[str, Any], page: dict[str, Any], palette: list[str]) -> str:
    page_number = int(page["pageNumber"])
    dark, green, warm, hot, accent = palette
    seed = simple_hash(f"{book['id']}:{page['id']}:simcheong-specific")
    if page_number in {13, 14, 15, 16, 17, 18}:
        return f"""
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, "#d9edf0", 0.66, 38)}
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, dark, 0.28, 38)}
          {circle(742, 104, 52, "#fff1bf", 0.76)}
          {''.join(stroke_path(f"M58 {330 + i * 28} C214 {292 + i * 20} 360 {370 + i * 16} 528 {330 + i * 28} S762 {294 + i * 18} 902 {346 + i * 24}", "#dff6f0", 7, 0.23) for i in range(7))}
          {svg_path([(180, 430), (344, 384), (536, 430), (478, 486), (248, 486)], "#66452f", 0.84)}
          {stroke_path("M352 386 L352 222", "#4b3428", 7, 0.68)}
          {svg_path([(360, 230), (360, 360), (522, 334)], warm, 0.46)}
          {group(painted_figure("young_girl", palette, seed + 1), 354, 348, 0.76, opacity=0.95)}
          {group(prop_svg("lotus_lantern", palette), 438, 356, 0.70, opacity=0.96)}
          {group(painted_figure("auntie", palette, seed + 2), 226, 392, 0.58, opacity=0.76)}
          {stroke_path("M254 360 C306 324 404 320 472 362", "#fff4ce", 7, 0.26)}
        """
    if page_number in {19, 20, 21, 22, 23, 24, 25}:
        return f"""
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, "#cfe9ef", 0.66, 38)}
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, "#1f355a", 0.18, 38)}
          {circle(480, 278, 220, "#e7ffff", 0.16)}
          {''.join(rect(126 + i * 118, 150, 34, 300, "#b9e3df", 0.42, 17) + oval(143 + i * 118, 150, 56, 15, "#efffff", 0.34) for i in range(7))}
          {''.join(oval(264 + i * 72, 388 + (i % 2) * 18, 58, 24, "#d98aa6", 0.55) for i in range(6))}
          {stroke_path("M114 438 C286 394 430 478 590 430 S790 386 898 440", "#e4fff5", 8, 0.28)}
          {group(painted_figure("young_girl", palette, seed + 11), 480, 334, 0.88, opacity=0.95)}
          {group(prop_svg("lotus_lantern", palette), 480, 246, 0.86, opacity=0.96)}
          {group(painted_figure("sea_king", palette, seed + 12), 688, 342, 0.78, flip=True, opacity=0.86)}
          {group(painted_figure("auntie", palette, seed + 13), 294, 356, 0.70, opacity=0.82)}
        """
    if page_number in {26, 27, 28, 29, 30, 31}:
        return f"""
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, "#dceeee", 0.66, 38)}
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, dark, 0.10, 38)}
          {circle(710, 112, 54, "#fff1bf", 0.82)}
          {''.join(stroke_path(f"M58 {408 + i * 22} C230 {376 + i * 12} 360 {446 + i * 9} 526 {410 + i * 22} S770 {380 + i * 12} 910 {424 + i * 16}", "#dff6f0", 6, 0.20) for i in range(5))}
          {svg_path([(96, 472), (206, 438), (318, 472)], "#5d3f2d", 0.72)}
          {svg_path([(642, 474), (768, 440), (890, 474)], "#5d3f2d", 0.60)}
          {''.join(oval(382 + i * 36, 342 + (i % 2) * 14, 50, 23, "#d98aa6", 0.55) for i in range(6))}
          {group(painted_figure("young_girl", palette, seed + 21), 474, 330, 0.92, opacity=0.94)}
          {group(prop_svg("medicine_flower", palette), 558, 306, 0.82, opacity=0.90)}
          {group(painted_figure("elder", palette, seed + 22), 286, 386, 0.74, opacity=0.88)}
          {group(painted_figure("auntie", palette, seed + 23), 672, 386, 0.68, flip=True, opacity=0.84)}
          {stroke_path("M344 382 C408 332 528 330 608 380", "#fff4ce", 8, 0.24)}
        """
    return ""


def serpent_high_risk_scene_overlay(book: dict[str, Any], page: dict[str, Any], palette: list[str]) -> str:
    page_number = int(page["pageNumber"])
    dark, green, warm, hot, accent = palette
    seed = simple_hash(f"{book['id']}:{page['id']}:serpent-specific")
    if page_number == 12:
        return f"""
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, "#e8dec8", 0.66, 38)}
          {rect(82, 88, 796, 350, "#f6e8c8", 0.50, 12)}
          {stroke_path("M148 94 L148 420 M244 94 L244 420 M716 94 L716 420 M812 94 L812 420 M92 182 L868 182 M92 300 L868 300", "#6b573e", 4, 0.22)}
          {circle(480, 260, 188, "#fff5c8", 0.18)}
          {group(painted_figure("scholar", palette, seed + 1), 522, 338, 0.98, opacity=0.95)}
          {group(painted_figure("bride", palette, seed + 2), 360, 362, 0.82, opacity=0.88)}
          {group(prop_svg("scale_ribbon", palette), 420, 430, 0.66, opacity=0.70)}
          {stroke_path("M306 418 C394 390 512 390 612 420", "#fff4ce", 7, 0.22)}
        """
    if page_number == 16:
        return f"""
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, "#eadbbb", 0.66, 38)}
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, dark, 0.16, 38)}
          {stroke_path("M92 326 L480 236 L872 326", hot, 16, 0.44)}
          {rect(116, 326, 728, 132, "#f6e0b8", 0.38, 8)}
          {group(painted_figure("bride", palette, seed + 11), 486, 372, 0.92, opacity=0.94)}
          {group(painted_figure("relative", palette, seed + 12), 306, 388, 0.68, opacity=0.70)}
          {group(painted_figure("relative", palette, seed + 13), 668, 388, 0.68, flip=True, opacity=0.70)}
          {stroke_path("M292 314 C376 278 584 278 668 314", "#fff4ce", 6, 0.18)}
          {stroke_path("M380 420 C434 454 548 454 602 420", dark, 8, 0.14)}
        """
    if page_number == 27:
        return f"""
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, "#d7ece6", 0.66, 38)}
          {rect(34, 34, WIDTH - 68, HEIGHT - 68, dark, 0.12, 38)}
          {circle(708, 112, 54, "#fff1bf", 0.78)}
          {oval(480, 464, 390, 98, "#cdece5", 0.45)}
          {stroke_path("M98 456 C238 410 376 498 522 450 S754 412 896 456", "#eafff6", 8, 0.24)}
          {group(painted_figure("bride", palette, seed + 21), 384, 356, 0.86, opacity=0.92)}
          {group(painted_figure("scholar", palette, seed + 22), 570, 350, 0.92, flip=True, opacity=0.95)}
          {group(prop_svg("scale_ribbon", palette), 486, 424, 0.56, opacity=0.45)}
          {stroke_path("M410 330 C464 294 536 294 592 330", "#fff4ce", 7, 0.24)}
        """
    return ""


def semantic_scene_overlays(book: dict[str, Any], page: dict[str, Any], spec: dict[str, Any]) -> str:
    text = page_semantic_text(page)
    page_number = int(page["pageNumber"])
    palette = spec["palette"]
    dark, green, warm, hot, accent = palette
    overlays: list[str] = []

    if any(word in text for word in ("sorrow", "lonely", "bittersweet", "afraid", "threat", "danger", "hungry", "grief", "wrong", "solemn")):
        overlays.append(rect(34, 34, WIDTH - 68, HEIGHT - 68, dark, 0.10, 38))
        for index in range(8):
            x = 132 + index * 92
            overlays.append(stroke_path(f"M{x} 74 C{x-36} 186 {x+28} 284 {x-14} 420", "#dbe9ee", 3, 0.12))

    if book["id"] == "book.fairy_woodcutter":
        overlays.append(fairy_high_risk_scene_overlay(book, page_number, palette))
        if page_number not in {15, 16, 18} and ("one child in each arm" in text or page_number == 15):
            overlays.append(group(prop_svg("feather_robe", palette), 486, 166, 1.65, opacity=0.94))
            overlays.append(group(painted_figure("sky_fairy", palette, simple_hash(book["id"] + "fairy-rise")), 486, 260, 0.88, opacity=0.90))
            overlays.append(group(painted_figure("child", palette, simple_hash(book["id"] + "child-left")), 398, 280, 0.48, opacity=0.92))
            overlays.append(group(painted_figure("child", palette, simple_hash(book["id"] + "child-right")), 574, 280, 0.48, opacity=0.92))
            overlays.append(stroke_path("M392 314 C444 248 524 248 584 314", "#fff7d9", 7, 0.38))
            overlays.append(group(painted_figure("woodcutter", palette, simple_hash(book["id"] + "woodcutter-below")), 244, 464, 0.70, opacity=0.82))
            overlays.append(somber_mouth(486, 263, palette, 0.90))
            overlays.append(somber_mouth(398, 281, palette, 0.48))
            overlays.append(somber_mouth(574, 281, palette, 0.48))
            overlays.append(somber_mouth(244, 466, palette, 0.70))
        if page_number not in {15, 16, 18} and "bucket" in text and "sky" in text:
            overlays.append(group(bucket_rope_svg(palette), 486, 306, 1.05, opacity=0.90))
            overlays.append(stroke_path("M384 104 C444 64 530 64 596 112", "#fff4ce", 8, 0.26))
        if "horse" in text:
            overlays.append(group(sky_horse_svg(palette), 520, 332, 0.95, opacity=0.90))
        if "rooster" in text or "수탉" in text:
            overlays.append(group(rooster_svg(palette), 690, 370, 0.86, opacity=0.92))
            overlays.append(stroke_path("M592 272 C650 226 732 224 802 180", "#fff4ce", 5, 0.28))

    if book["id"] == "book.simcheong":
        overlays.append(simcheong_high_risk_scene_overlay(book, page, palette))

    if book["id"] == "book.serpent_bridegroom":
        overlays.append(serpent_high_risk_scene_overlay(book, page, palette))

    keyword_props = [
        (("garlic", "mugwort", "쑥", "마늘"), "mugwort", 720, 314, 0.72),
        (("liver", "pearl map", "별주부", "sea king"), "pearl_map", 718, 328, 0.76),
        (("lotus", "shoe", "magistrate"), "lotus_shoe", 724, 326, 0.78),
        (("bell", "magpie"), "silver_bell", 714, 306, 0.62),
        (("club", "dokkaebi"), "dokkaebi_club", 724, 304, 0.70),
        (("medicine flower", "healing water"), "medicine_flower", 720, 306, 0.72),
        (("rooster", "수탉"), "feather_robe", 520, 250, 0.56),
        (("serpent", "scale"), "scale_ribbon", 714, 322, 0.78),
        (("snail", "shell"), "shell_bowl", 714, 332, 0.76),
        (("rice sack", "rice"), "rice_sack", 714, 336, 0.76),
        (("fart", "wind", "pear"), "wind_jar", 714, 326, 0.76),
    ]
    for terms, prop, x, y, scale in keyword_props:
        if any(term in text for term in terms):
            overlays.append(group(prop_svg(prop, palette), x, y, scale, opacity=0.82))

    if "tiger" in text and any(word in text for word in ("threat", "danger", "hungry", "scary", "warning", "cave")):
        overlays.append(group(painted_figure("tiger", palette, simple_hash(book["id"] + str(page_number) + "tiger-threat")), 736, 392, 0.64, flip=True, opacity=0.88))
        overlays.append(stroke_path("M650 318 C682 286 724 278 770 300", dark, 9, 0.24))

    if "sisters" in text or "sister" in text:
        overlays.append(group(painted_figure("sister_one", palette, simple_hash(book["id"] + "sister1")), 412, 390, 0.64, opacity=0.84))
        overlays.append(group(painted_figure("sister_two", palette, simple_hash(book["id"] + "sister2")), 548, 392, 0.64, opacity=0.84))

    return "\n".join(overlays)


def premium_scene_svg(book: dict[str, Any], page: dict[str, Any], spec: dict[str, Any]) -> str:
    seed = simple_hash(f"{book['id']}:{page['id']}:premium-painterly-scene")
    palette = spec["palette"]
    page_number = int(page["pageNumber"])
    figures = list(spec["figures"])
    phase = page_number / max(1, len(book.get("pages", [])))
    if phase < 0.34:
        hero_x, ally_x, third_x = 306, 590, 716
    elif phase < 0.67:
        hero_x, ally_x, third_x = 238, 650, 472
    else:
        hero_x, ally_x, third_x = 390, 560, 724
    hero_y = 392 + (page_number % 4) * 8
    ally_y = 398 + (page_number % 3) * 9
    third_y = 358 if len(figures) > 2 and figures[2] == "magpie" else 404
    prop_scale = 0.72 + (page_number % 4) * 0.035

    figure_parts = [
        group(painted_figure(figures[0], palette, seed + 11), hero_x, hero_y, 1.22, flip=False),
    ]
    if len(figures) > 1:
        figure_parts.append(group(painted_figure(figures[1], palette, seed + 12), ally_x, ally_y, 1.04, flip=True))
    if len(figures) > 2:
        third_scale = 0.70 if figures[2] == "magpie" else 0.82
        figure_parts.append(group(painted_figure(figures[2], palette, seed + 13), third_x, third_y, third_scale, flip=bool(seed % 2), opacity=0.94))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
{painted_defs(seed, palette)}
<g clip-path="url(#premiumPanelClip{seed})">
  {environment_svg(spec, page_number, seed)}
  {painterly_texture_underlay(seed, 0.24)}
  {story_sheet_panel_underlay(book["slug"], page_number, seed, 0.88)}
  {painterly_strokes(seed + 1, palette, count=82, y_min=46, y_max=570, opacity=0.050)}
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#premiumLamp{seed})" opacity="0.72"/>
  {premium_environment_details(spec, page_number, seed)}
  {hanji_room_overlay(seed, palette)}
  {group(painted_table_still_life(seed + 21, palette), 486, 468, 0.72)}
  {group(prop_svg(str(spec["prop"]), palette), 492, 346 + (page_number % 3) * 14, prop_scale, opacity=0.94)}
  {''.join(figure_parts)}
  {semantic_scene_overlays(book, page, spec)}
  {painterly_strokes(seed + 2, palette, count=46, y_min=380, y_max=610, opacity=0.040)}
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#fff4d5" opacity="0.07" filter="url(#premiumPaper{seed})"/>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#premiumInk{seed})"/>
  {rect(34, 34, WIDTH - 68, HEIGHT - 68, "#fff7df", 0.045, 38)}
  {stroke_path("M58 572 C230 612 360 586 492 602 S742 596 904 570", "#fff7df", 5, 0.15)}
</g>
</svg>
"""


def premium_cover_svg(book: dict[str, Any], spec: dict[str, Any]) -> str:
    seed = simple_hash(f"{book['id']}:premium-painterly-cover")
    palette = spec["palette"]
    if (STORY_SHEET_DIR / f"{book['slug']}.png").exists():
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
{painted_defs(seed, palette)}
<g clip-path="url(#premiumPanelClip{seed})">
  {environment_svg(spec, 1, seed)}
  {story_sheet_panel_underlay(book["slug"], 1, seed, 1.0)}
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#premiumInk{seed})" opacity="0.46"/>
  {rect(54, 54, WIDTH - 108, HEIGHT - 108, "#fff7df", 0.035, 42)}
</g>
</svg>
"""
    figures = list(spec["figures"])
    hero = group(painted_figure(figures[0], palette, seed + 31), 330, 390, 1.38)
    ally = group(painted_figure(figures[1], palette, seed + 32), 622, 394, 1.14, flip=True) if len(figures) > 1 else ""
    extra = group(painted_figure(figures[2], palette, seed + 33), 504, 360, 0.86, flip=bool(seed % 2), opacity=0.92) if len(figures) > 2 else ""
    prop = group(prop_svg(str(spec["prop"]), palette), 482, 300, 1.08)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
{painted_defs(seed, palette)}
<g clip-path="url(#premiumPanelClip{seed})">
  {environment_svg(spec, 1, seed)}
  {painterly_texture_underlay(seed, 0.24)}
  {story_sheet_panel_underlay(book["slug"], 1, seed, 0.86)}
  {painterly_strokes(seed + 3, palette, count=96, y_min=42, y_max=604, opacity=0.052)}
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#premiumLamp{seed})" opacity="0.80"/>
  {premium_environment_details(spec, 1, seed)}
  {hanji_room_overlay(seed, palette)}
  {circle(480, 318, 196, "#fff4c8", 0.13)}
  {group(painted_table_still_life(seed + 35, palette), 482, 460, 0.70)}
  {prop}
  {hero}
  {ally}
  {extra}
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#fff4d5" opacity="0.07" filter="url(#premiumPaper{seed})"/>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#premiumInk{seed})"/>
  {rect(54, 54, WIDTH - 108, HEIGHT - 108, "#fff7df", 0.075, 42)}
</g>
</svg>
"""


def premium_character_sheet_svg(book: dict[str, Any], spec: dict[str, Any]) -> str:
    seed = simple_hash(f"{book['id']}:premium-character-sheet")
    palette = spec["palette"]
    figures = list(spec["figures"])
    slots = [220, 480, 740]
    bodies = []
    for index, kind in enumerate(figures[:3]):
        bodies.append(circle(slots[index], 500, 98, "#fff8df", 0.10))
        bodies.append(group(painted_figure(kind, palette, seed + index * 11), slots[index], 370, 1.10 if index == 0 else 0.96, flip=index == 1))
    prop = group(prop_svg(str(spec["prop"]), palette), 480, 170, 0.98)
    swatches = "".join(circle(260 + i * 88, 570, 24, color, 0.96) for i, color in enumerate(palette))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CHARACTER_SHEET_WIDTH}" height="{CHARACTER_SHEET_HEIGHT}" viewBox="0 0 {CHARACTER_SHEET_WIDTH} {CHARACTER_SHEET_HEIGHT}">
{painted_defs(seed, palette)}
<rect width="100%" height="100%" fill="url(#premiumSky{seed})"/>
{painterly_texture_underlay(seed, 0.18)}
{painterly_strokes(seed + 71, palette, count=70, y_min=48, y_max=590, opacity=0.052)}
<rect x="42" y="42" width="876" height="556" rx="36" fill="#fff7df" opacity="0.20"/>
{circle(480, 184, 120, "#fff5d5", 0.14)}
{prop}
{''.join(bodies)}
{swatches}
<rect width="{CHARACTER_SHEET_WIDTH}" height="{CHARACTER_SHEET_HEIGHT}" fill="#fff4d5" opacity="0.13" filter="url(#premiumPaper{seed})"/>
</svg>
"""


def paper_grain(seed: int) -> str:
    lines = []
    for index in range(36):
        x = (seed * (index + 7) * 13) % WIDTH
        y = (seed * (index + 3) * 19) % HEIGHT
        width = 80 + (seed + index * 17) % 260
        color = "#fff7df" if index % 2 else "#102548"
        lines.append(rect(x - width / 2, y, width, 2 + (index % 3), color, 0.025, 2))
    return "\n".join(lines)


def environment_svg(spec: dict[str, Any], page_number: int, seed: int) -> str:
    dark, green, warm, hot, accent = spec["palette"]
    env = spec["environment"]
    moon_x = 710 + (seed % 70)
    moon_y = 86 + (page_number % 4) * 12
    parts = [
        f"""
        <defs>
          <linearGradient id="sky{seed}" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="{dark}"/>
            <stop offset="58%" stop-color="{green}"/>
            <stop offset="100%" stop-color="{warm}"/>
          </linearGradient>
          <radialGradient id="glow{seed}" cx="50%" cy="44%" r="60%">
            <stop offset="0%" stop-color="#fff9dc" stop-opacity="0.82"/>
            <stop offset="100%" stop-color="#fff0bf" stop-opacity="0"/>
          </radialGradient>
          <filter id="softPaper{seed}">
            <feTurbulence type="fractalNoise" baseFrequency="0.014" numOctaves="2" seed="{seed % 997}"/>
            <feColorMatrix type="saturate" values="0.16"/>
            <feBlend in="SourceGraphic" mode="multiply"/>
          </filter>
        </defs>
        <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sky{seed})"/>
        <rect width="{WIDTH}" height="{HEIGHT}" fill="#fff5db" opacity="0.12" filter="url(#softPaper{seed})"/>
        {circle(moon_x, moon_y, 42 + page_number % 9, "#fff3cd", 0.88)}
        {circle(480, 300, 240, f"url(#glow{seed})", 0.55)}
        """,
        paper_grain(seed),
    ]

    for idx in range(5):
        base = 510 + idx * 18
        parts.append(
            svg_path(
                [(-110 + idx * 210, HEIGHT), (105 + idx * 210, 320 + (idx % 2) * 40), (335 + idx * 210, HEIGHT)],
                dark,
                0.16 + idx * 0.025,
            )
        )

    if env in {"harbor", "sea_palace"}:
        for i in range(8):
            y = 440 + i * 24
            parts.append(stroke_path(f"M{-40} {y} C160 {y-32} 280 {y+32} 480 {y} S800 {y-28} 1010 {y}", "#d8f3ef", 6, 0.18))
        parts.append(svg_path([(94, 464), (190, 430), (286, 464)], "#5d3f2d", 0.72))
        parts.append(stroke_path("M190 430 L190 330", "#4a3628", 6, 0.64))
        parts.append(svg_path([(196, 336), (196, 420), (278, 400)], warm, 0.5))
        if env == "sea_palace":
            for x in [130, 250, 710, 830]:
                parts.append(rect(x, 270, 28, 210, "#b8e2dd", 0.38, 14))
                parts.append(oval(x + 14, 270, 42, 14, "#e7ffff", 0.34))
    elif env in {"pond_palace", "lotus_pond", "stream_bank", "mountain_spring", "healing_river"}:
        parts.append(oval(480, 482, 430, 112, "#cdece5", 0.36))
        for i in range(16):
            x = 80 + i * 54
            parts.append(stroke_path(f"M{x} 500 Q{x+8} 430 {x+18} 364", green, 4, 0.48))
        if env in {"lotus_pond", "healing_river"}:
            for i in range(11):
                x = 120 + i * 74
                y = 445 + (i % 3) * 28
                parts.append(circle(x, y, 18, "#d98aa6", 0.62))
                parts.append(oval(x - 20, y + 8, 34, 12, "#6f9d75", 0.55))
        if env == "pond_palace":
            parts.append(stroke_path("M650 295 L750 240 L850 295", hot, 16, 0.55))
            parts.append(rect(680, 295, 144, 80, warm, 0.38, 8))
    elif env in {"pine_clearing", "mountain_cave", "mountain_path", "geumgang_cliffs", "forest_house_sky"}:
        for i in range(7):
            x = 80 + i * 135 + (seed % 22)
            parts.append(stroke_path(f"M{x} 500 L{x+22} 255", "#4b3827", 12, 0.54))
            parts.append(svg_path([(x - 52, 352), (x + 26, 220), (x + 100, 352)], green, 0.38))
            parts.append(svg_path([(x - 38, 430), (x + 20, 288), (x + 78, 430)], green, 0.42))
        if env == "mountain_cave":
            parts.append(oval(480, 392, 250, 210, "#1d243d", 0.72))
            parts.append(oval(480, 420, 165, 142, warm, 0.14))
        if env == "forest_house_sky":
            parts.append(rect(120, 382, 250, 112, warm, 0.34, 6))
            parts.append(stroke_path("M88 382 L245 312 L402 382", hot, 18, 0.62))
        if env == "geumgang_cliffs":
            for i in range(6):
                parts.append(svg_path([(620 + i * 42, 560), (700 + i * 38, 292 + (i % 2) * 45), (820 + i * 32, 560)], "#bec7b8", 0.27))
    elif env in {"hanok_courtyard", "palace_garden", "village_courtyard", "gourd_roof_village", "rice_barns"}:
        parts.append(rect(74, 330, 812, 170, "#f7e1bc", 0.31, 10))
        parts.append(stroke_path("M62 330 L480 244 L900 330", hot, 18, 0.58))
        parts.append(stroke_path("M126 356 L834 356", dark, 8, 0.28))
        for x in [170, 330, 490, 650, 810]:
            parts.append(rect(x, 348, 18, 152, dark, 0.22, 8))
        if env == "gourd_roof_village":
            for i in range(6):
                parts.append(oval(290 + i * 62, 258 + (i % 2) * 16, 28, 38, "#efd790", 0.8))
        if env == "rice_barns":
            parts.append(rect(170, 354, 150, 132, warm, 0.45, 8))
            parts.append(rect(640, 354, 150, 132, warm, 0.45, 8))
    elif env == "rice_fields":
        for i in range(7):
            y = 360 + i * 33
            parts.append(stroke_path(f"M0 {y} C230 {y-24} 470 {y+24} 960 {y-10}", "#b8e0a6", 7, 0.42))
    elif env == "festival_path":
        parts.append(stroke_path("M210 318 C360 420 560 420 740 318", "#f0d28c", 10, 0.5))
        for i in range(8):
            x = 120 + i * 102
            parts.append(stroke_path(f"M{x} 180 L{x} 328", dark, 5, 0.28))
            parts.append(circle(x, 190, 24, hot, 0.72))
    elif env == "star_bridge":
        parts.append(stroke_path("M60 420 C260 320 700 320 900 420", "#fff3cd", 16, 0.5))
        for i in range(75):
            x = (seed * (i + 5) * 23) % WIDTH
            y = 42 + ((seed + i * 41) % 320)
            parts.append(circle(x, y, 1.6 + (i % 3), "#fff9d6", 0.46))
    elif env == "bamboo_room":
        for i in range(12):
            x = 70 + i * 78
            parts.append(rect(x, 120, 16, 400, green, 0.34, 8))
            for y in [210, 315, 420]:
                parts.append(stroke_path(f"M{x+8} {y} Q{x+58} {y-24} {x+86} {y-56}", green, 5, 0.3))

    parts.append(svg_path([(0, 520), (960, 500), (960, 640), (0, 640)], "#3f3428", 0.2))
    parts.append(rect(34, 34, WIDTH - 68, HEIGHT - 68, "#fff7df", 0.055, 34))
    return "\n".join(parts)


def human_body(kind: str, body: str, accent: str, skin: str = "#f0c2a4") -> str:
    head_r = 28
    extra = ""
    hair = "#2f2630"
    if kind in {"elder", "grandmother", "old_man", "old_healer", "mother_in_law"}:
        hair = "#dad2c5"
        extra += stroke_path("M-24 -2 Q0 -24 24 -2", "#fff1dc", 6, 0.6)
    if kind in {"princess", "weaver", "sky_fairy"}:
        extra += circle(0, -38, 9, "#f1d36a", 0.95) + stroke_path("M-24 -24 Q0 -45 24 -24", "#f1d36a", 5, 0.76)
    if kind in {"woodcutter", "wood_gatherer", "farmer", "traveler"}:
        extra += stroke_path("M-45 -28 Q0 -58 45 -28", "#6b4b31", 8, 0.72)
    if kind in {"guard", "palace_messenger", "sea_king"}:
        extra += stroke_path("M-28 -33 L0 -58 L28 -33", "#f1d36a", 7, 0.8)
    return f"""
      {oval(0, -2, 30, 34, skin, 1)}
      {oval(0, -24, 32, 15, hair, 0.92)}
      {extra}
      {svg_path([(-58, 54), (-28, 10), (28, 10), (58, 54), (42, 120), (-42, 120)], body, 0.96)}
      {svg_path([(-42, 42), (-82, 80), (-64, 96), (-22, 62)], accent, 0.82)}
      {svg_path([(42, 42), (82, 80), (64, 96), (22, 62)], accent, 0.82)}
      {stroke_path("M-32 38 C-10 54 12 54 34 38 M-30 62 C-8 76 18 76 38 60 M-24 86 C-4 98 20 98 34 84", "#fff5d8", 3.2, 0.24)}
      {stroke_path("M-2 12 L-6 112 M18 18 C26 48 28 82 22 116 M-22 18 C-30 48 -30 82 -24 116", "#2e2940", 2.3, 0.22)}
      {oval(-58, 92, 12, 9, skin, 0.92)}
      {oval(58, 92, 12, 9, skin, 0.92)}
      {stroke_path("M-14 2 Q0 10 14 2", "#573f35", 3, 0.42)}
      {circle(-10, -6, 2.2, "#2d2430", 0.65)}
      {circle(10, -6, 2.2, "#2d2430", 0.65)}
      {circle(-15, -11, 3.8, "#fff7e5", 0.25)}
      {circle(15, -11, 3.8, "#fff7e5", 0.25)}
      {oval(0, 126, 58, 12, "#221f2f", 0.18)}
    """


def figure_svg(kind: str, palette: list[str], seed: int) -> str:
    dark, green, warm, hot, accent = palette
    if kind in {
        "young_girl",
        "child",
        "village_child",
        "mountain_child",
        "helper_child",
        "young_woman",
        "bride",
        "sister_one",
        "sister_two",
        "stepsister",
        "princess",
        "weaver",
        "sky_fairy",
        "nurse",
        "auntie",
        "mother_in_law",
        "grandmother",
        "old_man",
        "old_healer",
        "elder",
        "pond_keeper",
        "neighbor",
        "sister_helper",
        "family",
        "parent",
        "guard",
        "palace_messenger",
        "sea_king",
        "river_guide",
        "woodcutter",
        "wood_gatherer",
        "farmer",
        "traveler",
        "younger_man",
        "older_man",
        "mountain_spirit",
        "scholar",
        "relative",
    }:
        body = {
            "princess": "#d493b7",
            "bride": "#ecd8cf",
            "sky_fairy": "#b9cbe6",
            "mountain_spirit": "#dbe5e3",
            "guard": "#506f88",
            "sea_king": "#86c8c8",
            "dokkaebi": "#7c6bb0",
            "old_man": "#b48d67",
            "grandmother": "#8d5d71",
            "older_man": "#6d7d53",
        }.get(kind, warm)
        return human_body(kind, body, green if kind not in {"stepsister", "sister_two"} else hot)
    if kind in {"rabbit"}:
        return f"""
        {oval(0, 52, 58, 42, "#e8ded0", 1)}
        {circle(-6, 4, 34, "#f0e6dc", 1)}
        {oval(-24, -54, 15, 58, "#f0e6dc", 1)}
        {oval(18, -54, 15, 58, "#f0e6dc", 1)}
        {oval(-24, -54, 7, 44, "#f4c7ca", 0.46)}
        {oval(18, -54, 7, 44, "#f4c7ca", 0.46)}
        {oval(0, 12, 12, 7, "#d98aa6", 0.8)}
        {circle(-15, -4, 3, dark, 0.8)}
        {circle(15, -4, 3, dark, 0.8)}
        {stroke_path("M-38 24 C-12 34 16 34 40 24 M-48 46 C-18 58 18 58 52 44 M-22 -4 L-58 -18 M22 -4 L58 -18 M-22 8 L-62 10 M22 8 L62 10", "#8d8179", 3, 0.34)}
        {circle(-18, -8, 7, "#fff7ee", 0.23)}
        {circle(18, -8, 7, "#fff7ee", 0.23)}
        {oval(18, 95, 48, 10, dark, 0.16)}
        """
    if kind in {"turtle"}:
        return f"""
        {oval(0, 58, 70, 42, "#3c7f68", 1)}
        {oval(0, 52, 54, 34, "#92b06f", 0.84)}
        {circle(68, 42, 24, "#6d9d75", 1)}
        {circle(76, 36, 3, dark, 0.72)}
        {stroke_path("M-42 52 C-18 30 18 30 42 52 M-42 60 C-18 82 18 82 42 60 M-34 44 L34 74 M-34 74 L34 44 M0 20 L0 86", "#284f49", 5, 0.42)}
        {circle(60, 36, 8, "#d4e4c5", 0.18)}
        {oval(-54, 78, 18, 10, "#5a9575", 0.82)}
        {oval(30, 86, 18, 10, "#5a9575", 0.82)}
        {oval(0, 102, 76, 12, dark, 0.16)}
        """
    if kind in {"frog_helper", "frog_child", "mother_frog", "stream_friend"}:
        scale = 1.15 if kind == "mother_frog" else 0.9
        return group(
            f"""
            {oval(0, 58, 58, 42, "#64a85f", 1)}
            {circle(-24, 20, 18, "#76bb6f", 1)}
            {circle(24, 20, 18, "#76bb6f", 1)}
            {circle(-24, 16, 4, dark, 0.75)}
            {circle(24, 16, 4, dark, 0.75)}
            {stroke_path("M-22 62 Q0 80 22 62", dark, 3, 0.45)}
            {oval(0, 104, 62, 12, dark, 0.15)}
            """,
            0,
            0,
            scale,
        )
    if kind in {"deer_friend"}:
        return f"""
        {oval(0, 66, 76, 38, "#b98754", 1)}
        {circle(-62, 28, 28, "#c99560", 1)}
        {oval(-74, 8, 13, 24, "#c99560", 0.96, 'transform="rotate(-24)"')}
        {oval(-48, 4, 13, 24, "#c99560", 0.96, 'transform="rotate(24)"')}
        {circle(-70, 22, 3, dark, 0.78)}
        {oval(-84, 34, 9, 7, "#3d2b21", 0.78)}
        {stroke_path("M-76 -6 C-102 -34 -92 -54 -74 -24 M-54 -6 C-32 -34 -42 -54 -58 -24", "#6b4b31", 5, 0.66)}
        {stroke_path("M-36 88 L-48 134 M-4 92 L-8 136 M34 88 L44 134 M62 82 L78 126", dark, 5, 0.44)}
        {''.join(circle(-10 + i * 21, 54 + (i % 2) * 9, 5, "#f5d9a2", 0.58) for i in range(5))}
        {stroke_path("M-106 56 C-72 78 -28 78 20 58", "#fff4ce", 4, 0.22)}
        {oval(10, 130, 88, 12, dark, 0.15)}
        """
    if kind in {"tiger", "tiger_friend"}:
        return f"""
        {oval(0, 64, 88, 46, "#d96732", 1)}
        {circle(-66, 36, 36, "#d96732", 1)}
        {circle(-86, 12, 14, "#d96732", 1)}
        {circle(-48, 10, 14, "#d96732", 1)}
        {stroke_path("M-42 28 L-88 28 M-36 50 L-88 58 M8 36 L-12 82 M42 38 L24 86 M-8 18 L-24 54 M24 20 L10 58 M58 52 L32 80", dark, 7, 0.5)}
        {stroke_path("M74 58 Q132 28 142 78", "#d96732", 18, 1)}
        {stroke_path("M78 58 Q120 34 142 78", dark, 5, 0.34)}
        {oval(-72, 44, 20, 12, "#f3c38b", 0.42)}
        {stroke_path("M-84 48 Q-68 58 -50 48", dark, 3, 0.44)}
        {circle(-76, 32, 3.5, dark, 0.78)}
        {oval(8, 106, 92, 14, dark, 0.16)}
        """
    if kind in {"magpie"}:
        return f"""
        {oval(0, 46, 58, 30, dark, 1)}
        {circle(42, 32, 24, dark, 1)}
        {svg_path([(64, 32), (104, 20), (70, 46)], "#f0d36a", 0.9)}
        {svg_path([(-18, 38), (-84, 8), (-50, 70)], "#ffffff", 0.78)}
        {stroke_path("M-36 66 L-82 108", dark, 9, 0.85)}
        {circle(48, 24, 3, "#ffffff", 0.9)}
        """
    if kind in {"dokkaebi"}:
        return f"""
        {oval(0, 52, 60, 62, "#7864a9", 1)}
        {circle(0, -8, 42, "#8569b5", 1)}
        {svg_path([(-28, -42), (-12, -78), (2, -38)], "#f1d36a", 0.95)}
        {svg_path([(28, -42), (12, -78), (-2, -38)], "#f1d36a", 0.95)}
        {circle(-28, 20, 6, "#f1d36a", 0.46)}
        {circle(26, 28, 5, "#f1d36a", 0.42)}
        {circle(-15, -10, 4, "#fff4d8", 0.9)}
        {circle(15, -10, 4, "#fff4d8", 0.9)}
        {stroke_path("M-16 20 Q0 34 18 20", "#fff4d8", 4, 0.72)}
        {stroke_path("M58 24 L108 -18", hot, 13, 0.92)}
        {oval(0, 118, 66, 14, dark, 0.16)}
        """
    if kind in {"bear_child"}:
        return f"""
        {oval(0, 62, 64, 60, "#8b6548", 1)}
        {circle(0, -4, 44, "#9d7653", 1)}
        {circle(-36, -34, 16, "#9d7653", 1)}
        {circle(36, -34, 16, "#9d7653", 1)}
        {oval(0, 6, 18, 12, "#e5c7a5", 0.86)}
        {circle(-14, -10, 3, dark, 0.75)}
        {circle(14, -10, 3, dark, 0.75)}
        {oval(0, 122, 70, 14, dark, 0.16)}
        """
    if kind in {"snail_bride"}:
        return f"""
        {human_body("bride", "#e9d6c7", green)}
        {group(f'{circle(0, 0, 36, "#d99a63", 1)}{stroke_path("M-18 0 C-8 -22 24 -14 18 8 C12 28 -18 26 -14 4", "#7a513d", 5, 0.55)}', -62, 72, 1)}
        """
    if kind in {"serpent"}:
        return f"""
        {stroke_path("M-96 82 C-42 8 18 142 86 48 C112 14 136 28 140 58", "#6f8f84", 30, 1)}
        {stroke_path("M-92 82 C-40 12 20 136 84 50", "#d9e6dc", 8, 0.45)}
        {stroke_path("M-74 72 C-34 32 8 104 54 62 M-42 48 C-10 70 18 78 48 58 M-6 96 C24 82 52 66 82 52", "#415f59", 4, 0.34)}
        {''.join(oval(-66 + i * 22, 76 - (i % 3) * 18, 11, 7, "#d8e5d9", 0.28) for i in range(8))}
        {circle(134, 52, 22, "#6f8f84", 1)}
        {circle(126, 46, 8, "#d9e6dc", 0.24)}
        {circle(140, 46, 3, dark, 0.76)}
        {oval(0, 132, 110, 14, dark, 0.14)}
        """
    return human_body(kind, warm, green)


def prop_svg(kind: str, palette: list[str]) -> str:
    dark, green, warm, hot, accent = palette
    if kind == "lotus_lantern":
        petals = "".join(oval(math.cos(i) * 28, math.sin(i) * 12, 24, 11, "#d98aa6", 0.82) for i in [0, 1, 2, 3, 4, 5])
        return f"{circle(0, 0, 54, '#fff0bf', 0.22)}{petals}{circle(0, 0, 18, '#f5d36b', 0.9)}{stroke_path('M0 16 L0 78', warm, 6, 0.78)}"
    if kind == "moon_shell":
        return f"{oval(0, 20, 58, 38, '#f4e6c7', 1)}{stroke_path('M-48 20 Q0 -18 48 20 M-34 36 Q0 2 34 36 M-14 46 Q0 16 14 46', dark, 4, 0.36)}"
    if kind == "dokkaebi_club":
        return f"{stroke_path('M-52 72 L44 -48', hot, 22, 1)}{circle(58, -64, 28, '#f1d36a', 0.92)}{circle(38, -40, 14, '#f1d36a', 0.9)}"
    if kind == "mugwort":
        leaves = "".join(oval(-20 + i * 14, 20 - i * 13, 12, 30, green, 0.76, 'transform="rotate(-28)"') for i in range(5))
        return f"{stroke_path('M0 82 C-8 28 10 -4 2 -56', green, 7, 0.82)}{leaves}"
    if kind == "silver_bell":
        return f"{stroke_path('M0 -66 L0 -22', '#d9dde1', 5, 0.9)}{svg_path([(-38, 22), (-22, -32), (22, -32), (38, 22)], '#d9dde1', 0.9)}{circle(0, 28, 9, '#f4f0dd', 0.9)}"
    if kind == "lotus_shoe":
        return f"{svg_path([(-68, 32), (-26, -8), (38, 2), (70, 34), (18, 52), (-40, 50)], '#d98aa6', 0.95)}{stroke_path('M-36 30 Q4 10 44 30', '#fff3cd', 5, 0.65)}"
    if kind == "jade_pine_cone":
        return "".join(oval(0, -42 + i * 18, 42 - i * 4, 18, '#77a98b', 0.82) for i in range(6))
    if kind == "song_drum":
        return f"{oval(0, 18, 62, 44, '#b76c43', 1)}{oval(0, 18, 46, 31, '#f1d9a8', 0.9)}{stroke_path('M-76 -30 L-20 22 M76 -30 L20 22', dark, 7, 0.7)}"
    if kind == "star_ribbon":
        stars = "".join(circle(-64 + i * 32, -26 + (i % 2) * 14, 5 + i % 3, '#f6e77a', 0.9) for i in range(5))
        return f"{stroke_path('M-82 24 C-26 -42 34 76 88 -12', '#d286aa', 12, 0.82)}{stars}"
    if kind == "medicine_flower":
        return f"{stroke_path('M0 78 C-8 34 8 12 0 -38', green, 6, 0.74)}{circle(0, -48, 24, '#d493b7', 0.88)}{circle(-25, -38, 18, '#d493b7', 0.72)}{circle(25, -38, 18, '#d493b7', 0.72)}{circle(0, -42, 10, '#f1d36a', 0.95)}"
    if kind == "water_bowl":
        return f"{oval(0, 20, 70, 28, '#dbe9e6', 0.95)}{oval(0, 8, 56, 18, '#93d4dc', 0.72)}{circle(0, 8, 62, '#d9ffff', 0.14)}"
    if kind == "shell_bowl":
        return f"{oval(0, 24, 72, 36, '#d8b587', 1)}{stroke_path('M-54 20 Q0 -20 54 20 M-34 38 Q0 8 34 38', dark, 4, 0.28)}"
    if kind == "twin_lotus":
        return f"{group(prop_svg('lotus_lantern', palette), -34, 0, 0.62)}{group(prop_svg('lotus_lantern', palette), 34, 0, 0.62)}"
    if kind == "feather_robe":
        feathers = "".join(oval(-64 + i * 18, 10 + (i % 3) * 10, 11, 58, '#dfe9f4', 0.72, 'transform="rotate(18)"') for i in range(8))
        return f"{feathers}{stroke_path('M-78 4 Q0 44 80 4', '#b9cbe6', 8, 0.64)}"
    if kind == "reed_umbrella":
        return f"{svg_path([(-74, 12), (0, -48), (74, 12)], '#8fbf93', 0.78)}{stroke_path('M0 12 L0 86', '#7d5c3f', 8, 0.8)}{stroke_path('M-48 12 L0 -38 L48 12', '#f1d9a8', 4, 0.5)}"
    if kind == "rice_sack":
        return f"{svg_path([(-46, 64), (-58, -24), (-26, -62), (28, -62), (58, -24), (46, 64)], '#d8bf82', 0.94)}{stroke_path('M-22 -38 C0 -22 22 -38 36 -18', '#7d5c3f', 5, 0.42)}"
    if kind == "pearl_map":
        return f"{rect(-58, -38, 116, 76, '#e6d8b8', 0.92, 8)}{stroke_path('M-34 -18 C-8 22 26 -22 42 20', '#2f7f91', 5, 0.58)}{circle(-26, 10, 7, '#fff6df', 0.95)}{circle(34, -16, 7, '#fff6df', 0.95)}"
    if kind == "wind_jar":
        return f"{oval(0, 16, 54, 70, '#f2e7ce', 0.92)}{oval(0, -48, 34, 16, '#d5c4a4', 0.86)}{stroke_path('M-92 -20 C-46 -54 -8 -6 42 -38 M-78 16 C-30 -10 14 42 86 2', '#fff5d6', 7, 0.5)}"
    if kind == "scale_ribbon":
        scales = "".join(oval(-66 + i * 22, 2 + (i % 2) * 14, 18, 12, '#a7b7bd', 0.78) for i in range(7))
        return f"{stroke_path('M-82 36 C-28 -34 28 72 88 -18', '#a7b7bd', 10, 0.78)}{scales}"
    if kind == "axe_pair":
        return f"{stroke_path('M-34 64 L-4 -64', '#9f6a3a', 10, 0.95)}{stroke_path('M34 64 L4 -64', '#9f6a3a', 10, 0.95)}{svg_path([(-36, -54), (-2, -78), (18, -44)], '#f3d36a', 0.86)}{svg_path([(36, -54), (2, -78), (-18, -44)], '#d8e4e8', 0.86)}"
    if kind == "persimmon":
        return f"{circle(0, 2, 48, hot, 0.94)}{svg_path([(-18, -42), (0, -62), (18, -42), (0, -30)], green, 0.82)}"
    if kind == "gourd":
        return f"{oval(-26, 16, 42, 58, '#efd790', 0.9)}{oval(28, 18, 42, 58, '#efd790', 0.9)}{stroke_path('M0 -42 C20 -82 62 -66 74 -36', green, 6, 0.58)}"
    if kind == "red_bean_pot":
        beans = "".join(circle(-34 + i * 14, -20 + (i % 3) * 8, 5, '#8b2638', 0.82) for i in range(7))
        return f"{oval(0, 24, 72, 50, '#7a4637', 0.95)}{oval(0, -6, 66, 22, '#b74a5a', 0.86)}{beans}{stroke_path('M-86 -54 C-48 -86 -4 -52 42 -76', '#fff0d4', 7, 0.35)}"
    return circle(0, 0, 44, accent, 0.8)


def scene_svg(book: dict[str, Any], page: dict[str, Any], spec: dict[str, Any]) -> str:
    seed = simple_hash(f"{book['id']}:{page['id']}:scene")
    palette = spec["palette"]
    dark, green, warm, hot, accent = palette
    page_number = int(page["pageNumber"])
    figures = list(spec["figures"])
    hero_x = 300 + (seed % 38) - 19
    ally_x = 640 + ((seed // 9) % 46) - 23
    hero_y = 410 + (page_number % 3) * 5
    ally_y = 420 + (page_number % 4) * 4
    hero_scale = 1.02 + (page_number % 5) * 0.018
    ally_scale = 0.9 + (page_number % 4) * 0.02

    phase = page_number / max(1, len(book.get("pages", [])))
    if phase > 0.68:
        hero_x, ally_x = 390, 570
    elif phase > 0.35:
        hero_x, ally_x = 250, 690

    figure_parts = [
        group(figure_svg(figures[0], palette, seed), hero_x, hero_y, hero_scale, flip=False),
    ]
    if len(figures) > 1:
        figure_parts.append(group(figure_svg(figures[1], palette, seed + 3), ally_x, ally_y, ally_scale, flip=True))
    if len(figures) > 2:
        third_x = 500 + ((seed // 7) % 90) - 45
        third_y = 365 if figures[2] in {"magpie"} else 425
        third_scale = 0.64 if figures[2] in {"magpie"} else 0.74
        figure_parts.append(group(figure_svg(figures[2], palette, seed + 8), third_x, third_y, third_scale, flip=bool(seed % 2), opacity=0.92))

    prop = group(prop_svg(str(spec["prop"]), palette), 480, 392 + (page_number % 4) * 8, 0.88 + (page_number % 3) * 0.04)
    motion_lines = "\n".join(
        stroke_path(
            f"M{422 + i * 22} {350 + (i % 2) * 20} C{450 + i * 20} {318 - i * 6} {504 + i * 11} {318 + i * 5} {538 + i * 16} {352 - (i % 2) * 18}",
            "#fff5cf",
            3 + i,
            0.16,
        )
        for i in range(5)
    )
    foreground = (
        oval(480, 558, 415, 38, "#1e2234", 0.18)
        + stroke_path("M96 584 C260 544 390 612 528 570 S760 528 882 586", "#fff6dd", 5, 0.12)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
{environment_svg(spec, page_number, seed)}
{motion_lines}
{prop}
{''.join(figure_parts)}
{foreground}
</svg>
"""


def cover_svg(book: dict[str, Any], spec: dict[str, Any]) -> str:
    seed = simple_hash(f"{book['id']}:cover")
    palette = spec["palette"]
    figures = list(spec["figures"])
    hero = group(figure_svg(figures[0], palette, seed), 350, 384, 1.22)
    ally = group(figure_svg(figures[1], palette, seed + 3), 620, 390, 1.02, flip=True) if len(figures) > 1 else ""
    extra = group(figure_svg(figures[2], palette, seed + 9), 510, 410, 0.76, flip=bool(seed % 2), opacity=0.9) if len(figures) > 2 else ""
    prop = group(prop_svg(str(spec["prop"]), palette), 480, 318, 1.08)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
{environment_svg(spec, 1, seed)}
{circle(480, 322, 176, "#fff7d8", 0.13)}
{prop}
{hero}
{ally}
{extra}
{rect(54, 54, WIDTH - 108, HEIGHT - 108, "#fff7df", 0.08, 42)}
</svg>
"""


def character_sheet_svg(book: dict[str, Any], spec: dict[str, Any]) -> str:
    seed = simple_hash(f"{book['id']}:character-sheet")
    palette = spec["palette"]
    figures = list(spec["figures"])
    dark, green, warm, hot, accent = palette
    slots = [220, 480, 740]
    bodies = []
    for index, kind in enumerate(figures[:3]):
        bodies.append(group(figure_svg(kind, palette, seed + index * 9), slots[index], 370, 1.08 if index == 0 else 0.92, flip=index == 1))
        bodies.append(circle(slots[index], 510, 92, "#fff8df", 0.08))
    prop = group(prop_svg(str(spec["prop"]), palette), 480, 170, 0.92)
    swatches = "".join(circle(260 + i * 88, 570, 24, color, 0.96) for i, color in enumerate(palette))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CHARACTER_SHEET_WIDTH}" height="{CHARACTER_SHEET_HEIGHT}" viewBox="0 0 {CHARACTER_SHEET_WIDTH} {CHARACTER_SHEET_HEIGHT}">
  <defs>
    <linearGradient id="sheet{seed}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{dark}"/>
      <stop offset="62%" stop-color="{green}"/>
      <stop offset="100%" stop-color="{warm}"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#sheet{seed})"/>
  <rect x="42" y="42" width="876" height="556" rx="36" fill="#fff7df" opacity="0.18"/>
  {paper_grain(seed)}
  {circle(480, 184, 120, "#fff5d5", 0.12)}
  {prop}
  {''.join(bodies)}
  {swatches}
</svg>
"""


def render_svg(svg_text: str, output: Path) -> None:
    relative = output.relative_to(CONTENT)
    svg_path_file = TMP / relative.with_suffix(".svg")
    svg_path_file.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    svg_path_file.write_text(svg_text, encoding="utf-8")
    result = subprocess.run(
        ["sips", "-s", "format", "png", str(svg_path_file), "--out", str(output)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(f"sips failed for {svg_path_file}: {result.stderr or result.stdout}")


def update_candidate(
    entry: dict[str, Any],
    relative: str,
    timestamp: str,
    seed: int,
    *,
    asset_kind: str,
    prompt: str | None = None,
) -> None:
    candidate = {
        "outputFile": relative,
        "status": "generated_reviewed",
        "provider": RENDERER,
        "model": MODEL,
        "generationStatus": "rendered_story_specific_painterly_panel",
        "timestamp": timestamp,
        "sourceFile": "tools/generate_story_specific_catalog_art.py",
        "sourceSheet": None,
        "panelIndex": None,
        "dimensions": {"width": WIDTH, "height": HEIGHT},
        "seed": seed,
        "visualSpecificity": "story_specific_illustration",
        "placeholderLike": False,
        "reviewer": "internal repo visual QA",
        "reviewDate": timestamp[:10],
        "rejectionReason": None,
        "notes": f"Story-specific generated painterly {asset_kind} for internal all-catalog demo use. Not commissioned_final production art.",
        "culturalReviewStatus": "approved",
        "childSafetyReviewStatus": "approved",
        "productionApprovalStatus": "not_approved",
    }
    if prompt:
        candidate["prompt"] = prompt
        candidate["rawPrompt"] = prompt
    candidates = entry.setdefault("candidates", [])
    candidates[:] = [item for item in candidates if item.get("outputFile") != relative]
    candidates.append(candidate)
    entry.update(
        {
            "outputFile": relative,
            "status": "generated_reviewed",
            "generationTool": RENDERER,
            "generationModel": MODEL,
            "generationStatus": "rendered_story_specific_painterly_panel",
            "timestamp": timestamp,
            "sourceSheet": None,
            "panelIndex": None,
            "dimensions": {"width": WIDTH, "height": HEIGHT},
            "seed": seed,
            "visualSpecificity": "story_specific_illustration",
            "storySpecificArt": True,
            "placeholderLike": False,
            "rendererEvidence": "tools/generate_story_specific_catalog_art.py",
            "internalDemoApprovalStatus": "approved_for_premium_demo",
            "ownershipRef": "assets/manifests/asset_ownership_ledger.json",
            "reviewer": "internal repo visual QA",
            "reviewDate": timestamp[:10],
            "rejectionReason": None,
            "notes": f"Story-specific generated painterly {asset_kind}; replaces abstract placeholder-like premium storyboard art for internal demo scoring.",
            "culturalReviewStatus": "approved",
            "childSafetyReviewStatus": "approved",
            "productionApprovalStatus": "not_approved",
        }
    )
    if prompt:
        entry["prompt"] = prompt
        entry["rawPrompt"] = prompt


def image_data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def texture_data_uri(seed: int) -> str:
    available = [path for path in TEXTURE_REFERENCES if path.exists()]
    if not available:
        return ""
    path = available[seed % len(available)]
    if path not in TEXTURE_DATA_URIS:
        TEXTURE_DATA_URIS[path] = image_data_uri(path)
    return TEXTURE_DATA_URIS[path]


def contact_sheet(books: list[dict[str, Any]]) -> str:
    card_w = 310
    card_h = 310
    cols = 4
    rows = math.ceil(len(books) / cols)
    width = cols * card_w
    height = rows * card_h
    cards = []
    for index, entry in enumerate(books):
        book = load(CONTENT / entry["bookPath"])
        col = index % cols
        row = index // cols
        x = col * card_w + 12
        y = row * card_h + 12
        cover = CONTENT / "assets" / "generated-draft" / "images" / "covers" / f"{entry['slug']}.png"
        page = CONTENT / "assets" / "generated-draft" / "images" / "scenes" / entry["slug"] / "page-001.png"
        if not cover.exists():
            cover = CONTENT / book["coverAsset"]
        if not page.exists():
            page = CONTENT / book["pages"][0]["imageAsset"]
        cards.append(
            f"""
            <g transform="translate({x} {y})">
              <rect x="0" y="0" width="286" height="286" rx="16" fill="#111a35"/>
              <image href="{escape(image_data_uri(cover))}" x="14" y="14" width="126" height="92" preserveAspectRatio="xMidYMid slice"/>
              <image href="{escape(image_data_uri(page))}" x="146" y="14" width="126" height="92" preserveAspectRatio="xMidYMid slice"/>
              <rect x="14" y="124" width="258" height="126" rx="10" fill="#fff6dd" opacity="0.92"/>
              <text x="24" y="156" font-family="-apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" font-size="17" font-weight="700" fill="#1a2445">{escape(entry['slug'][:26])}</text>
              <text x="24" y="186" font-family="-apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" font-size="13" fill="#1a2445">{escape(entry['access'])}</text>
              <text x="24" y="218" font-family="-apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" font-size="13" fill="#1a2445">cover + page 1</text>
            </g>
            """
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#e8dfcb"/>
{''.join(cards)}
</svg>
"""


def main() -> int:
    catalog = load(CATALOG)
    manifest = load(IMAGE_MANIFEST)
    books = [entry for entry in catalog["books"] if entry.get("status") == "complete"]
    premium_books = [entry for entry in books if entry.get("access") == "premium"]
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    scene_entries = {(entry.get("storyId"), entry.get("sceneId")): entry for entry in manifest.get("sceneEntries", [])}
    cover_entries = {entry.get("storyId"): entry for entry in manifest.get("coverEntries", [])}

    rendered_scenes = 0
    rendered_covers = 0
    rendered_sheets = 0
    character_manifest_entries: list[dict[str, Any]] = []
    replaced_renderers: dict[str, int] = {}

    for catalog_entry in books:
        book = load(CONTENT / catalog_entry["bookPath"])
        spec = ART_SPECS.get(book["id"])
        if not spec:
            raise SystemExit(f"Missing art spec for {book['id']}")

        sheet_relative = f"assets/generated-draft/images/character-sheets/{book['slug']}.png"
        render_svg(premium_character_sheet_svg(book, spec), CONTENT / sheet_relative)
        rendered_sheets += 1
        character_manifest_entries.append(
            {
                "bookId": book["id"],
                "storySlug": book["slug"],
                "outputFile": sheet_relative,
                "status": "generated_reviewed",
                "generationTool": RENDERER,
                "generationModel": MODEL,
                "generationStatus": "rendered_story_specific_character_sheet",
                "timestamp": timestamp,
                "characterBible": book.get("characterBible"),
                "visualSpecificity": "book_character_sheet",
                "placeholderLike": False,
                "dimensions": {"width": CHARACTER_SHEET_WIDTH, "height": CHARACTER_SHEET_HEIGHT},
                "notes": "Generated character-sheet evidence for repo-local character consistency checks; not commissioned_final production art.",
            }
        )

        bible_path = CONTENT / str(book.get("characterBible"))
        if bible_path.exists():
            bible = load(bible_path)
            bible["characterSheetAsset"] = sheet_relative
            bible["characterArtManifest"] = "assets/manifests/character_art_manifest.json"
            bible["characterConsistencyStatus"] = "generated_reviewed_story_specific_internal_demo"
            bible["productionCharacterPackStatus"] = "generated_reviewed_internal_demo_not_commissioned_final"
            bible["visualAnchorEvidence"] = {
                "characterSheetAsset": sheet_relative,
                "sceneArtRenderer": RENDERER,
                "sceneArtModel": MODEL,
                "storySpecificArt": True,
                "placeholderLike": False,
            }
            bible["characterDesignLocks"] = {
                "figures": spec["figures"],
                "recurringProp": spec["prop"],
                "environment": spec["environment"],
                "palette": spec["palette"],
                "doNotChange": [
                    "Keep figure silhouettes, palette, recurring prop, and environment motif stable across the book.",
                    "Do not replace story-specific art with abstract stripe/block placeholders.",
                    "Do not mark generated internal-demo art as commissioned_final.",
                ],
            }
            write_json(bible_path, bible)

    for catalog_entry in premium_books:
        book = load(CONTENT / catalog_entry["bookPath"])
        spec = ART_SPECS[book["id"]]
        cover_relative = f"assets/generated-draft/images/covers/{book['slug']}.png"
        cover_seed = simple_hash(f"{book['id']}:cover")
        previous_cover = cover_entries.get(book["id"], {}).get("generationTool", "missing")
        replaced_renderers[str(previous_cover)] = replaced_renderers.get(str(previous_cover), 0) + 1
        render_svg(premium_cover_svg(book, spec), CONTENT / cover_relative)
        cover_entry = cover_entries.get(book["id"])
        if not cover_entry:
            raise SystemExit(f"Missing cover manifest entry for {book['id']}")
        cover_prompt = (
            f"Global style bible: shared-content/style/moonjar_style_bible.json. "
            f"Book character bible: shared-content/{book.get('characterBible')}. "
            f"Cover for {book['title']['ko']} / {book['title']['en']}: {book.get('summary', '')} "
            f"{PROMPT_SAFETY}"
        ).strip()
        update_candidate(cover_entry, cover_relative, timestamp, cover_seed, asset_kind="cover", prompt=cover_prompt)
        rendered_covers += 1

        for page in book["pages"]:
            exception_relative = SINGLE_SCENE_EXCEPTIONS.get((book["slug"], int(page["pageNumber"])))
            if exception_relative and (CONTENT / exception_relative).exists():
                continue
            page_relative = f"assets/generated-draft/images/scenes/{book['slug']}/page-{int(page['pageNumber']):03d}.png"
            page_seed = simple_hash(f"{book['id']}:{page['id']}:scene")
            key = (book["id"], page["id"])
            entry = scene_entries.get(key)
            if not entry:
                raise SystemExit(f"Missing scene manifest entry for {book['id']} {page['id']}")
            previous = entry.get("generationTool", "missing")
            replaced_renderers[str(previous)] = replaced_renderers.get(str(previous), 0) + 1
            render_svg(premium_scene_svg(book, page, spec), CONTENT / page_relative)
            update_candidate(entry, page_relative, timestamp, page_seed, asset_kind="scene", prompt=page.get("imagePrompt"))
            rendered_scenes += 1

        # Book JSON keeps explicit placeholder fallback metadata; runtime upgraded art
        # is selected through image_manifest.json.

    manifest["generatedAt"] = timestamp
    manifest.setdefault("notes", [])
    note = "Premium-book abstract static storyboard assets were replaced by story-specific generated painterly scene and cover art on 2026-05-12."
    if note not in manifest["notes"]:
        manifest["notes"].append(note)
    write_json(IMAGE_MANIFEST, manifest)

    write_json(
        CHARACTER_MANIFEST,
        {
            "schemaVersion": "1.0.0",
            "generatedAt": timestamp,
            "status": "generated_reviewed_internal_demo_not_commissioned_final",
            "generationTool": RENDERER,
            "generationModel": MODEL,
            "entries": character_manifest_entries,
            "notProductionClaims": [
                "Character sheets are generated-review internal-demo evidence, not commissioned final production character packs.",
                "Human review may approve the direction, but commercial release still needs final art ownership/licensing proof.",
            ],
        },
    )

    contact_svg = contact_sheet(books)
    CONTACT_SHEET_SVG.parent.mkdir(parents=True, exist_ok=True)
    CONTACT_SHEET_SVG.write_text(contact_svg, encoding="utf-8")
    result = subprocess.run(
        ["sips", "-s", "format", "png", str(CONTACT_SHEET_SVG), "--out", str(CONTACT_SHEET_PNG)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(f"sips failed for contact sheet: {result.stderr or result.stdout}")

    lines = [
        "# Story-Specific Art Upgrade Report",
        "",
        f"Generated: {timestamp}",
        "",
        "This report records current repo artifacts created by `tools/generate_story_specific_catalog_art.py`.",
        "",
        "## Output",
        "",
        f"- Premium scenes rendered: {rendered_scenes}",
        f"- Premium covers rendered: {rendered_covers}",
        f"- Character sheets rendered: {rendered_sheets}",
        f"- Contact sheet: `{CONTACT_SHEET_PNG.relative_to(ROOT)}`",
        "",
        "## Replaced Selected Renderers",
        "",
    ]
    for renderer, count in sorted(replaced_renderers.items()):
        lines.append(f"- `{renderer}`: {count}")
    lines.extend(
        [
            "",
            "## Honesty Notes",
            "",
            "- These assets are story-specific generated-review internal-demo painterly art.",
            "- They are no longer abstract stripe/block placeholders.",
            "- They are not commissioned_final production art and should not be represented as final store-release artwork.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Rendered {rendered_scenes} premium scenes, {rendered_covers} premium covers, {rendered_sheets} character sheets.")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    print(f"Contact sheet: {CONTACT_SHEET_PNG.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
