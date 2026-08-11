"""List remaining high-risk concatenated activity targets."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1] / "content"
OUT = Path(__file__).resolve().parents[1] / "scripts" / "_remaining_concat.json"


def glued(p: str) -> bool:
    p = (p or "").strip()
    if len(p) < 20:
        return False
    if any(ch in p for ch in "。、？?　 "):
        return False
    return True


def main() -> None:
    rows = []
    for book in ("starter", "elementary1"):
        for path in sorted((ROOT / book).glob("*.yaml")):
            if "phrase" in path.name or path.name == "index.yaml":
                continue
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for a in data.get("activities") or []:
                mode = a.get("book_mode") or ""
                phrases = [p for p in (a.get("key_phrases") or []) if p]
                blanks = a.get("blanks") or []
                lab = str(a.get("label") or "")
                kind = str(a.get("kind") or "")
                if not phrases:
                    continue
                # Critical: one mega target for speak/fill/vocab
                if mode in (
                    "listen_repeat",
                    "listen_repeat_all",
                    "vocab_drill",
                    "pronunciation",
                    "listen_fill",
                ):
                    if len(phrases) == 1 and glued(phrases[0]) and not blanks:
                        rows.append(
                            {
                                "lesson": path.stem,
                                "id": a.get("id"),
                                "mode": mode,
                                "kind": kind,
                                "label": lab,
                                "severity": phrases[0][:120],
                                "severity_len": len(phrases[0]),
                            }
                        )
                # grammar_form still repeat with a glued phrase among many
                if ("katachi" in lab or kind == "grammar_form") and mode in (
                    "listen_repeat",
                    "listen_repeat_all",
                ):
                    bad = [p for p in phrases if glued(p) and len(p) >= 28]
                    if bad:
                        rows.append(
                            {
                                "lesson": path.stem,
                                "id": a.get("id"),
                                "mode": mode,
                                "kind": kind,
                                "label": lab,
                                "severity": bad[0][:120],
                                "phrase_len": len(bad[0]),
                                "n": len(phrases),
                                "note": "katachi_has_glued_phrase",
                            }
                        )
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(rows)} remaining -> {OUT}")


if __name__ == "__main__":
    main()
