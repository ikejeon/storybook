#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StoryExpectation:
    core_beats: str
    sensitive_beats: str
    required_terms: tuple[str, ...]


GENERIC_STORY_PATTERNS = (
    "we can choose ",
    "made the moment feel brave and gentle",
    "beside a moon jar",
)

GENERIC_PURPOSE_RE = r"\bbeat\s+\d+\b"


STORY_EXPECTATIONS: dict[str, StoryExpectation] = {
    "sun-and-moon": StoryExpectation(
        "Mother leaves with rice cakes; deceptive tiger threatens her and tests the siblings at the door; children escape to a tree; sky rope saves them; sun/moon transformation resolves the danger.",
        "Tiger must feel cunning, hungry, watchful, and meaningfully threatening without horror or gore; sibling fear and courage must stay visible.",
        ("rice cake", "tiger", "door", "shadow", "rope", "sun", "moon"),
    ),
    "gold-axe-silver-axe": StoryExpectation(
        "Poor woodcutter loses his old iron axe; mountain spirit tests him with gold and silver axes; honesty returns the old axe and brings a gift; greedy neighbor fails the same test.",
        "Honesty matters because the plain inherited axe matters emotionally; greedy consequence stays comic and non-cruel.",
        ("old iron axe", "gold", "silver", "mountain spirit", "honest"),
    ),
    "tiger-and-persimmon": StoryExpectation(
        "A boastful tiger scares a family until a dried persimmon name frightens him; thief and tiger confusion turns the danger into comedy.",
        "Tiger should be silly and comic here, unlike Sun/Moon; gotgam must be dried persimmons, not fresh fruit growing on a tree.",
        ("tiger", "gotgam", "dried persimmon", "eaves", "traveler"),
    ),
    "heungbu-and-nolbu": StoryExpectation(
        "Kind Heungbu helps an injured swallow; gourd seeds bring gifts; greedy Nolbu imitates harmfully and learns through restorative consequences.",
        "Sibling conflict should not glamorize cruelty; Nolbu's consequence should turn toward repair rather than vengeance.",
        ("Heungbu", "Nolbu", "swallow", "gourd", "seed"),
    ),
    "red-bean-porridge-grandma": StoryExpectation(
        "Grandma bargains with a boastful tiger, makes red bean porridge, and household helpers cooperate to chase him away.",
        "Tiger is threatening enough to motivate a clever plan, but the tone stays cozy, comic, and child-safe.",
        ("red bean porridge", "tiger", "helper", "kitchen", "threshold"),
    ),
    "simcheong": StoryExpectation(
        "Simcheong cares for her blind father; the sea offering is adapted as a brave journey; sea/lotus wonder protects her; she returns with healing and reunion.",
        "Avoid presenting sacrifice as cheerful or transactional; keep filial love, agency, fear, and hope together.",
        ("Simcheong", "father", "sea", "lotus", "offering", "return"),
    ),
    "rabbit-and-turtle": StoryExpectation(
        "Turtle brings Rabbit toward the Dragon King's court; Rabbit learns the liver demand and escapes through clever words.",
        "Body-harm detail must stay abstract and non-graphic; Rabbit is clever but not cruel, Turtle is pressured rather than evil.",
        ("Rabbit", "Turtle", "Dragon King", "liver", "palace", "shore"),
    ),
    "dokkaebi-club": StoryExpectation(
        "A kind wood gatherer meets playful dokkaebi and receives a magic club; a greedy neighbor imitates without respect and faces comic reversal.",
        "Dokkaebi should feel magical and mischievous, not demonic horror; greed consequence stays slapstick.",
        ("dokkaebi", "club", "magic", "neighbor", "pine"),
    ),
    "dangun-story": StoryExpectation(
        "Hwanung descends; bear and tiger seek transformation; bear patiently keeps the cave practice; Dangun's founding is framed as origin myth.",
        "Mythic transformation must be reverent and gentle; tiger leaving the cave is not villainy.",
        ("Hwanung", "bear", "tiger", "mugwort", "garlic", "Dangun"),
    ),
    "grateful-magpie": StoryExpectation(
        "Traveler saves a magpie from danger; later magpies repay the kindness by warning or saving him near a bell/temple.",
        "Snake/danger remains suspenseful but non-graphic; gratitude, not violence, is the emotional center.",
        ("traveler", "magpie", "snake", "bell", "gratitude"),
    ),
    "kongjwi-and-patjwi": StoryExpectation(
        "Kongjwi endures unfair chores; animal/magical helpers aid her; the lost lotus shoe reveals truth; Patjwi's cruelty is softened into accountability.",
        "Bullying should not become cozy; helpers and Kongjwi's dignity need to remain central.",
        ("Kongjwi", "Patjwi", "chore", "frog", "lotus shoe"),
    ),
    "geumgang-mountain-tiger": StoryExpectation(
        "A child meets a majestic Geumgang Mountain tiger; respect, courage, and mountain stewardship turn fear into trust.",
        "This tiger can be majestic and gentle, distinct from the Sun/Moon antagonist and Persimmon comic tiger.",
        ("Geumgang", "tiger", "mountain", "pine", "respect"),
    ),
    "lump-old-man": StoryExpectation(
        "An old man with a lump sings for dokkaebi; his gift is received with respect; greedy imitation fails.",
        "Physical difference must never be mocked; art and text should center music, dignity, and comic greed.",
        ("lump", "song", "dokkaebi", "neighbor", "respect"),
    ),
    "gyeonwu-and-jiknyeo": StoryExpectation(
        "Gyeonwu and Jiknyeo love each other, are separated across the star river, and meet once a year on the magpie bridge.",
        "Longing is tender and seasonal, not a simple happy romance; separation must remain emotionally true.",
        ("Gyeonwu", "Jiknyeo", "star", "magpie bridge", "river"),
    ),
    "bari-princess-part-1": StoryExpectation(
        "Princess Bari is abandoned/hidden, grows into her identity, and chooses a healing quest for the parents who failed her.",
        "Abandonment must be softened but not erased; Bari's agency and hurt should both be visible.",
        ("Bari", "princess", "abandoned", "quest", "medicine"),
    ),
    "bari-princess-part-2": StoryExpectation(
        "Bari crosses difficult otherworld paths, wins life water/medicine through compassion, and returns to heal.",
        "Underworld imagery must be wondrous and solemn, not horror; healing is earned through courage and compassion.",
        ("Bari", "river", "life water", "medicine", "return"),
    ),
    "snail-bride": StoryExpectation(
        "A farmer discovers the snail woman who has been helping; their relationship is adapted around consent, agency, and a threatened separation by local power.",
        "Do not make the bride an owned helper; her choice and safety must drive the retelling.",
        ("snail", "bride", "shell", "farmer", "choice"),
    ),
    "janghwa-and-hongryeon": StoryExpectation(
        "Two sisters face an unjust household mystery; their truth is heard; lotus imagery carries repair without horror.",
        "The source tale's horror must be heavily softened while preserving grief, injustice, and truth-seeking.",
        ("Janghwa", "Hongryeon", "sisters", "lotus", "truth"),
    ),
    "fairy-and-woodcutter": StoryExpectation(
        "Woodcutter helps deer, hides fairy's wing robe, reveals it before three children, fairy leaves with two children, sky-bucket ascent and rooster longing complete the consequence.",
        "Departure/ascent are bittersweet and consequential, never triumphant; the fairy's agency and the woodcutter's wrongdoing must remain clear.",
        ("wing robe", "deer", "three children", "two children", "sky bucket", "rooster"),
    ),
    "green-frog": StoryExpectation(
        "Contrary green frog ignores his mother, tries too late to listen, grieves by the stream, and worries during rain.",
        "Grief should be gentle and real; the mother should not vanish into a generic listening lesson.",
        ("green frog", "mother", "opposite", "stream", "rain"),
    ),
    "kind-brothers": StoryExpectation(
        "Two brothers secretly carry rice to each other's barns at night until they meet under the moon and laugh with love.",
        "The story is quiet generosity, not grand reward; rice sacks and moonlit paths are key props.",
        ("brother", "rice", "sack", "barn", "moon"),
    ),
    "byeoljubu": StoryExpectation(
        "Turtle envoy brings Rabbit toward the sea palace for the king's liver cure; Rabbit uses wit to escape and Turtle learns humility.",
        "Like Rabbit/Turtle, liver danger must remain abstract and child-safe; sea court pressure should not become graphic.",
        ("turtle", "rabbit", "sea king", "liver", "palace"),
    ),
    "farting-daughter-in-law": StoryExpectation(
        "A daughter-in-law hides a powerful fart, is shamed, then uses the wind to help with fruit/harvest and is welcomed.",
        "Body humor should remove shame and preserve belonging; the joke should be affectionate, not humiliating.",
        ("daughter-in-law", "fart", "wind", "pear", "family"),
    ),
    "serpent-bridegroom": StoryExpectation(
        "Youngest daughter chooses the serpent scholar, transformation reveals trust, a broken promise causes separation, and a quest restores the bond.",
        "Consent, promise, and transformation must be careful; the serpent should be mysterious/gentle, not horror.",
        ("serpent", "bridegroom", "promise", "quest", "transformation"),
    ),
}


PANEL_PHASE_LABELS = (
    "opening/world",
    "inciting choice or test",
    "deepening complication",
    "crisis or reveal",
    "consequence/repair",
    "resolution/afterglow",
)


PANEL_RANGES: dict[str, tuple[tuple[int, int, int], ...]] = {
    "simcheong": ((1, 6, 1), (7, 12, 2), (13, 18, 3), (19, 25, 4), (26, 31, 5), (32, 38, 6)),
    "rabbit-and-turtle": ((1, 5, 1), (6, 10, 2), (11, 15, 3), (16, 20, 4), (21, 25, 5), (26, 30, 6)),
    "dokkaebi-club": ((1, 5, 1), (6, 10, 2), (11, 15, 3), (16, 20, 4), (21, 24, 5), (25, 28, 6)),
    "dangun-story": ((1, 5, 1), (6, 10, 2), (11, 15, 3), (16, 20, 4), (21, 25, 5), (26, 30, 6)),
    "grateful-magpie": ((1, 5, 1), (6, 10, 2), (11, 15, 3), (16, 20, 4), (21, 24, 5), (25, 28, 6)),
    "kongjwi-and-patjwi": ((1, 6, 1), (7, 12, 2), (13, 18, 3), (19, 23, 4), (24, 28, 5), (29, 34, 6)),
    "geumgang-mountain-tiger": ((1, 5, 1), (6, 10, 2), (11, 15, 3), (16, 20, 4), (21, 24, 5), (25, 28, 6)),
    "lump-old-man": ((1, 5, 1), (6, 10, 2), (11, 15, 3), (16, 20, 4), (21, 25, 5), (26, 30, 6)),
    "gyeonwu-and-jiknyeo": ((1, 5, 1), (6, 10, 2), (11, 15, 3), (16, 20, 4), (21, 26, 5), (27, 32, 6)),
    "bari-princess-part-1": ((1, 4, 1), (5, 8, 2), (9, 12, 3), (13, 16, 4), (17, 21, 5), (22, 26, 6)),
    "bari-princess-part-2": ((1, 4, 1), (5, 8, 2), (9, 12, 3), (13, 16, 4), (17, 21, 5), (22, 26, 6)),
    "snail-bride": ((1, 5, 1), (6, 10, 2), (11, 15, 3), (16, 20, 4), (21, 25, 5), (26, 30, 6)),
    "janghwa-and-hongryeon": ((1, 5, 1), (6, 10, 2), (11, 15, 3), (16, 20, 4), (21, 26, 5), (27, 32, 6)),
    "fairy-and-woodcutter": ((1, 2, 1), (3, 4, 2), (5, 12, 3), (13, 14, 4), (15, 16, 5), (17, 32, 6)),
    "green-frog": ((1, 4, 1), (5, 8, 2), (9, 12, 3), (13, 16, 4), (17, 20, 5), (21, 24, 6)),
    "kind-brothers": ((1, 4, 1), (5, 8, 2), (9, 12, 3), (13, 16, 4), (17, 20, 5), (21, 24, 6)),
    "byeoljubu": ((1, 5, 1), (6, 10, 2), (11, 15, 3), (16, 20, 4), (21, 26, 5), (27, 32, 6)),
    "farting-daughter-in-law": ((1, 4, 1), (5, 8, 2), (9, 12, 3), (13, 16, 4), (17, 20, 5), (21, 24, 6)),
    "serpent-bridegroom": ((1, 5, 1), (6, 10, 2), (11, 15, 3), (16, 20, 4), (21, 26, 5), (27, 32, 6)),
}


def expected_panel_for_page(slug: str, page_number: int) -> int:
    for start, end, panel_index in PANEL_RANGES.get(slug, ()):
        if start <= page_number <= end:
            return panel_index
    return ((page_number - 1) % 6) + 1
