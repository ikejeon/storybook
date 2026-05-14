#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "shared-content"
BOOK_PATH = CONTENT / "books" / "fairy_woodcutter.json"
AUDIO_MANIFEST = CONTENT / "audio" / "manifests" / "audio_manifest.json"

BOOK_ID = "book.fairy_woodcutter"
SLUG = "fairy-and-woodcutter"
CHARACTER_BIBLE = "characters/fairy_woodcutter.character_bible.json"
AMBIENT_AUDIO = f"audio/synthetic-draft/books/{SLUG}/ambient/ambient-loop.wav"


PAGES: list[dict[str, str]] = [
    {
        "en": "Deep in the mountain, a woodcutter hid a frightened deer from hunters. Pine wind brushed the spring, and the deer bowed low. \"I will remember your kindness,\" it whispered.",
        "ko": "깊은 산 샘가에서 나무꾼은 사냥꾼에게 쫓기던 사슴을 숨겨 주었어요. 솔바람이 지나가자 사슴은 고개를 숙였지요. “은혜를 잊지 않겠습니다.”",
        "enLittle": "The woodcutter helped a frightened deer.",
        "koLittle": "나무꾼은 사슴을 숨겨 주었어요.",
        "purpose": "The woodcutter helps the deer and opens the folktale bargain.",
        "emotion": "kind, watchful, misty mountain suspense",
        "hook": "Then the grateful deer told him a secret that was not simple.",
        "interaction": "Tap the deer hiding beside the reeds.",
        "visual": "mountain spring at dusk, humble Korean woodcutter shielding a frightened deer behind reeds while distant hunters pass, pine forest, no violence",
    },
    {
        "en": "The deer pointed to a hidden pool where sky fairies came to bathe. \"If one wing robe is hidden, its owner cannot fly home,\" the deer said, and the words felt heavy.",
        "ko": "사슴은 선녀들이 내려와 목욕하는 숨은 못을 알려 주었어요. “날개옷 하나를 감추면 그 주인은 하늘로 돌아가지 못합니다.” 그 말은 이상하게 무거웠어요.",
        "enLittle": "The deer told him about the fairies' wing robes.",
        "koLittle": "사슴은 선녀들의 날개옷 이야기를 했어요.",
        "purpose": "Introduce the wing robe and make the moral danger visible.",
        "emotion": "tempted, uneasy, secretive",
        "hook": "The woodcutter listened, but the right choice already felt hard.",
        "interaction": "Trace the path from the deer to the hidden pool.",
        "visual": "deer beside moonlit mountain pool, woodcutter listening with worried face, folded white wing robes glimmering far away under trees",
    },
    {
        "en": "When the moon rose, white wing robes lay on a rock like folded clouds. The woodcutter reached out and hid one beneath pine branches, though his heart knew it was wrong.",
        "ko": "달이 오르자 흰 날개옷들이 바위 위에 구름처럼 놓였어요. 나무꾼은 손을 뻗어 하나를 솔가지 아래 감추었지만, 마음속으로는 잘못인 줄 알았어요.",
        "enLittle": "He hid one wing robe, though it was wrong.",
        "koLittle": "그는 잘못인 줄 알면서 날개옷을 감추었어요.",
        "purpose": "Show the central wrong choice plainly and child-safely.",
        "emotion": "ashamed, quiet, moonlit tension",
        "hook": "Soon one fairy searched the rocks with tears in her voice.",
        "interaction": "Tap the hidden pine branches.",
        "visual": "moonlit rock with white feather wing robes, woodcutter hiding one robe under pine branches, remorseful body language, Korean ink watercolor",
    },
    {
        "en": "The youngest fairy could not find her robe. The others rose toward the stars, but she stayed by the cold water, scared and alone.",
        "ko": "막내 선녀는 자기 날개옷을 찾지 못했어요. 다른 선녀들은 별빛 쪽으로 올라갔지만, 막내 선녀만 차가운 물가에 두려운 얼굴로 남았지요.",
        "enLittle": "One fairy could not fly home.",
        "koLittle": "한 선녀가 하늘로 돌아가지 못했어요.",
        "purpose": "Center the fairy's loss and agency rather than making the trick romantic.",
        "emotion": "lonely, worried, gentle sorrow",
        "hook": "The woodcutter stepped out, carrying a secret he should have returned.",
        "interaction": "Hold on the empty rock where the robe should be.",
        "visual": "young sky fairy alone at cold mountain pool, other fairies distant in the sky, empty robe rock, woodcutter half-hidden and guilty",
    },
    {
        "en": "The woodcutter brought the fairy to his cottage and gave her warm rice and a dry blanket. She thanked him, but every night she looked up through the hanji door.",
        "ko": "나무꾼은 선녀를 오두막으로 데려가 따뜻한 밥과 마른 이불을 내주었어요. 선녀는 고맙다고 했지만, 밤마다 한지문 너머 하늘을 바라보았어요.",
        "enLittle": "She was safe, but she missed the sky.",
        "koLittle": "선녀는 안전했지만 하늘이 그리웠어요.",
        "purpose": "Show care without erasing the hidden wrongdoing.",
        "emotion": "safe but homesick, warm lantern sadness",
        "hook": "Above the rafters, the hidden robe waited.",
        "interaction": "Open the hanji door glow.",
        "visual": "small Korean mountain cottage, warm lantern, sky fairy wrapped in blanket looking through hanji paper door toward stars, woodcutter worried",
    },
    {
        "en": "The deer returned in a dream and warned him, \"Do not show the wing robe until you have three children.\" The warning sounded like a promise and a trap.",
        "ko": "그날 밤 사슴이 꿈에 나타나 말했어요. “아이 셋을 낳기 전에는 날개옷을 보이면 안 됩니다.” 그 말은 약속 같기도 하고 덫 같기도 했어요.",
        "enLittle": "The deer warned him to wait for three children.",
        "koLittle": "사슴은 아이 셋이 될 때까지 기다리라 했어요.",
        "purpose": "Introduce the three-child warning from the traditional plot.",
        "emotion": "uneasy, secret-heavy, warning",
        "hook": "Not yet, not yet, the secret said from the rafters.",
        "interaction": "Count the three tiny moon dots in the dream.",
        "visual": "dream scene, deer under moonlight warning the sleeping woodcutter, three pale moon dots, hidden feather robe in cottage rafters",
        "refrain": "Not yet, not yet, wait for the third child.",
    },
    {
        "en": "Seasons passed. The fairy learned the village paths, and the woodcutter learned her sky songs. Still, he never told her where the wing robe slept.",
        "ko": "계절이 지나 선녀는 마을길을 익혔고, 나무꾼은 선녀의 하늘 노래를 배웠어요. 그래도 그는 날개옷이 어디 숨었는지 말하지 않았지요.",
        "enLittle": "They shared days, but he kept the secret.",
        "koLittle": "둘은 함께 지냈지만 그는 비밀을 숨겼어요.",
        "purpose": "Build domestic time while keeping the secret morally present.",
        "emotion": "tender, uneasy, hidden shame",
        "hook": "A cradle song soon filled the little room.",
        "interaction": "Tap the shadow under the roof beam.",
        "visual": "Korean cottage through seasons, fairy singing softly, woodcutter working, hidden robe shadow above rafters",
    },
    {
        "en": "Their first child was born on a rainy morning. The fairy smiled through tired tears and sang a star lullaby, while the woodcutter remembered the deer's warning.",
        "ko": "비 오는 아침 첫아이가 태어났어요. 선녀는 지친 눈물 사이로 웃으며 별의 자장가를 불렀고, 나무꾼은 사슴의 경고를 떠올렸어요.",
        "enLittle": "Their first child was born.",
        "koLittle": "첫아이가 태어났어요.",
        "purpose": "Mark the first child and deepen the warning count.",
        "emotion": "joy mixed with worry",
        "hook": "One child was not three.",
        "interaction": "Count one cradle ribbon.",
        "visual": "rainy Korean cottage interior, sky fairy holding first baby, woodcutter joyful but anxious, soft lantern, no medical detail",
        "refrain": "Not yet, not yet, wait for the third child.",
    },
    {
        "en": "The child grew, chasing moon shadows across the floor. Sometimes the fairy whispered, \"I dream of my sisters,\" and the room became very still.",
        "ko": "아이는 자라 달그림자를 따라 방 안을 뛰었어요. 가끔 선녀가 “언니들이 꿈에 보여요” 하고 속삭이면, 방 안은 아주 조용해졌지요.",
        "enLittle": "The fairy still dreamed of her sisters.",
        "koLittle": "선녀는 아직 언니들이 그리웠어요.",
        "purpose": "Keep the fairy's homesickness alive after family warmth appears.",
        "emotion": "soft, homesick, still",
        "hook": "The woodcutter looked away from the rafters.",
        "interaction": "Trace the moon shadow on the floor.",
        "visual": "child chasing moonlight inside hanji-door cottage, sky fairy gazing upward with homesick expression, woodcutter avoiding rafters",
    },
    {
        "en": "A second child arrived in spring, when pear blossoms opened white as feathers. The house was full of small socks, warm rice, and one hidden truth.",
        "ko": "배꽃이 깃털처럼 희게 피는 봄에 둘째 아이가 태어났어요. 집 안에는 작은 버선과 따뜻한 밥, 그리고 아직 숨은 진실이 가득했어요.",
        "enLittle": "A second child came in spring.",
        "koLittle": "봄에 둘째 아이가 태어났어요.",
        "purpose": "Mark the second child and bring the story close to the early reveal.",
        "emotion": "warm, crowded, worried",
        "hook": "Two children were still not three.",
        "interaction": "Count two tiny socks.",
        "visual": "spring pear blossoms outside Korean cottage, fairy with two small children, woodcutter holding rice bowl and looking troubled",
        "refrain": "Not yet, not yet, wait for the third child.",
    },
    {
        "en": "One evening the fairy asked, \"Why do you look at the roof as if it can answer you?\" The woodcutter's spoon stopped above the rice.",
        "ko": "어느 저녁 선녀가 물었어요. “왜 지붕을 보면 대답을 들을 것처럼 바라보나요?” 나무꾼의 숟가락이 밥 위에서 멈추었어요.",
        "enLittle": "She noticed his secret.",
        "koLittle": "선녀는 그의 비밀을 눈치챘어요.",
        "purpose": "Let the fairy actively confront the hidden secret.",
        "emotion": "tense, honest question, quiet table",
        "hook": "The truth was closer than his next breath.",
        "interaction": "Tap the stopped spoon.",
        "visual": "quiet dinner table in Korean cottage, fairy asking serious question, woodcutter frozen with spoon, two children nearby, rafters above",
    },
    {
        "en": "He could have said, \"I hid your robe, and I am sorry.\" Instead he carried the secret through another night, and the lantern seemed dimmer.",
        "ko": "그는 “내가 당신의 날개옷을 숨겼소. 미안하오”라고 말할 수도 있었어요. 하지만 또 하룻밤 비밀을 품었고, 등불은 더 흐려 보였어요.",
        "enLittle": "He should have told the truth.",
        "koLittle": "그는 사실을 말해야 했어요.",
        "purpose": "Name the better choice before he fails it.",
        "emotion": "ashamed, regretful, dim",
        "hook": "By morning, fear pushed him toward the rafters.",
        "interaction": "Hold on the dim lantern.",
        "visual": "woodcutter awake at night under dim lantern, feather robe hidden in rafters, fairy and children sleeping in distance",
    },
    {
        "en": "Before the third child was born, the woodcutter pulled down the white wing robe. \"I kept this from you,\" he said, and his voice shook.",
        "ko": "셋째 아이가 태어나기 전에, 나무꾼은 흰 날개옷을 꺼내 내려놓았어요. “내가 이것을 숨겼소.” 그의 목소리가 떨렸어요.",
        "enLittle": "He revealed the robe too soon.",
        "koLittle": "그는 너무 일찍 날개옷을 보였어요.",
        "purpose": "Show the too-early reveal that breaks the warning.",
        "emotion": "fearful, exposed, consequential",
        "hook": "The fairy touched the feathers and remembered the sky.",
        "interaction": "Drag from the rafters down to the robe.",
        "visual": "woodcutter lowering white feather wing robe from rafters, fairy serious and stunned, two children in cottage doorway",
        "refrain": "Not yet, not yet, wait for the third child.",
    },
    {
        "en": "The fairy held the robe to her heart. \"You should have trusted me with the truth,\" she said. Her sadness was quiet, but it filled the whole room.",
        "ko": "선녀는 날개옷을 가슴에 안았어요. “진실을 나에게 맡겨 주었어야 해요.” 선녀의 슬픔은 조용했지만 방 안을 가득 채웠어요.",
        "enLittle": "The fairy was sad about the hidden truth.",
        "koLittle": "선녀는 숨긴 진실이 슬펐어요.",
        "purpose": "Center trust and consequence in the fairy's own voice.",
        "emotion": "sad, dignified, betrayed",
        "hook": "Then the feathers opened like moonlit wings.",
        "interaction": "Open the folded robe.",
        "visual": "sky fairy holding feather robe close, sorrowful dignified face, woodcutter bowed in apology, children watching quietly",
    },
    {
        "en": "The robe became wings again. The fairy lifted one child in each arm. \"I must go home,\" she said, and the woodcutter did not smile.",
        "ko": "날개옷은 다시 하얀 날개가 되었어요. 선녀는 한 아이씩 두 팔에 안았지요. “나는 하늘 집으로 돌아가야 해요.” 나무꾼은 웃지 못했어요.",
        "enLittle": "She flew home with one child in each arm.",
        "koLittle": "선녀는 두 아이를 안고 하늘로 갔어요.",
        "purpose": "Correct the departure: it is consequence and loss, not a happy flight.",
        "emotion": "sorrowful, solemn, moonlit farewell",
        "hook": "The yard grew empty beneath the falling feathers.",
        "interaction": "Count the two children in her arms.",
        "visual": "sky fairy rising with one child in each arm, white feather wings, woodcutter reaching up in grief, Korean cottage yard at night, bittersweet not happy",
    },
    {
        "en": "The cottage was suddenly too quiet. Small sandals waited by the door, and the woodcutter finally understood that love without honesty can become loneliness.",
        "ko": "오두막은 갑자기 너무 조용해졌어요. 문가에는 작은 고무신만 남았고, 나무꾼은 정직하지 못한 사랑이 외로움이 될 수 있음을 깨달았어요.",
        "enLittle": "The house felt empty after they left.",
        "koLittle": "그들이 떠나자 집은 텅 빈 듯했어요.",
        "purpose": "Let the consequence land emotionally and accessibly.",
        "emotion": "lonely, sorry, still",
        "hook": "At dawn he went back to the spring to ask for help.",
        "interaction": "Tap the empty sandals by the door.",
        "visual": "empty Korean cottage doorway, two small sandals, woodcutter sitting alone in moonlight, quiet grief",
    },
    {
        "en": "At the spring, the deer appeared again. \"A sky bucket comes down for water,\" it said. \"If you climb in, hold tight and do not look down.\"",
        "ko": "샘가에 다시 사슴이 나타났어요. “하늘에서 물 긷는 두레박이 내려옵니다. 그 안에 타거든 꼭 붙잡고 아래를 보지 마세요.”",
        "enLittle": "The deer told him about a sky bucket.",
        "koLittle": "사슴은 하늘 두레박 이야기를 했어요.",
        "purpose": "Move into the ascent motif with caution instead of triumph.",
        "emotion": "hopeful, scared, dawn mist",
        "hook": "That night, a rope slid down from the stars.",
        "interaction": "Trace the rope from sky to spring.",
        "visual": "dawn mountain spring, deer advising woodcutter, pale rope and bucket hinted in clouds above, cautious hope",
    },
    {
        "en": "The sky bucket dipped into the spring with a silver splash. The woodcutter climbed inside, clutching the wet rope as mountains shrank below.",
        "ko": "하늘 두레박이 은빛 물소리를 내며 샘에 내려왔어요. 나무꾼은 그 안에 올라타 젖은 줄을 꼭 잡았고, 산들은 아래에서 작아졌어요.",
        "enLittle": "He climbed into the bucket to reach the sky.",
        "koLittle": "그는 두레박을 타고 하늘로 올라갔어요.",
        "purpose": "Show ascent as risky longing, not a carefree victory.",
        "emotion": "afraid, hopeful, dizzy",
        "hook": "Clouds opened around a faraway house of light.",
        "interaction": "Hold the bucket rope.",
        "visual": "woodcutter ascending in wooden water bucket on rope toward clouds, small mountains below, fearful hopeful expression, no smiling celebration",
    },
    {
        "en": "In the sky village, the fairy stood with the children beside a moon-bright gate. The woodcutter bowed low. \"I am sorry,\" he said.",
        "ko": "하늘 마을의 달빛 문 곁에 선녀와 아이들이 서 있었어요. 나무꾼은 깊이 고개를 숙였어요. “미안합니다.”",
        "enLittle": "He found his family and apologized.",
        "koLittle": "그는 가족을 찾아 사과했어요.",
        "purpose": "Make apology explicit before any reunion warmth.",
        "emotion": "sorry, tender, cautious hope",
        "hook": "The fairy listened, but the old mistake did not disappear.",
        "interaction": "Tap the bowed head.",
        "visual": "sky village gate with moonlight, fairy and two children standing calmly, woodcutter bowing deeply in apology, Korean celestial architecture",
    },
    {
        "en": "The fairy let him stay, and the children held his hands. Some evenings were gentle, but he could still feel the weight of the robe he had hidden.",
        "ko": "선녀는 그가 머물도록 허락했고 아이들은 그의 손을 잡았어요. 어떤 저녁은 다정했지만, 그는 자신이 숨겼던 날개옷의 무게를 잊지 못했어요.",
        "enLittle": "He stayed, but the mistake still mattered.",
        "koLittle": "그는 머물렀지만 잘못은 남아 있었어요.",
        "purpose": "Avoid a too-easy happy reset after the apology.",
        "emotion": "gentle, reflective, uneasy",
        "hook": "Then another longing began to tug at him.",
        "interaction": "Tap the three joined hands.",
        "visual": "quiet sky home, fairy and children with woodcutter, warm but reserved family scene, faint feather robe motif in background",
    },
    {
        "en": "Soon the woodcutter missed his old mother on earth. \"I want to see her once,\" he said. The fairy's face grew worried.",
        "ko": "얼마 지나지 않아 나무꾼은 땅에 계신 늙은 어머니가 그리워졌어요. “한 번만 뵙고 싶소.” 그 말에 선녀의 얼굴이 걱정스러워졌어요.",
        "enLittle": "He missed his mother on earth.",
        "koLittle": "그는 땅의 어머니가 그리웠어요.",
        "purpose": "Introduce the return-to-earth warning.",
        "emotion": "homesick, worried, tender",
        "hook": "The fairy gave him one more warning.",
        "interaction": "Choose the path between sky and earth.",
        "visual": "woodcutter gazing down from sky village toward earth, fairy worried beside him, children holding sleeves",
    },
    {
        "en": "\"Ride the sky horse,\" the fairy told him, \"but never let your feet touch the ground.\" Her voice was soft because warnings had already been broken once.",
        "ko": "선녀가 말했어요. “하늘말을 타고 다녀오세요. 하지만 절대로 발이 땅에 닿으면 안 됩니다.” 이미 한 번 경고가 깨졌기에 목소리는 부드럽고도 무거웠어요.",
        "enLittle": "She warned him not to touch the ground.",
        "koLittle": "선녀는 땅에 닿지 말라고 했어요.",
        "purpose": "Set up the final warning and echo the earlier mistake.",
        "emotion": "solemn, careful, loving concern",
        "hook": "The horse lowered through the clouds like a pale wind.",
        "interaction": "Tap the horse's floating hooves.",
        "visual": "white sky horse beside fairy and woodcutter, fairy giving solemn warning, clouds and Korean celestial palace, no comedy",
        "refrain": "Warnings are quiet, but they are heavy.",
    },
    {
        "en": "The sky horse carried him to his mother's yard. She wept with joy and set out steaming porridge, saying, \"Eat before it grows cold, my son.\"",
        "ko": "하늘말은 나무꾼을 어머니의 마당까지 데려다주었어요. 어머니는 기뻐 눈물을 흘리며 뜨거운 죽을 내놓았지요. “식기 전에 먹어라, 내 아들아.”",
        "enLittle": "His mother welcomed him with hot porridge.",
        "koLittle": "어머니는 뜨거운 죽을 내주었어요.",
        "purpose": "Bring warmth and danger together through the porridge scene.",
        "emotion": "joyful, fragile, steaming warmth",
        "hook": "One hot drop changed everything.",
        "interaction": "Tap the steam above the bowl.",
        "visual": "earthly Korean yard, elderly mother offering steaming porridge to woodcutter seated on white sky horse, joyful but fragile moment",
    },
    {
        "en": "A drop of hot porridge splashed the horse. It reared in pain, and the woodcutter slipped. For one breath, his foot touched earth.",
        "ko": "뜨거운 죽 한 방울이 하늘말에게 튀었어요. 말은 놀라 앞발을 들었고, 나무꾼은 미끄러졌어요. 숨 한 번 사이에 그의 발이 땅에 닿았지요.",
        "enLittle": "A hot drop made the horse leap.",
        "koLittle": "뜨거운 죽 한 방울에 말이 놀랐어요.",
        "purpose": "Show the warning breaking through accident and consequence.",
        "emotion": "startled, afraid, sudden",
        "hook": "The sky horse vanished upward without him.",
        "interaction": "Trace the falling drop.",
        "visual": "white sky horse startled by steaming porridge drop, woodcutter slipping with one foot touching ground, mother alarmed, child-safe no injury",
    },
    {
        "en": "The horse flew back into the clouds. The woodcutter ran after the fading hoofbeats, but the sky road had closed.",
        "ko": "하늘말은 구름 속으로 다시 날아가 버렸어요. 나무꾼은 멀어지는 발굽 소리를 따라 달렸지만, 하늘길은 이미 닫혀 있었어요.",
        "enLittle": "The sky road closed.",
        "koLittle": "하늘길이 닫혀 버렸어요.",
        "purpose": "Land the final separation without melodrama.",
        "emotion": "lonely, desperate, fading",
        "hook": "Only the mountain spring remembered the way.",
        "interaction": "Swipe upward after the fading horse.",
        "visual": "woodcutter reaching toward clouds as white horse disappears, elderly mother near cottage gate, closed sky path, twilight sorrow",
    },
    {
        "en": "He returned to the mountain spring again and again. The water reflected clouds, but no bucket came down, and no wing robe waited on the rock.",
        "ko": "그는 몇 번이고 산속 샘으로 돌아갔어요. 물에는 구름이 비쳤지만 두레박은 내려오지 않았고, 바위 위에는 날개옷도 없었어요.",
        "enLittle": "No bucket came back to the spring.",
        "koLittle": "두레박은 다시 내려오지 않았어요.",
        "purpose": "Show longing and closed passage.",
        "emotion": "lonely, waiting, quiet",
        "hook": "At dawn, his voice began to change.",
        "interaction": "Tap the empty reflection in the spring.",
        "visual": "woodcutter alone beside mountain spring at dawn, empty rock, cloud reflection in water, no bucket, quiet longing",
    },
    {
        "en": "Some tellers say he became the rooster who cries toward the morning sky. \"Kkokkio,\" he called, not from joy, but from longing.",
        "ko": "어떤 이야기꾼들은 그가 아침 하늘을 향해 우는 수탉이 되었다고 해요. “꼬끼오.” 그 울음은 기쁨이 아니라 그리움에서 나온 소리였어요.",
        "enLittle": "Some say he became a rooster calling to the sky.",
        "koLittle": "그가 수탉이 되었다고도 해요.",
        "purpose": "Include the traditional rooster ending in a gentle framing.",
        "emotion": "mythic, wistful, dawn",
        "hook": "The call rose every morning, thin and bright.",
        "interaction": "Tap the dawn sky above the rooster.",
        "visual": "wistful rooster on Korean cottage roof at dawn facing the sky, faint memory of woodcutter in silhouette, no comedy",
    },
    {
        "en": "Far above, the fairy heard the rooster's dawn call and held the children close. She did not laugh at him. She remembered the spring, the robe, and the truth.",
        "ko": "높은 하늘에서 선녀는 수탉의 새벽 울음소리를 듣고 아이들을 꼭 안았어요. 선녀는 그를 비웃지 않았어요. 샘과 날개옷, 그리고 진실을 기억했지요.",
        "enLittle": "The fairy remembered everything too.",
        "koLittle": "선녀도 모든 일을 기억했어요.",
        "purpose": "Give the fairy emotional dignity while connecting the rooster ending.",
        "emotion": "sad, dignified, compassionate",
        "hook": "The children asked why the morning sounded so lonely.",
        "interaction": "Hold on the two children beside her.",
        "visual": "sky fairy in celestial home holding two children close, listening to rooster dawn call from below, solemn compassionate expression",
    },
    {
        "en": "The children learned that love is not keeping someone by hiding what belongs to them. Love needs truth, even when truth is hard to say.",
        "ko": "아이들은 사랑이 누군가의 것을 숨겨 붙잡는 일이 아니라는 것을 배웠어요. 사랑에는 말하기 어려운 진실도 필요하다는 것을요.",
        "enLittle": "Love needs truth.",
        "koLittle": "사랑에는 진실이 필요해요.",
        "purpose": "Make the ethical lesson clear for children.",
        "emotion": "clear, reflective, gentle",
        "hook": "And every sunrise carried the lesson again.",
        "interaction": "Choose the open hand instead of the hidden robe.",
        "visual": "symbolic gentle scene, open hands with feather robe returned, children watching sunrise, Korean ink wash, no heavy sadness",
    },
    {
        "en": "So when morning roosters call, some people hear more than noise. They hear a story about a hidden robe, a broken warning, and a heart learning too late.",
        "ko": "그래서 아침 수탉이 울 때, 어떤 사람들은 그 소리에서 숨겨진 날개옷과 깨진 경고, 너무 늦게 배운 마음의 이야기를 들어요.",
        "enLittle": "The rooster call remembers the story.",
        "koLittle": "수탉 울음은 이야기를 기억해요.",
        "purpose": "Tie the folktale ending to the everyday rooster call.",
        "emotion": "wistful, memorable, dawn",
        "hook": "The sky brightened, but the lesson stayed.",
        "interaction": "Trace the sound from roof to sky.",
        "visual": "morning village rooftops, rooster call drifting toward brightening sky, subtle feather motif, Korean mountain village",
        "refrain": "Warnings are quiet, but they are heavy.",
    },
    {
        "en": "The mountain spring stayed clear. Children who visited it were told, \"Borrowed wings must be returned, and promises must be kept while there is time.\"",
        "ko": "산속 샘은 오래도록 맑았어요. 그곳을 찾는 아이들은 이런 말을 들었지요. “빌린 날개는 돌려주고, 약속은 늦기 전에 지켜야 한단다.”",
        "enLittle": "Borrowed wings should be returned.",
        "koLittle": "빌린 날개는 돌려주어야 해요.",
        "purpose": "Close with a child-safe maxim grounded in the story objects.",
        "emotion": "wise, calm, reflective",
        "hook": "The last ripple carried the tale home.",
        "interaction": "Rub the spring water to make one ripple.",
        "visual": "clear mountain spring in daylight, children listening to elder beside rocks and reeds, feather reflection in water, calm Korean landscape",
    },
    {
        "en": "And if the dawn sounds a little sad, listen carefully. The old tale is not cheering when he goes up or when she flies away; it is teaching us to be honest sooner.",
        "ko": "새벽 소리가 조금 슬프게 들린다면 귀 기울여 보세요. 이 옛이야기는 올라가거나 날아가는 장면을 마냥 기뻐하지 않아요. 더 일찍 정직하라고 알려 주는 이야기예요.",
        "enLittle": "This is a story about being honest sooner.",
        "koLittle": "이 이야기는 더 일찍 정직하라고 말해요.",
        "purpose": "Explicitly correct the tone: ascent and departure are bittersweet, not happy spectacle.",
        "emotion": "honest, tender, bittersweet",
        "hook": "The morning opened, and the story rested.",
        "interaction": "Hold the final dawn until the sky brightens.",
        "visual": "bittersweet final dawn over Korean mountains and cottage roof, rooster silhouette facing sky, faint fairy and children shapes in clouds, solemn not cheerful",
    },
]

VOCABULARY = {
    "날개옷": ("wing robe", "A magical robe that lets the sky fairy fly home.", "선녀가 하늘로 돌아가게 해 주는 신비한 옷이에요."),
    "선녀": ("sky fairy", "A heavenly woman from Korean folktales.", "한국 옛이야기에 나오는 하늘 세계의 여인이에요."),
    "나무꾼": ("woodcutter", "A person who gathers wood in the mountains.", "산에서 나무를 하는 사람이에요."),
    "사슴": ("deer", "The grateful animal who gives the woodcutter secret advice.", "나무꾼에게 비밀 조언을 해 주는 고마운 동물이에요."),
    "두레박": ("water bucket", "A bucket lowered by rope to draw water.", "줄에 매달아 물을 긷는 통이에요."),
    "하늘말": ("sky horse", "A magical horse that travels between sky and earth.", "하늘과 땅 사이를 오가는 신비한 말이에요."),
    "한지문": ("hanji door", "A Korean paper door that lets soft light through.", "부드러운 빛이 비치는 한국 종이문이에요."),
    "수탉": ("rooster", "A bird that calls at dawn in the folktale ending.", "옛이야기 끝에서 새벽에 우는 새예요."),
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def vocab_for(page_number: int) -> list[dict[str, str]]:
    keys_by_arc = [
        ["나무꾼", "사슴"],
        ["날개옷", "선녀"],
        ["날개옷", "한지문"],
        ["선녀", "날개옷"],
        ["한지문", "선녀"],
        ["사슴", "날개옷"],
        ["날개옷", "선녀"],
        ["선녀", "나무꾼"],
        ["한지문", "선녀"],
        ["날개옷", "선녀"],
        ["한지문", "나무꾼"],
        ["날개옷", "나무꾼"],
        ["날개옷", "선녀"],
        ["선녀", "날개옷"],
        ["날개옷", "선녀"],
        ["나무꾼", "선녀"],
        ["사슴", "두레박"],
        ["두레박", "나무꾼"],
        ["선녀", "나무꾼"],
        ["날개옷", "선녀"],
        ["하늘말", "나무꾼"],
        ["하늘말", "선녀"],
        ["하늘말", "나무꾼"],
        ["하늘말", "선녀"],
        ["두레박", "날개옷"],
        ["수탉", "나무꾼"],
        ["선녀", "수탉"],
        ["날개옷", "선녀"],
        ["수탉", "날개옷"],
        ["날개옷", "나무꾼"],
        ["수탉", "선녀"],
        ["수탉", "날개옷"],
    ][page_number - 1]
    return [
        {"ko": key, "en": VOCABULARY[key][0], "definitionEn": VOCABULARY[key][1], "definitionKo": VOCABULARY[key][2]}
        for key in keys_by_arc
    ]


def image_prompt(page_number: int, scene: str) -> str:
    return (
        "Global style bible: shared-content/style/moonjar_style_bible.json. "
        f"Book character bible: shared-content/characters/fairy_woodcutter.character_bible.json. "
        f"Page {page_number} for 선녀와 나무꾼 / The Fairy and the Woodcutter: {scene}. "
        "Premium Korean watercolor, gouache, soft ink, hanji texture, restrained emotional staging, "
        "fit-safe composition, safe margins, no cropping, no cropped faces or hands. "
        "Preserve the folktale's consequence and longing; do not make the departure or ascent look purely happy. "
        "No text, no letters, no watermark, labels, logos, modern objects, horror, or graphic harm."
    )


def animation_for(page_id: str) -> dict[str, Any]:
    base = f"assets/generated-draft/images/layers/{SLUG}/{page_id}"
    return {
        "type": "characterBreathing",
        "loopDuration": 3.2,
        "motionSafety": "subtle only, no flashing",
        "layers": [
            {"name": "background", "motion": "none or very slow parallax", "intensity": "low", "outputFile": f"{base}/background.png", "status": "generated_reviewed"},
            {"name": "midground", "motion": "subtle drift or sway where useful", "intensity": "low", "outputFile": f"{base}/midground.png", "status": "generated_reviewed"},
            {"name": "character", "motion": "subtle breathing, blink, small gesture", "intensity": "low", "outputFile": f"{base}/character.png", "status": "generated_reviewed"},
            {"name": "foreground", "motion": "tiny sway or none", "intensity": "low", "outputFile": f"{base}/foreground.png", "status": "generated_reviewed"},
            {"name": "effect", "motion": "soft moonlight, feather, or dawn glow", "intensity": "low", "outputFile": f"{base}/effect.png", "status": "generated_reviewed"},
            {"name": "particle_glow", "motion": "opacity pulse or slow particle drift", "intensity": "low", "outputFile": f"{base}/particle-glow.png", "status": "generated_reviewed"},
        ],
    }


def rebuild_pages() -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    for page_number, item in enumerate(PAGES, start=1):
        page_id = f"fairy_woodcutter_{page_number:03d}"
        page: dict[str, Any] = {
            "id": page_id,
            "pageNumber": page_number,
            "text": {
                "enLittle": item["enLittle"],
                "enStandard": item["en"],
                "koLittle": item["koLittle"],
                "koStandard": item["ko"],
            },
            "koreanText": item["ko"],
            "englishText": item["en"],
            "narrationScript": item["ko"],
            "vocabulary": vocab_for(page_number),
            "storyBeat": {
                "purpose": item["purpose"],
                "emotion": item["emotion"],
                "pageTurnHook": item["hook"],
                "readAloudCue": "Read with a measured, bittersweet folktale cadence; keep suspense gentle and never triumphant when trust breaks.",
                "childInteraction": item["interaction"],
            },
            "imagePrompt": image_prompt(page_number, item["visual"]),
            "imageAsset": f"assets/books/{SLUG}/page-{page_number:03d}.png",
            "imageAssetStatus": "placeholder",
            "audioPrompt": "English-first warm professional picture-book narration; Korean optional narration should sound natural, musical, culturally grounded, and bittersweet rather than cheerful in consequence scenes.",
            "narrationAudio": f"audio/synthetic-draft/narration/{SLUG}/ko/page-{page_number:03d}.wav",
            "narrationAudioStatus": "synthetic_draft",
            "narrationVoice": "Grandma (Korean (South Korea))",
            "audioGenerationTool": "offline_synthetic_stub",
            "ambientAudio": AMBIENT_AUDIO,
            "characterBible": CHARACTER_BIBLE,
            "animation": animation_for(page_id),
        }
        if "refrain" in item:
            page["refrain"] = item["refrain"]
        pages.append(page)
    return pages


def update_book() -> None:
    book = load(BOOK_PATH)
    book.update(
        {
            "summary": (
                "A child-safe but honest adaptation of The Fairy and the Woodcutter: a hidden wing robe, "
                "a warning to wait for three children, an early reveal, a sorrowful return to the sky, "
                "and a final lesson about trust, honesty, and longing."
            ),
            "sensitivityNotes": [
                "Authenticity repair: preserves the robe-hiding, three-child warning, early reveal, sky return, and rooster-ending motifs in child-safe language.",
                "Frames the woodcutter's hidden robe as a wrong choice with consequences; does not portray the fairy's departure or his ascent as purely happy.",
                "External children’s editor and Korean cultural review remain required before final release.",
            ],
            "themes": ["honesty", "trust", "consequence", "longing", "family"],
            "characters": ["woodcutter", "sky_fairy", "deer_friend", "two_children", "old_mother", "sky_horse", "rooster"],
            "pages": rebuild_pages(),
        }
    )
    write_json(BOOK_PATH, book)


def update_audio_manifest() -> int:
    manifest = load(AUDIO_MANIFEST)
    pages = {page["id"]: page for page in rebuild_pages()}
    updated = 0
    for entry in manifest.get("narrationEntries", []):
        if entry.get("storyId") != BOOK_ID:
            continue
        page = pages.get(entry.get("sceneId"))
        if not page:
            continue
        entry["koreanNarrationText"] = page["narrationScript"]
        entry["englishNarrationText"] = page["englishText"]
        entry["storySlug"] = SLUG
        entry["pageNumber"] = page["pageNumber"]
        for candidate in entry.get("candidates", []):
            if entry.get("language") == "ko":
                candidate["text"] = page["narrationScript"]
            elif entry.get("language") == "en":
                candidate["text"] = page["englishText"]
            candidate["notes"] = (
                "Synthetic draft coverage only; text updated by fairy woodcutter authenticity repair. "
                "Replace with reviewed provider or human narration before production."
            )
        updated += 1
    manifest["generatedAt"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    write_json(AUDIO_MANIFEST, manifest)
    return updated


def main() -> int:
    if len(PAGES) != 32:
        raise SystemExit(f"Expected 32 pages, got {len(PAGES)}")
    update_book()
    updated_audio_entries = update_audio_manifest()
    print(f"Updated {BOOK_PATH.relative_to(ROOT)} with {len(PAGES)} authentic story pages.")
    print(f"Updated {updated_audio_entries} fairy-and-woodcutter narration manifest entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
