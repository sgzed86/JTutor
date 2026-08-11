"""Find vocab/pronunciation activities with concatenated OCR word lists."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODES = {"vocab_drill", "pronunciation", "listen_repeat_all", "listen_repeat"}


def looks_concatenated(phrase: str) -> bool:
    p = (phrase or "").strip()
    if len(p) < 20:
        return False
    # OCR leftovers that glue many vocab items with letter markers / いい / ビ
    markers = sum(p.count(x) for x in ("ビ", "いい", "ジ", "け", "え"))
    # Many short food/vocab items jammed together often lack punctuation
    if "。" in p or "、" in p or "？" in p:
        return False
    if len(p) >= 30 and markers >= 2:
        return True
    if len(p) >= 40 and not any(ch in p for ch in "。？、　 "):
        return True
    return False


def main() -> None:
    for book in ("starter", "elementary1"):
        print("===", book, "===")
        for path in sorted((ROOT / "content" / book).glob("*.yaml")):
            if "phrase" in path.name or path.name == "index.yaml":
                continue
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for act in data.get("activities") or []:
                mode = act.get("book_mode") or ""
                phrases = [p for p in (act.get("key_phrases") or []) if p]
                if mode in MODES:
                    bad = [p for p in phrases if looks_concatenated(p)]
                    if bad or (mode == "vocab_drill" and len(phrases) == 1 and len(phrases[0]) > 25):
                        print(
                            f"{path.stem} {act.get('id')} mode={mode} "
                            f"n={len(phrases)} bad={len(bad) or (1 if phrases else 0)}"
                        )
                        for p in phrases[:3]:
                            print(f"  {p[:100]}")
                # also flag vocab section junk
            for v in data.get("vocab") or []:
                jp = v.get("jp") or ""
                if looks_concatenated(jp):
                    print(f"{path.stem} vocab: {jp[:80]}")


if __name__ == "__main__":
    main()
