"""Demote listen_fill activities whose blanks are only grammar-ending heuristics."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
HEURISTIC = {
    "です",
    "ます",
    "でした",
    "ですね",
    "ね",
    "ください",
    "お願いします",
    "おねがいします",
}


def _is_heuristic(blanks: list[dict]) -> bool:
    answers = [str(a) for b in blanks for a in (b.get("answers") or [])]
    if not answers:
        return True
    if set(answers) <= HEURISTIC:
        return True
    if any(len(a) > 16 or "入門" in a or "トピック" in a for a in answers):
        return True
    # Mostly polite endings (+ at most one particle) — not a real worksheet.
    endings = sum(1 for a in answers if a in HEURISTIC)
    return endings >= max(2, len(answers) - 1)


def _replace_mode_in_text(text: str, act_id: str) -> str | None:
    """Demote one activity without dumping the whole YAML file."""
    import re

    m = re.search(rf"(?m)^- id: {re.escape(act_id)}\s*$", text)
    if not m:
        return None
    start = m.start()
    rest = text[start + 1 :]
    nxt = re.search(r"(?m)^- id: ", rest)
    end = start + 1 + (nxt.start() if nxt else len(rest))
    chunk = text[start:end]
    chunk = re.sub(r"(?m)^  book_mode:.*$", "  book_mode: listen_repeat_all", chunk, count=1)
    chunk = re.sub(
        r"(?m)^  prompt_en:.*$",
        '  prompt_en: Focus on the expressions used. Listen and say each pattern.',
        chunk,
        count=1,
    )
    chunk = re.sub(r"(?ms)^  blanks:.*?(?=^  [a-z_]+:|\Z)", "", chunk)
    chunk = re.sub(r"(?m)^  fill_pdf_page:.*\n?", "", chunk)
    if not chunk.endswith("\n"):
        chunk += "\n"
    return text[:start] + chunk + text[end:]


def main() -> int:
    n = 0
    for book in ("starter", "elementary1"):
        d = ROOT / "content" / book
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.yaml")):
            if "phrase" in path.name or path.name == "index.yaml":
                continue
            raw = path.read_text(encoding="utf-8")
            data = yaml.safe_load(raw) or {}
            text = raw
            for act in data.get("activities") or []:
                if act.get("book_mode") != "listen_fill":
                    continue
                # Curated PDF fills keep fill_pdf_page even when answers include ください.
                if act.get("fill_pdf_page"):
                    continue
                blanks = act.get("blanks") or []
                if not _is_heuristic(blanks):
                    continue
                new_text = _replace_mode_in_text(text, act["id"])
                if new_text is None:
                    continue
                text = new_text
                n += 1
                print(f"demote {path.name} {act['id']}")
            if text != raw:
                path.write_text(text, encoding="utf-8")
    print("demoted", n, "heuristic fill activities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
