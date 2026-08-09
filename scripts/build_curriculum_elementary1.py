#!/usr/bin/env python3
"""Build content/elementary1/ELXX.yaml from audio + PDF scripts + grammar (no Whisper)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from books import get_book  # noqa: E402
from build_curriculum import (  # noqa: E402
    _dialog,
    apply_generic_book_flow,
    attach_phrase_meta,
)

BOOK = get_book("elementary1")

SKILL_KIND = {
    "listening": "listening",
    "speaking": "speaking",
    "grammar_form": "grammar_form",
    "conversation": "conversation",
    "vocabulary": "vocabulary",
    "kotoba": "vocabulary",
    "reading": "listening",
    "hiragana": "script",
    "katakana": "script",
    "classroom": "classroom",
    "other": "other",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def split_concatenated_can_dos(entries: list[dict]) -> list[dict]:
    """TOC parse sometimes glues '… 2. title 18 Can …' into one statement."""
    out: list[dict] = []
    for e in entries:
        en = e.get("statement_en") or ""
        # Split on "N. … NN Can"
        chunks = re.split(r"(?=\d+\.\s+[^\n]{0,40}?\s*\d{2}\s+Can\s)", en)
        if len(chunks) <= 1:
            # Also split bare "NN Can"
            parts = re.split(r"(?=\d{2}\s+Can\s)", en)
            if len(parts) > 1 and parts[0].strip() == "":
                parts = parts[1:]
            if len(parts) > 1:
                chunks = parts
            else:
                out.append(e)
                continue
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            m = re.search(r"(\d{2})\s+(Can\s.+)$", chunk, re.I | re.DOTALL)
            if m:
                num = int(m.group(1))
                stmt = re.sub(r"\s+", " ", m.group(2)).strip()
            else:
                m2 = re.match(r"Can\s+", chunk, re.I)
                if not m2:
                    continue
                num = e.get("can_do_number") or (out[-1]["can_do_number"] + 1 if out else 1)
                stmt = re.sub(r"\s+", " ", chunk).strip()
            # Drop trailing next-activity Japanese titles glued on
            stmt = re.split(r"\s+\d+\.\s+\S", stmt)[0].strip()
            out.append(
                {
                    "can_do_number": num,
                    "statement_en": stmt,
                    "statement_jp": e.get("statement_jp") or "",
                    "activity_hint": "",
                }
            )
    # Fix ids with lesson from first entry
    fixed = []
    for e in out:
        # infer lesson from original id CD_EL01_xx
        lid_m = re.search(r"CD_EL(\d+)_", entries[0].get("id", "CD_EL01_01"))
        lesson = int(lid_m.group(1)) if lid_m else 1
        num = int(e["can_do_number"])
        fixed.append(
            {
                "id": f"CD_EL{lesson:02d}_{num:02d}",
                "can_do_number": num,
                "statement_en": e["statement_en"],
                "statement_jp": e.get("statement_jp") or "",
                "activity_hint": "",
            }
        )
    # Dedup by can_do_number
    by_num = {}
    for e in fixed:
        by_num[e["can_do_number"]] = e
    return [by_num[k] for k in sorted(by_num)]


def merge_can_dos(extracted: list[dict], lesson_num: int) -> list[dict]:
    split = split_concatenated_can_dos(extracted) if extracted else []
    # Ensure ids use this lesson
    out = []
    for e in split:
        num = int(e["can_do_number"])
        must = []
        jp = e.get("statement_jp") or ""
        for tok in ("ください", "ますか", "ですか", "ました", "たい", "から", "です"):
            if tok in jp:
                must.append(tok)
        out.append(
            {
                "id": f"CD_EL{lesson_num:02d}_{num:02d}",
                "can_do_number": num,
                "statement_en": e.get("statement_en") or "",
                "statement_jp": jp,
                "activity_hint": e.get("activity_hint") or "",
                "rubric": {"must_include": must[:4], "min_score": 80},
            }
        )
    if not out:
        out = [
            {
                "id": f"CD_EL{lesson_num:02d}_01",
                "can_do_number": 1,
                "statement_en": f"Complete Elementary 1 lesson {lesson_num} can-dos.",
                "statement_jp": "",
                "activity_hint": "",
                "rubric": {"must_include": ["です"], "min_score": 80},
            }
        ]
    return out


def build_activities(tracks: list[dict], can_dos: list[dict]) -> list[dict]:
    skill_tracks = [t for t in tracks if t["kind"] not in ("classroom",)]
    cd_ids = [c["id"] for c in can_dos] or ["CD_EL01_01"]
    cd_i = 0
    act_n = 0
    activities = []
    for t in skill_tracks:
        if t["kind"] in ("hiragana", "katakana", "script"):
            act_n += 1
            activities.append(
                {
                    "id": f"A{act_n}",
                    "kind": "script",
                    "book_activity": act_n,
                    "can_do_id": None,
                    "label": t["label"],
                    "audio": [t["rel_path"]],
                    "key_phrases": [],
                    "prompt_en": f"Practice with the book audio ({t['filename']}).",
                    "book_skip": True,
                }
            )
            continue
        act_n += 1
        cd = cd_ids[cd_i % len(cd_ids)]
        cd_i += 1
        kind = SKILL_KIND.get(t["kind"], t["kind"])
        prompt = {
            "listening": "Listen to the audio and check understanding for this can-do.",
            "speaking": "Practice speaking along with the model audio, then say it yourself.",
            "grammar_form": "Focus on the grammar form (katachi). Listen and repeat the patterns.",
            "conversation": "Listen to the conversation, then practice both roles.",
            "vocabulary": "Learn the vocabulary with the audio, then say each item aloud.",
        }.get(kind, "Complete this activity with the book audio.")
        activities.append(
            {
                "id": f"A{act_n}",
                "kind": kind,
                "book_activity": act_n,
                "can_do_id": cd,
                "label": t["label"],
                "audio": [t["rel_path"]],
                "track": t.get("track"),
                "key_phrases": [],
                "prompt_en": prompt,
            }
        )
    return activities


def apply_phrases_from_scripts(
    lesson_num: int,
    activities: list[dict],
    script: dict,
) -> None:
    """Map PDF script phrases onto activities by CD track number."""
    by_track = script.get("by_track") or {}
    pool = list(script.get("phrases") or [])
    dialogs = list(script.get("dialogs") or [])
    dialog_i = 0
    pool_i = 0
    listen_counter = 0
    lid = f"EL{lesson_num:02d}"

    for a in activities:
        if a.get("kind") in ("script", "classroom") or a.get("book_skip"):
            continue
        kind = a.get("kind") or "activity"
        track = a.get("track")
        phrases = list(by_track.get(str(track), [])) if track is not None else []
        # Prefer real A/B dialog pairs for speaking/conversation
        if kind in ("speaking", "conversation") and dialog_i < len(dialogs):
            partner, learner = dialogs[dialog_i]
            dialog_i += 1
            a["book_mode"] = "dialog"
            a["dialog_script"] = _dialog(partner, learner)
            audio = list(a.get("audio") or [])
            if audio:
                a["dialog_listen_audio"] = audio[:2]
            alts = [p for p in phrases if p not in (partner, learner)][:2]
            a["key_phrases"] = [learner, partner, *alts]
            attach_phrase_meta(a)
            continue

        if not phrases and pool:
            while pool_i < len(pool) * 2:
                cand = pool[pool_i % len(pool)]
                pool_i += 1
                if "ましょう" in cand or "トピック" in cand:
                    continue
                phrases = [cand]
                break

        if phrases:
            a["key_phrases"] = [p for p in phrases if "ましょう" not in p][:4] or phrases[:4]
            attach_phrase_meta(a)

        if kind in ("speaking", "conversation"):
            if len(a.get("key_phrases") or []) >= 2:
                kp = a["key_phrases"]
                a["book_mode"] = "dialog"
                a["dialog_script"] = _dialog(kp[1], kp[0])
                audio = list(a.get("audio") or [])
                if audio:
                    a["dialog_listen_audio"] = audio[:2]
            elif a.get("key_phrases"):
                a["book_mode"] = "listen_repeat"
            continue

        if kind == "listening":
            listen_counter += 1
            a["book_mode"] = "listen_repeat" if listen_counter == 1 else "listen_select"
            if a["book_mode"] == "listen_select":
                a["picture_has_image"] = True
                a["picture_hint_en"] = (
                    f"{lid} activity {a.get('book_activity')}: listen to the CD, "
                    f"then say the phrase that matches the book."
                )
            continue
        if kind == "grammar_form":
            a["book_mode"] = "listen_repeat"
            continue
        if kind == "vocabulary":
            a["book_mode"] = "listen_repeat_all" if len(phrases) >= 5 else "listen_repeat"
            continue

    apply_generic_book_flow(lesson_num, activities)


def build_quiz_scenarios(can_dos: list[dict], activities: list[dict]) -> list[dict]:
    by_cd: dict[str, list[str]] = {}
    for a in activities:
        cd = a.get("can_do_id")
        if not cd:
            continue
        for p in a.get("key_phrases") or []:
            if p and len(p) >= 2:
                by_cd.setdefault(cd, [])
                if p not in by_cd[cd]:
                    by_cd[cd].append(p)
    out = []
    for c in can_dos:
        phrases = by_cd.get(c["id"]) or []
        must = (c.get("rubric") or {}).get("must_include") or []
        expected = list(dict.fromkeys([*phrases[:4], *must]))[:6]
        if not expected:
            continue
        partner = phrases[0] if phrases else "では、お願いします。"
        out.append(
            {
                "can_do_id": c["id"],
                "partner_jp": partner if str(partner).endswith("。") else f"{partner}。",
                "expected": expected,
                "hint_en": c.get("statement_en") or "Reply using a phrase from this lesson.",
            }
        )
        out.append(
            {
                "can_do_id": c["id"],
                "partner_jp": "もう一度、お願いします。",
                "expected": expected,
                "hint_en": f"Again — {(c.get('statement_en') or '')[:80]}",
            }
        )
    return out


def build_intro_questions(title_en: str, topic_en: str, can_dos: list[dict]) -> list[dict]:
    first = (can_dos[0].get("statement_en") if can_dos else "") or ""
    return [
        {
            "jp": f"{title_en} について、あなたの けいけんは？",
            "en": f'Thinking about "{topic_en or title_en}" — what is your experience?',
        },
        {
            "jp": "この レッスンで、何が できるように なりたいですか？",
            "en": (
                f"This lesson aims at: {first} What do you want to be able to do?"
                if first
                else "What do you want to be able to do after this lesson?"
            ),
        },
    ]


def main() -> None:
    audio = load_json(BOOK.content_dir / "audio_index.json")
    pdf = load_json(BOOK.content_dir / "pdf_extract.json")
    scripts = {}
    sp = BOOK.content_dir / "script_extract.json"
    if sp.exists():
        scripts = load_json(sp).get("lessons") or {}
    grammar = {}
    gpath = BOOK.content_dir / "grammar_extract.json"
    if gpath.exists():
        grammar = load_json(gpath)

    index_lessons = []
    for n in range(1, 19):
        lid = f"EL{n:02d}"
        tracks = audio.get("by_lesson", {}).get(lid, [])
        pdf_L = pdf.get("lessons", {}).get(lid, {})
        can_dos = merge_can_dos(pdf_L.get("can_dos") or [], n)
        activities = build_activities(tracks, can_dos)
        apply_phrases_from_scripts(n, activities, scripts.get(lid) or {})

        g = grammar.get("lessons", {}).get(lid, {})
        grammar_points = [
            {"point": p["point"], "worksheet_pages": [p["page"]], "examples": []}
            for p in g.get("points", [])
        ]
        vocab = []
        seen = set()
        for a in activities:
            if a["kind"] == "vocabulary":
                for ph in a.get("key_phrases") or []:
                    if ph in seen:
                        continue
                    seen.add(ph)
                    vocab.append({"jp": ph, "reading": "", "en": "", "tags": [lid]})

        title_en = pdf_L.get("title_en") or f"Lesson {n}"
        topic_en = pdf_L.get("topic_en") or ""
        quiz_scenarios = build_quiz_scenarios(can_dos, activities)
        # Drop helper field before write
        for a in activities:
            a.pop("track", None)

        lesson = {
            "lesson_id": lid,
            "lesson": n,
            "book_id": "elementary1",
            "title_en": title_en,
            "title_jp": pdf_L.get("title_jp") or "",
            "topic_en": topic_en,
            "pdf_pages": pdf_L.get("pdf_pages") or [],
            "intro_questions": build_intro_questions(title_en, topic_en, can_dos),
            "can_dos": can_dos,
            "activities": activities,
            "grammar": grammar_points,
            "vocab": vocab,
            "quiz_bank": [
                {
                    "type": "roleplay",
                    "can_do_id": c["id"],
                    "prompt_en": f"Demonstrate: {c.get('statement_en') or c.get('statement_jp')}",
                    "spoken_required": True,
                }
                for c in can_dos
            ],
            "quiz_scenarios": quiz_scenarios,
            "english_notes": (pdf_L.get("english_notes") or "")[:1500],
            "unlock_requires_mastery": True,
        }
        out = BOOK.content_dir / f"{lid}.yaml"
        out.write_text(
            yaml.safe_dump(lesson, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        with_p = sum(1 for a in activities if a.get("key_phrases") and not a.get("book_skip"))
        skill = sum(1 for a in activities if not a.get("book_skip"))
        index_lessons.append(
            {
                "lesson_id": lid,
                "lesson": n,
                "book_id": "elementary1",
                "title_en": title_en,
                "title_jp": lesson["title_jp"],
                "topic_en": topic_en,
                "can_do_count": len(can_dos),
                "activity_count": len(activities),
            }
        )
        print(
            f"Wrote {lid}.yaml: skill={skill} phrases={with_p} "
            f"can_dos={len(can_dos)} | {title_en[:40]}"
        )

    index = {
        "book_id": "elementary1",
        "book_title": BOOK.title,
        "level": BOOK.level,
        "lessons": index_lessons,
    }
    (BOOK.content_dir / "index.yaml").write_text(
        yaml.safe_dump(index, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"Wrote index.yaml ({len(index_lessons)} lessons)")


if __name__ == "__main__":
    main()
