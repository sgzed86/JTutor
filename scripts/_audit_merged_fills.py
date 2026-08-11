"""Audit lessons for concatenated repeat/fill/katachi targets."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1] / "content"


def looks_concat(p: str) -> bool:
    p = (p or "").strip()
    if len(p) < 18:
        return False
    if any(ch in p for ch in "。、？?　 "):
        return False
    hits = sum(p.count(x) for x in ("ますか", "ですか", "です", "ます", "ください", "お願いします"))
    if len(p) >= 20 and hits >= 2:
        return True
    if len(p) >= 35:
        return True
    return False


def is_katachi(a: dict) -> bool:
    lab = str(a.get("label") or "") + str(a.get("kind") or "")
    return "katachi" in lab or a.get("kind") == "grammar_form"


def main() -> None:
    for book in ("starter", "elementary1"):
        print("===", book, "===")
        for path in sorted((ROOT / book).glob("*.yaml")):
            if path.name.startswith("index") or "phrase" in path.name:
                continue
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for a in data.get("activities") or []:
                mode = a.get("book_mode") or ""
                phrases = [p for p in (a.get("key_phrases") or []) if p]
                blanks = a.get("blanks") or []
                aid = a.get("id")
                if mode in ("listen_repeat", "listen_repeat_all") and phrases:
                    bad = [p for p in phrases if looks_concat(p)]
                    if bad or (len(phrases) == 1 and looks_concat(phrases[0])):
                        tag = "KATACHI" if is_katachi(a) else "REPEAT"
                        print(
                            f"{path.stem} {aid} [{tag}] mode={mode} "
                            f"n={len(phrases)} len0={len(phrases[0])}"
                        )
                        print(" ", phrases[0][:100])
                if mode == "listen_fill" and not blanks:
                    print(f"{path.stem} {aid} EMPTY_FILL")
                if is_katachi(a) and mode not in ("listen_fill", "dialog", "listen_choose") and not blanks:
                    if len(phrases) == 1 and len(phrases[0]) >= 18:
                        # already covered above if concat
                        pass
                    elif mode in ("listen_repeat", "listen_repeat_all") and len(phrases) >= 2:
                        # multi-phrase repeat may still belong as fill on worksheet pages
                        print(
                            f"{path.stem} {aid} [KATACHI_MULTI] mode={mode} n={len(phrases)}"
                        )
                if mode == "listen_choose":
                    for c in a.get("choices") or []:
                        lab = c.get("label_jp") or ""
                        if looks_concat(lab) and len(lab) >= 40:
                            print(f"{path.stem} {aid} BAD_CHOICE {lab[:80]}")
                            break


if __name__ == "__main__":
    import sys

    out = ROOT.parent / "scripts" / "_audit_merged_out.txt"
    lines: list[str] = []

    def emit(s: str = "") -> None:
        lines.append(s)

    # patch print in main by rewriting briefly
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        main()
    text = buf.getvalue()
    out.write_text(text, encoding="utf-8")
    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
    print(f"\nWrote {out}", file=sys.stderr)
