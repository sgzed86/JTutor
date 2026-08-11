"""Rescan OCR junk: dialog_script / key_phrases glued, EL listen_choose bad labels.

Writes scripts/_still_dirty.json and scripts/_still_dirty_summary.txt.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
OUT = ROOT / "scripts" / "_still_dirty.json"
SUMMARY = ROOT / "scripts" / "_still_dirty_summary.txt"

# Keep in sync with scripts/_audit_bad_choices.py
_LEADING_TRACK = re.compile(
    r"^(?:"
    r"[0-9]{1,2}(?=[\u3040-\u30ff\u4e00-\u9fff])(?![年人日月時分番個目度円ヶカかこ戸階回])"
    r"|よん(?=[\u3040-\u30ff\u4e00-\u9fff])"
    r"|[一二三四](?![年人日月時分番個目度円ヶカかこ戸階回緒季])"
    r")"
)

# Truncated OCR instruction stems (must match as whole-ish phrase, not substring of clean JP).
_EL_TRUNCATED = re.compile(
    r"^(?:"
    r"のどれですか。?"
    r"|人の人が話しています。?"
    r"|それぞれどんな特徴があります。?"
    r"|はとても寒くなります。?"
    r"|何について質問しています。?"
    r"|答えはどうですか。?"
    r"|材料や消費期限などを質問しています。?"
    r"|それについてどう言っています。?"
    r"|どんなことばを使っています。?"
    r"|ています。?"
    r"|をしています。?"
    r"|で天気予報を見ています。?"
    r"|の店への行き方聞いています。?"
    r"|の準備について話しています。?"
    r"|だれが何を持って行きます。?"
    r")$"
)


def glued(p: str) -> bool:
    """Long Japanese with no punctuation — classic OCR mega-string."""
    p = (p or "").strip()
    if len(p) < 22:
        return False
    # repeated OCR token even with spaces
    if re.search(r"(.{2,8})\1{3,}", p):
        return True
    if any(ch in p for ch in "。、？?　 "):
        return False
    # short single-clause lines without 。 are common; require length or multi-predicate
    if len(p) >= 32:
        return True
    preds = p.count("です") + p.count("ます") + p.count("ください") + p.count("ですか")
    return preds >= 2


def bad_label(lab: str) -> bool:
    p = (lab or "").strip()
    if not p:
        return True
    if len(p) >= 40 and not any(ch in p for ch in "。、？?　 "):
        return True
    if _LEADING_TRACK.match(p) and len(p) >= 10:
        return True
    if "???" in p:
        return True
    if len(p) >= 20 and sum(1 for ch in p if ch in "GH") >= 2 and re.search(r"[0-9]G", p):
        return True
    if len(p) >= 25 and not any(ch in p for ch in "。、？?　，") and (
        p.count("です") + p.count("ます") + p.count("ください") >= 2
    ):
        return True
    # repeated token OCR (私は私は私は / 同様に同様に)
    if re.search(r"(.{2,6})\1{3,}", p):
        return True
    return False


def el_choose_dirty(act: dict) -> str | None:
    phrases = [str(p).strip() for p in (act.get("key_phrases") or []) if p]
    choices = act.get("choices") or []
    for p in phrases:
        if bad_label(p):
            return p[:80]
    for c in choices:
        lab = str(c.get("label_jp") or "").strip()
        if bad_label(lab):
            return lab[:80]
    # leftover scaffolding: choose_mode all + truncated instruction stems as "correct"
    # (only when corrects themselves are mostly truncated stems — avoids flagging
    #  every EL listen_choose that still has a distractor with OCR leftovers)
    if (act.get("choose_mode") or "") == "all":
        corrects = set(act.get("correct_ids") or [])
        if len(corrects) >= 3:
            stem_hits = []
            for c in choices:
                if c.get("id") not in corrects:
                    continue
                lab = str(c.get("label_jp") or "").strip()
                if _EL_TRUNCATED.match(lab):
                    stem_hits.append(lab)
            if len(stem_hits) >= 2:
                return stem_hits[0][:80]
    if not (act.get("correct_ids") or []):
        return "(no correct_ids)"
    return None


def scan() -> list[dict]:
    rows: list[dict] = []
    for path in sorted((CONTENT / "starter").glob("L*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for a in data.get("activities") or []:
            if (a.get("book_mode") or "") != "dialog":
                continue
            lid, aid = path.stem, a.get("id")
            for turn in a.get("dialog_script") or []:
                jp = str(turn.get("jp") or "")
                if glued(jp) or bad_label(jp):
                    rows.append({"type": "dialog", "lesson": lid, "id": aid, "jp": jp[:120]})
                    break
            for p in a.get("key_phrases") or []:
                jp = str(p or "")
                if glued(jp) or bad_label(jp):
                    rows.append({"type": "dialog_phrase", "lesson": lid, "id": aid, "jp": jp[:120]})
                    break

    for path in sorted((CONTENT / "elementary1").glob("EL*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for a in data.get("activities") or []:
            if (a.get("book_mode") or "") != "listen_choose":
                continue
            sample = el_choose_dirty(a)
            if sample:
                rows.append(
                    {
                        "type": "el_choose",
                        "lesson": path.stem,
                        "id": a.get("id"),
                        "jp": sample,
                    }
                )
    return rows


def main() -> int:
    rows = scan()
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = Counter(r["type"] for r in rows)
    lines = [
        f"total: {len(rows)}",
        f"by_type: {dict(counts)}",
        "",
        "ids:",
    ]
    for r in rows:
        lines.append(f"  {r['type']} {r['lesson']} {r['id']}: {r['jp'][:60]}")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(rows)} dirty -> {OUT}")
    print(dict(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
