#!/usr/bin/env python3
"""Extract Irodori Starter textbook structure from irodori_starter.pdf."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pypdf import PdfReader
from text_cleanup import cleanup_text, extract_english_blocks

PDF = ROOT / "assets" / "irodori_starter.pdf"
OUT = ROOT / "content" / "starter" / "pdf_extract.json"

# Official Starter lesson titles / topics (seed; enriched from PDF)
LESSON_META = {
    1: {"title_en": "Good morning!", "title_jp": "おはようございます", "topic_en": "Starting to Speak Japanese"},
    2: {"title_en": "I'm sorry, I don't really understand.", "title_jp": "すみません、よくわかりません", "topic_en": "Starting to Speak Japanese"},
    3: {"title_en": "Nice to meet you.", "title_jp": "よろしくお願いします", "topic_en": "About Myself"},
    4: {"title_en": "I live in Tokyo.", "title_jp": "東京に住んでいます", "topic_en": "About Myself"},
    5: {"title_en": "I like udon.", "title_jp": "うどんが好きです", "topic_en": "Food"},
    6: {"title_en": "I'd like a cheeseburger, please.", "title_jp": "チーズバーガーをください", "topic_en": "Food"},
    7: {"title_en": "There are four rooms.", "title_jp": "部屋が４つあります", "topic_en": "Homes and Workplaces"},
    8: {"title_en": "Where is Yamada-san?", "title_jp": "山田さんはどこですか", "topic_en": "Homes and Workplaces"},
    9: {"title_en": "Lunch is from noon to 1 o'clock.", "title_jp": "12時から1時まで昼休みです", "topic_en": "Daily Life"},
    10: {"title_en": "Please lend me the stapler.", "title_jp": "ホチキス貸してください", "topic_en": "Daily Life"},
    11: {"title_en": "What kind of manga do you like?", "title_jp": "どんなマンガが好きですか？", "topic_en": "What I Like to Do"},
    12: {"title_en": "Do you want to go for a drink together?", "title_jp": "一緒に飲みに行きませんか", "topic_en": "What I Like to Do"},
    13: {"title_en": "Does this bus go to the airport?", "title_jp": "このバスは空港に行きますか？", "topic_en": "Walking around Town"},
    14: {"title_en": "It's a big building, isn't it.", "title_jp": "大きい建物ですね", "topic_en": "Walking around Town"},
    15: {"title_en": "I need some batteries.", "title_jp": "電池がほしいんですが…", "topic_en": "At Stores"},
    16: {"title_en": "How much is this?", "title_jp": "これ、いくらですか？", "topic_en": "At Stores"},
    17: {"title_en": "I went to see a movie.", "title_jp": "映画を見に行きました", "topic_en": "Holidays"},
    18: {"title_en": "I want to go to a hot spring.", "title_jp": "温泉に入りたいです", "topic_en": "Holidays"},
}

# English TOC pages (1-indexed) from prior scan
TOC_PAGES = range(36, 42)
CANDO_CHECK_PAGES = range(506, 515)


def safe_text(page) -> str:
    try:
        t = page.extract_text() or ""
    except Exception:
        return ""
    # Drop surrogate code points that break UTF-8
    return t.encode("utf-8", errors="ignore").decode("utf-8")


def find_lesson_starts(reader: PdfReader) -> dict[int, int]:
    """Map lesson number -> 1-indexed start page."""
    starts: dict[int, int] = {}
    # Pattern like "入門 L5 -" or "Lesson 5" on chapter openers
    for i, page in enumerate(reader.pages):
        t = safe_text(page)
        m = re.search(r"入門\s*L(\d+)\s*[-–]", t)
        if m:
            n = int(m.group(1))
            if n not in starts:
                starts[n] = i + 1
            continue
        m2 = re.search(r"第\s*(\d+)\s*課", t)
        if m2 and "Can-do" not in t[:80]:
            n = int(m2.group(1))
            # Prefer early occurrence as start; skip TOC (pages < 45)
            if i + 1 >= 45 and n not in starts:
                starts[n] = i + 1
    return starts


def parse_en_toc(reader: PdfReader) -> dict[int, list[dict]]:
    """Parse English Table of Contents into can-dos per lesson."""
    blob = "\n".join(safe_text(reader.pages[i - 1]) for i in TOC_PAGES)
    blob = cleanup_text(blob)
    # Split by Lesson N
    parts = re.split(r"Lesson\s+(\d+)\s+", blob)
    # parts: [preamble, '1', body1, '2', body2, ...]
    can_dos: dict[int, list[dict]] = {}
    for idx in range(1, len(parts), 2):
        lesson = int(parts[idx])
        body = parts[idx + 1] if idx + 1 < len(parts) else ""
        # Title: first line-ish until Activities
        title_m = re.match(r"(.+?)Activities", body, re.DOTALL | re.IGNORECASE)
        title = title_m.group(1).strip().split("\n")[0].strip() if title_m else LESSON_META.get(lesson, {}).get("title_en", "")
        # Can-do rows: "01 Can exchange..." or "1. ... 01 Can ..."
        entries = []
        for m in re.finditer(
            r"(?:(\d+)\.\s*[^\n]*?)?(\d{2})\s+(Can\s+[^\n]+(?:\n(?!\d{2}\s+Can)[^\n]+)*)",
            body,
            re.IGNORECASE,
        ):
            num = int(m.group(2))
            statement = cleanup_text(m.group(3))
            statement = re.sub(r"\s+", " ", statement).strip()
            entries.append(
                {
                    "can_do_number": num,
                    "statement_en": statement,
                    "activity_hint": (m.group(1) or "").strip(),
                }
            )
        if not entries:
            # Fallback simpler: lines starting with Can
            for m in re.finditer(r"(\d{2})\s+(Can\s.+?)(?=\d{2}\s+Can|\Z)", body, re.DOTALL | re.IGNORECASE):
                statement = re.sub(r"\s+", " ", cleanup_text(m.group(2))).strip()
                entries.append({"can_do_number": int(m.group(1)), "statement_en": statement, "activity_hint": ""})
        can_dos[lesson] = entries
        if title and lesson in LESSON_META:
            LESSON_META[lesson]["title_en"] = title.rstrip(".")
    return can_dos


def parse_jp_toc(reader: PdfReader) -> dict[int, list[dict]]:
    """Parse Japanese 内容一覧 for JP can-do statements."""
    blob = "\n".join(safe_text(reader.pages[i - 1]) for i in range(30, 36))
    can_dos: dict[int, list[dict]] = {}
    parts = re.split(r"第\s*(\d+)\s*課", blob)
    for idx in range(1, len(parts), 2):
        lesson = int(parts[idx])
        body = parts[idx + 1] if idx + 1 < len(parts) else ""
        entries = []
        for m in re.finditer(r"(\d{2})\s+([^\d\n][^\n]{5,120})", body):
            num = int(m.group(1))
            stmt = cleanup_text(m.group(2))
            # Skip if mostly English
            if re.search(r"[A-Za-z]{8,}", stmt) and "できる" not in stmt:
                continue
            if "できる" in stmt or "理解" in stmt or "質問" in stmt or "言う" in stmt or "答" in stmt:
                entries.append({"can_do_number": num, "statement_jp": re.sub(r"\s+", " ", stmt).strip()})
        can_dos[lesson] = entries
    return can_dos


def extract_lesson_pages(reader: PdfReader, starts: dict[int, int]) -> dict[int, dict]:
    """Collect page ranges and cleaned text samples per lesson."""
    ordered = sorted(starts.items())
    result = {}
    _total = len(reader.pages)
    for i, (lesson, start) in enumerate(ordered):
        end = (ordered[i + 1][1] - 1) if i + 1 < len(ordered) else min(start + 40, 505)
        pages = list(range(start, end + 1))
        # Sample: first 3 pages + any with Can-do
        texts = []
        for p in pages[:4]:
            raw = safe_text(reader.pages[p - 1])
            texts.append({"page": p, "text": cleanup_text(raw)[:4000]})
        # Key phrases: pull short JP quoted / example lines from first pages
        joined = "\n".join(t["text"] for t in texts)
        phrases = []
        for m in re.finditer(r"[「『]([^」』]{2,40})[」』]", joined):
            phrases.append(m.group(1))
        # Also lines that look like dialogue A：
        for m in re.finditer(r"[ABＡＢ]\s*[：:]\s*([^\n]{2,60})", joined):
            phrases.append(cleanup_text(m.group(1)))
        result[lesson] = {
            "pdf_pages": [start, end],
            "page_samples": texts,
            "key_phrases": list(dict.fromkeys(phrases))[:30],
            "english_notes": extract_english_blocks(joined)[:2000],
        }
    return result


def main() -> None:
    if not PDF.exists():
        raise SystemExit(f"Missing PDF: {PDF}")
    reader = PdfReader(str(PDF))
    print(f"PDF pages: {len(reader.pages)}")
    starts = find_lesson_starts(reader)
    print(f"Lesson starts found: {sorted(starts.items())}")
    en_cando = parse_en_toc(reader)
    jp_cando = parse_jp_toc(reader)
    lesson_pages = extract_lesson_pages(reader, starts) if starts else {}

    lessons = {}
    for n in range(1, 19):
        meta = LESSON_META[n]
        cds = []
        en_list = en_cando.get(n, [])
        jp_map = {c["can_do_number"]: c.get("statement_jp", "") for c in jp_cando.get(n, [])}
        for e in en_list:
            num = e["can_do_number"]
            cds.append(
                {
                    "id": f"CD_L{n:02d}_{num:02d}",
                    "can_do_number": num,
                    "statement_en": e["statement_en"],
                    "statement_jp": jp_map.get(num, ""),
                    "activity_hint": e.get("activity_hint", ""),
                }
            )
        # If EN parse failed, use JP only
        if not cds and jp_cando.get(n):
            for j in jp_cando[n]:
                num = j["can_do_number"]
                cds.append(
                    {
                        "id": f"CD_L{n:02d}_{num:02d}",
                        "can_do_number": num,
                        "statement_en": "",
                        "statement_jp": j["statement_jp"],
                        "activity_hint": "",
                    }
                )
        lp = lesson_pages.get(n, {})
        lessons[f"L{n:02d}"] = {
            "lesson_id": f"L{n:02d}",
            "lesson": n,
            **meta,
            "pdf_pages": lp.get("pdf_pages", []),
            "can_dos": cds,
            "key_phrases": lp.get("key_phrases", []),
            "english_notes": lp.get("english_notes", ""),
            "page_samples": lp.get("page_samples", []),
        }

    payload = {
        "source": "assets/irodori_starter.pdf",
        "page_count": len(reader.pages),
        "lesson_starts": starts,
        "lessons": lessons,
        "cando_check_pages": list(CANDO_CHECK_PAGES),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    for lid, L in lessons.items():
        print(f"  {lid}: {len(L['can_dos'])} can-dos, pages {L.get('pdf_pages')}")


if __name__ == "__main__":
    main()
