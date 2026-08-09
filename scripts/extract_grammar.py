#!/usr/bin/env python3
"""Extract grammar points from Grammar_Worksheets_X.pdf by lesson."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pypdf import PdfReader

from text_cleanup import cleanup_text

PDF = ROOT / "assets" / "Grammar_Worksheets_X.pdf"
OUT = ROOT / "content" / "starter" / "grammar_extract.json"


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
    # Map each page to a lesson via 第 N 課
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

        # Grammar point headers like "❶ N です" or "1. ～てください"
        for pm in re.finditer(
            r"(?:[❶❷❸❹❺❻❼❽❾❿①②③④⑤⑥⑦⑧⑨⑩]|\d+)\s*[.)．]?\s*([^\n]{2,60})",
            text,
        ):
            point = cleanup_text(pm.group(1))
            if len(point) < 2:
                continue
            # Prefer lines with Japanese particles / です / ます
            if re.search(r"[はがをにでとですます]", point) or "N" in point or "～" in point:
                by_lesson[current]["points"].append(
                    {"point": point, "page": i + 1}
                )

        # English instruction lines for practice
        for em in re.finditer(r"(Fill in[^\n]+|Say the[^\n]+|Complete[^\n]+|Practice[^\n]+)", text, re.I):
            by_lesson[current].setdefault("practice_prompts_en", []).append(em.group(1).strip())

    # Deduplicate points
    for L in by_lesson.values():
        seen = set()
        uniq = []
        for p in L["points"]:
            key = p["point"]
            if key in seen:
                continue
            seen.add(key)
            uniq.append(p)
        L["points"] = uniq[:20]
        L["practice_prompts_en"] = list(dict.fromkeys(L.get("practice_prompts_en", [])))[:10]
        # Drop bulky raw after we have points — keep first 2 chunks only
        L["raw_chunks"] = L["raw_chunks"][:2]

    payload = {
        "source": "assets/Grammar_Worksheets_X.pdf",
        "page_count": len(reader.pages),
        "lessons": {f"L{n:02d}": by_lesson[n] for n in sorted(by_lesson)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(by_lesson)} lessons)")
    for n in sorted(by_lesson):
        print(f"  L{n:02d}: {len(by_lesson[n]['points'])} points, pages {by_lesson[n]['pages'][:3]}...")


if __name__ == "__main__":
    main()
