#!/usr/bin/env python3
"""Extract Irodori Elementary 1 textbook structure → content/elementary1/pdf_extract.json."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pypdf import PdfReader

from books import get_book
from text_cleanup import cleanup_text, extract_english_blocks

BOOK = get_book("elementary1")
PDF = BOOK.textbook_pdf
OUT = BOOK.content_dir / "pdf_extract.json"

# Seed titles (enriched from EN TOC when possible)
LESSON_META: dict[int, dict] = {
    1: {
        "title_en": "I work at a restaurant",
        "title_jp": "レストランで働いています",
        "topic_en": "About Me Now",
    },
    2: {
        "title_en": "I came to Japan in September last year",
        "title_jp": "去年の９月に日本に来ました",
        "topic_en": "About Me Now",
    },
    3: {
        "title_en": "It gets very cold in winter",
        "title_jp": "冬はとても寒くなります",
        "topic_en": "Seasons and Weather",
    },
    4: {
        "title_en": "It rained heavily yesterday",
        "title_jp": "昨日はすごい雨でしたね",
        "topic_en": "Seasons and Weather",
    },
    5: {
        "title_en": "It's lively and convenient",
        "title_jp": "とてもにぎやかで便利です",
        "topic_en": "Towns and Neighborhoods",
    },
    6: {
        "title_en": "Please tell me how to get there",
        "title_jp": "行き方を教えてください",
        "topic_en": "Towns and Neighborhoods",
    },
    7: {
        "title_en": "Shall we go together?",
        "title_jp": "いっしょに行きませんか",
        "topic_en": "Going Out",
    },
    8: {
        "title_en": "Have you ever played baseball?",
        "title_jp": "野球、したことありますか？",
        "topic_en": "Going Out",
    },
    9: {
        "title_en": "I'd like to reserve a table",
        "title_jp": "予約したいんですが",
        "topic_en": "Eating Out",
    },
    10: {
        "title_en": "How was the food?",
        "title_jp": "料理、どうでしたか",
        "topic_en": "Eating Out",
    },
    11: {
        "title_en": "I will bring meat and vegetables",
        "title_jp": "肉と野菜は私が買って行きます",
        "topic_en": "Shopping and Cooking",
    },
    12: {
        "title_en": "Which one is better?",
        "title_jp": "どっちがいいですか",
        "topic_en": "Shopping and Cooking",
    },
    13: {
        "title_en": "Could you help me?",
        "title_jp": "手伝っていただけませんか",
        "topic_en": "At Work",
    },
    14: {
        "title_en": "May I take a day off?",
        "title_jp": "休みを取ってもいいでしょうか？",
        "topic_en": "At Work",
    },
    15: {
        "title_en": "I caught a cold",
        "title_jp": "かぜをひきました",
        "topic_en": "Health",
    },
    16: {
        "title_en": "Please take care of yourself",
        "title_jp": "お大事に",
        "topic_en": "Health",
    },
    17: {
        "title_en": "This is a personal amulet my older brother gave me",
        "title_jp": "兄がくれたお守りです",
        "topic_en": "Visiting People",
    },
    18: {
        "title_en": "Thank you for inviting me",
        "title_jp": "招待してくれてありがとう",
        "topic_en": "Visiting People",
    },
}


def safe_text(page) -> str:
    try:
        t = page.extract_text() or ""
    except Exception:
        return ""
    return t.encode("utf-8", errors="ignore").decode("utf-8")


def find_lesson_starts(reader: PdfReader) -> dict[int, int]:
    """First page of each lesson: 'L3 - 1' + topic marker (skip How-to false hits)."""
    starts: dict[int, int] = {}
    for i, page in enumerate(reader.pages):
        if i + 1 < 40:
            continue
        t = safe_text(page)
        if "トピック" not in t and "▶" not in t:
            continue
        m = re.search(r"L(\d+)\s*[-–]\s*1\b", t)
        if not m:
            continue
        n = int(m.group(1))
        if 1 <= n <= 18 and n not in starts:
            starts[n] = i + 1
    return starts


def parse_en_toc(reader: PdfReader) -> dict[int, list[dict]]:
    # English TOC spans several pages; include a little extra for Lesson 1–2 that appear mid-block
    pages = list(range(36, 43))
    blob = "\n".join(safe_text(reader.pages[i - 1]) for i in pages)
    blob = cleanup_text(blob)
    can_dos: dict[int, list[dict]] = {}
    parts = re.split(r"Lesson\s+(\d+)\s+", blob)
    for idx in range(1, len(parts), 2):
        lesson = int(parts[idx])
        body = parts[idx + 1] if idx + 1 < len(parts) else ""
        title_m = re.match(r"(.+?)(?:Activities|Can-do)", body, re.DOTALL | re.IGNORECASE)
        title = title_m.group(1).strip().split("\n")[0].strip() if title_m else ""
        if title and lesson in LESSON_META:
            LESSON_META[lesson]["title_en"] = re.sub(r"\s+", " ", title).rstrip(".")
        entries = []
        # "01\nCan ..." or "01 Can ..." — stop before next numbered can-do / Kanji Words
        for m in re.finditer(
            r"(\d{2})\s*\n?\s*(Can\s.+?)(?=\n\s*\d{2}\s*\n?\s*Can|\nKanji|\nGrammar|\nLesson\s+\d+|\Z)",
            body,
            re.DOTALL | re.IGNORECASE,
        ):
            num = int(m.group(1))
            statement = re.sub(r"\s+", " ", cleanup_text(m.group(2))).strip()
            statement = re.split(r"\bKanji\b|\bGrammar\b", statement)[0].strip()
            if len(statement) < 12:
                continue
            entries.append(
                {
                    "can_do_number": num,
                    "statement_en": statement,
                    "activity_hint": "",
                }
            )
        can_dos[lesson] = entries
    return can_dos


def parse_jp_toc(reader: PdfReader) -> dict[int, list[dict]]:
    blob = "\n".join(safe_text(reader.pages[i - 1]) for i in BOOK.toc_jp_pages)
    can_dos: dict[int, list[dict]] = {}
    parts = re.split(r"第\s*(\d+)\s*課", blob)
    for idx in range(1, len(parts), 2):
        lesson = int(parts[idx])
        body = parts[idx + 1] if idx + 1 < len(parts) else ""
        title_m = re.search(r"([^\n]{4,40})", body)
        if title_m and lesson in LESSON_META:
            tj = cleanup_text(title_m.group(1)).strip()
            if tj and "活動" not in tj and "Can-do" not in tj:
                LESSON_META[lesson]["title_jp"] = tj[:40]
        entries = []
        for m in re.finditer(r"(\d{2})\s+([^\d\n][^\n]{5,160})", body):
            num = int(m.group(1))
            stmt = cleanup_text(m.group(2))
            if re.search(r"[A-Za-z]{10,}", stmt) and "できる" not in stmt:
                continue
            if any(x in stmt for x in ("できる", "理解", "質問", "言う", "答", "話", "読", "書")):
                entries.append(
                    {
                        "can_do_number": num,
                        "statement_jp": re.sub(r"\s+", " ", stmt).strip(),
                    }
                )
        can_dos[lesson] = entries
    return can_dos


def extract_lesson_pages(reader: PdfReader, starts: dict[int, int]) -> dict[int, dict]:
    ordered = sorted(starts.items())
    result = {}
    total = len(reader.pages)
    for i, (lesson, start) in enumerate(ordered):
        end = (ordered[i + 1][1] - 1) if i + 1 < len(ordered) else min(start + 30, total)
        pages = list(range(start, end + 1))
        texts = []
        for p in pages[:4]:
            raw = safe_text(reader.pages[p - 1])
            texts.append({"page": p, "text": cleanup_text(raw)[:4000]})
        joined = "\n".join(t["text"] for t in texts)
        phrases = []
        for m in re.finditer(r"[「『]([^」』]{2,40})[」』]", joined):
            phrases.append(m.group(1))
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
                    "id": f"CD_EL{n:02d}_{num:02d}",
                    "can_do_number": num,
                    "statement_en": e["statement_en"],
                    "statement_jp": jp_map.get(num, ""),
                    "activity_hint": e.get("activity_hint", ""),
                }
            )
        if not cds and jp_cando.get(n):
            for j in jp_cando[n]:
                num = j["can_do_number"]
                cds.append(
                    {
                        "id": f"CD_EL{n:02d}_{num:02d}",
                        "can_do_number": num,
                        "statement_en": "",
                        "statement_jp": j["statement_jp"],
                        "activity_hint": "",
                    }
                )
        lp = lesson_pages.get(n, {})
        lessons[f"EL{n:02d}"] = {
            "lesson_id": f"EL{n:02d}",
            "lesson": n,
            "book_id": "elementary1",
            **meta,
            "pdf_pages": lp.get("pdf_pages", []),
            "can_dos": cds,
            "key_phrases": lp.get("key_phrases", []),
            "english_notes": lp.get("english_notes", ""),
            "page_samples": lp.get("page_samples", []),
        }

    payload = {
        "source": str(PDF.relative_to(ROOT)).replace("\\", "/"),
        "book_id": "elementary1",
        "page_count": len(reader.pages),
        "lesson_starts": starts,
        "lessons": lessons,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    for lid, L in lessons.items():
        print(f"  {lid}: {len(L['can_dos'])} can-dos, pages {L.get('pdf_pages')}")


if __name__ == "__main__":
    main()
