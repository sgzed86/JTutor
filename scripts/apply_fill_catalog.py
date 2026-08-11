"""Apply curated starter fill blanks + demote OCR junk."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_clean_fill_extracts import dump_blanks, patch_activity  # noqa: E402
from demote_heuristic_fills import _replace_mode_in_text  # noqa: E402
from fill_catalog_starter import DEMOTE, FILL_CATALOG  # noqa: E402


def main() -> int:
    for (lid, aid), (page, blanks) in FILL_CATALOG.items():
        path = ROOT / "content" / "starter" / f"{lid}.yaml"
        text = path.read_text(encoding="utf-8")
        # Ensure activity exists and is fill-capable
        data = yaml.safe_load(text)
        act = next((a for a in data.get("activities") or [] if a.get("id") == aid), None)
        if act is None:
            print(f"missing {lid} {aid}")
            continue
        block = dump_blanks(blanks, page)
        text = patch_activity(text, aid, block)
        path.write_text(text, encoding="utf-8")
        print(f"curated {lid} {aid}: {len(blanks)} blanks p.{page}")

    for lid, aid in DEMOTE:
        path = ROOT / "content" / "starter" / f"{lid}.yaml"
        text = path.read_text(encoding="utf-8")
        new = _replace_mode_in_text(text, aid)
        if new is None:
            print(f"demote miss {lid} {aid}")
            continue
        path.write_text(new, encoding="utf-8")
        print(f"demoted {lid} {aid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
