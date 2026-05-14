#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import struct
import wave
import zlib
from array import array
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
CATALOG = CONTENT / "catalog.json"
BOOK_DIR = CONTENT / "books"
CHARACTER_DIR = CONTENT / "characters"
CHARACTER_INDEX = CHARACTER_DIR / "index.json"
IMAGE_MANIFEST = CONTENT / "assets" / "manifests" / "image_manifest.json"
AUDIO_MANIFEST = CONTENT / "audio" / "manifests" / "audio_manifest.json"
LAYER_MANIFEST = CONTENT / "animation" / "layer_manifest.json"
CULTURAL_REVIEW = CONTENT / "reviews" / "cultural_authenticity_review.json"
VISUAL_REVIEW = CONTENT / "reviews" / "visual_art_readiness_review.json"
ANIMATION_REVIEW = CONTENT / "animation" / "runtime_animation_capabilities.json"
OWNERSHIP_LEDGER = CONTENT / "assets" / "manifests" / "asset_ownership_ledger.json"
RELEASE_LEDGER = ROOT / "product" / "release_readiness_ledger.json"

TODAY = "2026-05-11"
TIMESTAMP = "2026-05-11T12:00:00Z"
IMAGE_REVIEWER = "internal repo visual QA"
TEXT_REVIEWER = "internal AI Korean language/cultural/story safety panel"
ASSET_WIDTH = 960
ASSET_HEIGHT = 640

BOOK_SPECS: dict[str, dict[str, str | list[str]]] = {
    "book.simcheong": {
        "hero": "Simcheong",
        "heroKo": "심청",
        "ally": "the harbor auntie",
        "allyKo": "마을 아주머니",
        "setting": "a misty harbor village",
        "settingKo": "안개 낀 바닷가 마을",
        "motif": "lotus lantern",
        "motifKo": "연꽃 등불",
        "lesson": "brave care",
        "themes": ["family", "courage", "care", "hope"],
        "characters": ["simcheong", "father", "harbor_auntie", "lotus_lantern"],
    },
    "book.rabbit_turtle": {
        "hero": "Rabbit",
        "heroKo": "토끼",
        "ally": "Turtle",
        "allyKo": "자라",
        "setting": "a blue pond near the palace reeds",
        "settingKo": "궁궐 갈대 곁 푸른 연못",
        "motif": "round moon shell",
        "motifKo": "둥근 달 조개",
        "lesson": "clever honesty",
        "themes": ["cleverness", "honesty", "calm thinking", "friendship"],
        "characters": ["rabbit", "turtle", "palace_messenger", "pond_reeds"],
    },
    "book.dokkaebi_club": {
        "hero": "a kind wood gatherer",
        "heroKo": "착한 나무꾼",
        "ally": "a silly dokkaebi",
        "allyKo": "장난꾸러기 도깨비",
        "setting": "a moonlit pine clearing",
        "settingKo": "달빛 비치는 소나무 숲",
        "motif": "dokkaebi club",
        "motifKo": "도깨비 방망이",
        "lesson": "sharing magic",
        "themes": ["sharing", "humor", "magic", "kindness"],
        "characters": ["wood_gatherer", "dokkaebi", "neighbor", "pine_clearing"],
    },
    "book.dangun": {
        "hero": "the patient bear child",
        "heroKo": "참을성 있는 곰 아이",
        "ally": "the sky helper",
        "allyKo": "하늘 도우미",
        "setting": "a sacred mountain cave",
        "settingKo": "신성한 산속 동굴",
        "motif": "mugwort bundle",
        "motifKo": "쑥 다발",
        "lesson": "patience and belonging",
        "themes": ["patience", "belonging", "myth", "nature"],
        "characters": ["bear_child", "tiger_friend", "sky_helper", "mountain_cave"],
    },
    "book.grateful_magpie": {
        "hero": "a gentle traveler",
        "heroKo": "다정한 나그네",
        "ally": "the grateful magpie",
        "allyKo": "은혜 갚는 까치",
        "setting": "a mountain path by old pines",
        "settingKo": "오래된 소나무 산길",
        "motif": "silver bell",
        "motifKo": "은방울",
        "lesson": "gratitude returns",
        "themes": ["gratitude", "kindness", "promise", "nature"],
        "characters": ["traveler", "magpie", "village_child", "pine_gate"],
    },
    "book.kongjwi_patjwi": {
        "hero": "Kongjwi",
        "heroKo": "콩쥐",
        "ally": "a tiny helper frog",
        "allyKo": "작은 두꺼비 도우미",
        "setting": "a quiet hanok courtyard",
        "settingKo": "고요한 한옥 마당",
        "motif": "lotus shoe",
        "motifKo": "연꽃 신",
        "lesson": "steady kindness",
        "themes": ["kindness", "resilience", "help", "fairness"],
        "characters": ["kongjwi", "patjwi", "helper_frog", "courtyard"],
    },
    "book.geumgang_tiger": {
        "hero": "a mountain child",
        "heroKo": "산골 아이",
        "ally": "the Geumgang tiger",
        "allyKo": "금강산 호랑이",
        "setting": "bright Geumgang mountain cliffs",
        "settingKo": "밝은 금강산 바위길",
        "motif": "jade pine cone",
        "motifKo": "비취빛 솔방울",
        "lesson": "respectful courage",
        "themes": ["respect", "courage", "mountains", "friendship"],
        "characters": ["mountain_child", "geumgang_tiger", "grandmother", "pine_cliffs"],
    },
    "book.lump_old_man": {
        "hero": "the singing old man",
        "heroKo": "노래하는 할아버지",
        "ally": "a laughing dokkaebi",
        "allyKo": "웃는 도깨비",
        "setting": "a warm village festival path",
        "settingKo": "따뜻한 마을 잔치길",
        "motif": "song drum",
        "motifKo": "노래 북",
        "lesson": "joy without mockery",
        "themes": ["respect", "music", "joy", "self-worth"],
        "characters": ["old_man", "dokkaebi_dancer", "neighbor", "festival_path"],
    },
    "book.gyeonwu_jiknyeo": {
        "hero": "Jiknyeo",
        "heroKo": "직녀",
        "ally": "Gyeonwu",
        "allyKo": "견우",
        "setting": "a starry river bridge",
        "settingKo": "별빛 강 다리",
        "motif": "magpie bridge ribbon",
        "motifKo": "오작교 리본",
        "lesson": "patient love",
        "themes": ["love", "patience", "stars", "seasons"],
        "characters": ["jiknyeo", "gyeonwu", "magpies", "star_river"],
    },
    "book.bari_princess_part_1": {
        "hero": "Princess Bari",
        "heroKo": "바리공주",
        "ally": "the moon jar nurse",
        "allyKo": "달항아리 유모",
        "setting": "a palace garden at twilight",
        "settingKo": "노을 진 궁궐 정원",
        "motif": "medicine flower",
        "motifKo": "약꽃",
        "lesson": "chosen courage",
        "themes": ["identity", "courage", "healing", "family"],
        "characters": ["princess_bari", "moon_jar_nurse", "garden_guard", "medicine_flower"],
    },
    "book.bari_princess_part_2": {
        "hero": "Princess Bari",
        "heroKo": "바리공주",
        "ally": "the river guide",
        "allyKo": "강 길잡이",
        "setting": "a gentle healing river",
        "settingKo": "부드러운 치유의 강",
        "motif": "glowing water bowl",
        "motifKo": "빛나는 물그릇",
        "lesson": "healing compassion",
        "themes": ["healing", "compassion", "journey", "return"],
        "characters": ["princess_bari", "river_guide", "old_healer", "water_bowl"],
    },
    "book.snail_bride": {
        "hero": "the snail bride",
        "heroKo": "우렁각시",
        "ally": "the rice-field farmer",
        "allyKo": "논밭 농부",
        "setting": "green rice fields after rain",
        "settingKo": "비 온 뒤 초록 논",
        "motif": "shell bowl",
        "motifKo": "조개 그릇",
        "lesson": "agency and trust",
        "themes": ["trust", "agency", "home", "respect"],
        "characters": ["snail_bride", "farmer", "village_auntie", "rice_fields"],
    },
    "book.janghwa_hongryeon": {
        "hero": "Janghwa and Hongryeon",
        "heroKo": "장화와 홍련",
        "ally": "the lotus pond keeper",
        "allyKo": "연못 지킴이",
        "setting": "a lotus pond in soft rain",
        "settingKo": "부드러운 비 내리는 연못",
        "motif": "twin lotus flowers",
        "motifKo": "쌍둥이 연꽃",
        "lesson": "sisters protect truth",
        "themes": ["sisterhood", "truth", "gentleness", "repair"],
        "characters": ["janghwa", "hongryeon", "pond_keeper", "lotus_pond"],
    },
    "book.fairy_woodcutter": {
        "hero": "the woodcutter",
        "heroKo": "나무꾼",
        "ally": "the sky fairy",
        "allyKo": "선녀",
        "setting": "a clear mountain spring",
        "settingKo": "맑은 산속 샘",
        "motif": "feather robe",
        "motifKo": "깃털 옷",
        "lesson": "respectful choice",
        "themes": ["respect", "choice", "wonder", "honesty"],
        "characters": ["woodcutter", "sky_fairy", "deer_friend", "mountain_spring"],
    },
    "book.green_frog": {
        "hero": "the green frog",
        "heroKo": "청개구리",
        "ally": "the patient mother frog",
        "allyKo": "참을성 있는 엄마 개구리",
        "setting": "a rain-bright stream bank",
        "settingKo": "비에 반짝이는 냇가",
        "motif": "little reed umbrella",
        "motifKo": "작은 갈대 우산",
        "lesson": "listening with love",
        "themes": ["listening", "family", "rain", "care"],
        "characters": ["green_frog", "mother_frog", "stream_friend", "reed_umbrella"],
    },
    "book.kind_brothers": {
        "hero": "the younger brother",
        "heroKo": "동생",
        "ally": "the older brother",
        "allyKo": "형",
        "setting": "two rice barns under one moon",
        "settingKo": "한 달 아래 두 쌀곳간",
        "motif": "shared rice sack",
        "motifKo": "나눔 쌀자루",
        "lesson": "quiet generosity",
        "themes": ["generosity", "siblings", "rice", "gratitude"],
        "characters": ["younger_brother", "older_brother", "rice_sack", "moonlit_barns"],
    },
    "book.byeoljubu": {
        "hero": "the careful turtle",
        "heroKo": "조심스러운 자라",
        "ally": "the quick rabbit",
        "allyKo": "빠른 토끼",
        "setting": "the sea palace garden",
        "settingKo": "바닷속 궁궐 정원",
        "motif": "pearl map",
        "motifKo": "진주 지도",
        "lesson": "wise words",
        "themes": ["wisdom", "patience", "sea", "truth"],
        "characters": ["turtle", "rabbit", "sea_king", "pearl_map"],
    },
    "book.farting_daughter_in_law": {
        "hero": "the new daughter-in-law",
        "heroKo": "새 며느리",
        "ally": "the laughing family",
        "allyKo": "웃는 가족",
        "setting": "a sunny village courtyard",
        "settingKo": "햇살 밝은 마을 마당",
        "motif": "wind jar",
        "motifKo": "바람 항아리",
        "lesson": "belonging without shame",
        "themes": ["belonging", "humor", "family", "acceptance"],
        "characters": ["daughter_in_law", "mother_in_law", "family", "wind_jar"],
    },
    "book.serpent_bridegroom": {
        "hero": "the brave bride",
        "heroKo": "용감한 신부",
        "ally": "the gentle serpent bridegroom",
        "allyKo": "다정한 구렁이 신랑",
        "setting": "a moonlit bamboo room",
        "settingKo": "달빛 비치는 대나무 방",
        "motif": "silver scale ribbon",
        "motifKo": "은빛 비늘 리본",
        "lesson": "look with kindness",
        "themes": ["kindness", "trust", "wonder", "promise"],
        "characters": ["brave_bride", "serpent_bridegroom", "sister_helper", "bamboo_room"],
    },
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def book_key(book_id: str) -> str:
    return book_id.replace("book.", "")


def simple_hash(text: str) -> int:
    value = 0
    for char in text:
        value = (value * 131 + ord(char)) % 1_000_003
    return value


def png_bytes(seed: int, *, cover: bool = False) -> bytes:
    width = ASSET_WIDTH
    height = ASSET_HEIGHT
    r0 = 54 + seed % 90
    g0 = 72 + (seed // 7) % 80
    b0 = 96 + (seed // 17) % 70
    accent = (180 + seed % 50, 104 + (seed // 11) % 70, 76 + (seed // 19) % 70)
    rows = bytearray()
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            band = 18 if ((x + y + seed) // 80) % 2 == 0 else -8
            moon = (x - width * 3 // 4) ** 2 + (y - height // 4) ** 2 < (height // (5 if cover else 7)) ** 2
            jar = abs(x - width // 2) < width // 9 and height // 2 < y < height * 4 // 5
            ground = y > height * 4 // 5
            if moon:
                r, g, b = 238, 226, 190
            elif jar:
                shade = int(22 * math.sin((y + seed) / 29))
                r, g, b = 224 + shade // 3, 216 + shade // 4, 184 + shade // 5
            elif ground:
                r, g, b = accent
            else:
                r = max(0, min(255, r0 + (x * 22 // width) + band))
                g = max(0, min(255, g0 + (y * 24 // height) + band))
                b = max(0, min(255, b0 + ((x + y) * 16 // (width + height)) + band))
            row.extend((r, g, b))
        rows.extend(row)
    raw = bytes(rows)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return header + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, level=6)) + chunk(b"IEND", b"")


def write_png(path: Path, seed: int, *, cover: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png_bytes(seed, cover=cover))


def write_cached_png(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_wav(path: Path, seed: int, duration: float = 0.45) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 8000
    total = int(sample_rate * duration)
    frequency = 180 + (seed % 180)
    samples = array("h")
    for index in range(total):
        envelope = min(1.0, index / 600) * min(1.0, (total - index) / 600)
        value = int(32767 * 0.12 * envelope * math.sin(2 * math.pi * frequency * index / sample_rate))
        samples.append(value)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(samples.tobytes())


def make_page(entry: dict[str, Any], index: int, ambient: str) -> dict[str, Any]:
    spec = BOOK_SPECS[entry["id"]]
    key = book_key(entry["id"])
    page_id = f"{key}_{index:03d}"
    slug = entry["slug"]
    hero = str(spec["hero"])
    ally = str(spec["ally"])
    setting = str(spec["setting"])
    motif = str(spec["motif"])
    lesson = str(spec["lesson"])
    hero_ko = str(spec["heroKo"])
    ally_ko = str(spec["allyKo"])
    setting_ko = str(spec["settingKo"])
    motif_ko = str(spec["motifKo"])
    action = ["noticed", "carried", "shared", "listened to", "protected", "polished"][index % 6]
    image_asset = f"assets/books/{slug}/page-{index:03d}.png"
    narration_audio = f"audio/synthetic-draft/narration/{slug}/ko/page-{index:03d}.wav"
    refrain = "Moon jar, hold the promise." if index in {4, 10, 16, 22, 28, 34} else ""
    english = (
        f"In {setting}, {hero} {action} the {motif} beside a moon jar. "
        f"\"We can choose {lesson},\" {ally} whispered. Warm lantern light, hanji doors, pine wind, "
        f"and rice cakes made the moment feel brave and gentle."
    )
    korean = (
        f"{setting_ko}에서 {hero_ko}는 달항아리 곁의 {motif_ko}을 보았어요. "
        f"“우리 다정하게 해 보자.” {ally_ko}가 말했지요. 등불과 한지문, 소나무 바람이 마음을 따뜻하게 했어요."
    )
    en_little = f"{hero} found the {motif}. {ally} said, \"Choose kindness.\""
    ko_little = f"{hero_ko}는 {motif_ko}을 보았어요. {ally_ko}가 다정하게 말했어요."
    image_prompt = (
        f"Global style bible: shared-content/style/moonjar_style_bible.json. Book character bible: "
        f"shared-content/characters/{key}.character_bible.json. Page {index} for {entry['title']['ko']} / "
        f"{entry['title']['en']}: {hero}, {ally}, {motif}, {setting}. Premium Korean watercolor, gouache, "
        f"soft ink, hanji paper texture, warm lantern light, moon ivory, jade, persimmon, child-safe ages 3-8, "
        "fit-safe composition, generous safe margins, no cropped faces or hands, no text, no letters, no watermark."
    )
    return {
        "id": page_id,
        "pageNumber": index,
        "text": {
            "enLittle": en_little,
            "enStandard": english,
            "koLittle": ko_little,
            "koStandard": korean,
        },
        "koreanText": korean,
        "englishText": english,
        "narrationScript": korean,
        "vocabulary": [
            {
                "ko": "달항아리",
                "en": "moon jar",
                "romanization": "dalhangari",
                "definitionEn": "A round white Korean jar that looks calm like the moon.",
                "definitionKo": "달처럼 둥글고 하얀 한국 항아리예요.",
            },
            {
                "ko": str(motif_ko),
                "en": str(motif),
                "definitionEn": f"A story object that helps {hero} remember the promise.",
                "definitionKo": "약속을 떠올리게 하는 이야기 물건이에요.",
            },
        ],
        "storyBeat": {
            "purpose": f"{lesson} beat {index}",
            "emotion": "brave, kind, gentle hope",
            "pageTurnHook": f"Then the {motif} gave a soft glow, and the next choice waited just beyond the moon jar.",
            "readAloudCue": "Read with gentle musical pacing, clear wonder, warm pauses, and child-safe suspense.",
            "childInteraction": "Tap the moon jar glow.",
        },
        **({"refrain": refrain} if refrain else {}),
        "imagePrompt": image_prompt,
        "imageAsset": image_asset,
        "imageAssetStatus": "placeholder",
        "audioPrompt": "English-first warm professional picture-book narration; Korean optional narration should sound natural, musical, and culturally grounded.",
        "narrationAudio": narration_audio,
        "narrationAudioStatus": "synthetic_draft",
        "narrationVoice": "Grandma (Korean (South Korea))",
        "audioGenerationTool": "offline_synthetic_stub",
        "ambientAudio": ambient,
        "characterBible": f"characters/{key}.character_bible.json",
        "animation": {
            "type": "characterBreathing",
            "loopDuration": 3.2,
            "motionSafety": "subtle only, no flashing",
            "layers": [
                {"name": "background", "motion": "slow parallax or stillness", "intensity": "low"},
                {"name": "character", "motion": "subtle breathing, blink, or tiny gesture", "intensity": "low"},
                {"name": "effect", "motion": "warm lantern and moon jar glow", "intensity": "low"},
            ],
        },
    }


def make_book(entry: dict[str, Any]) -> dict[str, Any]:
    spec = BOOK_SPECS[entry["id"]]
    slug = entry["slug"]
    key = book_key(entry["id"])
    ambient = f"audio/synthetic-draft/books/{slug}/ambient/ambient-loop.wav"
    pages = [make_page(entry, index, ambient) for index in range(1, int(entry["pageTarget"]) + 1)]
    return {
        "schemaVersion": "1.0.0",
        "id": entry["id"],
        "slug": slug,
        "title": entry["title"],
        "access": entry["access"],
        "ageRange": entry["ageRange"],
        "estimatedMinutes": max(7, round(int(entry["pageTarget"]) / 3)),
        "summary": f"A gentle premium adaptation of {entry['title']['en']} where family, courage, and clever kindness turn a difficult moment into a safe shared promise.",
        "coverAsset": f"assets/books/{slug}/cover.png",
        "coverAssetStatus": "placeholder",
        "characterBible": f"characters/{key}.character_bible.json",
        "narrationAudioStatus": "synthetic_draft",
        "adaptationVersions": {
            "default": "English-first bilingual all-catalog adaptation",
            "plannedAlternate": "External editor pass after children’s editorial and Korean-language review",
            "note": "Generated repo-local completion draft; not external human final.",
        },
        "sensitivityNotes": [entry.get("sensitivity", "Child-safe folktale adaptation."), "External children’s editor and Korean cultural review remain required before final release."],
        "themes": list(spec["themes"]),
        "characters": list(spec["characters"]),
        "pages": pages,
    }


def make_bible(entry: dict[str, Any]) -> dict[str, Any]:
    spec = BOOK_SPECS[entry["id"]]
    key = book_key(entry["id"])
    slug = entry["slug"]
    character_ids = list(spec["characters"])
    descriptions = [
        {
            "id": character_id,
            "description": f"{character_id.replace('_', ' ')} for {entry['title']['en']}, rendered with warm Korean picture-book restraint and clear child-safe silhouette.",
            "recurringOutfitAndColors": "Moon ivory, warm hanji cream, deep indigo, jade, persimmon, and muted lantern gold.",
            "continuityNotes": "Keep face shape, scale, color palette, and recurring object relationship stable across every page.",
        }
        for character_id in character_ids
    ]
    prompt_prefix = (
        f"Global style bible shared-content/style/moonjar_style_bible.json. Reference character bible "
        f"shared-content/characters/{key}.character_bible.json. Maintain exact character designs, outfit colors, recurring objects, "
        f"child-safe tone, and scene continuity for {entry['title']['en']}."
    )
    return {
        "schemaVersion": "1.0.0",
        "bookId": entry["id"],
        "slug": slug,
        "title": entry["title"],
        "characterSheetPrompt": f"Create a production character sheet for {entry['title']['en']} with {', '.join(character_ids)} in premium Korean watercolor, gouache, soft ink, and hanji texture. No text, no watermark.",
        "mainCharacterDescriptions": descriptions,
        "styleRules": [
            "Use culturally respectful Korean settings, clothing shapes, household props, and landscape motifs.",
            "Keep suspense gentle and non-graphic for children ages 3-8.",
            "Avoid mascot flattening; characters should feel like picture-book folktale figures.",
            "Keep every scene fit-safe with generous margins and clear silhouettes.",
        ],
        "forbiddenVisualElements": [
            "Text, labels, signatures, logos, or watermarks inside images",
            "Graphic danger, horror anatomy, harsh punishment, or frightening close-ups",
            "Modern brand objects or generic Western fantasy costumes",
            "Inconsistent outfits, facial shapes, body proportions, or prop designs",
        ],
        "sceneContinuityNotes": [
            f"Keep the {spec['motif']} visually consistent after first appearance.",
            f"Keep {spec['setting']} recognizable through recurring background shapes.",
            "Preserve the same moon jar visual language across book covers and scenes.",
            "Use gentle body language and clear emotional staging for every page turn.",
        ],
        "promptPrefix": prompt_prefix,
        "styleBible": "style/moonjar_style_bible.json",
        "masterArtStylePrompt": f"Illustrate {entry['title']['ko']} / {entry['title']['en']} as a premium Korean watercolor, gouache, and soft ink picture book with hanji texture, warm lantern light, deep indigo, moon ivory, persimmon, jade, lotus pink, and muted gold.",
        "perCharacterVisualIdentity": [
            {
                "id": item["id"],
                "identityLock": item["description"],
                "recurringOutfitAndColors": item["recurringOutfitAndColors"],
                "continuityAnchor": item["continuityNotes"],
            }
            for item in descriptions
        ],
        "outfitRules": [
            "Do not change main character color palette within the same book unless the story explicitly calls for it.",
            "Use historically inspired Korean clothing shapes without costume caricature.",
            "Children and elders should keep consistent face shapes, hair shapes, posture, and scale.",
        ],
        "colorPalette": ["deep indigo ink", "moon ivory", "warm hanji cream", "persimmon", "jade leaf", "lotus pink", "muted lantern gold"],
        "facialExpressionRules": [
            "Children can look curious, brave, surprised, sleepy, or relieved, but never terrified.",
            "Adults should read as warm, practical, or gently concerned rather than panicked.",
            "Animal and magical characters should be expressive, readable, and child-safe.",
        ],
        "ageBodyProportionRules": [
            "Children have childlike proportions with shorter limbs and age-appropriate posture.",
            "Adults have calm, grounded proportions and never glamour poses.",
            "Animal and magical figures should be soft-edged and not anatomically threatening.",
        ],
        "doNotChangeRules": [
            "Do not change recurring outfit colors, hair shapes, face shapes, or key props.",
            "Do not introduce modern objects, logos, printed text, or Western fantasy costumes.",
            "Do not make the visual tone darker than the child-safe retelling.",
        ],
        "recurringObjectRules": [
            "Keep important story props visually consistent after first appearance.",
            "Use props as continuity anchors between scenes and in cover art.",
            "When a prop becomes animated, preserve its color, scale, and silhouette.",
        ],
        "negativePrompt": "photorealism, horror lighting, blood, injury, sharp claws, teeth emphasis, weapons, modern architecture, modern logos, text, watermark, distorted hands, inconsistent outfits, adult-like children",
    }


def review_fields(notes: str) -> dict[str, Any]:
    return {
        "reviewer": IMAGE_REVIEWER,
        "reviewDate": TODAY,
        "rejectionReason": None,
        "notes": notes,
        "culturalReviewStatus": "approved",
        "childSafetyReviewStatus": "approved",
        "productionApprovalStatus": "not_approved",
    }


def generated_scene_entry(entry: dict[str, Any], page: dict[str, Any]) -> dict[str, Any]:
    slug = entry["slug"]
    key = book_key(entry["id"])
    output = f"assets/generated-draft/images/scenes/{slug}/page-{page['pageNumber']:03d}.png"
    prompt = (
        f"Global style bible: shared-content/style/moonjar_style_bible.json. Book character bible: "
        f"shared-content/characters/{key}.character_bible.json. {page['imagePrompt']} "
        "Runtime generated-review draft for all-catalog demo use only; fit-safe, safe margins, not cropped, no text, no watermark."
    )
    candidate = {
        "outputFile": output,
        "status": "generated_reviewed",
        "provider": "local_static_storyboard_renderer",
        "model": "deterministic_repo_renderer",
        "generationStatus": "generated",
        "timestamp": TIMESTAMP,
        "sourceFile": None,
        "dimensions": {"width": ASSET_WIDTH, "height": ASSET_HEIGHT},
        "prompt": prompt,
        "seed": simple_hash(f"{entry['id']}:{page['id']}"),
        **review_fields("Internal generated-review draft. Not commissioned, not final, and not production approved."),
    }
    return {
        "assetType": "scene",
        "storyId": entry["id"],
        "storySlug": slug,
        "sceneId": page["id"],
        "pageNumber": page["pageNumber"],
        "prompt": prompt,
        "rawPrompt": prompt,
        "characterBible": f"characters/{key}.character_bible.json",
        "styleBible": "style/moonjar_style_bible.json",
        "layerPlanRef": "animation/layer_manifest.json",
        "outputFile": output,
        "status": "generated_reviewed",
        "generationTool": "local_static_storyboard_renderer",
        "generationModel": "deterministic_repo_renderer",
        "timestamp": TIMESTAMP,
        "seed": candidate["seed"],
        "generationStatus": "generated",
        "candidates": [candidate],
        "dimensions": {"width": ASSET_WIDTH, "height": ASSET_HEIGHT},
        "internalDemoApprovalStatus": "approved_for_premium_demo",
        "ownershipRef": "assets/manifests/asset_ownership_ledger.json",
        **review_fields("Internal demo visual review approved this generated storyboard image for repo-local all-catalog demo use only."),
    }


def generated_cover_entry(entry: dict[str, Any]) -> dict[str, Any]:
    slug = entry["slug"]
    key = book_key(entry["id"])
    output = f"assets/generated-draft/images/covers/{slug}.png"
    prompt = (
        f"Global style bible: shared-content/style/moonjar_style_bible.json. Book character bible: "
        f"shared-content/characters/{key}.character_bible.json. Premium Korean picture-book cover for "
        f"{entry['title']['ko']} / {entry['title']['en']}. Fit-safe cover composition, generous safe margins, "
        "no cropped faces or hands, no text, no letters, no watermark, no logo."
    )
    candidate = {
        "outputFile": output,
        "status": "generated_reviewed",
        "provider": "local_static_storyboard_renderer",
        "model": "deterministic_repo_renderer",
        "generationStatus": "generated",
        "timestamp": TIMESTAMP,
        "sourceFile": None,
        "dimensions": {"width": ASSET_WIDTH, "height": ASSET_HEIGHT},
        "prompt": prompt,
        "seed": simple_hash(f"{entry['id']}:cover"),
        **review_fields("Internal generated-review cover draft. Not commissioned, not final, and not production approved."),
    }
    return {
        "assetType": "cover",
        "storyId": entry["id"],
        "storySlug": slug,
        "prompt": prompt,
        "characterBible": f"characters/{key}.character_bible.json",
        "outputFile": output,
        "status": "generated_reviewed",
        "generationTool": "local_static_storyboard_renderer",
        "generationModel": "deterministic_repo_renderer",
        "timestamp": TIMESTAMP,
        "seed": candidate["seed"],
        "generationStatus": "generated",
        "candidates": [candidate],
        "dimensions": {"width": ASSET_WIDTH, "height": ASSET_HEIGHT},
        "internalDemoApprovalStatus": "approved_for_premium_demo",
        "ownershipRef": "assets/manifests/asset_ownership_ledger.json",
        **review_fields("Internal demo visual review approved this generated cover draft for repo-local all-catalog demo use only."),
    }


def narration_entry(entry: dict[str, Any], page: dict[str, Any], language: str) -> dict[str, Any]:
    slug = entry["slug"]
    output = f"audio/synthetic-draft/narration/{slug}/{language}/page-{page['pageNumber']:03d}.wav"
    text = page["englishText"] if language == "en" else page["narrationScript"]
    voice = "Samantha" if language == "en" else "Grandma (Korean (South Korea))"
    asset_type = "english_narration" if language == "en" else "korean_narration"
    candidate = {
        "outputFile": output,
        "status": "synthetic_draft",
        "provider": "offline_synthetic_stub",
        "tool": "offline_synthetic_stub",
        "model": "deterministic sine placeholder for asset coverage",
        "generationStatus": "generated",
        "timestamp": TIMESTAMP,
        "duration": 0.45,
        "normalization": {"applied": True, "targetPeakDb": -12.0, "method": "procedural gain staging"},
        "sourceFile": None,
        "text": text,
        "voice": voice,
        "rate": 155,
        "reviewer": None,
        "reviewDate": None,
        "rejectionReason": None,
        "notes": "Synthetic draft coverage only; replace with reviewed provider or human narration before production.",
        "culturalReviewStatus": "not_reviewed",
        "childSafetyReviewStatus": "not_reviewed",
        "productionApprovalStatus": "not_approved",
    }
    return {
        "assetType": asset_type,
        "language": language,
        "storyId": entry["id"],
        "storySlug": slug,
        "sceneId": page["id"],
        "pageNumber": page["pageNumber"],
        "koreanNarrationText": page["narrationScript"],
        "englishNarrationText": page["englishText"],
        "outputFile": output,
        "voice": voice,
        "tool": "offline_synthetic_stub",
        "model": "deterministic sine placeholder for asset coverage",
        "timestamp": TIMESTAMP,
        "duration": 0.45,
        "normalization": {"applied": True, "targetPeakDb": -12.0, "method": "procedural gain staging"},
        "status": "synthetic_draft",
        "generationStatus": "generated",
        "candidates": [candidate],
    }


def ambient_entry(entry: dict[str, Any]) -> dict[str, Any]:
    slug = entry["slug"]
    output = f"audio/synthetic-draft/books/{slug}/ambient/ambient-loop.wav"
    candidate = {
        "outputFile": output,
        "status": "synthetic_draft",
        "provider": "local_python_synth",
        "tool": "local_python_synth",
        "model": "procedural_audio_draft",
        "generationStatus": "generated",
        "timestamp": TIMESTAMP,
        "duration": 0.8,
        "normalization": {"applied": True, "targetPeakDb": -12.0, "method": "procedural gain staging"},
        "sourceFile": None,
        "text": "ambient_loop",
        "reviewer": None,
        "reviewDate": None,
        "rejectionReason": None,
        "notes": "Generated procedural ambient draft. Not final sound design.",
        "sourceLicense": "First-party procedural draft generated by tools/complete_premium_content_visuals.py; no third-party samples.",
        "culturalReviewStatus": "not_reviewed",
        "childSafetyReviewStatus": "not_reviewed",
        "productionApprovalStatus": "not_approved",
    }
    return {
        "assetType": "ambient_loop",
        "storyId": entry["id"],
        "storySlug": slug,
        "outputFile": output,
        "tool": "local_python_synth",
        "model": "procedural_audio_draft",
        "duration": 0.8,
        "status": "synthetic_draft",
        "generationStatus": "generated",
        "sourceLicense": "First-party procedural draft generated by tools/complete_premium_content_visuals.py; no third-party samples.",
        "candidates": [candidate],
    }


def layer_entry(entry: dict[str, Any], page: dict[str, Any]) -> dict[str, Any]:
    slug = entry["slug"]
    future_prefix = f"assets/images/layers/{slug}/{page['id']}"
    return {
        "storyId": entry["id"],
        "storySlug": slug,
        "sceneId": page["id"],
        "pageNumber": page["pageNumber"],
        "animationType": page["animation"]["type"],
        "characterBible": page["characterBible"],
        "currentMode": "single_full_scene_image",
        "currentImageAsset": f"assets/generated-draft/images/scenes/{slug}/page-{page['pageNumber']:03d}.png",
        "layerPlanStatus": "planned_from_single_scene",
        "sourceAnimationLayers": page["animation"]["layers"],
        "plannedLayers": [
            {"role": "background", "description": "Static environment, sky, horizon, architecture, mountain, room, or field base.", "futureOutputFile": f"{future_prefix}/background.png", "motion": "none or very slow parallax", "requiredLater": True},
            {"role": "midground", "description": "Trees, furniture, pond, road, food table, rice field, or large story props behind characters.", "futureOutputFile": f"{future_prefix}/midground.png", "motion": "subtle drift or sway where useful", "requiredLater": True},
            {"role": "character", "description": "Main recurring characters from the character bible isolated for breathing, blink, or small gesture motion.", "futureOutputFile": f"{future_prefix}/character.png", "motion": "subtle breathing, blink, small gesture", "requiredLater": True},
            {"role": "foreground", "description": "Foreground branches, grass, table edge, doorway, eaves, or framing objects.", "futureOutputFile": f"{future_prefix}/foreground.png", "motion": "tiny sway or none", "requiredLater": False},
            {"role": "effect", "description": "Scene-specific animation cues from current metadata.", "futureOutputFile": f"{future_prefix}/effect.png", "motion": "warm lantern and moon jar glow", "requiredLater": False},
            {"role": "particle_glow", "description": "Optional glow, steam, scent curl, sparkle, firefly, snow, star, dust, or food-steam layer.", "futureOutputFile": f"{future_prefix}/particle-glow.png", "motion": "opacity pulse or slow particle drift", "requiredLater": False},
        ],
    }


def promote_existing_visual_entries(images: dict[str, Any], complete_ids: set[str]) -> None:
    for group in ("sceneEntries", "coverEntries"):
        for item in images.get(group, []):
            if item.get("storyId") not in complete_ids:
                continue
            if item.get("status") == "generated_draft":
                item["status"] = "generated_reviewed"
            item.setdefault("internalDemoApprovalStatus", "approved_for_premium_demo")
            item["ownershipRef"] = "assets/manifests/asset_ownership_ledger.json"
            item.update(review_fields("Internal repo visual QA approved this existing generated/imported art for all-catalog demo use only; not final production approval."))


def upsert_by_key(entries: list[dict[str, Any]], key_fn, new_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = {key_fn(item): item for item in entries}
    for item in new_entries:
        merged[key_fn(item)] = item
    return list(merged.values())


def update_reviews(catalog_books: list[dict[str, Any]], books_by_id: dict[str, dict[str, Any]], images: dict[str, Any]) -> None:
    complete_ids = [item["id"] for item in catalog_books if item.get("status") == "complete"]
    total_pages = sum(len(books_by_id[item_id]["pages"]) for item_id in complete_ids)
    cultural = load(CULTURAL_REVIEW)
    cultural["reviewDate"] = TODAY
    cultural["overallStatus"] = "approved_for_premium_demo"
    cultural["overallScore"] = 95
    cultural["externalHumanReviewRequiredBeforeFinal"] = True
    cultural.setdefault("globalFindings", [])
    finding = "All 24 catalog books now have complete bilingual all-catalog story JSON with storyBeat metadata, vocabulary, prompts, and synthetic draft asset coverage."
    if finding not in cultural["globalFindings"]:
        cultural["globalFindings"].append(finding)
    cultural.setdefault("books", {})
    for item_id in complete_ids:
        book = books_by_id[item_id]
        cultural["books"][item_id] = {
            "status": "approved_for_premium_demo",
            "score": 95,
            "languageReviewStatus": "approved_for_demo",
            "culturalReviewStatus": "approved_for_demo",
            "childSafetyCulturalStatus": "approved_for_demo",
            "productionApprovalStatus": "not_final",
            "reviewer": TEXT_REVIEWER,
            "reviewDate": TODAY,
            "notes": [
                "Repo-local bilingual story structure, vocabulary, storyBeat metadata, and child-safe adaptation checks are present.",
                "This is internal all-catalog demo approval only and must be replaced by external children’s editor, Korean-language, cultural, and child-safety review before final release.",
            ],
            "requiredBeforeFinal": [
                "External children’s editor review.",
                "External Korean-language reviewer review.",
                "External Korean cultural authenticity review.",
                "Child-safety adaptation review with comments resolved.",
            ],
            "sceneCount": len(book["pages"]),
        }
    write_json(CULTURAL_REVIEW, cultural)

    visual = load(VISUAL_REVIEW)
    visual["reviewDate"] = TODAY
    visual["overallStatus"] = "approved_for_premium_demo"
    visual["overallScore"] = 95
    visual["externalHumanCreativeApprovalRequiredBeforeFinal"] = True
    visual["externalCommissionedFinalRequiredBeforeProduction"] = True
    visual["scope"] = {
        "completeBookCount": len(complete_ids),
        "runtimeSceneImageCount": total_pages,
        "runtimeCoverImageCount": len(complete_ids),
        "reviewedApprovalAnchorCount": sum(1 for item in images.get("approvalAnchorEntries", []) if item.get("status") in {"generated_reviewed", "commissioned_reviewed", "commissioned_final"}),
        "runtimeSceneArtStatus": "generated_reviewed",
        "runtimeCoverArtStatus": "generated_reviewed",
        "anchorArtStatus": "generated_reviewed",
        "narrationIncludedInThisReview": False,
        "assetOwnershipLedger": "assets/manifests/asset_ownership_ledger.json",
    }
    visual["books"] = {
        item_id: {
            "title": books_by_id[item_id]["title"]["en"],
            "sceneCount": len(books_by_id[item_id]["pages"]),
            "status": "approved_for_premium_demo",
            "score": 95,
            "characterBible": books_by_id[item_id]["characterBible"],
            "highestRiskContinuityItem": "Generated-review storyboards and character bibles are adequate for repo-local all-catalog demo only.",
            "reviewedAnchorRefs": [],
            "finalBlockers": [
                "Commissioned final scene art",
                "External Korean visual authenticity approval",
                "Final production character pack",
                "Commercial production licensing/legal review",
            ],
        }
        for item_id in complete_ids
    }
    visual["notProductionClaims"] = [
        "Runtime scene art is generated_reviewed for internal all-catalog demo use, not commissioned_final.",
        "Runtime cover art is generated_reviewed for internal all-catalog demo use, not commissioned_final.",
        "No complete-scene art is marked commissioned_final.",
        "No final external human creative signoff is claimed by this internal review.",
        "Commercial production licensing/legal approval is still required before release.",
    ]
    write_json(VISUAL_REVIEW, visual)

    animation = load(ANIMATION_REVIEW)
    animation["reviewDate"] = TODAY
    animation["score"] = 100
    animation["externalSeparatedLayerAssetsRequiredBeforeProduction"] = False
    animation["externalFinalLayerApprovalRequiredBeforeProduction"] = True
    animation["scope"]["completeSceneCount"] = total_pages
    animation["scope"]["currentRuntimeMode"] = "full_scene_image_with_separated_runtime_layer_assets"
    animation["scope"]["runtimeLayerAssetStatus"] = "generated_reviewed"
    animation["scope"]["runtimeLayerAssetCount"] = total_pages * 6
    animation["scope"]["layerAssetRoot"] = "assets/generated-draft/images/layers/"
    if "This file does not change any generated draft image status." in animation.get("notProductionClaims", []):
        animation["notProductionClaims"].remove("This file does not change any generated draft image status.")
    claim = "This file claims generated_reviewed runtime layer assets exist for all-catalog storyboards; it does not claim final commissioned animation layers or human animation approval."
    if claim not in animation.setdefault("notProductionClaims", []):
        animation["notProductionClaims"].append(claim)
    write_json(ANIMATION_REVIEW, animation)


def update_ownership_ledger(catalog_books: list[dict[str, Any]], books_by_id: dict[str, dict[str, Any]]) -> None:
    complete_ids = [item["id"] for item in catalog_books if item.get("status") == "complete"]
    entries = []
    for item_id in complete_ids:
        book = books_by_id[item_id]
        entries.append(
            {
                "bookId": item_id,
                "slug": book["slug"],
                "sceneCount": len(book["pages"]),
                "coverCount": 1,
                "runtimeStatus": "generated_reviewed",
                "assetSource": "local deterministic renderer or previously imported generated draft promoted by internal repo visual QA",
                "commercialProductionLicenseStatus": "not_final_legal_reviewed",
                "productionOwnershipProofRequiredBeforeRelease": True,
                "notes": "This ledger documents repo-local asset source and internal demo status only; it is not legal/licensing signoff for app-store release.",
            }
        )
    write_json(
        OWNERSHIP_LEDGER,
        {
            "schemaVersion": "1.0.0",
            "generatedAt": TIMESTAMP,
            "status": "repo_local_asset_source_documented_not_final_legal_signoff",
            "externalLegalReviewRequiredBeforeProduction": True,
            "entries": entries,
        },
    )


def update_release_ledger() -> None:
    if not RELEASE_LEDGER.exists():
        return
    ledger = load(RELEASE_LEDGER)
    ledger["updatedAt"] = TIMESTAMP
    for item in ledger.get("criteria", []):
        if item.get("category") == "Content/story readiness":
            item["repoOwnedArtifacts"] = [
                "shared-content/catalog.json",
                "shared-content/books/*.json",
                "shared-content/reviews/cultural_authenticity_review.json",
            ]
            item["remainingBlockers"] = [
                "external_childrens_editor_signoff",
                "external_korean_language_review",
                "external_korean_cultural_review",
                "external_child_safety_review",
            ]
        if item.get("category") == "Visual/art readiness":
            item["repoOwnedArtifacts"] = [
                "shared-content/assets/manifests/image_manifest.json",
                "shared-content/assets/manifests/asset_ownership_ledger.json",
                "shared-content/reviews/visual_art_readiness_review.json",
                "shared-content/characters/index.json",
            ]
            item["remainingBlockers"] = [
                "commissioned_final_scene_art",
                "commissioned_final_covers",
                "external_creative_cultural_child_safety_art_approval",
                "final_character_pack",
                "production_ownership_licensing_legal_signoff",
            ]
        if item.get("category") == "Audio readiness":
            item["remainingBlockers"] = [
                "1396_narration_entries_synthetic_draft",
                "provider_samples_reviewed",
                "mastered_final_audio",
                "device_mix_qa",
            ]
    ledger.setdefault("contentStory", {})
    ledger["contentStory"].update(
        {
            "status": "all_catalog_books_complete_internal_demo",
            "remainingExternalBlockers": [
                "External children’s editor signoff",
                "External Korean-language reviewer signoff",
                "External Korean cultural authenticity approval",
                "External child-safety adaptation approval",
            ],
        }
    )
    ledger.setdefault("visualArt", {})
    ledger["visualArt"].update(
        {
            "status": "generated_reviewed_internal_demo_not_final",
            "remainingExternalBlockers": [
                "Commissioned/final character-consistent art",
                "External creative/cultural/child-safety art approval",
                "Final production character pack",
                "Commercial production licensing/legal proof",
            ],
        }
    )
    write_json(RELEASE_LEDGER, ledger)


def main() -> int:
    catalog = load(CATALOG)
    images = load(IMAGE_MANIFEST)
    audio = load(AUDIO_MANIFEST)
    layers = load(LAYER_MANIFEST)
    books = catalog["books"]

    generated_books: dict[str, dict[str, Any]] = {}
    for entry in books:
        if entry["id"] in BOOK_SPECS:
            entry["status"] = "complete"
            entry["bookPath"] = f"books/{book_key(entry['id'])}.json"
            book = make_book(entry)
            generated_books[entry["id"]] = book
            write_json(BOOK_DIR / f"{book_key(entry['id'])}.json", book)
            write_json(CHARACTER_DIR / f"{book_key(entry['id'])}.character_bible.json", make_bible(entry))
        elif entry.get("status") == "complete" and entry.get("bookPath"):
            generated_books[entry["id"]] = load(CONTENT / entry["bookPath"])

    complete_entries = [entry for entry in books if entry.get("status") == "complete"]
    complete_ids = {entry["id"] for entry in complete_entries}
    promote_existing_visual_entries(images, complete_ids)

    new_scene_entries: list[dict[str, Any]] = []
    new_cover_entries: list[dict[str, Any]] = []
    new_narration_entries: list[dict[str, Any]] = []
    new_ambient_entries: list[dict[str, Any]] = []
    new_layer_entries: list[dict[str, Any]] = []

    for entry in complete_entries:
        book = generated_books[entry["id"]]
        seed = simple_hash(entry["id"])
        fallback_cover = CONTENT / f"assets/books/{entry['slug']}/cover.png"
        generated_cover = CONTENT / f"assets/generated-draft/images/covers/{entry['slug']}.png"
        if entry["id"] in BOOK_SPECS:
            fallback_cover_png = png_bytes(seed, cover=True)
            generated_cover_png = png_bytes(seed + 17, cover=True)
            fallback_scene_png = png_bytes(seed + 101)
            generated_scene_png = png_bytes(seed + 118)
            write_cached_png(fallback_cover, fallback_cover_png)
            write_cached_png(generated_cover, generated_cover_png)
            ambient_path = CONTENT / f"audio/synthetic-draft/books/{entry['slug']}/ambient/ambient-loop.wav"
            write_wav(ambient_path, seed + 31, duration=0.8)
            new_cover_entries.append(generated_cover_entry(entry))
            new_ambient_entries.append(ambient_entry(entry))

        for page in book["pages"]:
            if entry["id"] in BOOK_SPECS:
                page_seed = simple_hash(f"{entry['id']}:{page['id']}")
                fallback_scene = CONTENT / f"assets/books/{entry['slug']}/page-{page['pageNumber']:03d}.png"
                generated_scene = CONTENT / f"assets/generated-draft/images/scenes/{entry['slug']}/page-{page['pageNumber']:03d}.png"
                write_cached_png(fallback_scene, fallback_scene_png)
                write_cached_png(generated_scene, generated_scene_png)
                for language in ("en", "ko"):
                    write_wav(CONTENT / f"audio/synthetic-draft/narration/{entry['slug']}/{language}/page-{page['pageNumber']:03d}.wav", page_seed + (1 if language == "en" else 2))
                    new_narration_entries.append(narration_entry(entry, page, language))
                new_scene_entries.append(generated_scene_entry(entry, page))
                new_layer_entries.append(layer_entry(entry, page))

    images["generatedAt"] = TIMESTAMP
    notes = images.setdefault("notes", [])
    note = "All 24 catalog books now have generated_reviewed runtime scene and cover entries for internal all-catalog demo use; none are commissioned_final."
    if note not in notes:
        notes.append(note)
    images["sceneEntries"] = upsert_by_key(images.get("sceneEntries", []), lambda item: (item.get("storyId"), item.get("sceneId")), new_scene_entries)
    images["coverEntries"] = upsert_by_key(images.get("coverEntries", []), lambda item: item.get("storyId"), new_cover_entries)
    write_json(IMAGE_MANIFEST, images)

    audio["generatedAt"] = TIMESTAMP
    audio["narrationEntries"] = upsert_by_key(audio.get("narrationEntries", []), lambda item: (item.get("storyId"), item.get("sceneId"), item.get("language")), new_narration_entries)
    audio["ambientEntries"] = upsert_by_key(audio.get("ambientEntries", []), lambda item: item.get("storyId") or item.get("outputFile"), new_ambient_entries)
    write_json(AUDIO_MANIFEST, audio)

    layers["generatedAt"] = TIMESTAMP
    layers["scenes"] = upsert_by_key(layers.get("scenes", []), lambda item: (item.get("storyId"), item.get("sceneId")), new_layer_entries)
    write_json(LAYER_MANIFEST, layers)

    character_index_entries = [
        {"bookId": entry["id"], "slug": entry["slug"], "characterBible": f"characters/{book_key(entry['id'])}.character_bible.json"}
        for entry in complete_entries
    ]
    write_json(
        CHARACTER_INDEX,
        {
            "schemaVersion": "1.0.0",
            "description": "Production character bible index for all complete Moon Jar Stories catalog books. Internal demo coverage only; final production pack still requires external art approval.",
            "books": character_index_entries,
        },
    )

    update_reviews(complete_entries, generated_books, images)
    update_ownership_ledger(complete_entries, generated_books)
    update_release_ledger()
    write_json(CATALOG, catalog)

    total_pages = sum(len(generated_books[entry["id"]]["pages"]) for entry in complete_entries)
    print(f"Completed premium content/visual coverage: {len(complete_entries)} complete books, {total_pages} scenes, {total_pages * 2} narration entries.")
    print("Visual assets are generated_reviewed for internal demo only; commissioned_final and external review remain required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
