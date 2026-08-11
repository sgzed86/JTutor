"""Rewrite quiz_scenarios in starter + elementary1 lesson YAML from curated catalogs."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from roleplay_catalog_elementary1 import ELEMENTARY1  # noqa: E402
from roleplay_catalog_starter import STARTER  # noqa: E402

CATALOG = {**STARTER, **ELEMENTARY1}
WEAK = {
    "では、お願いします。",
    "もう一度、お願いします。",
    "ちち。",
    "ちちです。",
}


def dump_scenarios(scenarios: list[dict]) -> str:
    lines = [
        "quiz_scenarios:",
        "# Real role-plays for Can-do checks (LLM-judged; expected = fallback examples).",
    ]
    for s in scenarios:
        lines.append(f"- can_do_id: {s['can_do_id']}")
        lines.append(f"  setup_en: {_yaml_str(s['setup_en'])}")
        lines.append(f"  goal_en: {_yaml_str(s['goal_en'])}")
        lines.append(f"  partner_jp: {_yaml_str(s['partner_jp'])}")
        lines.append("  expected:")
        for e in s.get("expected") or []:
            # Always quote — bare 1/10 would parse as ints and break grading.
            lines.append(f"  - {_yaml_str(str(e), force_quote=True)}")
        hint = s.get("hint_en") or s.get("setup_en")
        if hint:
            lines.append(f"  hint_en: {_yaml_str(hint)}")
    return "\n".join(lines) + "\n"


def _yaml_str(value: str, *, force_quote: bool = False) -> str:
    """Quote when needed for safe YAML scalars."""
    text = str(value)
    if force_quote or any(ch in text for ch in ":#{}[],&*!|>%@`'\"\n") or text[:1] in "-?" or text.isdigit():
        return yaml.dump(text, allow_unicode=True, default_style='"').strip()
    return text


def scenarios_for_lesson(can_dos: list[dict]) -> list[dict]:
    out: list[dict] = []
    missing: list[str] = []
    for cd in can_dos:
        cid = cd["id"]
        items = CATALOG.get(cid)
        if not items:
            missing.append(cid)
            # Minimal fallback so every can-do still gets a role-play shell.
            stmt = (cd.get("statement_en") or "").strip()
            must = list((cd.get("rubric") or {}).get("must_include") or [])
            items = [
                {
                    "setup_en": f"Role-play — show that you can: {stmt}",
                    "goal_en": f"Learner demonstrates: {stmt}",
                    "partner_jp": "じゃあ、やってみましょう。",
                    "expected": must or ["です"],
                }
            ]
        for item in items:
            row = {
                "can_do_id": cid,
                "setup_en": item["setup_en"],
                "goal_en": item["goal_en"],
                "partner_jp": item["partner_jp"],
                "expected": list(item.get("expected") or []),
                "hint_en": item.get("hint_en") or item["setup_en"],
            }
            out.append(row)
    return out, missing


def replace_quiz_block(text: str, new_block: str) -> str:
    marker = "quiz_scenarios:"
    start = text.find(marker)
    if start < 0:
        # Insert before english_notes if present, else append.
        en = text.find("\nenglish_notes:")
        if en >= 0:
            return text[:en] + "\n" + new_block + text[en + 1 :]
        return text.rstrip() + "\n\n" + new_block
    # End at next top-level mapping key (e.g. english_notes:), not list items.
    rest = text[start:]
    end_rel = None
    for i, line in enumerate(rest.splitlines(keepends=True)):
        if i == 0:
            continue
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        # Top-level key: no indent, starts with identifier + colon (not "- ").
        if line[0].isspace():
            continue
        if stripped.startswith("-"):
            continue
        if ":" in stripped.split()[0] or (stripped.split(":", 1)[0].replace("_", "").isalnum() and ":" in stripped):
            end_rel = sum(len(x) for x in rest.splitlines(keepends=True)[:i])
            break
    if end_rel is None:
        return text[:start] + new_block
    return text[:start] + new_block + rest[end_rel:]


def main() -> None:
    paths = sorted((ROOT / "content" / "starter").glob("L*.yaml")) + sorted(
        (ROOT / "content" / "elementary1").glob("EL*.yaml")
    )
    # Skip phrase reference / index helpers
    paths = [p for p in paths if p.stem in {f"L{n:02d}" for n in range(1, 19)} | {f"EL{n:02d}" for n in range(1, 19)}]

    all_missing: list[str] = []
    updated = 0
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        can_dos = data.get("can_dos") or []
        if not can_dos:
            continue
        scenarios, missing = scenarios_for_lesson(can_dos)
        all_missing.extend(missing)
        block = dump_scenarios(scenarios)
        new_text = replace_quiz_block(raw, block)
        if new_text != raw:
            path.write_text(new_text, encoding="utf-8")
            updated += 1
            print(f"updated {path.name}: {len(scenarios)} scenarios")
        else:
            print(f"unchanged {path.name}")

        # Validate parse
        check = yaml.safe_load(path.read_text(encoding="utf-8"))
        qs = check.get("quiz_scenarios") or []
        assert qs, path
        assert all(s.get("setup_en") and s.get("goal_en") for s in qs), path
        assert all((s.get("partner_jp") or "") not in WEAK for s in qs), path

    if all_missing:
        print("MISSING CATALOG ENTRIES (used fallback):")
        for m in all_missing:
            print(" ", m)
        raise SystemExit(1)
    print(f"done — {updated} files, catalog size {len(CATALOG)}")


if __name__ == "__main__":
    main()
