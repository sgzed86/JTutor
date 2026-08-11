"""Curated fixes for OCR-concatenated katachi / counting / vocab mega-strings.

Keys: (lesson_id, activity_id)

- REPEAT_ALL: split into separate key_phrases; book_mode listen_repeat_all
- FILL: convert to listen_fill with blanks + cleaned key_phrases
- VOCAB: per-word vocab_drill lists (starter or elementary1)
"""

from __future__ import annotations

# (lesson_id, activity_id) -> list of phrases (one per step)
REPEAT_ALL: dict[tuple[str, str], list[str]] = {
    ("L06", "A17"): [
        "ひとつ",
        "ふたつ",
        "みっつ",
        "よっつ",
        "いつつ",
        "むっつ",
        "ななつ",
        "やっつ",
        "ここのつ",
        "いくつ",
    ],
    ("L10", "A16"): [
        "一時",
        "二時",
        "三時",
        "四時",
        "五時",
        "六時",
        "七時",
        "八時",
        "九時",
        "十時",
        "十一時",
        "十二時",
        "半",
    ],
    ("L15", "A17"): [
        "一階",
        "二階",
        "三階",
        "四階",
        "五階",
        "六階",
        "七階",
        "八階",
        "九階",
        "十階",
    ],
    ("L16", "A24"): [
        "一個",
        "二個",
        "三個",
        "四個",
        "五個",
        "六個",
        "七個",
        "八個",
        "九個",
        "十個",
    ],
}

# (lesson_id, activity_id) -> (pdf_page, blanks, key_phrases)
FILL: dict[tuple[str, str], tuple[int, list[dict], list[str]]] = {
    ("L05", "A33"): (
        140,
        [
            {
                "prompt_jp": "朝ご飯、いつも何を＿か？",
                "answers": ["食べます"],
                "full_jp": "朝ご飯、いつも何を食べますか？",
            },
            {
                "prompt_jp": "私はシリアルを＿。",
                "answers": ["食べます"],
                "full_jp": "私はシリアルを食べます。",
            },
            {
                "prompt_jp": "私は朝ご飯はあまり＿。",
                "answers": ["食べません"],
                "full_jp": "私は朝ご飯はあまり食べません。",
            },
            {
                "prompt_jp": "私も＿です。",
                "answers": ["食べない"],
                "full_jp": "私も食べないです。",
            },
        ],
        [
            "朝ご飯、いつも何を食べますか",
            "私はシリアルを食べます",
            "私は朝ご飯はあまり食べません",
            "私も食べないです",
        ],
    ),
    ("L05", "A34"): (
        140,
        [
            {
                "prompt_jp": "朝ご飯、いつも何を＿か？",
                "answers": ["食べます"],
                "full_jp": "朝ご飯、いつも何を食べますか？",
            },
            {
                "prompt_jp": "私はパンと卵とヨーグルトをよく＿。",
                "answers": ["食べます"],
                "full_jp": "私はパンと卵とヨーグルトをよく食べます。",
            },
            {
                "prompt_jp": "朝ご飯はあまり＿。",
                "answers": ["食べません"],
                "full_jp": "朝ご飯はあまり食べません。",
            },
        ],
        [
            "朝ご飯、いつも何を食べますか",
            "私はパンと卵とヨーグルトをよく食べます",
            "朝ご飯はあまり食べません",
        ],
    ),
    ("L08", "A12"): (
        221,
        [
            {
                "prompt_jp": "山田さんは＿いますか？",
                "answers": ["どこに"],
                "full_jp": "山田さんはどこにいますか？",
            },
            {
                "prompt_jp": "食堂＿。",
                "answers": ["にいます"],
                "full_jp": "食堂にいます。",
            },
            {
                "prompt_jp": "長井さんは＿ですか？",
                "answers": ["どこ"],
                "full_jp": "長井さんはどこですか？",
            },
            {
                "prompt_jp": "会議室＿よ。",
                "answers": ["にいる"],
                "full_jp": "会議室にいるよ。",
                "answer_alts": ["にいます"],
            },
            {
                "prompt_jp": "土田さんは＿か？",
                "answers": ["います"],
                "full_jp": "土田さんはいますか？",
            },
            {
                "prompt_jp": "＿ね。",
                "answers": ["いません"],
                "full_jp": "いませんね。",
            },
            {
                "prompt_jp": "アマンダさんは＿か？",
                "answers": ["います"],
                "full_jp": "アマンダさんはいますか？",
            },
            {
                "prompt_jp": "＿ですね。",
                "answers": ["いない"],
                "full_jp": "いないですね。",
                "answer_alts": ["いません"],
            },
        ],
        [
            "山田さんはどこにいますか",
            "食堂にいます",
            "長井さんはどこですか",
            "会議室にいるよ",
            "土田さんはいますか",
            "いませんね",
            "アマンダさんはいますか",
            "いないですね",
        ],
    ),
    ("L16", "A15"): (
        432,
        [
            {
                "prompt_jp": "そのカレンダー、＿か？",
                "answers": ["いくらです"],
                "full_jp": "そのカレンダー、いくらですか？",
            },
            {
                "prompt_jp": "これは＿です。",
                "answers": ["240円"],
                "full_jp": "これは240円です。",
                "answer_alts": ["二百四十円"],
            },
            {
                "prompt_jp": "じゃあ、＿。",
                "answers": ["それください"],
                "full_jp": "じゃあ、それください。",
            },
            {
                "prompt_jp": "このお菓子、＿か？",
                "answers": ["いくらです"],
                "full_jp": "このお菓子、いくらですか？",
            },
            {
                "prompt_jp": "＿です。",
                "answers": ["230円"],
                "full_jp": "230円です。",
                "answer_alts": ["二百三十円"],
            },
            {
                "prompt_jp": "じゃあ、＿。",
                "answers": ["これもお願いします"],
                "full_jp": "じゃあ、これもお願いします。",
            },
            {
                "prompt_jp": "そのまねきねこは＿です。",
                "answers": ["800円"],
                "full_jp": "そのまねきねこは800円です。",
                "answer_alts": ["八百円"],
            },
            {
                "prompt_jp": "あのTシャツ、＿か？",
                "answers": ["いくらです"],
                "full_jp": "あのTシャツ、いくらですか？",
            },
            {
                "prompt_jp": "あれは＿です。",
                "answers": ["1990円"],
                "full_jp": "あれは1990円です。",
                "answer_alts": ["千九百九十円", "1,990円"],
            },
            {
                "prompt_jp": "じゃあ、＿。",
                "answers": ["あれください"],
                "full_jp": "じゃあ、あれください。",
            },
        ],
        [
            "そのカレンダー、いくらですか",
            "これは240円です",
            "じゃあ、それください",
            "このお菓子、いくらですか",
            "230円です",
            "じゃあ、これもお願いします",
            "そのまねきねこは800円です",
            "あのTシャツ、いくらですか",
            "あれは1990円です",
            "じゃあ、あれください",
        ],
    ),
    ("L18", "A12"): (
        488,
        [
            {
                "prompt_jp": "京都へ＿です。",
                "answers": ["行きたい"],
                "full_jp": "京都へ行きたいです。",
                "answer_alts": ["いきたい"],
            },
            {
                "prompt_jp": "新宿の水族館に＿です。",
                "answers": ["行きたい"],
                "full_jp": "新宿の水族館に行きたいです。",
                "answer_alts": ["いきたい"],
            },
        ],
        [
            "京都へ行きたいです",
            "新宿の水族館に行きたいです",
        ],
    ),
    # Clean key_phrases on already-curated fill (OCR mega-string left behind)
    ("L06", "A16"): (
        170,
        [
            {
                "prompt_jp": "生ビール＿と、ウーロン茶＿（お願いします）。",
                "answers": ["3つ", "1つ"],
                "full_jp": "生ビール3つと、ウーロン茶1つ（お願いします）。",
                "answer_alts": ["みっつ", "ひとつ"],
            },
            {
                "prompt_jp": "枝豆＿、ください。",
                "answers": ["2つ"],
                "full_jp": "枝豆2つ、ください。",
                "answer_alts": ["ふたつ"],
            },
            {
                "prompt_jp": "マヨネーズ、＿か？",
                "answers": ["あります"],
                "full_jp": "マヨネーズ、ありますか？",
            },
        ],
        [
            "生ビール3つと、ウーロン茶1つ、お願いします",
            "枝豆2つ、ください",
            "マヨネーズ、ありますか",
        ],
    ),
}

# book is inferred from lesson id prefix: L* -> starter, EL* -> elementary1
VOCAB: dict[tuple[str, str], list[str]] = {
    ("L12", "A3"): [
        "カレンダー",
        "今日",
        "明日",
        "あさって",
        "今週",
        "来週",
    ],
    ("EL16", "A1"): [
        "顔",
        "頭",
        "歯",
        "首",
        "目",
        "耳",
        "口",
        "体",
        "胸",
        "おなか",
        "足",
        "背中",
        "腰",
        "腕",
        "手",
        "指",
    ],
    ("EL16", "A2"): [
        "頭が痛いです",
        "歯が痛いです",
        "目が痛いです",
        "耳が痛いです",
        "胸が痛いです",
        "腰が痛いです",
        "肩が痛いです",
        "背中が痛いです",
        "お腹が痛いです",
        "足が痛いです",
    ],
}

# Audio transcript cleanups keyed by relative audio path under content/*/audio_transcripts.json
TRANSCRIPT_FIXES: dict[str, str] = {
    "assets/audio/X_[06-17]_katachi2_counting.mp3": "ひとつ ふたつ みっつ よっつ いつつ むっつ ななつ やっつ ここのつ いくつ",
    "assets/audio/X_[10-16]_katachi2_time.mp3": "一時 二時 三時 四時 五時 六時 七時 八時 九時 十時 十一時 十二時 半",
    "assets/audio/X_[15-17]_katachi2_floor.mp3": "一階 二階 三階 四階 五階 六階 七階 八階 九階 十階",
    "assets/audio/X_[16-24]_katachi2_number.mp3": "一個 二個 三個 四個 五個 六個 七個 八個 九個 十個",
    "assets/audio/X_[18-12]_katachi.mp3": "京都へ行きたいです。新宿の水族館に行きたいです。",
    "assets/audio/X_[16-15]_katachi.mp3": (
        "そのカレンダー、いくらですか？これは240円です。じゃあ、それください。"
        "このお菓子、いくらですか？230円です。じゃあ、これもお願いします。"
        "そのまねきねこは800円です。あのTシャツ、いくらですか？"
        "あれは1990円です。じゃあ、あれください。"
    ),
    "assets/audio/X_[08-12]_katachi.mp3": (
        "山田さんはどこにいますか？食堂にいます。長井さんはどこですか？"
        "会議室にいるよ。土田さんはいますか？いませんね。"
        "アマンダさんはいますか？いないですね。"
    ),
    "assets/audio/X_[05-33]_katachi1.mp3": (
        "朝ご飯、いつも何を食べますか？私はシリアルを食べます。牛乳を飲みます。"
        "私は朝ご飯はあまり食べません。私も食べないです。"
    ),
    "assets/audio/X_[05-34]_katachi2.mp3": (
        "朝ご飯、いつも何を食べますか？私はパンと卵とヨーグルトをよく食べます。"
        "朝ご飯はあまり食べません。"
    ),
    "assets/audio/X_[12-03]_kotoba1.mp3": "カレンダー 今日 明日 あさって 今週 来週",
    "assets/audio/X_[06-16]_katachi1.mp3": (
        "生ビール3つと、ウーロン茶1つ、お願いします。枝豆2つ、ください。マヨネーズ、ありますか？"
    ),
    "assets/audio/Y_[16-01]_kotoba1.mp3": (
        "顔 頭 歯 首 目 耳 口 体 胸 おなか 足 背中 腰 腕 手 指"
    ),
    "assets/audio/Y_[16-02]_kotoba2.mp3": (
        "頭が痛いです 歯が痛いです 目が痛いです 耳が痛いです 胸が痛いです "
        "腰が痛いです 肩が痛いです 背中が痛いです お腹が痛いです 足が痛いです"
    ),
}
