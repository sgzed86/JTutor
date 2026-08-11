"""Find listen_choose activities with OCR / concatenated choice labels."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1] / "content"
OUT = Path(__file__).resolve().parents[1] / "scripts" / "_audit_bad_choices.json"


# Track-number prefixes glued onto Japanese (OCR like "2あのー", "よんすみません").
# Do NOT use bare ご/ろく — they start normal words (ご案内, ろくに).
# Require the next char to be Japanese so "14番"/"100円" don't match via digit backtracking.
_LEADING_TRACK = re.compile(
    r"^(?:"
    r"[0-9]{1,2}(?=[\u3040-\u30ff\u4e00-\u9fff])(?![年人日月時分番個目度円ヶカかこ戸階])"
    r"|よん(?=[\u3040-\u30ff\u4e00-\u9fff])"
    # 一/二/三/四 as OCR track nums — not real words like 一年中 / 四季 / 二階
    r"|[一二三四](?![年人日月時分番個目度円ヶカかこ戸階季五六七八九十])"
    r")"
)


def bad_label(lab: str) -> bool:
    p = (lab or "").strip()
    if not p:
        return True
    if len(p) >= 40 and not any(ch in p for ch in "。、？?　 "):
        return True
    # leading track numbers glued on (avoid 一年中 / 一戸建て / 14番 / 100円 / よかったら)
    if _LEADING_TRACK.match(p) and len(p) >= 12:
        return True
    # OCR garbage markers (Latin track crumbs like "13G…", not ビル)
    junk = ("???",)
    if any(x in p for x in junk):
        return True
    if len(p) >= 20 and sum(1 for ch in p if ch in "GH") >= 2 and re.search(r"[0-9]G", p):
        return True
    # common OCR mishits glued without punctuation
    if len(p) >= 25 and not any(ch in p for ch in "。、？?　、，") and (
        p.count("です") + p.count("ます") + p.count("ください") >= 2
    ):
        return True
    return False


def main() -> None:
    rows = []
    for book in ("starter", "elementary1"):
        for path in sorted((ROOT / book).glob("*.yaml")):
            if "phrase" in path.name or path.name == "index.yaml":
                continue
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for a in data.get("activities") or []:
                if (a.get("book_mode") or "") != "listen_choose":
                    continue
                choices = a.get("choices") or []
                bad = []
                for c in choices:
                    lab = str(c.get("label_jp") or "")
                    if bad_label(lab):
                        bad.append({"id": c.get("id"), "label_jp": lab[:100]})
                if not bad and not (a.get("correct_ids") or []):
                    bad.append({"id": "?", "label_jp": "(no correct_ids)"})
                # also flag if key_phrases themselves are OCR mega
                phrases = [p for p in (a.get("key_phrases") or []) if p]
                phrase_bad = any(bad_label(p) for p in phrases)
                if bad or phrase_bad:
                    rows.append(
                        {
                            "book": book,
                            "lesson": path.stem,
                            "id": a.get("id"),
                            "label": a.get("label"),
                            "audio": (a.get("audio") or [None])[0],
                            "phrases": [str(p)[:80] for p in phrases[:4]],
                            "bad_choices": bad[:8],
                            "n_choices": len(choices),
                            "correct_ids": a.get("correct_ids") or [],
                            "choose_mode": a.get("choose_mode"),
                            "phrase_bad": phrase_bad,
                        }
                    )
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(rows)} activities -> {OUT}")


if __name__ == "__main__":
    main()
