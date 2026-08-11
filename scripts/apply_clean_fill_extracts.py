"""Apply only fully-resolved, clean PDF fill blanks (surgical YAML edits)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import extract_fill_blanks as ex  # noqa: E402


def _q(text: str) -> str:
    text = str(text)
    if any(ch in text for ch in ":#{}[],&*!|>%@`'\"\n") or text[:1] in "-?" or text.isdigit():
        return yaml.dump(text, allow_unicode=True, default_style='"').strip()
    return text


def dump_blanks(blanks: list[dict], pdf_page: int) -> str:
    lines = ["  blanks:"]
    for b in blanks:
        lines.append(f"  - prompt_jp: {_q(b['prompt_jp'])}")
        lines.append("    answers:")
        for a in b.get("answers") or []:
            lines.append(f"    - {_q(a)}")
        alts = b.get("answer_alts") or []
        if alts:
            lines.append("    answer_alts:")
            for a in alts:
                lines.append(f"    - {_q(a)}")
        if b.get("full_jp"):
            lines.append(f"    full_jp: {_q(b['full_jp'])}")
    lines.append(f"  fill_pdf_page: {pdf_page}")
    return "\n".join(lines) + "\n"


def patch_activity(text: str, act_id: str, blanks_block: str) -> str:
    m = re.search(rf"(?m)^- id: {re.escape(act_id)}\s*$", text)
    if not m:
        raise KeyError(act_id)
    start = m.start()
    rest = text[start + 1 :]
    nxt = re.search(r"(?m)^- id: ", rest)
    end = start + 1 + (nxt.start() if nxt else len(rest))
    chunk = text[start:end]
    if re.search(r"(?m)^  book_mode:", chunk):
        chunk = re.sub(r"(?m)^  book_mode:.*$", "  book_mode: listen_fill", chunk, count=1)
    else:
        chunk = chunk.rstrip() + "\n  book_mode: listen_fill\n"
    if re.search(r"(?m)^  prompt_en:", chunk):
        chunk = re.sub(
            r"(?m)^  prompt_en:.*$",
            "  prompt_en: Listen to the recording and fill in the blanks.",
            chunk,
            count=1,
        )
    chunk = re.sub(r"(?ms)^  blanks:.*?(?=^  [a-z_]+:|\Z)", "", chunk)
    chunk = re.sub(r"(?m)^  fill_pdf_page:.*\n?", "", chunk)
    chunk = chunk.rstrip() + "\n" + blanks_block
    if not chunk.endswith("\n"):
        chunk += "\n"
    return text[:start] + chunk + text[end:]


def enrich(item: dict) -> dict:
    if item.get("answers") == ["何歳"]:
        item["answer_alts"] = list(
            dict.fromkeys((item.get("answer_alts") or []) + ["何歳ですか", "なんさい"])
        )
    if item.get("answers") == ["いくつ"]:
        item["answer_alts"] = list(
            dict.fromkeys((item.get("answer_alts") or []) + ["いくつですか"])
        )
    if item.get("answers") == ["ちょっと"]:
        item["answer_alts"] = list(
            dict.fromkeys((item.get("answer_alts") or []) + ["ちょっと…", "ちょっと……"])
        )
    return item


def main() -> int:
    total = 0
    for book in ("starter", "elementary1"):
        cfg = ex.BOOKS[book]
        originals: dict[Path, str] = {}
        for path in sorted(cfg["dir"].glob(cfg["glob"])):
            if "phrase" in path.name:
                continue
            originals[path] = path.read_text(encoding="utf-8")

        transcripts = ex.load_transcripts(book)
        doc = ex.pymupdf.open(cfg["pdf"])
        texts = dict(originals)

        for page in range(1, doc.page_count + 1):
            pdf_text = doc[page - 1].get_text()
            if ex.FILL_EN not in pdf_text:
                continue
            prompts = ex.rebuild_fill_chunk(pdf_text)
            if not prompts:
                continue
            tracks = ex.track_ids(pdf_text)
            lesson_data = [(p, yaml.safe_load(texts[p]) or {}) for p in texts]
            loc = ex.lesson_for_page(lesson_data, page)
            if not loc:
                continue
            path, lesson = loc
            act = ex.find_activity_for_tracks(lesson, tracks)
            if not act:
                continue
            existing = act.get("blanks") or []
            if (
                existing
                and not ex._is_heuristic_blanks(existing)
                and len(existing) >= len(prompts)
            ):
                continue

            corpus = ex.dialog_corpus(doc, page)
            phrases = list(
                dict.fromkeys(
                    ex.phrases_from_transcripts(transcripts, tracks)
                    + list(act.get("key_phrases") or [])
                )
            )
            blanks: list[dict] = []
            unresolved = 0
            for prompt in prompts:
                item = ex.resolve_line(prompt, corpus, phrases)
                if item and all(ex._good_answer(a) for a in item["answers"]):
                    blanks.append(enrich(item))
                else:
                    unresolved += 1
            if unresolved or len(blanks) != len(prompts):
                print(
                    f"[{book}] {lesson.get('lesson_id')} {act.get('id')} p.{page}: "
                    f"skip ({len(blanks)}/{len(prompts)}, miss={unresolved})"
                )
                continue
            texts[path] = patch_activity(texts[path], act["id"], dump_blanks(blanks, page))
            total += 1
            print(
                f"[{book}] {lesson.get('lesson_id')} {act.get('id')} p.{page}: "
                f"{len(blanks)} blanks — "
                + "; ".join(f"{b['prompt_jp']}⇒{b['answers']}" for b in blanks)
            )

        for path, new_text in texts.items():
            if new_text != originals[path]:
                path.write_text(new_text, encoding="utf-8")
                print(f"wrote {path.name}")
    print(f"updated {total} fill activities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
