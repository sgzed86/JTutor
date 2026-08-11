"""Extract Irodori 「漢字のことば」 sections from textbook PDFs.

Supports Starter (`irodori_starter.pdf`) and Elementary 1 (`Elementary1.pdf`).
Writes `kanji_words` onto each lesson YAML and upserts a `KANJI` activity
(study → read → type) before CULTURE when present.
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
        "min_lesson": 3,  # L1–L2 use kana instead of kanji
        "chrome_prefixes": ("入門", "第"),
    },
    "elementary1": {
        "pdf": ROOT / "assets" / "Elementary1.pdf",
        "dir": ROOT / "content" / "elementary1",
        "glob": "EL*.yaml",
        "min_lesson": 1,
        "chrome_prefixes": ("初級", "第"),
    },
}

# Optional English glosses (Starter + Elementary 1 headwords).
GLOSS: dict[str, str] = {
    "名前": "name",
    "国": "country",
    "私": "I / me",
    "父": "father",
    "母": "mother",
    "子ども": "child / children",
    "日本": "Japan",
    "水": "water",
    "食べます": "to eat",
    "飲みます": "to drink",
    "魚": "fish",
    "肉": "meat",
    "好き": "like",
    "好き（な）": "like (na-adjective)",
    "家": "house / home",
    "新しい": "new",
    "広い": "spacious / wide",
    "古い": "old",
    "上": "above / on",
    "下": "below / under",
    "中": "inside",
    "月": "Monday / month",
    "火": "Tuesday / fire",
    "木": "Thursday / tree",
    "金": "Friday / gold",
    "土": "Saturday / earth",
    "日": "Sunday / day / sun",
    "曜日": "day of the week",
    "朝": "morning",
    "昼": "noon / daytime",
    "夜": "night",
    "時": "o'clock / hour",
    "分": "minute",
    "半": "half",
    "枚": "counter for flat objects",
    "読みます": "to read",
    "本": "book",
    "聞きます": "to listen / ask",
    "友だち": "friend",
    "見ます": "to see / watch",
    "何": "what",
    "年": "year",
    "今日": "today",
    "今週": "this week",
    "今度": "next time / this time",
    "東": "east",
    "西": "west",
    "南": "south",
    "北": "north",
    "来ます": "to come",
    "行きます": "to go",
    "乗ります": "to ride / board",
    "会社": "company",
    "大きい": "big",
    "小さい": "small",
    "高い": "tall / expensive",
    "低い": "low / short",
    "前": "front / before",
    "後ろ": "behind",
    "横": "side",
    "入口": "entrance",
    "出口": "exit",
    "階": "floor / storey",
    "押す": "to push",
    "引く": "to pull",
    "安い": "cheap",
    "一": "one",
    "二": "two",
    "三": "three",
    "四": "four",
    "五": "five",
    "六": "six",
    "七": "seven",
    "八": "eight",
    "九": "nine",
    "十": "ten",
    "千": "thousand",
    "百": "hundred",
    "万": "ten thousand",
    "円": "yen",
    "休み": "holiday / day off",
    "映画": "movie",
    "日本語": "Japanese language",
    "勉強します": "to study",
    "買います": "to buy",
    "温泉": "hot spring",
    "予定": "plans / schedule",
    "来週": "next week",
    "会います": "to meet",
    "入ります": "to enter",
    "旅行します": "to travel",
    # Elementary 1
    "学生": "student",
    "仕事": "work / job",
    "学校": "school",
    "元気": "fine / healthy / energetic",
    "元気（な）": "fine / energetic (na-adjective)",
    "生活": "life / daily life",
    "忙しい": "busy",
    "去年": "last year",
    "働く": "to work",
    "先週": "last week",
    "作る": "to make / grow",
    "人": "person / people",
    "英語": "English",
    "音楽": "music",
    "習う": "to learn / take lessons",
    "犬": "dog",
    "話す": "to speak",
    "家族": "family",
    "出かける": "to go out",
    "夕方": "evening",
    "季節": "season",
    "花": "flower",
    "春": "spring",
    "同じ": "same",
    "夏": "summer",
    "暑い": "hot (weather)",
    "秋": "autumn",
    "寒い": "cold (weather)",
    "冬": "winter",
    "天気": "weather",
    "今": "now",
    "晴れ": "clear / sunny",
    "昨日": "yesterday",
    "雨": "rain",
    "明日": "tomorrow",
    "雪": "snow",
    "毎日": "every day",
    "風": "wind",
    "強い": "strong",
    "町": "town",
    "静か": "quiet",
    "店": "shop / store",
    "有名": "famous",
    "食堂": "cafeteria / dining hall",
    "多い": "many / much",
    "便利": "convenient",
    "少ない": "few / little",
    "不便": "inconvenient",
    "遠い": "far",
    "道": "road / way",
    "右": "right",
    "公園": "park",
    "左": "left",
    "銀行": "bank",
    "近く": "near / nearby",
    "お寺": "temple",
    "車": "car",
    "神社": "shrine",
    "送る": "to send / see off",
    "時間": "time",
    "電車": "train",
    "場所": "place",
    "待つ": "to wait",
    "駅": "station",
    "止まる": "to stop",
    "受付": "reception",
    "着く": "to arrive",
    "門": "gate",
    "急ぐ": "to hurry",
    "お金": "money",
    "試合": "match / game",
    "食事": "meal",
    "楽しい": "fun / enjoyable",
    "難しい": "difficult",
    "博物館": "museum",
    "動物園": "zoo",
    "登る": "to climb",
    "高校": "high school",
    "言う": "to say",
    "大学": "university",
    "書く": "to write",
    "無料": "free (of charge)",
    "教える": "to teach",
    "貸す": "to lend",
    "練習": "practice",
    "漢字": "kanji",
    "説明する": "to explain",
    "午前": "morning (a.m.)",
    "全部": "all / everything",
    "午後": "afternoon (p.m.)",
    "回": "times (counter)",
    "教科書": "textbook",
    "参加する": "to participate",
    "教室": "classroom",
    "用意する": "to prepare",
    "先生": "teacher",
    "飲み物": "drink",
    "牛肉": "beef",
    "お茶": "tea",
    "豚肉": "pork",
    "お酒": "alcohol / sake",
    "皿": "plate",
    "材料": "ingredients",
    "売る": "to sell",
    "野菜": "vegetables",
    "卵": "egg",
    "味": "taste / flavor",
    "料理": "cooking / cuisine",
    "甘い": "sweet",
    "お湯": "hot water",
    "辛い": "spicy / hot",
    "調理方法": "cooking method",
    "苦手": "not good at / dislike",
    "少し": "a little",
    "コピー機": "copy machine",
    "悪い": "bad",
    "数字": "number",
    "動く": "to move / work (machine)",
    "電気": "electricity / light",
    "使う": "to use",
    "音": "sound",
    "終わる": "to end / finish",
    "机": "desk",
    "都合": "convenience / circumstances",
    "早く": "early / quickly",
    "氏名": "full name",
    "理由": "reason",
    "吸う": "to smoke / inhale",
    "用事": "errand / business",
    "取る": "to take",
    "連絡先": "contact information",
    "帰る": "to return home",
    "別に": "not particularly",
    "伝える": "to convey / tell",
    "熱": "fever / heat",
    "才": "years old (counter)",
    "薬": "medicine",
    "痛い": "painful / hurt",
    "病院": "hospital",
    "眠い": "sleepy",
    "病気": "illness",
    "寝る": "to sleep",
    "医者": "doctor",
    "記入する": "to fill in (a form)",
    "住所": "address",
    "体": "body",
    "足": "foot / leg",
    "顔": "face",
    "手": "hand",
    "目": "eye",
    "起きる": "to get up / wake up",
    "耳": "ear",
    "歩く": "to walk",
    "口": "mouth",
    "走る": "to run",
    "頭": "head",
    "運動する": "to exercise",
    "お父さん": "father",
    "弟": "younger brother",
    "お母さん": "mother",
    "妹": "younger sister",
    "兄": "older brother",
    "夫": "husband",
    "お兄さん": "older brother (polite)",
    "妻": "wife",
    "姉": "older sister",
    "両親": "parents",
    "お姉さん": "older sister (polite)",
    "男の子": "boy",
    "幸せ": "happy / happiness",
    "女の子": "girl",
    "生まれる": "to be born",
    "お祝い": "celebration / congratulations",
    "思う": "to think",
    "誕生日": "birthday",
    "選ぶ": "to choose",
    "結婚": "marriage",
    "合格する": "to pass (an exam)",
    "時計": "clock / watch",
    "～人": "counter for people",
    "お願いします": "please (request)",
}


CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"


def _has_kanji(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def _is_kana(s: str) -> bool:
    return bool(re.fullmatch(r"[ぁ-んァ-ンー（）()〜～・]+", s or ""))


def _norm_kanji(s: str) -> str:
    return (s or "").replace("ニ", "二").replace("～", "").strip()


def find_kanji_page(doc: pymupdf.Document, start: int, end: int) -> int | None:
    for p in range(start, end + 1):
        if p - 1 >= doc.page_count:
            continue
        text = doc[p - 1].get_text()
        if "Read and check the meaning of the following kanji" in text:
            return p
    return None


def cleanup_sentence(s: str) -> str:
    # Keep a single ideographic space between paired examples (一月　八月).
    s = (s or "").replace("\u3000", " ").strip()
    s = re.sub(r"\s+", "　", s)
    # Truncate if step-3 instruction leaked into the last example.
    s = re.split(r"(?:キーボードやスマートフォンで入|上の.+のことばを)", s, maxsplit=1)[0]
    return s.strip(" 　")


def extract_sentences(text: str) -> list[str]:
    """Pull ①–⑩ example lines; skip ruby lines so multi-line PDF text rejoins."""
    start = re.search(r"Read the following and pay careful attention[^\n]*\n?", text)
    end = re.search(r"Enter the words with|キーボードやスマートフォンで入", text)
    if start and end and end.start() > start.end():
        chunk = text[start.end() : end.start()]
    elif start:
        chunk = text[start.end() :]
    else:
        chunk = text

    # (text, paired_indent) — paired_indent marks a second example on the same
    # numbered line (PDF indents 八月 under ① 一月).
    lines: list[tuple[str, bool]] = []
    for raw in chunk.splitlines():
        paired = bool(re.match(r"^[\t \u3000]+", raw or ""))
        ln = (raw or "").replace("\u3000", " ").strip()
        if not ln:
            continue
        if ln.startswith("©") or "Japan Foundation" in ln:
            continue
        # Drop pure ruby / furigana lines between kanji fragments.
        if _is_kana(ln) and not any(c in ln for c in CIRCLED):
            continue
        # Step-3 JP instruction (before English) — stop collecting.
        if ln.startswith("3") and "ことば" in ln:
            break
        if ln in {"3", "上"} or ln.startswith("上の"):
            break
        lines.append((ln, paired))

    sentences: list[str] = []
    current: str | None = None
    for ln, paired in lines:
        m = re.match(rf"^([{CIRCLED}])\s*(.*)$", ln)
        if m:
            if current:
                cleaned = cleanup_sentence(current)
                if cleaned:
                    sentences.append(cleaned)
            current = m.group(2) or ""
            continue
        if current is not None:
            if paired and ln:
                current += "　" + ln
            else:
                current += ln
    if current:
        cleaned = cleanup_sentence(current)
        if cleaned:
            sentences.append(cleaned)
    return sentences


def _as_reading_fragment(s: str) -> str | None:
    """Keep only kana from a PDF line (handles mixed lines like の子 / お祝 / せ（な）)."""
    s = (s or "").replace("～", "").replace("~", "")
    s = re.sub(r"[（(]な[）)]", "", s)
    s = re.sub(r"[（）()]", "", s)
    frag = "".join(
        ch
        for ch in s
        if ("\u3040" <= ch <= "\u309f") or ("\u30a0" <= ch <= "\u30ff") or ch == "ー"
    )
    return frag or None


def _is_na_marker(s: str) -> bool:
    return bool(re.fullmatch(r"[（(]な[）)]", (s or "").strip()))


def _reading_from_slice(slice_lines: list[str], word: str) -> str:
    """Assemble reading only from lines between the previous headword and this one."""
    parts: list[str] = []
    for prev in reversed(slice_lines):
        if _norm_kanji(prev) == word:
            break
        if _is_na_marker(prev):
            continue
        frag = _as_reading_fragment(prev)
        if frag:
            parts.append(frag)
            continue
        # Pure short kanji glyph between reading chunks (学 / 生 / 計 …).
        if _has_kanji(prev) and not re.search(r"[ぁ-んァ-ン]", prev) and len(prev) <= 2:
            continue
        break
    parts.reverse()
    return "".join(parts)


def _card_section(text: str) -> str:
    """Prefer the type-in card block after the English step-3 prompt."""
    m = re.search(r"Enter the words with[^\n]*\n?", text)
    return text[m.end() :] if m else text


def extract_items(text: str, chrome_prefixes: tuple[str, ...] = ("入門", "初級", "第")) -> list[dict]:
    """Parse headwords: Starter repeats 3×, Elementary 1 repeats 2×."""
    text = _card_section(text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Do NOT strip single kana like じ/こ/かん — those are often real reading chunks.
    skip = {
        "漢字のことば",
        "The Japan Foundation",
        "example",
    }
    cleaned: list[str] = []
    for ln in lines:
        if ln in skip or ln.startswith("©") or "Japan Foundation" in ln:
            continue
        if any(ln.startswith(p) for p in chrome_prefixes):
            continue
        cleaned.append(ln)
    # Drop trailing 「漢字のことば」 title glyphs if present as separate lines.
    footer = ["漢", "かん", "字", "じ", "の", "こ", "と", "ば"]
    if cleaned[-len(footer) :] == footer:
        cleaned = cleaned[: -len(footer)]
    lines = cleaned

    items: list[dict] = []
    i = 0
    last_end = -1

    def add_item(word: str, reading: str | None) -> None:
        item: dict = {"kanji": word, "reading": reading or None}
        gloss = GLOSS.get(word) or GLOSS.get(f"{word}（な）") or GLOSS.get(word.replace("（な）", ""))
        if gloss:
            item["gloss_en"] = gloss
        if not any(x["kanji"] == word and (x.get("reading") or "") == (reading or "") for x in items):
            items.append(item)

    while i < len(lines):
        # Standalone suffix card: ～人 / にん  (not followed by 人/人 double)
        if lines[i].startswith("～") and _has_kanji(lines[i]) and i + 1 < len(lines):
            stem = _norm_kanji(lines[i])
            nxt = lines[i + 1]
            followed_by_double = i + 3 < len(lines) and lines[i + 2] == stem and lines[i + 3] == stem
            if (
                not followed_by_double
                and (_is_kana(nxt) or _as_reading_fragment(nxt))
                and not (i + 2 < len(lines) and lines[i + 2] == stem)
            ):
                word = f"～{stem}"
                reading = _as_reading_fragment(nxt) or nxt
                add_item(word, reading)
                last_end = i + 1
                i += 2
                continue

        # Alternating pair card: お願い / します / お願い / します
        if (
            i + 3 < len(lines)
            and lines[i] == lines[i + 2]
            and lines[i + 1] == lines[i + 3]
            and _has_kanji(lines[i])
            and lines[i] != lines[i + 1]
        ):
            word = f"{lines[i]}{lines[i + 1]}"
            reading = _reading_from_slice(lines[last_end + 1 : i], word)
            add_item(word, reading)
            last_end = i + 3
            i += 4
            continue

        if i + 1 < len(lines) and _has_kanji(lines[i]) and len(lines[i]) <= 12:
            a, b = lines[i], lines[i + 1]
            c = lines[i + 2] if i + 2 < len(lines) else None
            same3 = c is not None and a == b == c
            almost3 = c is not None and a == c and (b == a or _norm_kanji(b) == _norm_kanji(a))
            same2 = a == b and _norm_kanji(a) == _norm_kanji(b)
            if same3 or almost3 or same2:
                word = _norm_kanji(a)
                # Prefer consuming a triple when present so we don't stop early on Starter.
                consume = 3 if (same3 or almost3) else 2
                reading = _reading_from_slice(lines[last_end + 1 : i], word)
                add_item(word, reading)
                last_end = i + consume - 1
                i += consume
                continue
        i += 1
    return _normalize_items(items)


# Canonical readings when PDF assembly concatenates neighbouring cards.
_CANONICAL_READINGS: dict[str, str] = {
    "子ども": "こども",
    "曜日": "ようび",
    "聞きます": "ききます",
    "来ます": "きます",
    "乗ります": "のります",
    "行きます": "いきます",
    "会社": "かいしゃ",
    "見ます": "みます",
    "読みます": "よみます",
    "本": "ほん",
    "友だち": "ともだち",
    "何": "なに",
    "東": "ひがし",
    "西": "にし",
    "南": "みなみ",
    "北": "きた",
}


def _normalize_items(items: list[dict]) -> list[dict]:
    """Merge split cards like ～曜 + 曜日 → 曜日／ようび; fix known bad readings."""
    out: list[dict] = []
    i = 0
    while i < len(items):
        cur = items[i]
        nxt = items[i + 1] if i + 1 < len(items) else None
        kanji = cur.get("kanji") or ""
        if nxt and kanji in {"～曜", "〜曜"} and (nxt.get("kanji") or "") == "曜日":
            out.append(
                {
                    "kanji": "曜日",
                    "reading": "ようび",
                    "gloss_en": GLOSS.get("曜日", "day of the week"),
                }
            )
            i += 2
            continue
        item = dict(cur)
        reading = item.get("reading") or ""
        canon = _CANONICAL_READINGS.get(kanji)
        if canon and (not reading or len(reading) > len(canon) + 1 or reading != canon):
            # Replace concatenated / missing readings; keep exact canon matches.
            if reading != canon:
                item["reading"] = canon
        if "gloss_en" not in item and kanji in GLOSS:
            item["gloss_en"] = GLOSS[kanji]
        out.append(item)
        i += 1
    return out


def _prefer_items(old: list[dict], new: list[dict]) -> list[dict]:
    """Keep prior headwords when a fresh parse clearly regresses."""
    new = _normalize_items(new)
    old = _normalize_items(old)
    if not new:
        return old
    if not old:
        return new
    if len(new) + 2 < len(old):
        return old
    # Absurd mega-readings → prefer old (after normalize).
    if any(len(i.get("reading") or "") > 12 for i in new) and not any(
        len(i.get("reading") or "") > 12 for i in old
    ):
        return old
    return new


def extract_lesson(
    doc: pymupdf.Document,
    lesson: dict,
    chrome_prefixes: tuple[str, ...],
) -> dict | None:
    pages = lesson.get("pdf_pages") or []
    page = None
    if len(pages) >= 2:
        start, end = int(pages[0]), int(pages[1])
        page = find_kanji_page(doc, start, end)
    # Fall back to the page already stored on the KANJI activity.
    if page is None:
        for act in lesson.get("activities") or []:
            if act.get("id") == "KANJI" or act.get("book_mode") == "kanji_words":
                if act.get("pdf_page"):
                    page = int(act["pdf_page"])
                    break
    if page is None:
        return None
    text = doc[page - 1].get_text()
    items = extract_items(text, chrome_prefixes=chrome_prefixes)
    sentences = extract_sentences(text)
    if not items and not sentences:
        return None
    return {
        "pdf_page": page,
        "items": items,
        "sentences": sentences,
    }


def upsert_activity(lesson: dict, section: dict) -> None:
    acts = list(lesson.get("activities") or [])
    existing = next(
        (a for a in acts if a.get("id") == "KANJI" or a.get("book_mode") == "kanji_words"),
        None,
    )
    old_items = list((existing or {}).get("kanji_items") or [])
    items = _prefer_items(old_items, list(section.get("items") or []))
    sentences = list(section.get("sentences") or []) or list((existing or {}).get("kanji_sentences") or [])
    if not items and not sentences:
        return

    acts = [a for a in acts if a.get("id") != "KANJI" and a.get("book_mode") != "kanji_words"]
    max_ba = max((float(a.get("book_activity") or 0) for a in acts), default=0)
    culture = next((a for a in acts if a.get("id") == "CULTURE"), None)
    ba = (
        float(existing["book_activity"])
        if existing and existing.get("book_activity") is not None
        else (float(culture["book_activity"]) - 0.5 if culture else max_ba + 1)
    )
    activity = {
        "id": "KANJI",
        "kind": "kanji",
        "book_activity": ba,
        "label": "kanji_kotoba",
        "audio": [],
        "key_phrases": [it["kanji"] for it in items],
        "book_mode": "kanji_words",
        "prompt_en": "Kanji words — check meanings, read the example lines, then type each word.",
        "pdf_page": section["pdf_page"],
        "kanji_items": items,
        "kanji_sentences": sentences,
        "picture_has_image": False,
    }
    acts.append(activity)
    acts.sort(key=lambda a: float(a.get("book_activity") or 0))
    lesson["activities"] = acts
    lesson["kanji_words"] = {
        "pdf_page": section["pdf_page"],
        "items": items,
        "sentences": sentences,
    }


def process_book(book: str, *, dry_run: bool) -> int:
    cfg = BOOKS[book]
    pdf: Path = cfg["pdf"]
    if not pdf.is_file():
        raise SystemExit(f"missing PDF: {pdf}")

    doc = pymupdf.open(pdf)
    updated = 0
    for path in sorted(cfg["dir"].glob(cfg["glob"])):
        if "phrase" in path.name:
            continue
        lesson = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        lid = lesson.get("lesson_id") or path.stem
        num = int(re.sub(r"\D", "", lid) or "0")
        if num < int(cfg["min_lesson"]):
            continue
        section = extract_lesson(doc, lesson, chrome_prefixes=tuple(cfg["chrome_prefixes"]))
        if not section:
            print(f"[{book}] {lid} NO SECTION")
            continue
        print(
            f"[{book}] {lid} p.{section['pdf_page']}: "
            f"{len(section['items'])} words, {len(section['sentences'])} sentences — "
            + ", ".join(i["kanji"] for i in section["items"])
        )
        if not dry_run:
            upsert_activity(lesson, section)
            path.write_text(
                yaml.safe_dump(lesson, allow_unicode=True, sort_keys=False, width=100),
                encoding="utf-8",
            )
        updated += 1
    return updated


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--book",
        choices=["starter", "elementary1", "all"],
        default="all",
        help="Which textbook content to update (default: all)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    books = list(BOOKS) if args.book == "all" else [args.book]
    total = 0
    for book in books:
        n = process_book(book, dry_run=args.dry_run)
        print(("would update" if args.dry_run else "updated"), n, f"{book} lessons")
        total += n
    if len(books) > 1:
        print(("would update" if args.dry_run else "updated"), total, "lessons total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
