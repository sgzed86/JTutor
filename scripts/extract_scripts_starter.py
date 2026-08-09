#!/usr/bin/env python3
"""
Extract speak/listen targets from Starter PDF dialog scripts
(A：/B： lines + CD markers like 03-04) → content/starter/script_extract.json

No Whisper — phrases come from the textbook. Run after pdf_extract.json exists.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pypdf import PdfReader

from books import get_book
from text_cleanup import cleanup_text

BOOK = get_book("starter")
PDF = BOOK.textbook_pdf
PDF_EXTRACT = BOOK.content_dir / "pdf_extract.json"
OUT = BOOK.content_dir / "script_extract.json"

DIALOG_RE = re.compile(r"[ＡABＢ]\s*[：:]\s*([^\n]+)")
CD_RE = re.compile(r"(?<!\d)(\d{2})-(\d{2})(?!\d)")
MODEL_RE = re.compile(
    r"((?:お)?[\u3040-\u30ff\u4e00-\u9fffー]{2,16}"
    r"(?:ですか|です|ます|ください|ました|ません|ありがとう)[。？！]?)"
)
_INSTR = re.compile(
    r"(ましょう|スクリプト|設定|トピック|聞きましょう|選|確認|シャドー|練習|書いて)"
)


def safe_text(page) -> str:
    try:
        t = page.extract_text() or ""
    except Exception:
        return ""
    return t.encode("utf-8", errors="ignore").decode("utf-8")


def collapse(s: str) -> str:
    s = cleanup_text(s or "")
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[A-Za-z]{3,}", "", s)
    return s.strip("・.．,， ")


_SKIP_PHRASE = re.compile(
    r"^(きましょう|言いましょう|しましょう|聞きましょう|見てください|"
    r"事があります|ありますか)$"
)


def good(s: str) -> bool:
    if not s or not (2 <= len(s) <= 48):
        return False
    jp = len(re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]", s))
    if jp < 2:
        return False
    if re.fullmatch(r"[\u3040-\u309f\u30a0-\u30ff]{1,4}", s):
        return False
    core = s.rstrip("。．.!！?？")
    if _SKIP_PHRASE.match(core):
        return False
    return True


def uniq(xs: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in xs:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def extract_lesson(reader: PdfReader, lesson_num: int, start: int, end: int) -> dict:
    by_track: dict[int, list[str]] = defaultdict(list)
    phrases: list[str] = []
    dialogs: list[list[str]] = []
    lesson_tag = f"{lesson_num:02d}"

    for p in range(start, min(end, len(reader.pages)) + 1):
        raw = safe_text(reader.pages[p - 1])
        text = cleanup_text(raw)

        tracks = sorted(
            {
                int(m.group(2))
                for m in CD_RE.finditer(text)
                if m.group(1) == lesson_tag
            }
        )

        dialog_lines = [collapse(x) for x in DIALOG_RE.findall(text)]
        dialog_lines = [x for x in dialog_lines if good(x)]
        for i in range(0, len(dialog_lines) - 1, 2):
            dialogs.append([dialog_lines[i], dialog_lines[i + 1]])

        model_lines = []
        for m in MODEL_RE.finditer(text):
            c = collapse(m.group(1))
            if good(c) and not _INSTR.search(c):
                model_lines.append(c)

        page_phrases = uniq(dialog_lines + model_lines)
        phrases.extend(page_phrases)

        for t in tracks:
            for ph in dialog_lines + model_lines:
                if ph not in by_track[t] and not _INSTR.search(ph):
                    by_track[t].append(ph)

    return {
        "by_track": {str(k): v[:8] for k, v in sorted(by_track.items())},
        "phrases": uniq(phrases)[:100],
        "dialogs": dialogs[:50],
    }


def main() -> None:
    if not PDF.exists():
        raise SystemExit(f"Missing {PDF}")
    if not PDF_EXTRACT.exists():
        raise SystemExit("Run starter PDF extract first (pdf_extract.json)")

    meta = json.loads(PDF_EXTRACT.read_text(encoding="utf-8"))
    reader = PdfReader(str(PDF))
    lessons = {}
    for n in range(1, 19):
        lid = f"L{n:02d}"
        pages = (meta.get("lessons") or {}).get(lid, {}).get("pdf_pages") or []
        if len(pages) < 2:
            lessons[lid] = {"lesson_id": lid, "by_track": {}, "phrases": [], "dialogs": []}
            print(f"{lid}: no pages")
            continue
        start, end = int(pages[0]), int(pages[1])
        if end < start:
            start, end = end, start
        data = extract_lesson(reader, n, start, end)
        lessons[lid] = {"lesson_id": lid, "pdf_pages": [start, end], **data}
        print(
            f"{lid}: tracks={len(data['by_track'])} phrases={len(data['phrases'])} "
            f"dialogs={len(data['dialogs'])}"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "source": str(PDF),
                "book_id": "starter",
                "lessons": lessons,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
