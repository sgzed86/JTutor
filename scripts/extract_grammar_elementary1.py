#!/usr/bin/env python3
"""Extract grammar points from Grammar_Elementary_1.pdf."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from books import get_book
from pypdf import PdfReader
from text_cleanup import cleanup_text

BOOK = get_book("elementary1")
PDF = BOOK.grammar_pdf
OUT = BOOK.content_dir / "grammar_extract.json"


def safe_text(page) -> str:
    try:
        t = page.extract_text() or ""
    except Exception:
        return ""
    return t.encode("utf-8", errors="ignore").decode("utf-8")


def main() -> None:
    if not PDF.exists():
        raise SystemExit(f"Missing PDF: {PDF}")
    reader = PdfReader(str(PDF))
    by_lesson: dict[int, dict] = {}
    current = None
    for i, page in enumerate(reader.pages):
        raw = safe_text(page)
        text = cleanup_text(raw)
        m = re.search(r"第\s*(\d+)\s*課", text)
        if m:
            current = int(m.group(1))
            by_lesson.setdefault(
                current,
                {"lesson": current, "pages": [], "points": [], "raw_chunks": []},
            )
        if current is None:
            continue
        by_lesson[current]["pages"].append(i + 1)
        by_lesson[current]["raw_chunks"].append({"page": i + 1, "text": text[:3000]})
        for pm in re.finditer(
            r"(?:[❶❷❸❹❺❻❼❽❾❿①②③④⑤⑥⑦⑧⑨⑩]|\d+)\s*[.)．]?\s*([^\n]{2,60})",
            text,
        ):
            point = cleanup_text(pm.group(1))
            if len(point) < 2:
                continue
            if re.search(r"[はがをにでとですます]", point) or "N" in point or "～" in point:
                by_lesson[current]["points"].append({"point": point, "page": i + 1})
        for em in re.finditer(
            r"(Fill in[^\n]+|Say the[^\n]+|Complete[^\n]+|Practice[^\n]+)", text, re.I
        ):
            by_lesson[current].setdefault("practice_prompts_en", []).append(em.group(1).strip())

    for L in by_lesson.values():
        seen = set()
        uniq = []
        for p in L["points"]:
            if p["point"] in seen:
                continue
            seen.add(p["point"])
            uniq.append(p)
        L["points"] = uniq[:20]

    lessons = {
        f"EL{n:02d}": {
            "lesson_id": f"EL{n:02d}",
            "lesson": n,
            "pages": by_lesson.get(n, {}).get("pages", []),
            "points": by_lesson.get(n, {}).get("points", []),
            "practice_prompts_en": by_lesson.get(n, {}).get("practice_prompts_en", [])[:10],
        }
        for n in range(1, 19)
    }
    payload = {
        "source": str(PDF.relative_to(ROOT)).replace("\\", "/"),
        "book_id": "elementary1",
        "page_count": len(reader.pages),
        "lessons": lessons,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    for lid, L in lessons.items():
        print(f"  {lid}: {len(L['points'])} points, pages {L['pages'][:3]}...")


if __name__ == "__main__":
    main()
