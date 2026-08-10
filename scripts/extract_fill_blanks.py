"""Extract textbook fill-in-the-blank worksheets into lesson YAML.

Finds pages with \"Listen to the recording and fill in the blanks\", rebuilds the
blanked lines (ideographic spaces → ＿), recovers answers from nearby dialog
pages / activity key_phrases, and attaches them to the matching activity via
the CD track id in the PDF footer (e.g. 04-09 → X_[04-09]_…).

Replaces heuristic です/ます ending blanks that did not match the book.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pymupdf
import yaml

ROOT = Path(__file__).resolve().parents[1]

BOOKS = {
    "starter": {
        "pdf": ROOT / "assets" / "irodori_starter.pdf",
        "dir": ROOT / "content" / "starter",
        "glob": "L*.yaml",
    },
    "elementary1": {
        "pdf": ROOT / "assets" / "Elementary1.pdf",
        "dir": ROOT / "content" / "elementary1",
        "glob": "EL*.yaml",
    },
}

FILL_EN = "Listen to the recording and fill in the blanks"
STOP_MARKERS = (
    "Focus on the expressions used",
    "What expression was used",
    "What expressions were used",
    "文法ノート",
    "文\n法",
)


def _is_kana(s: str) -> bool:
    return bool(re.fullmatch(r"[ぁ-んァ-ンー（）()〜～・]+", s or ""))


def _has_kanji(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))


def _norm(s: str) -> str:
    s = (s or "").replace("\u3000", "").replace(" ", "").replace("\t", "")
    s = s.replace("？", "?").replace("！", "!")
    return s


def strip_speaker(s: str) -> str:
    # Do not use \\s after the marker — it would swallow ideographic-space blanks.
    return re.sub(r"^[ＡＢABａｂ][:：\t]+", "", (s or "").lstrip(" \t"))


def rebuild_fill_chunk(text: str) -> list[str]:
    """Return worksheet lines after the English prompt, ruby-stripped, blanks as ＿."""
    start = text.find(FILL_EN)
    if start < 0:
        return []
    # Cut worksheet before grammar-note / part (2) chrome — not only English markers.
    early_stops = (
        "What expression",
        "What expressions",
        "Focus on the expressions",
        "年齢を質問",
        "好きなものを言",
        "（2 ）",
        "(2 )",
        "（2）",
    )
    chunk = text[start + len(FILL_EN) :]
    for m in list(STOP_MARKERS) + list(early_stops):
        idx = chunk.find(m)
        if idx >= 0:
            chunk = chunk[:idx]
            break

    buf = ""
    lines: list[str] = []
    for raw in chunk.splitlines():
        # Keep ideographic spaces — those are the blanks. Only trim ASCII whitespace.
        ln = raw.strip(" \t\r\n")
        if not ln or ln == "\u3000" * len(ln) and len(ln) < 2:
            # pure blank spacer lines — keep if they are blank markers between parts? skip
            if ln.count("\u3000") >= 2 and buf:
                buf += ln
            continue
        if ln.startswith("©") or "Japan Foundation" in ln:
            continue
        if re.fullmatch(r"\d{2}-\d{2}", ln.strip()):
            break
        if any(ln.lstrip("\u3000").startswith(x) for x in ("（2", "(2", "形", "Focus on")):
            break
        if _is_kana(ln.strip("\u3000")):
            continue
        bare = ln.lstrip(".\u3000 　").strip()
        if bare in {"2", "1", "漢"}:
            continue
        buf += ln
        endswith = ln.rstrip("\u3000 \t")
        if endswith.endswith(("。", "？", "?", "！", "!")) or (
            "／" in ln and endswith.endswith(("？", "?"))
        ):
            lines.append(buf)
            buf = ""
    if buf.strip("\u3000 \t"):
        lines.append(buf)

    out: list[str] = []
    for ln in lines:
        ln = strip_speaker(ln)
        # Drop leading page-fragment junk like "." (but keep digits that are part of answers, e.g. 4＿です)
        ln = re.sub(r"^\.+", "", ln)
        ln = re.sub(r"^［.*?］", "", ln)
        # Ideographic / regular space runs → blank marker
        ln = re.sub(r"[\u3000 ]{2,}", "＿", ln)
        ln = re.sub(r"＿+", "＿", ln)
        ln = ln.replace("\t", "")
        if "＿" not in ln:
            continue
        if len(re.sub(r"＿", "", ln)) < 1:
            continue
        out.append(ln)
    return out


def track_ids(text: str) -> list[str]:
    """CD track ids after the fill prompt (footer), de-duplicated preserving order."""
    start = text.find(FILL_EN)
    region = text[start:] if start >= 0 else text
    found = re.findall(r"\b(\d{2}-\d{2})\b", region)
    out: list[str] = []
    for t in found:
        if t not in out:
            out.append(t)
    return out


def dialog_corpus(doc: pymupdf.Document, page: int, back: int = 3) -> list[str]:
    """Collect ruby-stripped dialog-ish lines from nearby pages."""
    lines: list[str] = []
    for p in range(max(1, page - back), page):
        text = doc[p - 1].get_text()
        # Split roughly on speaker turns
        parts = re.split(r"(?=\n?[^\n：:]{1,16}[：:])", text)
        for part in parts:
            buf = ""
            for raw in part.splitlines():
                ln = raw.strip(" \t\r\n")
                if not ln or _is_kana(ln.strip("\u3000")):
                    continue
                if ln.startswith("©") or "Japan Foundation" in ln:
                    continue
                if re.match(r"^[^\u3040-\u30ff\u4e00-\u9fff]*$", ln) and "Listen" in ln:
                    continue
                buf += ln
                if ln.rstrip("\u3000 ").endswith(("。", "？", "?", "！", "!")):
                    cleaned = strip_speaker(buf.replace("\t", ""))
                    cleaned = re.sub(r"[\u3000 ]+", "", cleaned)
                    # Drop speaker name prefixes like ミロ： / 上田（父）：
                    cleaned = re.sub(r"^[^。？?]{0,16}：", "", cleaned)
                    if cleaned and len(cleaned) <= 60:
                        lines.append(cleaned)
                    buf = ""
            if buf.strip("\u3000 "):
                cleaned = strip_speaker(re.sub(r"[\u3000\t ]+", "", buf))
                cleaned = re.sub(r"^[^。？?]{0,16}：", "", cleaned)
                if cleaned and len(cleaned) <= 60:
                    lines.append(cleaned)
    seen: set[str] = set()
    out: list[str] = []
    for ln in lines:
        n = _norm(ln)
        if not n or n in seen or len(n) < 2:
            continue
        if not (_has_kanji(ln) or re.search(r"[ぁ-ん]", ln)):
            continue
        seen.add(n)
        out.append(ln)
    return out


def extract_between(full: str, parts: list[str]) -> list[str] | None:
    """If `full` is parts[0] + a0 + parts[1] + a1 + …, return the a_i answers."""
    if not parts:
        return None
    pos = 0
    answers: list[str] = []
    f = full
    for i, part in enumerate(parts):
        if part == "":
            if i == 0:
                continue
            # empty part between blanks — shouldn't happen after split
            continue
        idx = f.find(part, pos)
        if idx < 0:
            # try normalized loose match
            return None
        if i == 0 and idx > 0 and parts[0] != "":
            # leading material before first fixed part — only ok if part is first non-empty
            if parts[0]:
                # allow speaker leftovers already stripped
                pass
        if i > 0 or (i == 0 and parts[0] == ""):
            # answer is f[pos:idx]
            ans = f[pos:idx]
            answers.append(ans)
        pos = idx + len(part)
    if parts[-1] == "" or (len(parts) > 1 and full.endswith(parts[-1]) is False):
        # trailing blank
        if len(answers) < len(parts) - 1:
            answers.append(f[pos:])
    elif pos < len(f) and f[pos:]:
        # trailing leftover after last part — not a blank
        pass
    # Expected answer count = number of ＿ = len(parts)-1
    need = len(parts) - 1
    if len(answers) != need:
        # Leading blank case: parts[0]==''
        if parts and parts[0] == "":
            # re-parse
            answers = []
            pos = 0
            # full = a0 + parts[1] + a1 + parts[2] + ...
            rest = f
            ok = True
            for i in range(1, len(parts)):
                part = parts[i]
                if part == "":
                    if i == len(parts) - 1:
                        answers.append(rest)
                    continue
                idx = rest.find(part)
                if idx < 0:
                    ok = False
                    break
                answers.append(rest[:idx])
                rest = rest[idx + len(part) :]
            if ok and len(answers) == need:
                return [a for a in answers]
            return None
        return None
    return answers


def _norm_loose(s: str) -> str:
    return _norm(re.sub(r"[。？?！!]+$", "", s or ""))


def _match_slots(prompt: str, candidate: str) -> list[str] | None:
    """Return answers if candidate fills prompt's ＿ slots structurally."""
    parts = re.split(r"＿+", prompt)
    need = len(parts) - 1
    if need < 1:
        return None
    c = _norm(candidate)
    # Build regex: escape fixed parts (loose punct), capture blanks
    pieces: list[str] = []
    for i, part in enumerate(parts):
        if i > 0:
            pieces.append("(.+?)")
        p = _norm_loose(part) if part else ""
        if part and not p and part.strip("。？?！!"):
            p = _norm(part)
        if i == len(parts) - 1 and part and _norm(part) in {"。", "？", "?", "！", "!"}:
            # trailing punct optional
            pieces.append(r"[。？?！!]*")
        elif p:
            pieces.append(re.escape(p))
            if i == len(parts) - 1:
                pieces.append(r"[。？?！!]*")
        elif i == 0 and part == "":
            pass
    pat = "^" + "".join(pieces) + "$"
    m = re.match(pat, _norm_loose(candidate) if need else c)
    # Also try on fully normalized candidate including punct stripped
    if not m:
        m = re.match(pat, _norm_loose(c))
    if not m:
        # try original compact with optional punct
        m = re.match(pat, c)
    if not m:
        return None
    answers = [g for g in m.groups()]
    if len(answers) != need:
        return None
    if any(not a or len(a) > 40 for a in answers):
        return None
    return answers


def _good_answer(a: str) -> bool:
    a = (a or "").strip()
    if not a or len(a) > 16:
        return False
    if re.search(r"[A-Za-z]{3,}", a):
        return False
    if any(x in a for x in ("入門", "トピック", "第課", "Listen", "Focus")):
        return False
    return True


def resolve_line(prompt: str, corpus: list[str], phrases: list[str]) -> dict | None:
    """Build a blank item with answers for one worksheet line."""
    prompt = strip_speaker(prompt.strip())
    prompt = re.sub(r"^[ＡＢ]：\s*", "", prompt).strip()
    if "＿" not in prompt:
        return None
    need = prompt.count("＿")

    # Special: two questions joined with ／ — resolve with disjoint phrase picks
    if "／" in prompt and need >= 2:
        left, right = prompt.split("／", 1)
        if "＿" in left and "＿" in right:
            l = resolve_line(left, corpus, phrases)
            used = set(l["answers"]) if l else set()
            right_phrases = [p for p in phrases if not any(u in p for u in used)] or phrases
            r = resolve_line(right, corpus, right_phrases)
            if l and r:
                if l["answers"] == r["answers"] and len(phrases) >= 2:
                    for p in phrases:
                        alt = _match_slots(right, p)
                        if alt and alt != l["answers"] and all(_good_answer(x) for x in alt):
                            r = {
                                "prompt_jp": right,
                                "answers": alt,
                                "full_jp": _fill(right, alt),
                            }
                            break
                if all(_good_answer(x) for x in l["answers"] + r["answers"]):
                    return {
                        "prompt_jp": prompt,
                        "answers": list(l["answers"]) + list(r["answers"]),
                        "full_jp": f"{l['full_jp']}／{r['full_jp']}",
                    }

    # Prefer short dialog/phrase candidates so blanks get 歳 not a whole sentence.
    pool = list(dict.fromkeys(list(phrases) + list(corpus)))
    pool.sort(key=lambda s: (len(_norm(s)), s))
    windows = _blank_windows(prompt)

    best: dict | None = None
    best_score = -10**9
    phrase_blob = " ".join(phrases)

    def score(answers: list[str]) -> int:
        s = 0
        for a in answers:
            if a in phrase_blob:
                s += 20
            elif any(a in p for p in phrases):
                s += 20
            if a in {"そう", "はい", "いいえ", "ええ", "うん", "まあ"}:
                s -= 80
            # Mild preference for compact worksheet answers
            s -= len(a)
        return s

    for cand in pool:
        for window in windows:
            answers = _match_slots(window, cand)
            if answers is None:
                continue
            if len(answers) != need:
                continue
            if not all(_good_answer(a) for a in answers):
                continue
            sc = score(answers)
            # Phrase candidates get a boost
            if cand in phrases:
                sc += 5
            if sc > best_score:
                best_score = sc
                best = {
                    "prompt_jp": prompt,
                    "answers": answers,
                    "full_jp": _fill(prompt, answers),
                }
    return best


def _blank_windows(prompt: str) -> list[str]:
    out = [prompt]
    idxs = [i for i, ch in enumerate(prompt) if ch == "＿"]
    if not idxs:
        return out
    before = prompt[: idxs[0]]
    start = 0
    for sep in ("。", "、", "：", ":", "？", "?"):
        p = before.rfind(sep)
        if p >= start:
            start = p + 1
    local = prompt[start:].lstrip()
    if local and "＿" in local:
        out.append(local)
    tight_start = max(0, idxs[0] - 4)
    out.append(prompt[tight_start:])
    # Drop windows with no fixed Japanese context (＿？ alone matches anything).
    filtered = []
    for x in out:
        fixed = re.sub(r"[＿。？?！!\s]+", "", x)
        if fixed:
            filtered.append(x)
    return list(dict.fromkeys(filtered))

def _fill(prompt: str, answers: list[str]) -> str:
    parts = re.split(r"＿+", prompt)
    out = parts[0]
    for i, ans in enumerate(answers):
        out += ans
        if i + 1 < len(parts):
            out += parts[i + 1]
    return out


def activity_tracks(act: dict) -> set[str]:
    found: set[str] = set()
    for a in act.get("audio") or []:
        found.update(re.findall(r"(\d{2}-\d{2})", str(a)))
    return found


def find_activity_for_tracks(lesson: dict, tracks: list[str]) -> dict | None:
    """Pick the activity whose audio matches a fill-related track on the page."""
    if not tracks:
        return None
    acts = list(lesson.get("activities") or [])

    def score(act: dict) -> int:
        mode = (act.get("book_mode") or "").strip()
        kind = (act.get("kind") or "").strip()
        label = (act.get("label") or "").lower()
        s = 0
        if mode == "listen_fill" or act.get("blanks"):
            s += 5
        if kind == "grammar_form" or "katachi" in label:
            s += 4
        if "kiku" in label or kind == "listening":
            s += 1
        return s

    best = None
    best_score = -1
    for tr in tracks:
        for act in acts:
            if tr not in activity_tracks(act):
                continue
            sc = score(act)
            # Prefer earlier tracks slightly
            sc += max(0, 3 - tracks.index(tr))
            if sc > best_score:
                best_score = sc
                best = act
        if best and best_score >= 4:
            return best
    return best


def lesson_for_page(lessons: list[tuple[Path, dict]], page: int) -> tuple[Path, dict] | None:
    for path, data in lessons:
        pages = data.get("pdf_pages") or []
        if len(pages) >= 2 and int(pages[0]) <= page <= int(pages[1]):
            return path, data
    return None


def apply_blanks(act: dict, blanks: list[dict], pdf_page: int) -> None:
    act["blanks"] = blanks
    act["book_mode"] = "listen_fill"
    act["prompt_en"] = "Listen to the recording and fill in the blanks."
    act["fill_pdf_page"] = pdf_page
    # Prefer key_phrases from full answers for TTS / notes
    phrases = []
    for b in blanks:
        full = (b.get("full_jp") or "").strip()
        if full and full not in phrases:
            phrases.append(full)
        for a in b.get("answers") or []:
            if a and a not in phrases and len(str(a)) >= 2:
                pass
    if phrases:
        # Keep existing key_phrases if richer; else set from blanks
        existing = [p for p in (act.get("key_phrases") or []) if p]
        if len(existing) < len(phrases):
            act["key_phrases"] = phrases


def process_book(book: str, *, dry_run: bool, force: bool) -> int:
    cfg = BOOKS[book]
    pdf = cfg["pdf"]
    if not pdf.is_file():
        raise SystemExit(f"missing PDF: {pdf}")

    lessons: list[tuple[Path, dict]] = []
    for path in sorted(cfg["dir"].glob(cfg["glob"])):
        if "phrase" in path.name:
            continue
        lessons.append((path, yaml.safe_load(path.read_text(encoding="utf-8")) or {}))

    doc = pymupdf.open(pdf)
    updated = 0
    touched_paths: set[Path] = set()

    for page in range(1, doc.page_count + 1):
        text = doc[page - 1].get_text()
        if FILL_EN not in text:
            continue
        prompts = rebuild_fill_chunk(text)
        if not prompts:
            print(f"[{book}] p.{page}: no blank lines parsed")
            continue
        tracks = track_ids(text)
        loc = lesson_for_page(lessons, page)
        if not loc:
            print(f"[{book}] p.{page}: no lesson for page — {prompts[:2]}")
            continue
        path, lesson = loc
        act = find_activity_for_tracks(lesson, tracks)
        if not act:
            # Fallback: grammar_form / katachi near this page's activity number
            print(f"[{book}] p.{page}: no activity for tracks {tracks} prompts={prompts}")
            continue
        if act.get("blanks") and not force:
            answers = [a for b in act["blanks"] for a in (b.get("answers") or [])]
            heuristic = bool(answers) and set(answers) <= {
                "です", "ます", "でした", "ですね", "ね", "ください", "お願いします", "おねがいします",
            }
            if not heuristic:
                print(
                    f"[{book}] {lesson.get('lesson_id')} {act.get('id')} p.{page}: "
                    f"keep existing blanks ({len(act['blanks'])})"
                )
                continue

        corpus = dialog_corpus(doc, page)
        phrases = [p for p in (act.get("key_phrases") or []) if p]
        blanks: list[dict] = []
        unresolved = 0
        for prompt in prompts:
            item = resolve_line(prompt, corpus, phrases)
            if item:
                blanks.append(item)
            else:
                unresolved += 1
                print(f"  ! unresolved: {prompt}")
        if len(blanks) < max(1, (len(prompts) + 1) // 2):
            print(
                f"[{book}] {lesson.get('lesson_id')} {act.get('id')} p.{page}: "
                f"skip weak extract ({len(blanks)} ok / {unresolved} miss / {len(prompts)} lines)"
            )
            continue
        existing = act.get("blanks") or []
        if existing and len(blanks) < len(existing):
            old_ans = [a for b in existing for a in (b.get("answers") or [])]
            if old_ans and not (
                set(old_ans)
                <= {"です", "ます", "でした", "ですね", "ね", "ください", "お願いします", "おねがいします"}
            ):
                print(
                    f"[{book}] {lesson.get('lesson_id')} {act.get('id')} p.{page}: "
                    f"keep stronger existing ({len(existing)} > {len(blanks)})"
                )
                continue
        # Add common alts for short age questions
        for b in blanks:
            if b.get("answers") == ["何歳"]:
                b["answer_alts"] = list(
                    dict.fromkeys((b.get("answer_alts") or []) + ["何歳ですか", "なんさい"])
                )
            if b.get("answers") == ["いくつ"]:
                b["answer_alts"] = list(
                    dict.fromkeys((b.get("answer_alts") or []) + ["いくつですか"])
                )
        print(
            f"[{book}] {lesson.get('lesson_id')} {act.get('id')} p.{page} tracks={tracks[:3]}: "
            f"{len(blanks)} blanks — " + "; ".join(f"{b['prompt_jp']}⇒{b['answers']}" for b in blanks)
        )
        if not dry_run:
            apply_blanks(act, blanks, page)
            touched_paths.add(path)
        updated += 1

    if not dry_run:
        for path, data in lessons:
            if path in touched_paths:
                path.write_text(
                    yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100),
                    encoding="utf-8",
                )
    return updated


def main() -> int:
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", choices=["starter", "elementary1", "all"], default="starter")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="Overwrite even non-heuristic blanks")
    args = ap.parse_args()
    books = list(BOOKS) if args.book == "all" else [args.book]
    total = 0
    for book in books:
        n = process_book(book, dry_run=args.dry_run, force=args.force)
        print(("would update" if args.dry_run else "updated"), n, f"{book} fill activities")
        total += n
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
