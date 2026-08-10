"""Rebuild one starter lesson YAML with current curated overrides."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_curriculum as bc  # noqa: E402


def rebuild(n: int) -> None:
    audio = bc.load_json(bc.AUDIO_INDEX)
    pdf = bc.load_json(bc.PDF_EXTRACT)
    gpath = bc.STARTER / "grammar_extract.json"
    grammar = bc.load_json(gpath) if gpath.exists() else {"lessons": {}}
    transcripts = bc.load_json(bc.AUDIO_TRANSCRIPTS) if bc.AUDIO_TRANSCRIPTS.exists() else {}
    lid = f"L{n:02d}"
    tracks = audio.get("by_lesson", {}).get(lid, [])
    pdf_L = pdf.get("lessons", {}).get(lid, {})
    phrases = pdf_L.get("key_phrases") or []
    can_dos = bc.merge_can_dos(n, pdf_L.get("can_dos") or [], phrases)
    activities = bc.build_activities(n, tracks, can_dos)

    if n == 3:
        if transcripts:
            bc.apply_phrases_from_transcripts(n, activities, transcripts)
        bc.apply_l03_phrases(activities)
        bc.apply_generic_book_flow(n, activities)
        bc.apply_l03_book_flow_overrides(activities)
        grammar_points = [dict(p) for p in bc.L03_GRAMMAR]
    elif n == 4:
        if transcripts:
            bc.apply_phrases_from_transcripts(n, activities, transcripts)
        bc.apply_l04_phrases(activities)
        bc.apply_generic_book_flow(n, activities)
        bc.apply_l04_book_flow_overrides(activities)
        grammar_points = [dict(p) for p in bc.L04_GRAMMAR]
    else:
        raise SystemExit(f"No curated rebuild path for {lid}")

    quiz_scenarios = bc.build_quiz_scenarios(n, can_dos)
    quiz_scenarios = bc.enrich_quiz_scenarios(n, activities, can_dos, quiz_scenarios)
    quiz_scenarios = bc.enrich_quiz_from_activities(n, can_dos, activities, quiz_scenarios)

    title_en = pdf_L.get("title_en") or lid
    topic_en = pdf_L.get("topic_en") or ""
    vocab = []
    seen: set[str] = set()
    for a in activities:
        if a["kind"] == "vocabulary":
            for ph in a.get("key_phrases") or []:
                if ph not in seen:
                    seen.add(ph)
                    vocab.append({"jp": ph, "reading": "", "en": "", "tags": [lid]})

    lesson = {
        "lesson_id": lid,
        "lesson": n,
        "title_en": title_en,
        "title_jp": pdf_L.get("title_jp") or "",
        "topic_en": topic_en,
        "pdf_pages": pdf_L.get("pdf_pages") or [],
        "intro_questions": bc.build_intro_questions(n, title_en, topic_en, can_dos),
        "can_dos": can_dos,
        "activities": activities,
        "grammar": grammar_points,
        "vocab": vocab,
        "quiz_bank": bc.build_quiz(can_dos, phrases),
        "quiz_scenarios": quiz_scenarios,
        "english_notes": (pdf_L.get("english_notes") or "")[:1500],
        "unlock_requires_mastery": True,
        "schema_version": 1,
    }
    lesson = bc.apply_lesson_overrides(lesson, lid)
    out = bc.STARTER / f"{lid}.yaml"
    out.write_text(
        yaml.safe_dump(lesson, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    print(f"Wrote {out}")
    for a in activities:
        print(f"  {a['id']} {a.get('book_mode')} ({len(a.get('key_phrases') or [])})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson", type=int)
    rebuild(ap.parse_args().lesson)
