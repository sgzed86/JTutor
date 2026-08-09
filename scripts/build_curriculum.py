#!/usr/bin/env python3
"""Merge audio index + PDF + grammar extracts into content/starter/LXX.yaml."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from transcript_phrases import _jp_len, _norm, infer_dialog, pick_phrases  # noqa: E402

STARTER = ROOT / "content" / "starter"
AUDIO_INDEX = STARTER / "audio_index.json"
AUDIO_TRANSCRIPTS = STARTER / "audio_transcripts.json"
PDF_EXTRACT = STARTER / "pdf_extract.json"
GRAMMAR_EXTRACT = STARTER / "grammar_extract.json"

# Curated English can-dos from Irodori Starter TOC (fallback / merge)
CURATED_CANDOS: dict[int, list[tuple[int, str, str, list[str]]]] = {
    # (number, en, jp, must_include)
    1: [
        (1, "Can exchange greetings when you meet someone.", "人に会ったとき、あいさつをすることができる。", ["おはよう", "こんにちは"]),
        (2, "Can exchange greetings when parting from someone.", "人と別れるとき、あいさつをすることができる。", ["じゃあ", "失礼", "お疲れ"]),
        (3, "Can thank someone or apologize.", "人にお礼を言ったり、謝ったりすることができる。", ["ありがとう", "すみません"]),
    ],
    2: [
        (4, "Can say that you don't understand.", "わからないことを伝えることができる。", ["わかりません", "わからない"]),
        (5, "Can ask someone to repeat what they said.", "もう一度言ってもらうよう頼むことができる。", ["もう一度", "ゆっくり"]),
        (6, "Can say numbers and understand numbers you hear.", "数字を言ったり、聞いて理解したりすることができる。", ["いち", "に", "さん", "ゼロ", "じゅう"]),
    ],
    3: [
        (7, "Can give a simple self-introduction (name, country/hometown).", "簡単な自己紹介（名前・国など）をすることができる。", ["です", "から来ました"]),
        (8, "Can ask someone's name and where they are from.", "相手の名前や出身を質問することができる。", ["お名前", "どこ"]),
        (9, "Can use simple set phrases when meeting someone for the first time.", "初めて会った人に簡単な定型表現を使うことができる。", ["よろしく"]),
    ],
    4: [
        (12, "Can listen to a family being introduced and understand who is who.", "家族の紹介を聞いて、家族のメンバーを理解することができる。", ["家族"]),
        (13, "Can ask and answer about where you live, age, etc.", "住んでいるところや年齢などを質問したり、答えたりすることができる。", ["住んで"]),
        (14, "Can ask simple questions about a photo (who someone is, etc.).", "写真を見ながら簡単な質問をしたり答えたりすることができる。", ["誰", "だれ"]),
    ],
    5: [
        (15, "Can say what foods you like and don't like.", "好きな食べ物・嫌いな食べ物を言うことができる。", ["好き"]),
        (16, "Can ask what foods someone likes.", "好きな食べ物について質問することができる。", ["好き"]),
        (17, "Can talk simply about favorite foods.", "好きな食べ物について簡単に話すことができる。", ["好き"]),
    ],
    6: [
        (18, "Can order food and drinks at a restaurant/cafe.", "飲食店で食べ物や飲み物を注文することができる。", ["ください"]),
        (19, "Can ask about menu items simply.", "メニューについて簡単に質問することができる。", []),
        (20, "Can understand simple questions from staff when ordering.", "注文のとき店員の簡単な質問を理解することができる。", []),
    ],
    7: [
        (26, "Can understand a simple house tour and layout.", "家の中を案内してもらいながら、間取りを理解することができる。", []),
        (27, "Can ask whether needed items are in a room/house.", "家や部屋に必要なものがそろっているか質問して確認することができる。", ["ありますか"]),
        (28, "Can simply describe where you live.", "どこに住んでいるか簡単に説明することができる。", ["住んで"]),
    ],
    8: [
        (29, "Can ask where someone is.", "人がどこにいるか質問することができる。", ["どこ"]),
        (30, "Can say where someone/something is using location words.", "場所を表す言葉を使って、人やものの場所を言うことができる。", ["です"]),
        (31, "Can understand simple directions about location at work/home.", "職場や家での簡単な位置の説明を理解することができる。", []),
    ],
    9: [
        (32, "Can say what time something starts and ends.", "何時から何時までか言うことができる。", ["時"]),
        (33, "Can ask about daily schedules simply.", "毎日のスケジュールについて簡単に質問することができる。", ["何時"]),
        (34, "Can understand simple spoken times and schedules.", "簡単な時刻やスケジュールを聞いて理解することができる。", []),
    ],
    10: [
        (39, "Can understand short simple instructions at work.", "仕事での短く簡単な指示を聞いて理解することができる。", []),
        (40, "Can ask someone to lend you something.", "ものを貸してくれるよう頼むことができる。", ["貸して", "ください"]),
        (41, "Can make simple requests at work or home.", "職場や家で簡単な依頼をすることができる。", ["ください"]),
    ],
    11: [
        (44, "Can answer simply when asked about hobbies.", "趣味について質問されたとき、簡単に答えることができる。", ["趣味"]),
        (45, "Can ask and answer about hobbies and likes.", "趣味や好きなことを質問したり答えたりすることができる。", ["好き"]),
        (46, "Can say simply what you do on days off.", "休みの日に何をするか簡単に言うことができる。", ["休み"]),
    ],
    12: [
        (47, "Can invite someone to do something together.", "一緒に何かをするよう誘うことができる。", ["ませんか", "一緒"]),
        (48, "Can accept or decline an invitation simply.", "誘いを受けたり断ったりすることができる。", []),
        (49, "Can suggest a simple plan for going out.", "簡単な外出の計画を提案することができる。", []),
    ],
    13: [
        (52, "Can ask whether a train/bus goes where you want and understand the answer.", "電車やバスが行きたいところに行くか質問し、答えを理解することができる。", ["行きますか"]),
        (53, "Can ask where you are when announcements are unclear.", "車内アナウンスがわからないとき、今どこか質問することができる。", ["どこ"]),
        (54, "Can understand simple transit information.", "簡単な交通情報を理解することができる。", []),
    ],
    14: [
        (55, "Can comment simply on buildings and places you see.", "建物や場所について簡単に感想を言うことができる。", ["ですね"]),
        (56, "Can ask/confirm what a place is.", "それが何の場所か質問したり確認したりすることができる。", []),
        (57, "Can describe size/appearance with simple adjectives.", "簡単な形容詞で大きさや様子を説明することができる。", []),
    ],
    15: [
        (58, "Can say what you want/need at a store.", "店でほしいもの・必要なものを言うことができる。", ["ほしい"]),
        (59, "Can ask store staff for a product.", "店員に商品についてたずねることができる。", []),
        (60, "Can understand simple replies from store staff.", "店員の簡単な返事を理解することができる。", []),
    ],
    16: [
        (66, "Can listen to and understand the price of a product.", "商品の値段を聞いて理解することができる。", ["円"]),
        (67, "Can ask staff the price of an item.", "店の人に値段を質問して、答えを理解することができる。", ["いくら"]),
        (68, "Can say the amount/quantity you need when shopping.", "買い物をするとき、必要な量や数を伝えることができる。", ["ください"]),
    ],
    17: [
        (69, "Can say what you did on a day off.", "休みの日にしたことを言うことができる。", ["ました"]),
        (70, "Can ask how something was (impressions).", "どうだったか感想を質問することができる。", ["どう"]),
        (71, "Can give a simple impression of an event/outing.", "出来事や外出について簡単な感想を言うことができる。", ["でした"]),
    ],
    18: [
        (72, "Can say what you want to do.", "したいことを言うことができる。", ["たい"]),
        (73, "Can ask why and give a simple reason.", "どうしてか質問したり、簡単な理由を言ったりすることができる。", ["どうして", "から"]),
        (74, "Can talk simply about future holiday plans.", "これからの休みの予定について簡単に話すことができる。", ["たい"]),
    ],
}

# L1 speak targets by book activity # (CD 01-XX). Source: Irodori Starter PDF
# 聴解スクリプト L1-11–L1-13 + book sections L1-3, L1-5, L1-8.
L01_PHRASE_BY_ACTIVITY: dict[int, list[str]] = {
    1: ["おはよう"],  # 01-01 listen & repeat (first line)
    2: ["こんにちは"],  # 01-02
    3: ["おはようございます"],  # 01-03
    4: ["こんばんは"],  # 01-04
    5: ["おはよう"],  # 01-05
    6: ["おはようございます"],  # 01-06 morning shadow
    7: ["おはよう"],  # 01-07
    8: ["こんにちは"],  # 01-08 afternoon
    9: ["こんばんは"],  # 01-09 evening
    10: ["じゃあ、また"],  # 01-10
    11: ["失礼します"],  # 01-11
    12: ["お先に失礼します"],  # 01-12
    13: ["おやすみなさい"],  # 01-13
    14: ["お先に失礼します"],  # 01-14 shadow ①
    15: ["失礼します"],  # 01-15
    16: ["お疲れさまでした"],  # 01-16 shadow ②
    17: ["おやすみ"],  # 01-17 shadow ③
    18: ["ありがとうございます"],  # 01-18
    19: ["すみません"],  # 01-19
    20: ["ありがとうございます"],  # 01-20
    21: ["どうも"],  # 01-21
    22: ["どうもありがとう"],  # 01-22
    23: ["すみません"],  # 01-23
    24: ["ごめん"],  # 01-24
    25: ["すみません"],  # 01-25
    26: ["ありがとうございます"],  # 01-26
    27: ["すみません"],  # 01-27
    28: ["ありがとうございます"],  # 01-28 (also says すみません first)
    29: ["すみません"],  # 01-29
}

# Can-do quiz: tutor speaks partner_jp; learner replies with one of expected.
L01_QUIZ_SCENARIOS: list[dict] = [
    {
        "can_do_id": "CD_L01_01",
        "partner_jp": "おはよう！",
        "expected": ["おはよう", "おはようございます"],
        "hint_en": "A coworker greets you in the morning. Greet them back.",
    },
    {
        "can_do_id": "CD_L01_01",
        "partner_jp": "こんにちは。",
        "expected": ["こんにちは"],
        "hint_en": "Someone says hello in the afternoon. Reply with a greeting.",
    },
    {
        "can_do_id": "CD_L01_01",
        "partner_jp": "こんばんは。",
        "expected": ["こんばんは"],
        "hint_en": "Evening greeting — respond in kind.",
    },
    {
        "can_do_id": "CD_L01_02",
        "partner_jp": "じゃあ、また。",
        "expected": ["じゃあ、また", "じゃあまた"],
        "hint_en": "Your classmate is leaving. Say goodbye the same way.",
    },
    {
        "can_do_id": "CD_L01_02",
        "partner_jp": "お先に失礼します。",
        "expected": ["お先に失礼します", "失礼します"],
        "hint_en": "A senior colleague is leaving the office. Reply appropriately.",
    },
    {
        "can_do_id": "CD_L01_02",
        "partner_jp": "お疲れさまでした。",
        "expected": ["お疲れさまでした", "お疲れ"],
        "hint_en": "Work is over for the day. Reply to their closing phrase.",
    },
    {
        "can_do_id": "CD_L01_03",
        "partner_jp": "どうぞ。",
        "expected": ["ありがとう", "ありがとうございます", "どうも"],
        "hint_en": "Someone offers you something. Thank them.",
    },
    {
        "can_do_id": "CD_L01_03",
        "partner_jp": "あ、すみません！",
        "expected": ["すみません", "ごめん"],
        "hint_en": "You bumped into someone. Apologize.",
    },
    {
        "can_do_id": "CD_L01_03",
        "partner_jp": "ありがとうございます。",
        "expected": ["どうも", "いいえ", "どういたしまして"],
        "hint_en": "They thanked you. Give a short polite reply.",
    },
]

# Numbers 0–10 (Irodori L2 数字). Used for CD 02-04 listen & repeat drill.
L02_NUMBERS_0_10: list[str] = [
    "ゼロ",
    "いち",
    "に",
    "さん",
    "よん",
    "ご",
    "ろく",
    "なな",
    "はち",
    "きゅう",
    "じゅう",
]

# L2 speak/listen targets by book activity # (CD 02-XX).
# Phrases follow the official MP3 contents (verified by transcription), not worksheet a–e letter order.
L02_PHRASE_BY_ACTIVITY: dict[int, list[str]] = {
    1: ["よくわかりません", "よく分かりません"],
    # CD 02-02 / 02-03: book labels b/c are swapped on the official MP3s vs worksheet order.
    2: ["もう少し、ゆっくり言ってください", "もうすこし、ゆっくり言ってください"],
    3: ["もういちど、お願いします", "もう一度、お願いします", "もう一度お願いします"],
    # CD 02-04: full 0–10 list (book: 聞いて言いましょう) — not a single “さん” probe
    4: list(L02_NUMBERS_0_10),
    5: ["もういちど、お願いします", "もう一度、お願いします", "もう一度お願いします"],
    6: ["もう少し、ゆっくり言ってください", "もうすこし、ゆっくり言ってください"],
    # CD 02-07..10 (languages): MP3 order ≠ worksheet a/b/c listing
    7: ["日本語、できますか"],  # 02-07 おでん屋
    8: ["日本語、わかりますか", "英語、わかりますか"],  # 02-08 役所
    9: ["中国語、できますか"],  # 02-09 テーマパーク
    10: ["インドネシア語、わかりますか"],  # 02-10 インドネシア料理店
    # CD 02-11..14 speaking models (Q → A)
    11: ["はい、すこしできます", "はい、少しできます", "すこしできます", "はい、できます"],
    12: ["すみません、わかりません", "わかりません"],
    13: ["はい、すこしできます", "はい、少しできます", "すこしできます", "はい、できます"],
    14: ["すみません、わかりません", "わかりません"],
    # CD 02-15..16: 「これは日本語で何（と）言いますか」
    15: ["これは日本語で何ですか", "これは、日本語で何ですか"],
    16: ["これは日本語で何と言いますか", "これは、日本語で何と言いますか"],
    # CD 02-17..20: ask-how-to-say + clarification (not language できます/わかります)
    17: ["もう少し、ゆっくり言ってください", "もうすこし、ゆっくり言ってください"],
    18: ["もういちど、お願いします", "もう一度、お願いします", "もう一度お願いします"],
    19: ["もう少し、ゆっくり言ってください", "もうすこし、ゆっくり言ってください"],
    20: ["もういちど、お願いします", "もう一度、お願いします", "もう一度お願いします"],
    # CD 02-21..23 speaking: ask what something is called
    21: ["これは日本語で何ですか", "これは、日本語で何ですか"],
    22: ["もういちど、お願いします", "もう一度、お願いします", "もう一度お願いします"],
    23: ["もう少し、ゆっくり言ってください", "もうすこし、ゆっくり言ってください"],
}

# Partner / learner lines for L02 dialog activities (must match CD models).
# Partner speaks first in the tutor flow, then the learner answers / replies.
L02_DIALOG_BY_ACTIVITY: dict[int, tuple[str, str]] = {
    5: ("部屋は、213です。", "もういちど、お願いします"),
    6: ("部屋は、213です。", "もう少し、ゆっくり言ってください"),
    11: ("日本語、できますか", "はい、すこしできます"),
    12: ("日本語、わかりますか", "すみません、わかりません"),
    13: ("インドネシア語、できますか", "はい、すこしできます"),
    14: ("インドネシア語、わかりますか", "すみません、わかりません"),
}

# Ask-how-to-say speaking tracks: listen CD, then say your line (not inverted Q/A dialog).
L02_LISTEN_REPEAT_ACTIVITIES: set[int] = {21, 22, 23}

L02_QUIZ_SCENARIOS: list[dict] = [
    {
        "can_do_id": "CD_L02_04",
        "partner_jp": "部屋は213です。",
        "expected": ["よくわかりません", "わかりません", "わからない"],
        "hint_en": "You didn't catch the room number. Say you don't understand.",
    },
    {
        "can_do_id": "CD_L02_04",
        "partner_jp": "ここは受付です。",
        "expected": ["よくわかりません", "わかりません"],
        "hint_en": "The clerk spoke too fast. Say you don't understand well.",
    },
    {
        "can_do_id": "CD_L02_05",
        "partner_jp": "部屋は213です。",
        "expected": ["もういちど、お願いします", "もう一度"],
        "hint_en": "Ask them to say it again.",
    },
    {
        "can_do_id": "CD_L02_05",
        "partner_jp": "在留カードを見せてください。",
        "expected": ["もう少し、ゆっくり言ってください", "ゆっくり"],
        "hint_en": "Ask them to speak a little more slowly.",
    },
    {
        "can_do_id": "CD_L02_06",
        "partner_jp": "数字を言ってください。いち。",
        "expected": ["いち", "1", "一"],
        "hint_en": "Repeat the number: 1.",
    },
    {
        "can_do_id": "CD_L02_06",
        "partner_jp": "数字を言ってください。さん。",
        "expected": ["さん", "3", "三"],
        "hint_en": "Repeat the number: 3.",
    },
    {
        "can_do_id": "CD_L02_06",
        "partner_jp": "数字を言ってください。ご。",
        "expected": ["ご", "5", "五"],
        "hint_en": "Repeat the number: 5.",
    },
    {
        "can_do_id": "CD_L02_06",
        "partner_jp": "数字を言ってください。じゅう。",
        "expected": ["じゅう", "10", "十"],
        "hint_en": "Repeat the number: 10.",
    },
    {
        "can_do_id": "CD_L02_06",
        "partner_jp": "いくつですか。",
        "expected": list(L02_NUMBERS_0_10) + ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        "hint_en": "Answer with any number in Japanese (0–10).",
    },
]

SKILL_KIND = {
    "listening": "listening",
    "speaking": "speaking",
    "grammar_form": "grammar_form",
    "conversation": "conversation",
    "vocabulary": "vocabulary",
    "kotoba": "vocabulary",
    "hiragana": "script",
    "katakana": "script",
    "classroom": "classroom",
    "other": "other",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def must_include_from_phrases(phrases: list[str], statement: str) -> list[str]:
    """Pick short JP tokens useful as rubric keywords."""
    cands = []
    for p in phrases:
        p = p.strip()
        if 2 <= len(p) <= 20 and re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", p):
            cands.append(p)
    # Also pull quoted JP from statement if any
    for m in re.finditer(r"[「『]([^」』]+)[」』]", statement):
        cands.append(m.group(1))
    return list(dict.fromkeys(cands))[:5]


def apply_l01_phrases(activities: list[dict]) -> None:
    for a in activities:
        n = int(a.get("book_activity") or 0)
        if n in L01_PHRASE_BY_ACTIVITY:
            a["key_phrases"] = list(L01_PHRASE_BY_ACTIVITY[n])


def _dialog(partner: str, learner: str) -> list[dict]:
    return [{"speaker": "partner", "jp": partner}, {"speaker": "learner", "jp": learner}]


def apply_l01_book_flow(activities: list[dict]) -> None:
    """Book-faithful modes: listen & repeat → picture select → role-play (+ swap)."""
    sections: dict[int, tuple[str, str]] = {
        1: (
            "Can-do 1 — 人に会ったときのあいさつ。まず 聞いて、言いましょう。",
            "Can-do 1: Greetings when you meet someone. Listen and repeat, then choose from pictures.",
        ),
        6: (
            "2. 人と会ったときに、あいさつをしましょう。",
            "Section 2: Greet people when you meet them — morning, afternoon, evening dialogs.",
        ),
        10: (
            "Can-do 2 — 人と別れるときのあいさつ。",
            "Can-do 2: Greetings when you part — listen and match, then practice.",
        ),
        18: (
            "Can-do 3 — お礼と 謝り方。",
            "Can-do 3: Thank someone or apologize.",
        ),
    }
    picture: dict[int, str] = {
        2: "Book ① (01-02): morning — which greeting do you hear? Say it.",
        3: "Book ② (01-03): afternoon — say the greeting.",
        4: "Book ③ (01-04): evening — say the greeting.",
        5: "Book ④ (01-05): morning (casual) — say the greeting.",
        10: "Goodbye ① (01-10): say the phrase you hear.",
        11: "Goodbye ② (01-11): say the phrase.",
        12: "Goodbye ③ (01-12): say the phrase.",
        13: "Goodbye ④ (01-13): say the phrase.",
        19: "Thanks / sorry — listen and say the phrase (01-19).",
        20: "Say the thanks phrase (01-20).",
        21: "Short thanks どうも (01-21).",
        22: "Say どうもありがとう (01-22).",
        23: "Apology すみません (01-23).",
        24: "Casual ごめん (01-24).",
        25: "Apology in context (01-25).",
    }
    dialogs: dict[int, list[dict]] = {
        6: _dialog("おはようございます", "おはよう"),
        8: _dialog("こんにちは", "こんにちは"),
        9: _dialog("こんばんは", "こんばんは"),
        14: _dialog("お先に失礼します", "失礼します"),
        15: _dialog("失礼します", "失礼します"),
        16: _dialog("お疲れさまでした", "お疲れさま"),
        17: _dialog("おやすみなさい", "おやすみ"),
        26: _dialog("どうぞ", "ありがとうございます"),
        27: _dialog("あ、すみません", "すみません"),
        28: _dialog("ありがとうございます", "どうも"),
        29: _dialog("すみません", "いいえ"),
    }
    listen_select = {2, 3, 4, 5, 10, 11, 12, 13, 19, 20, 21, 22, 23, 24, 25}
    listen_repeat_only = {1, 18}
    for a in activities:
        n = int(a.get("book_activity") or 0)
        if n == 7:
            a["book_skip"] = True
            continue
        if n in sections:
            jp, en = sections[n]
            a["book_section_jp"] = jp
            a["book_section_en"] = en
        if n in picture:
            a["picture_hint_en"] = picture[n]
        if n in dialogs:
            a["book_mode"] = "dialog"
            a["dialog_script"] = dialogs[n]
            audio = list(a.get("audio") or [])
            if n == 6:
                audio = [
                    "assets/audio/X_[01-06]_hanasu1-1.mp3",
                    "assets/audio/X_[01-07]_hanasu1-2.mp3",
                ]
            if audio:
                a["dialog_listen_audio"] = audio
        elif n in listen_select:
            a["book_mode"] = "listen_select"
        elif n in listen_repeat_only:
            a["book_mode"] = "listen_repeat"
        elif a.get("kind") == "speaking" and n not in dialogs:
            a["book_mode"] = "listen_repeat"


def phrase_difficulty_tags(phrase: str) -> list[str]:
    """Optional metadata on activities — backward compatible (new field only)."""
    p = (phrase or "").strip()
    tags: list[str] = []
    if not p:
        return tags
    if len(p) <= 10:
        tags.append("short")
    else:
        tags.append("long")
    if any(x in p for x in ("ございます", "ください", "ます", "です", "ません")):
        tags.append("polite")
    if any(x in p for x in ("じゃあ", "ごめん", "どうも", "おやすみ")) or p.endswith("よ"):
        tags.append("casual")
    return tags or ["short"]


def attach_phrase_meta(activity: dict) -> None:
    phrases = activity.get("key_phrases") or []
    if not phrases:
        return
    activity["phrase_meta"] = [{"jp": p, "tags": phrase_difficulty_tags(p)} for p in phrases[:6]]


def apply_generic_book_flow(lesson_num: int, activities: list[dict]) -> None:
    """
    L02–L18 book modes: listening → choose & say; speaking/conversation → dialog + swap.
    Skips script/classroom rows. Does not overwrite book_mode if already set (e.g. L01).
    """
    listen_counter = 0
    lid = f"L{lesson_num:02d}"
    for a in activities:
        if a.get("kind") in ("script", "classroom") or a.get("book_skip"):
            continue
        attach_phrase_meta(a)
        if a.get("book_mode"):
            continue
        n = int(a.get("book_activity") or 0)
        kind = a.get("kind") or "activity"
        phrases = [p for p in (a.get("key_phrases") or []) if p]

        if kind == "listening":
            listen_counter += 1
            if listen_counter == 1 and lesson_num > 1:
                a["book_mode"] = "listen_repeat"
            else:
                a["book_mode"] = "listen_select"
                a["picture_has_image"] = True
                a["picture_hint_en"] = (
                    f"{lid} activity {n}: look at the book illustration, listen to the CD, "
                    f"then say the matching phrase."
                )
        elif kind in ("speaking", "conversation"):
            a["book_mode"] = "dialog"
            if len(phrases) >= 2:
                a["dialog_script"] = _dialog(phrases[0], phrases[1])
            elif phrases:
                a["dialog_script"] = _dialog(phrases[0], phrases[0])
            else:
                a["dialog_script"] = _dialog("では、始めましょう。", "はい")
            audio = list(a.get("audio") or [])
            if audio:
                a["dialog_listen_audio"] = audio[:2]
        elif kind == "vocabulary":
            a["book_mode"] = "listen_repeat"
        else:
            a["book_mode"] = "listen_repeat"


def enrich_quiz_scenarios(
    lesson_num: int,
    activities: list[dict],
    can_dos: list[dict],
    scenarios: list[dict],
) -> list[dict]:
    """Add role-play scenarios from dialog activities (keeps existing scenarios)."""
    out = [dict(s) for s in scenarios]
    seen = {(s.get("can_do_id"), s.get("partner_jp")) for s in out}
    cd_ids = [c["id"] for c in can_dos] or [f"CD_L{lesson_num:02d}_01"]
    cd_i = 0
    for a in activities:
        if a.get("book_mode") != "dialog":
            continue
        script = a.get("dialog_script") or []
        partner = next((ln.get("jp") for ln in script if ln.get("speaker") == "partner"), None)
        learner = next((ln.get("jp") for ln in script if ln.get("speaker") == "learner"), None)
        if not partner:
            continue
        cd = a.get("can_do_id") or cd_ids[cd_i % len(cd_ids)]
        cd_i += 1
        key = (cd, partner)
        if key in seen:
            continue
        seen.add(key)
        expected = [x for x in [learner, *(a.get("key_phrases") or [])] if x]
        out.append(
            {
                "can_do_id": cd,
                "partner_jp": partner,
                "expected": list(dict.fromkeys(expected))[:6],
                "hint_en": a.get("picture_hint_en")
                or f"Reply as in the book dialog (activity {a.get('book_activity')}).",
            }
        )
    return out


def apply_l02_phrases(activities: list[dict]) -> None:
    for a in activities:
        n = int(a.get("book_activity") or 0)
        if n in L02_PHRASE_BY_ACTIVITY:
            a["key_phrases"] = list(L02_PHRASE_BY_ACTIVITY[n])


def apply_l02_book_flow_overrides(activities: list[dict]) -> None:
    """L02 fixes: numbers drill + dialog scripts aligned to official MP3s."""
    for a in activities:
        n = int(a.get("book_activity") or 0)
        if n == 4:
            a["book_mode"] = "listen_repeat_all"
            a["key_phrases"] = list(L02_NUMBERS_0_10)
            a["picture_has_image"] = False
            a.pop("picture_hint_en", None)
            a["prompt_en"] = (
                "Listen to numbers 0–10 on the CD, then say each number in order."
            )
            attach_phrase_meta(a)
            continue
        if n in L02_LISTEN_REPEAT_ACTIVITIES:
            a["book_mode"] = "listen_repeat"
            a.pop("dialog_script", None)
            a.pop("dialog_listen_audio", None)
            a["picture_has_image"] = False
            a.pop("picture_hint_en", None)
            attach_phrase_meta(a)
            continue
        if n in L02_DIALOG_BY_ACTIVITY:
            partner, learner = L02_DIALOG_BY_ACTIVITY[n]
            a["book_mode"] = "dialog"
            a["dialog_script"] = _dialog(partner, learner)
            audio = list(a.get("audio") or [])
            if audio:
                a["dialog_listen_audio"] = audio[:2]
            # Learner target (+ alternates from key_phrases)
            phrases = list(a.get("key_phrases") or [])
            if learner not in phrases:
                phrases = [learner, *phrases]
            a["key_phrases"] = phrases
            attach_phrase_meta(a)


def _activity_transcript(activity: dict, transcripts: dict[str, str]) -> str:
    for rel in activity.get("audio") or []:
        t = transcripts.get(rel)
        if t and t.strip():
            return t.strip()
    return ""


def apply_phrases_from_transcripts(
    lesson_num: int,
    activities: list[dict],
    transcripts: dict[str, str],
) -> None:
    """L03+: key_phrases and dialog scripts from cached Whisper transcripts."""
    listen_counter = 0
    lid = f"L{lesson_num:02d}"
    for a in activities:
        if a.get("kind") in ("script", "classroom") or a.get("book_skip"):
            continue
        text = _activity_transcript(a, transcripts)
        if not text:
            continue
        kind = a.get("kind") or "activity"
        max_p = 6 if kind == "vocabulary" else 4
        phrases = pick_phrases(text, kind, max_phrases=max_p)
        if not phrases and kind == "grammar_form":
            t = _norm(text)
            if _jp_len(t) >= 2:
                phrases = [t[:80]]
        if not phrases:
            continue
        a["key_phrases"] = phrases
        attach_phrase_meta(a)

        if kind in ("speaking", "conversation"):
            pair = infer_dialog(text)
            if pair:
                partner, learner = pair
                a["book_mode"] = "dialog"
                a["dialog_script"] = _dialog(partner, learner)
                audio = list(a.get("audio") or [])
                if audio:
                    a["dialog_listen_audio"] = audio[:2]
                alts = [p for p in phrases if p != learner]
                a["key_phrases"] = [learner, *alts[:3]]
                attach_phrase_meta(a)
            continue

        if kind == "listening":
            listen_counter += 1
            a["book_mode"] = "listen_repeat" if listen_counter == 1 else "listen_select"
            if a["book_mode"] == "listen_select":
                a["picture_has_image"] = True
                a["picture_hint_en"] = (
                    f"{lid} activity {a.get('book_activity')}: listen to the CD, "
                    f"then say the phrase that matches the book."
                )
            continue

        if kind == "grammar_form":
            a["book_mode"] = "listen_repeat"
            continue

        if kind == "vocabulary":
            if len(phrases) >= 5:
                a["book_mode"] = "listen_repeat_all"
            else:
                a["book_mode"] = "listen_repeat"
            continue

    apply_generic_book_flow(lesson_num, activities)


def enrich_quiz_from_activities(
    lesson_num: int,
    can_dos: list[dict],
    activities: list[dict],
    scenarios: list[dict],
) -> list[dict]:
    """Add one role-play per can-do using real activity phrases (L03+)."""
    if lesson_num <= 2:
        return scenarios
    out = [dict(s) for s in scenarios]
    seen = {(s.get("can_do_id"), s.get("partner_jp")) for s in out}
    by_cd: dict[str, list[str]] = {}
    for a in activities:
        cd = a.get("can_do_id")
        if not cd:
            continue
        for p in a.get("key_phrases") or []:
            if p and len(p) >= 2:
                by_cd.setdefault(cd, [])
                if p not in by_cd[cd]:
                    by_cd[cd].append(p)
    for c in can_dos:
        cd = c["id"]
        phrases = by_cd.get(cd) or []
        must = (c.get("rubric") or {}).get("must_include") or []
        expected = list(dict.fromkeys([*phrases[:4], *must]))[:6]
        if not expected:
            continue
        partner = phrases[0] if phrases else "では、お願いします。"
        key = (cd, partner)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "can_do_id": cd,
                "partner_jp": partner if partner.endswith("。") else f"{partner}。",
                "expected": expected,
                "hint_en": c.get("statement_en") or "Reply using a phrase from this lesson.",
            }
        )
    return out


def write_l01_phrase_reference(activities: list[dict]) -> None:
    rows = []
    for a in activities:
        n = int(a.get("book_activity") or 0)
        audio = (a.get("audio") or [""])[0]
        cd = ""
        m = re.search(r"\[01-(\d+)\]", audio)
        if m:
            cd = f"01-{int(m.group(1)):02d}"
        rows.append(
            {
                "book_activity": n,
                "activity_id": a.get("id"),
                "cd": cd,
                "kind": a.get("kind"),
                "label": a.get("label"),
                "key_phrase": (a.get("key_phrases") or [""])[0],
                "audio": audio,
            }
        )
    out = STARTER / "L01_phrase_reference.yaml"
    out.write_text(
        yaml.safe_dump(
            {"source": "Irodori Starter PDF 聴解スクリプト L1-11–13", "steps": rows},
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def build_activities(lesson: int, tracks: list[dict], can_dos: list[dict]) -> list[dict]:
    activities = []
    # Group tracks by kind order of appearance
    skill_tracks = [t for t in tracks if t["kind"] not in ("classroom",)]
    # Map can-dos round-robin onto non-script activities
    cd_ids = [c["id"] for c in can_dos] or [f"CD_L{lesson:02d}_01"]
    cd_i = 0
    act_n = 0
    for t in skill_tracks:
        if t["kind"] in ("hiragana", "katakana", "script"):
            # Bundle script drills as supporting activities without mastery gate
            act_n += 1
            activities.append(
                {
                    "id": f"A{act_n}",
                    "kind": "script",
                    "book_activity": act_n,
                    "can_do_id": None,
                    "label": t["label"],
                    "audio": [t["rel_path"]],
                    "key_phrases": [],
                    "prompt_en": f"Practice {t['kind']} with the book audio ({t['filename']}).",
                }
            )
            continue
        act_n += 1
        cd = cd_ids[cd_i % len(cd_ids)]
        cd_i += 1
        kind = SKILL_KIND.get(t["kind"], t["kind"])
        prompt = {
            "listening": "Listen to the audio and check understanding for this can-do.",
            "speaking": "Practice speaking along with the model audio, then say it yourself.",
            "grammar_form": "Focus on the grammar form (katachi). Listen and repeat the patterns.",
            "conversation": "Listen to the conversation, then practice both roles.",
            "vocabulary": "Learn the vocabulary with the audio, then say each item aloud.",
        }.get(kind, "Complete this activity with the book audio.")
        activities.append(
            {
                "id": f"A{act_n}",
                "kind": kind,
                "book_activity": act_n,
                "can_do_id": cd,
                "label": t["label"],
                "audio": [t["rel_path"]],
                "key_phrases": [],
                "prompt_en": prompt,
            }
        )
    return activities


def build_quiz(can_dos: list[dict], phrases: list[str]) -> list[dict]:
    quizzes = []
    for c in can_dos:
        en = c["statement_en"]
        quizzes.append(
            {
                "type": "roleplay",
                "can_do_id": c["id"],
                "prompt_en": f"Demonstrate this can-do in Japanese: {en}",
                "spoken_required": True,
            }
        )
        quizzes.append(
            {
                "type": "roleplay",
                "can_do_id": c["id"],
                "prompt_en": f"In a new everyday situation, show you can: {en}",
                "spoken_required": True,
            }
        )
    return quizzes


def build_intro_questions(lesson_num: int, title_en: str, topic_en: str, can_dos: list[dict]) -> list[dict]:
    """
    Warm-up questions (Irodori introductory questions). Optional YAML field.
    Kept short/personal so intro_chat can accept free answers without grading.
    """
    curated: dict[int, list[dict]] = {
        1: [
            {
                "jp": "あなたの 国では、会ったとき、何と いいますか？",
                "en": "In your language, what do you say when you meet someone?",
            },
            {
                "jp": "朝と 夜で、あいさつは ちがいますか？",
                "en": "Do your greetings change between morning and evening?",
            },
        ],
        2: [
            {
                "jp": "日本語が わからないとき、どうしますか？",
                "en": "When you don't understand Japanese, what do you do?",
            },
        ],
    }
    if lesson_num in curated:
        return curated[lesson_num]
    topic = topic_en or title_en or f"Lesson {lesson_num}"
    first_cd = (can_dos[0].get("statement_en") if can_dos else "") or ""
    title = title_en or topic
    q2_en = (
        f"This lesson aims at: {first_cd} What do you want to be able to do?"
        if first_cd
        else "What do you want to be able to do after this lesson?"
    )
    return [
        {
            "jp": f"{title} について、あなたの けいけんは？",
            "en": f'Thinking about "{topic}" — what is your experience?',
        },
        {
            "jp": "この レッスンで、何が できるように なりたいですか？",
            "en": q2_en,
        },
    ]


def build_quiz_scenarios(lesson_num: int, can_dos: list[dict]) -> list[dict]:
    if lesson_num == 1:
        return [dict(s) for s in L01_QUIZ_SCENARIOS]
    if lesson_num == 2:
        return [dict(s) for s in L02_QUIZ_SCENARIOS]
    out: list[dict] = []
    for c in can_dos:
        must = (c.get("rubric") or {}).get("must_include") or []
        if not must:
            continue
        stmt = (c.get("statement_jp") or c.get("statement_en") or "")[:40]
        out.append(
            {
                "can_do_id": c["id"],
                "partner_jp": "では、お願いします。",
                "expected": list(must),
                "hint_en": f"Situation: {c.get('statement_en', '')} Reply using lesson phrases.",
            }
        )
        out.append(
            {
                "can_do_id": c["id"],
                "partner_jp": "もう一度、お願いします。",
                "expected": list(must),
                "hint_en": f"Again — {stmt}",
            }
        )
    return out


def merge_can_dos(lesson: int, extracted: list[dict], phrases: list[str]) -> list[dict]:
    curated = CURATED_CANDOS.get(lesson, [])
    by_num: dict[int, dict] = {}
    for e in extracted:
        by_num[e["can_do_number"]] = dict(e)
    for num, en, jp, must in curated:
        # Prefer curated statements — PDF TOC parse often concatenates multiple can-dos
        if num in by_num:
            by_num[num]["statement_en"] = en
            by_num[num]["statement_jp"] = jp or by_num[num].get("statement_jp", "")
            by_num[num]["_must"] = must
        else:
            by_num[num] = {
                "id": f"CD_L{lesson:02d}_{num:02d}",
                "can_do_number": num,
                "statement_en": en,
                "statement_jp": jp,
                "activity_hint": "",
                "_must": must,
            }
    # Drop extracted can-dos that look like concatenated TOC junk (>200 chars)
    curated_nums = {c[0] for c in curated}
    for num in list(by_num):
        en = by_num[num].get("statement_en") or ""
        if len(en) > 200 and num not in curated_nums:
            del by_num[num]
    result = []
    for num in sorted(by_num):
        c = by_num[num]
        c["id"] = f"CD_L{lesson:02d}_{num:02d}"
        stmt = c.get("statement_jp") or c.get("statement_en") or ""
        must = c.pop("_must", None)
        if must is None:
            must = must_include_from_phrases(phrases, stmt)
        c["rubric"] = {"must_include": must, "min_score": 80}
        result.append(c)
    return result


def main() -> None:
    audio = load_json(AUDIO_INDEX)
    pdf = load_json(PDF_EXTRACT) if PDF_EXTRACT.exists() else {"lessons": {}}
    grammar = load_json(GRAMMAR_EXTRACT) if GRAMMAR_EXTRACT.exists() else {"lessons": {}}
    transcripts: dict[str, str] = {}
    if AUDIO_TRANSCRIPTS.exists():
        transcripts = load_json(AUDIO_TRANSCRIPTS)

    index_lessons = []
    for n in range(0, 19):
        lid = f"L{n:02d}"
        tracks = audio.get("by_lesson", {}).get(lid, [])
        if n == 0:
            lesson = {
                "lesson_id": "L00",
                "lesson": 0,
                "title_en": "Classroom Japanese",
                "title_jp": "教室の日本語",
                "topic_en": "Getting started",
                "pdf_pages": [],
                "can_dos": [],
                "activities": [
                    {
                        "id": f"A{i+1}",
                        "kind": "classroom",
                        "book_activity": i + 1,
                        "can_do_id": None,
                        "label": t["label"],
                        "audio": [t["rel_path"]],
                        "key_phrases": [],
                        "prompt_en": "Listen to classroom Japanese used by the teacher.",
                    }
                    for i, t in enumerate(tracks)
                ],
                "grammar": [],
                "vocab": [],
                "quiz_bank": [],
                "unlock_requires_mastery": False,
            }
        else:
            pdf_L = pdf.get("lessons", {}).get(lid, {})
            phrases = pdf_L.get("key_phrases") or []
            can_dos = merge_can_dos(n, pdf_L.get("can_dos") or [], phrases)
            # Attach key phrases onto first matching activities later
            activities = build_activities(n, tracks, can_dos)
            if n == 1:
                apply_l01_phrases(activities)
                apply_l01_book_flow(activities)
                write_l01_phrase_reference(activities)
                for a in activities:
                    attach_phrase_meta(a)
            elif n == 2:
                apply_l02_phrases(activities)
                apply_generic_book_flow(n, activities)
                apply_l02_book_flow_overrides(activities)
            elif transcripts:
                apply_phrases_from_transcripts(n, activities, transcripts)
            else:
                pi = 0
                for a in activities:
                    if a["kind"] in ("speaking", "listening", "conversation", "vocabulary") and phrases:
                        a["key_phrases"] = phrases[pi : pi + 3]
                        pi = (pi + 3) % max(len(phrases), 1)
                apply_generic_book_flow(n, activities)
            quiz_scenarios = build_quiz_scenarios(n, can_dos)
            quiz_scenarios = enrich_quiz_scenarios(n, activities, can_dos, quiz_scenarios)
            quiz_scenarios = enrich_quiz_from_activities(n, can_dos, activities, quiz_scenarios)
            g = grammar.get("lessons", {}).get(lid, {})
            grammar_points = [
                {
                    "point": p["point"],
                    "worksheet_pages": [p["page"]],
                    "examples": [],
                }
                for p in g.get("points", [])
            ]
            vocab = []
            for a in activities:
                if a["kind"] == "vocabulary":
                    for ph in a.get("key_phrases") or []:
                        vocab.append({"jp": ph, "reading": "", "en": "", "tags": [lid]})
            # Dedup vocab
            seen = set()
            uniq_v = []
            for v in vocab:
                if v["jp"] in seen:
                    continue
                seen.add(v["jp"])
                uniq_v.append(v)

            title_en = pdf_L.get("title_en") or f"Lesson {n}"
            topic_en = pdf_L.get("topic_en") or ""
            lesson = {
                "lesson_id": lid,
                "lesson": n,
                "title_en": title_en,
                "title_jp": pdf_L.get("title_jp") or "",
                "topic_en": topic_en,
                "pdf_pages": pdf_L.get("pdf_pages") or [],
                "intro_questions": build_intro_questions(n, title_en, topic_en, can_dos),
                "can_dos": can_dos,
                "activities": activities,
                "grammar": grammar_points,
                "vocab": uniq_v,
                "quiz_bank": build_quiz(can_dos, phrases),
                "quiz_scenarios": quiz_scenarios,
                "english_notes": (pdf_L.get("english_notes") or "")[:1500],
                "unlock_requires_mastery": True,
            }

        out = STARTER / f"{lid}.yaml"
        out.write_text(
            yaml.safe_dump(lesson, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8",
        )
        index_lessons.append(
            {
                "lesson_id": lid,
                "title_en": lesson["title_en"],
                "topic_en": lesson.get("topic_en", ""),
                "can_do_count": len(lesson.get("can_dos") or []),
                "activity_count": len(lesson.get("activities") or []),
                "audio_count": len(tracks),
            }
        )
        print(f"Wrote {out.name}: {index_lessons[-1]}")

    index = {
        "book": "irodori_starter",
        "level": "A1",
        "title": "Irodori Starter",
        "lessons": index_lessons,
        "assets": {
            "pdf": "assets/irodori_starter.pdf",
            "grammar_pdf": "assets/Grammar_Worksheets_X.pdf",
            "audio_dir": "assets/audio",
        },
    }
    (STARTER / "index.yaml").write_text(
        yaml.safe_dump(index, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print("Wrote index.yaml")


if __name__ == "__main__":
    main()
