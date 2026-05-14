#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import shutil
import struct
import subprocess
import wave
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
ASSETS = CONTENT / "assets"
AUDIO = CONTENT / "audio"
PRESENTATION = ASSETS / "presentation"

SCENE_WIDTH = 1024
SCENE_HEIGHT = 768
SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 1024

BOOK_PALETTES = {
    "sun-and-moon": ("#1f294f", "#2f806c", "#f4dfa7", "#d65c31"),
    "gold-axe-silver-axe": ("#263a55", "#387e69", "#f3d36a", "#c8d8de"),
    "tiger-and-persimmon": ("#22315c", "#d85c2f", "#f0b23a", "#31745d"),
    "heungbu-and-nolbu": ("#28385b", "#4b8b62", "#e2c36a", "#c95036"),
    "red-bean-porridge-grandma": ("#252c52", "#9c3144", "#f1d7ab", "#5c8a82"),
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        next_line = word if not current else f"{current} {word}"
        if len(next_line) <= max_chars:
            current = next_line
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:3]


def svg_text_lines(lines: list[str], x: int, y: int, size: int, fill: str, weight: str = "500", anchor: str = "start") -> str:
    parts = []
    for index, line in enumerate(lines):
        parts.append(
            f'<text x="{x}" y="{y + index * int(size * 1.28)}" fill="{fill}" '
            f'font-family="-apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" '
            f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(line)}</text>'
        )
    return "\n".join(parts)


def scene_motif(slug: str, page_number: int, width: int, height: int) -> str:
    moon = f'<circle cx="{width * 0.74:.0f}" cy="{height * 0.22:.0f}" r="{92 + page_number % 5}" fill="#fff3d1" opacity="0.88"/>'
    mountains = "\n".join(
        [
            f'<path d="M{-120+i*230} {height} L{80+i*230} {height*0.46 + (i % 3) * 36:.0f} L{330+i*230} {height} Z" fill="#1f294f" opacity="{0.18 + i*0.035:.2f}"/>'
            for i in range(6)
        ]
    )
    clouds = "\n".join(
        [
            f'<ellipse cx="{150+i*260 + (page_number*17)%90}" cy="{105+i*42}" rx="{74+i*5}" ry="{22+i*3}" fill="#fff8e4" opacity="0.28"/>'
            for i in range(3)
        ]
    )

    if slug == "sun-and-moon":
        figures = f"""
        <circle cx="{width*0.38:.0f}" cy="{height*0.60:.0f}" r="30" fill="#f6c7b6"/>
        <path d="M{width*0.34:.0f} {height*0.69:.0f} Q{width*0.38:.0f} {height*0.58:.0f} {width*0.42:.0f} {height*0.69:.0f} Z" fill="#ecdcc6"/>
        <circle cx="{width*0.46:.0f}" cy="{height*0.63:.0f}" r="24" fill="#f6c7b6"/>
        <path d="M{width*0.43:.0f} {height*0.71:.0f} Q{width*0.46:.0f} {height*0.62:.0f} {width*0.49:.0f} {height*0.71:.0f} Z" fill="#eaa0b8"/>
        <path d="M700 620 Q760 520 828 618" stroke="#d65c31" stroke-width="38" fill="none" stroke-linecap="round"/>
        <circle cx="836" cy="594" r="42" fill="#d65c31"/>
        <path d="M808 582 L864 582 M812 606 L860 606" stroke="#1f294f" stroke-width="5" opacity="0.5"/>
        """
    elif slug == "gold-axe-silver-axe":
        figures = f"""
        <ellipse cx="500" cy="545" rx="190" ry="54" fill="#7fb7b0" opacity="0.62"/>
        <path d="M420 506 L606 584" stroke="#d9b23d" stroke-width="18" stroke-linecap="round"/>
        <path d="M580 472 L722 564" stroke="#ccd6dc" stroke-width="18" stroke-linecap="round"/>
        <circle cx="320" cy="500" r="34" fill="#f3c7a8"/>
        <path d="M270 628 Q322 492 374 628 Z" fill="#386b59"/>
        """
    elif slug == "tiger-and-persimmon":
        fruits = "\n".join(
            [
                f'<circle cx="{250+(i%5)*82}" cy="{310+(i//5)*70}" r="22" fill="#e66f2e"/><path d="M{250+(i%5)*82-9} {288+(i//5)*70} Q{250+(i%5)*82} {278+(i//5)*70} {250+(i%5)*82+9} {288+(i//5)*70}" fill="#4f8a59"/>'
                for i in range(10)
            ]
        )
        figures = f"""
        <path d="M500 640 Q560 395 650 640" stroke="#5f4b2e" stroke-width="28" fill="none"/>
        {fruits}
        <ellipse cx="745" cy="570" rx="112" ry="68" fill="#d65c31"/>
        <circle cx="670" cy="528" r="54" fill="#d65c31"/>
        <path d="M630 515 L710 515 M642 546 L698 546" stroke="#1f294f" stroke-width="7" opacity="0.55"/>
        <path d="M825 560 Q894 510 925 586" stroke="#d65c31" stroke-width="24" fill="none" stroke-linecap="round"/>
        """
    elif slug == "heungbu-and-nolbu":
        gourds = "\n".join(
            [
                f'<ellipse cx="{355+i*92}" cy="{438+(i%2)*42}" rx="42" ry="56" fill="#efe1a5" opacity="0.95"/>'
                for i in range(4)
            ]
        )
        figures = f"""
        <path d="M250 620 L338 430 L426 620 Z" fill="#8a6540" opacity="0.65"/>
        <path d="M320 402 Q528 340 704 418" stroke="#3f8a55" stroke-width="22" fill="none" stroke-linecap="round"/>
        {gourds}
        <path d="M710 280 q52 -38 104 0 q-50 28 -104 0" fill="#22315c"/>
        <path d="M765 282 q42 -30 82 2 q-39 23 -82 -2" fill="#ffffff" opacity="0.78"/>
        """
    else:
        figures = f"""
        <circle cx="345" cy="528" r="72" fill="#9c3144" opacity="0.86"/>
        <ellipse cx="345" cy="500" rx="118" ry="42" fill="#6f2e3d"/>
        <path d="M262 610 Q345 690 428 610" fill="#bf5162"/>
        <circle cx="675" cy="564" r="72" fill="#d65c31"/>
        <path d="M610 558 L740 558 M628 592 L720 592" stroke="#1f294f" stroke-width="7" opacity="0.55"/>
        <circle cx="522" cy="612" r="34" fill="#fff4d8"/>
        <ellipse cx="520" cy="684" rx="82" ry="22" fill="#8a6b41"/>
        """

    return f"{moon}\n{mountains}\n{clouds}\n{figures}"


def scene_svg(book: dict, page: dict) -> str:
    dark, accent, warm, hot = BOOK_PALETTES.get(book["slug"], BOOK_PALETTES["sun-and-moon"])
    page_number = page["pageNumber"]
    title = book["title"]["ko"]
    english = book["title"]["en"]
    prompt_lines = wrap_text(page["englishText"], 54)
    animation_label = page["animation"]["type"].replace("_", " ")
    motif = scene_motif(book["slug"], page_number, SCENE_WIDTH, SCENE_HEIGHT)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SCENE_WIDTH}" height="{SCENE_HEIGHT}" viewBox="0 0 {SCENE_WIDTH} {SCENE_HEIGHT}">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{dark}"/>
      <stop offset="58%" stop-color="{accent}"/>
      <stop offset="100%" stop-color="{warm}"/>
    </linearGradient>
    <filter id="paper" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="2" seed="{page_number + len(book['slug'])}" result="noise"/>
      <feColorMatrix type="saturate" values="0.18"/>
      <feBlend in="SourceGraphic" in2="noise" mode="multiply"/>
    </filter>
    <radialGradient id="jar" cx="50%" cy="42%" r="58%">
      <stop offset="0%" stop-color="#fffaf0" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#fff1ce" stop-opacity="0.24"/>
    </radialGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#sky)"/>
  <rect width="100%" height="100%" fill="#fff4dd" opacity="0.14" filter="url(#paper)"/>
  <circle cx="512" cy="325" r="238" fill="url(#jar)" opacity="0.24"/>
  <circle cx="512" cy="325" r="176" fill="none" stroke="#fff6df" stroke-width="18" opacity="0.5"/>
  {motif}
  <rect x="48" y="46" width="300" height="64" rx="32" fill="#fff8e8" opacity="0.82"/>
  <text x="84" y="87" fill="{dark}" font-family="-apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" font-size="27" font-weight="800">{escape(title)}</text>
  <rect x="700" y="52" width="276" height="46" rx="23" fill="{hot}" opacity="0.78"/>
  <text x="838" y="83" fill="#fff8e8" font-family="-apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" font-size="21" font-weight="700" text-anchor="middle">Scene {page_number:02d} · {escape(animation_label)}</text>
  <rect x="70" y="632" width="884" height="86" rx="28" fill="#fff9eb" opacity="0.82"/>
  {svg_text_lines(prompt_lines, 104, 669, 22, dark, "600")}
  <text x="104" y="602" fill="#fff8e8" font-family="-apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" font-size="24" font-weight="700">{escape(english)}</text>
</svg>
"""


def cover_svg(book: dict) -> str:
    dark, accent, warm, hot = BOOK_PALETTES.get(book["slug"], BOOK_PALETTES["sun-and-moon"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="768" viewBox="0 0 1024 768">
  <defs>
    <linearGradient id="cover" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{dark}"/>
      <stop offset="55%" stop-color="{accent}"/>
      <stop offset="100%" stop-color="{hot}"/>
    </linearGradient>
  </defs>
  <rect width="1024" height="768" fill="url(#cover)"/>
  <circle cx="512" cy="310" r="178" fill="none" stroke="#fff5dc" stroke-width="22" opacity="0.86"/>
  <circle cx="512" cy="310" r="128" fill="#fff5dc" opacity="0.18"/>
  <path d="M120 612 Q512 478 904 612 L904 768 L120 768 Z" fill="{warm}" opacity="0.36"/>
  <text x="512" y="575" fill="#fff8e8" font-family="-apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" font-size="70" font-weight="800" text-anchor="middle">{escape(book['title']['ko'])}</text>
  <text x="512" y="635" fill="#fff8e8" font-family="-apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif" font-size="34" font-weight="600" text-anchor="middle">{escape(book['title']['en'])}</text>
</svg>
"""


def app_icon_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1f294f"/>
      <stop offset="58%" stop-color="#307f6b"/>
      <stop offset="100%" stop-color="#d04f2e"/>
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" rx="220" fill="url(#bg)"/>
  <circle cx="512" cy="456" r="242" fill="#fff4dd" opacity="0.2"/>
  <circle cx="512" cy="456" r="190" fill="none" stroke="#fff7e6" stroke-width="34"/>
  <path d="M290 666 Q512 590 734 666 Q646 806 512 806 Q378 806 290 666 Z" fill="#fff7e6" opacity="0.9"/>
  <circle cx="405" cy="360" r="38" fill="#f0b23a"/>
  <circle cx="620" cy="350" r="30" fill="#f0b23a"/>
  <path d="M384 532 Q512 602 640 532" stroke="#fff7e6" stroke-width="28" fill="none" stroke-linecap="round"/>
</svg>
"""


def presentation_svg(kind: str, books: list[dict]) -> str:
    first = books[0]
    scene = first["pages"][0]
    if kind == "library":
        cards = []
        for idx, book in enumerate(books[:5]):
            x = 86 + (idx % 3) * 394
            y = 230 + (idx // 3) * 330
            dark, accent, warm, hot = BOOK_PALETTES[book["slug"]]
            cards.append(f"""
              <rect x="{x}" y="{y}" width="320" height="250" rx="18" fill="#fff9eb" opacity="0.92"/>
              <rect x="{x+18}" y="{y+18}" width="284" height="130" rx="14" fill="{accent}"/>
              <circle cx="{x+160}" cy="{y+82}" r="42" fill="none" stroke="#fff8e8" stroke-width="10"/>
              <text x="{x+28}" y="{y+188}" fill="#1f294f" font-size="30" font-weight="800" font-family="-apple-system, Helvetica">{escape(book['title']['ko'])}</text>
              <text x="{x+28}" y="{y+224}" fill="#1f294f" font-size="19" font-weight="600" opacity="0.65" font-family="-apple-system, Helvetica">{escape(book['title']['en'][:28])}</text>
            """)
        body = "\n".join(cards)
        title = "Library"
    elif kind == "reader":
        body = f"""
          <rect x="76" y="132" width="1214" height="640" rx="28" fill="#fff4dd" opacity="0.32"/>
          <image href="../books/{first['slug']}/page-001.png" x="112" y="168" width="1142" height="520" preserveAspectRatio="xMidYMid slice"/>
          <rect x="112" y="708" width="1142" height="130" rx="22" fill="#fff9eb" opacity="0.94"/>
          {svg_text_lines(wrap_text(scene['englishText'], 80), 152, 760, 30, "#1f294f", "700")}
          <circle cx="683" cy="902" r="42" fill="#d04f2e"/><text x="683" y="914" fill="#fff8e8" font-size="38" text-anchor="middle" font-family="-apple-system, Helvetica">▶</text>
        """
        title = "Reader"
    else:
        body = """
          <rect x="360" y="190" width="646" height="650" rx="34" fill="#fff9eb" opacity="0.94"/>
          <circle cx="683" cy="330" r="96" fill="none" stroke="#307f6b" stroke-width="18"/>
          <text x="683" y="490" fill="#1f294f" font-size="48" font-weight="850" text-anchor="middle" font-family="-apple-system, Helvetica">Premium Korean Library</text>
          <rect x="440" y="550" width="486" height="76" rx="18" fill="#1f294f" opacity="0.08"/>
          <text x="478" y="600" fill="#1f294f" font-size="30" font-weight="750" font-family="-apple-system, Helvetica">Monthly</text>
          <text x="878" y="600" fill="#1f294f" font-size="30" font-weight="750" text-anchor="end" font-family="-apple-system, Helvetica">$4.99</text>
          <rect x="440" y="646" width="486" height="76" rx="18" fill="#1f294f" opacity="0.08"/>
          <text x="478" y="696" fill="#1f294f" font-size="30" font-weight="750" font-family="-apple-system, Helvetica">Annual</text>
          <text x="878" y="696" fill="#1f294f" font-size="30" font-weight="750" text-anchor="end" font-family="-apple-system, Helvetica">$39.99</text>
          <rect x="440" y="754" width="486" height="70" rx="35" fill="#d04f2e"/>
          <text x="683" y="800" fill="#fff8e8" font-size="29" font-weight="800" text-anchor="middle" font-family="-apple-system, Helvetica">Parent Check</text>
        """
        title = "Paywall"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SCREEN_WIDTH}" height="{SCREEN_HEIGHT}" viewBox="0 0 {SCREEN_WIDTH} {SCREEN_HEIGHT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#faf3de"/>
      <stop offset="100%" stop-color="#e7d09d"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#bg)"/>
  <text x="76" y="88" fill="#1f294f" font-size="54" font-weight="850" font-family="-apple-system, Helvetica">Moon Jar Stories · {title}</text>
  {body}
</svg>
"""


def convert_svg_to_png(svg: Path, png: Path) -> None:
    png.parent.mkdir(parents=True, exist_ok=True)
    sips = shutil.which("sips")
    if not sips:
        raise RuntimeError("macOS 'sips' is required to convert generated SVG placeholders to PNG.")
    subprocess.run([sips, "-s", "format", "png", str(svg), "--out", str(png)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def write_tone_wav(path: Path, duration: float, frequency: float = 0.0, amplitude: float = 0.0, sample_rate: int = 22050) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(duration * sample_rate)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        data = bytearray()
        for i in range(frames):
            if frequency > 0 and amplitude > 0:
                envelope = min(1.0, i / max(1, sample_rate * 0.05), (frames - i) / max(1, sample_rate * 0.08))
                value = int(32767 * amplitude * envelope * math.sin(2 * math.pi * frequency * i / sample_rate))
            else:
                value = 0
            data.extend(struct.pack("<h", value))
        handle.writeframes(bytes(data))


def main() -> None:
    catalog = load_json(CONTENT / "catalog.json")
    complete_books: list[dict] = []

    for entry in catalog["books"]:
        if entry["status"] != "complete":
            continue
        book_path = CONTENT / entry["bookPath"]
        book = load_json(book_path)
        complete_books.append(book)
        book_asset_dir = ASSETS / "books" / book["slug"]
        book_audio_dir = AUDIO / "books" / book["slug"]
        book_asset_dir.mkdir(parents=True, exist_ok=True)

        cover_source = book_asset_dir / "cover.svg"
        cover_png = book_asset_dir / "cover.png"
        cover_source.write_text(cover_svg(book), encoding="utf-8")
        convert_svg_to_png(cover_source, cover_png)

        ambient_path = book_audio_dir / "ambient" / "ambient-loop.wav"
        write_tone_wav(ambient_path, duration=1.0, frequency=174.0, amplitude=0.015)

        for page in book["pages"]:
            page_number = page["pageNumber"]
            page_base = f"page-{page_number:03d}"
            svg_path = book_asset_dir / f"{page_base}.svg"
            png_path = book_asset_dir / f"{page_base}.png"
            audio_path = book_audio_dir / "ko" / f"{page_base}.wav"

            svg_path.write_text(scene_svg(book, page), encoding="utf-8")
            convert_svg_to_png(svg_path, png_path)
            write_tone_wav(audio_path, duration=0.65, frequency=220.0 + (page_number % 7) * 24.0, amplitude=0.012)

            page["imageAsset"] = f"assets/books/{book['slug']}/{page_base}.png"
            page["imageSource"] = f"assets/books/{book['slug']}/{page_base}.svg"
            page["narrationAudio"] = f"audio/books/{book['slug']}/ko/{page_base}.wav"
            page["ambientAudio"] = f"audio/books/{book['slug']}/ambient/ambient-loop.wav"

        book["coverAsset"] = f"assets/books/{book['slug']}/cover.png"
        write_json(book_path, book)

    ui_asset_dir = ASSETS / "ui"
    ui_audio_dir = AUDIO / "ui"
    ui_asset_dir.mkdir(parents=True, exist_ok=True)
    icon_svg = ui_asset_dir / "app-icon.svg"
    icon_png = ui_asset_dir / "app-icon.png"
    icon_svg.write_text(app_icon_svg(), encoding="utf-8")
    convert_svg_to_png(icon_svg, icon_png)

    write_tone_wav(ui_audio_dir / "page-flip.wav", duration=0.24, frequency=440.0, amplitude=0.035)
    write_tone_wav(ui_audio_dir / "button-tap.wav", duration=0.12, frequency=660.0, amplitude=0.02)

    PRESENTATION.mkdir(parents=True, exist_ok=True)
    for kind in ("library", "reader", "paywall"):
        svg_path = PRESENTATION / f"{kind}-mockup.svg"
        png_path = PRESENTATION / f"{kind}-mockup.png"
        svg_path.write_text(presentation_svg(kind, complete_books), encoding="utf-8")
        convert_svg_to_png(svg_path, png_path)

    print(f"Generated demo scene assets for {len(complete_books)} books.")
    print(f"Assets: {ASSETS}")
    print(f"Audio: {AUDIO}")
    print(f"Presentation mockups: {PRESENTATION}")


if __name__ == "__main__":
    main()

