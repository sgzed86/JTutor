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


def main() -> int:
    n = 0
    for book in ("starter", "elementary1"):
        d = ROOT / "content" / book
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.yaml")):
            if "phrase" in path.name or path.name == "index.yaml":
                continue
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            changed = False
            for act in data.get("activities") or []:
                if act.get("book_mode") != "listen_fill":
                    continue
                blanks = act.get("blanks") or []
                answers = [a for b in blanks for a in (b.get("answers") or [])]
                if not answers:
                    continue
                if set(answers) <= HEURISTIC or any(
                    len(str(a)) > 16 or "入門" in str(a) or "トピック" in str(a) for a in answers
                ):
                    act.pop("blanks", None)
                    act.pop("fill_pdf_page", None)
                    act["book_mode"] = "listen_repeat_all"
                    act["prompt_en"] = (
                        "Focus on the expressions used. Listen and say each pattern."
                    )
                    changed = True
                    n += 1
            if changed:
                path.write_text(
                    yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100),
                    encoding="utf-8",
                )
    print("demoted", n, "heuristic fill activities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
