"""Upgrade Starter (and optional Elementary) YAML for book exercise types 1–8.

Adds / rewires:
1. listen_choose — true multiple-choice after CD (from former listen_select)
2. listen_fill — cloze blanks for katachi / fill-in notes
3. vocab_drill — vocabulary with EN glosses where known
4. pronunciation — dedicated はつおん pass on short vocab sets
5. grammar examples — leave existing; flag thin points for soft enrichment
6. culture_read — Life & culture step from english_notes
7. reading — yomu / notice-style reading checks
8. note_take — typed notes after listening (“Take notes”)

Idempotent: safe to re-run. Does not delete curated blanks/choices.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# High-frequency Starter glosses (family, greetings, food, etc.)
GLOSS_EN: dict[str, str] = {
    "ちち": "father (one's own)",
    "はは": "mother (one's own)",
    "あに": "older brother (one's own)",
    "あね": "older sister (one's own)",
    "おとうと": "younger brother",
    "いもうと": "younger sister",
    "おっと": "husband",
    "つま": "wife",
    "こども": "child / children",
    "家族": "family",
    "はじめまして": "Nice to meet you",
    "よろしくお願いします": "Please treat me kindly / Nice to meet you",
    "こんにちは": "Hello",
    "おはよう": "Good morning",
    "おはようございます": "Good morning (polite)",
    "ありがとう": "Thank you",
    "ありがとうございます": "Thank you (polite)",
    "すみません": "Excuse me / sorry",
    "はい": "Yes",
    "いいえ": "No",
    "です": "polite copula",
    "から来ました": "came from…",
    "住んでいます": "live (in…)",
    "好きです": "like…",
    "好きじゃないです": "don't like…",
    "ください": "please (give me)",
    "お願いします": "please / I'd like…",
}

# Endings we can blank for listen_fill heuristics on grammar_form lines.
_BLANK_RULES: list[tuple[re.Pattern[str], str, list[str]]] = [
    (re.compile(r"^(.+?)です$"), "＿。", ["です"]),
    (re.compile(r"^(.+?)から来ました$"), "＿。", ["から来ました", "からきました"]),
    (re.compile(r"^(.+?)からきました$"), "＿。", ["から来ました", "からきました"]),
    (re.compile(r"^(.+?)と(.+?)です$"), None, ["と"]),  # special
    (re.compile(r"^(.+?)が好きです$"), "＿。", ["が好きです", "好きです"]),
    (re.compile(r"^(.+?)が好きじゃないです$"), "＿。", ["が好きじゃないです", "好きじゃないです"]),
    (re.compile(r"^(.+?)ください$"), "＿。", ["ください"]),
    (re.compile(r"^(.+?)お願いします$"), "＿。", ["お願いします", "おねがいします"]),
    (re.compile(r"^(.+?)ます$"), "＿。", ["ます"]),
    (re.compile(r"^(.+?)でした$"), "＿。", ["でした"]),
    (re.compile(r"^(.+?)ですね$"), "＿。", ["ですね", "ね"]),
]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _dump(path: Path, data: dict) -> None:
    # Keep unicode readable; match existing style loosely.
    text = yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        width=100,
        default_flow_style=False,
    )
    path.write_text(text, encoding="utf-8")


def _stable_shuffle(items: list, seed: str) -> list:
    scored = []
    for i, item in enumerate(items):
        h = hashlib.md5(f"{seed}:{i}:{item}".encode()).hexdigest()
        scored.append((h, item))
    scored.sort(key=lambda x: x[0])
    return [x[1] for x in scored]


def _letter(i: int) -> str:
    return chr(ord("a") + i) if i < 26 else f"o{i}"


def _clean_phrase(p: str) -> bool:
    p = (p or "").strip()
    if not p or len(p) > 40:
        return False
    # Reject obvious Whisper garbage (long Latin / digit soup).
    latin = sum(ch.isascii() and ch.isalpha() for ch in p)
    if latin >= max(4, len(p) // 3):
        return False
    if re.search(r"\d{3,}", p):
        return False
    return True


def _phrases(act: dict) -> list[str]:
    return [p for p in (act.get("key_phrases") or []) if _clean_phrase(p)]


def _build_choices(act: dict, lesson: dict) -> tuple[list[dict], list[str]]:
    """Build MCQ choices; correct = activity phrases; distractors from elsewhere."""
    existing = act.get("choices")
    if existing and act.get("correct_ids"):
        return list(existing), list(act["correct_ids"])

    correct = _phrases(act)[:6]
    if not correct:
        # Fall back to any key_phrases even if noisy — still better than speech-only.
        correct = [p for p in (act.get("key_phrases") or []) if p][:4]
    if not correct:
        return [], []

    pool: list[str] = []
    for other in lesson.get("activities") or []:
        if other is act or other.get("id") == act.get("id"):
            continue
        for p in _phrases(other):
            if p not in correct and p not in pool:
                pool.append(p)
    distractors = _stable_shuffle(pool, str(act.get("id")))[: max(2, min(4, len(correct) + 1))]
    labels = correct + distractors
    labels = _stable_shuffle(labels, f"choices:{act.get('id')}")
    # Cap total options
    labels = labels[:8]
    choices = [{"id": _letter(i), "label_jp": lab} for i, lab in enumerate(labels)]
    correct_ids = [c["id"] for c in choices if c["label_jp"] in correct]
    return choices, correct_ids


def _blanks_from_phrases(phrases: list[str]) -> list[dict]:
    blanks: list[dict] = []
    for phrase in phrases:
        phrase = phrase.strip()
        if not phrase or not _clean_phrase(phrase):
            continue
        # AとBです → blank と
        m = re.match(r"^(.+?)と(.+?)です$", phrase)
        if m:
            blanks.append(
                {
                    "prompt_jp": f"{m.group(1)}＿{m.group(2)}です。",
                    "answers": ["と"],
                    "full_jp": phrase,
                }
            )
            continue
        for pat, suffix, answers in _BLANK_RULES:
            m = pat.match(phrase)
            if not m:
                continue
            if suffix is None:
                continue
            stem = m.group(1)
            blanks.append(
                {
                    "prompt_jp": f"{stem}{suffix}",
                    "answers": list(answers[:1]),
                    "answer_alts": list(answers[1:]),
                    "full_jp": phrase,
                }
            )
            break
    return blanks


def _culture_snippet(notes: str, limit: int = 900) -> str:
    notes = (notes or "").strip()
    if not notes:
        return ""
    # Prefer a "Life and culture" / 生活と文化 chunk when present.
    markers = ("Life and culture", "生活と文化", "Culture", "文化")
    lower = notes
    start = 0
    for m in markers:
        idx = lower.find(m)
        if idx >= 0:
            start = idx
            break
    chunk = notes[start : start + limit].strip()
    return chunk or notes[:limit].strip()


def _note_keywords(act: dict) -> list[str]:
    return _phrases(act)[:8]


def upgrade_activity(act: dict, lesson: dict) -> dict:
    kind = (act.get("kind") or "").strip()
    label = (act.get("label") or "").lower()
    mode = (act.get("book_mode") or "").strip()
    prompt = (act.get("prompt_en") or "").lower()
    phrases = _phrases(act)

    # 3) Vocabulary → vocab_drill with glosses
    if kind == "vocabulary" or label.startswith("kotoba"):
        act["book_mode"] = "vocab_drill"
        glosses = act.get("glosses_en") or {}
        for p in phrases:
            if p not in glosses and p in GLOSS_EN:
                glosses[p] = GLOSS_EN[p]
        if glosses:
            act["glosses_en"] = glosses
        act["prompt_en"] = act.get("prompt_en") or "Learn the words — listen, check the meaning, then say each one."
        return act

    # 4) Pronunciation — short word lists / hatsuwon labels
    if "hatsu" in label or "pronun" in label or kind == "pronunciation":
        act["book_mode"] = "pronunciation"
        act["prompt_en"] = act.get("prompt_en") or "Pronunciation — listen carefully, then say each item clearly."
        return act

    # 7) Reading
    if kind == "yomu" or "yomu" in label or mode == "reading":
        act["book_mode"] = "reading"
        if not act.get("passage_en"):
            act["passage_en"] = act.get("prompt_en") or (
                "Read the text in your book (menu, notice, or passage), then answer."
            )
        if not act.get("choices"):
            choices, correct = _build_choices(act, lesson)
            if choices:
                act["choices"] = choices
                act["correct_ids"] = correct
                act["choose_mode"] = "any" if len(correct) <= 1 else "all"
        act["prompt_en"] = act.get("prompt_en") or "Read, then choose the best answer."
        return act

    # 1) Listen & choose (upgrade listen_select)
    if mode == "listen_select" or (
        kind == "listening" and ("choose" in prompt or "match" in prompt or "select" in prompt)
    ):
        act["book_mode"] = "listen_choose"
        choices, correct = _build_choices(act, lesson)
        if choices:
            act["choices"] = choices
            act["correct_ids"] = correct
            act["choose_mode"] = "all" if len(correct) > 1 else "any"
        hint = act.get("picture_hint_en") or ""
        act["prompt_en"] = (
            act.get("prompt_en")
            if "choose" in (act.get("prompt_en") or "").lower()
            else (hint or "Listen to the CD, then choose what you heard.")
        )
        return act

    # 8) Note-taking listens
    if "take notes" in prompt or "take note" in prompt or "notes in the blank" in prompt:
        act["book_mode"] = "note_take"
        act["note_keywords"] = _note_keywords(act)
        act["prompt_en"] = act.get("prompt_en") or "Listen and type brief notes about what you heard."
        return act

    # Also disable ending-heuristic generation: blanks must come from the book worksheet.
    # Keep listen_fill only when curated/extracted blanks already exist.
    if kind == "grammar_form" or "katachi" in label:
        if act.get("blanks"):
            act["book_mode"] = "listen_fill"
            return act
        # Prefer listen-and-repeat for grammar forms without real worksheet blanks
        if phrases and mode in ("", "listen_repeat", "listen_select", "listen_fill"):
            act["book_mode"] = "listen_repeat_all"
            act["prompt_en"] = act.get("prompt_en") or (
                "Focus on the grammar form. Listen and say each pattern."
            )
        return act

    return act


def upgrade_lesson(data: dict) -> dict:
    acts = list(data.get("activities") or [])
    # First pass: upgrade each activity
    upgraded = [upgrade_activity(dict(a), data) for a in acts]

    # Add pronunciation twin for first clean vocab_drill if lesson has none
    has_pron = any((a.get("book_mode") == "pronunciation") for a in upgraded)
    if not has_pron:
        for a in upgraded:
            if a.get("book_mode") == "vocab_drill" and _phrases(a):
                short = [p for p in _phrases(a) if len(p) <= 12][:6]
                if len(short) >= 2:
                    twin = {
                        "id": f"{a.get('id')}_PRON",
                        "kind": "pronunciation",
                        "book_activity": float(a.get("book_activity") or 0) + 0.1,
                        "can_do_id": a.get("can_do_id"),
                        "label": "hatsuwon",
                        "audio": list(a.get("audio") or []),
                        "key_phrases": short,
                        "book_mode": "pronunciation",
                        "prompt_en": "Pronunciation — say each word clearly (watch long vowels and mora).",
                        "picture_has_image": False,
                    }
                    upgraded.append(twin)
                    break

    # 6) Culture activity once per lesson
    notes = _culture_snippet(data.get("english_notes") or "")
    if notes and not any(a.get("book_mode") == "culture_read" for a in upgraded):
        max_ba = max((float(a.get("book_activity") or 0) for a in upgraded), default=0)
        upgraded.append(
            {
                "id": "CULTURE",
                "kind": "culture",
                "book_activity": int(max_ba) + 1,
                "label": "seikatsu_bunka",
                "audio": [],
                "key_phrases": [],
                "book_mode": "culture_read",
                "prompt_en": "Life and culture — read the note, then continue.",
                "culture_notes_en": notes,
                "picture_has_image": False,
            }
        )

    # 8) If english_notes mention take notes but no note_take activity, convert a listening act
    enotes = (data.get("english_notes") or "").lower()
    if "take notes" in enotes and not any(a.get("book_mode") == "note_take" for a in upgraded):
        for a in upgraded:
            if a.get("kind") == "listening" and a.get("book_mode") in (
                "listen_choose",
                "listen_select",
                "listen_repeat",
                "listen_repeat_all",
            ):
                # Prefer second listening activity when present
                continue
        # Pick first listening with phrases
        for a in upgraded:
            if a.get("kind") == "listening" and (_phrases(a) or a.get("key_phrases")):
                if a.get("book_mode") in ("dialog", "listen_fill", "vocab_drill", "pronunciation"):
                    continue
                a["book_mode"] = "note_take"
                a["note_keywords"] = _note_keywords(a)
                a["prompt_en"] = "Listen and type brief notes (who / what / where)."
                break

    # Normalize book_activity to int where possible
    for a in upgraded:
        ba = a.get("book_activity")
        if isinstance(ba, float) and ba == int(ba):
            a["book_activity"] = int(ba)

    upgraded.sort(key=lambda x: float(x.get("book_activity") or 0))
    data["activities"] = upgraded
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", default="starter", choices=("starter", "elementary1", "all"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    books = ["starter", "elementary1"] if args.book == "all" else [args.book]

    changed = 0
    for book in books:
        folder = ROOT / "content" / book
        if not folder.is_dir():
            print("skip missing", folder)
            continue
        for path in sorted(folder.glob("L*.yaml")) + sorted(folder.glob("EL*.yaml")):
            data = _load(path)
            if not data.get("activities"):
                continue
            before = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
            upgraded = upgrade_lesson(data)
            after = yaml.safe_dump(upgraded, allow_unicode=True, sort_keys=False)
            if before == after:
                continue
            modes = {}
            for a in upgraded["activities"]:
                m = a.get("book_mode") or "?"
                modes[m] = modes.get(m, 0) + 1
            print(f"{path.name}: {modes}")
            if not args.dry_run:
                _dump(path, upgraded)
            changed += 1
    print(("would change" if args.dry_run else "updated"), changed, "lessons")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
