"""Curated listen_fill blanks for activities the PDF extractor cannot resolve cleanly.

Keys: (lesson_id, activity_id)
"""

from __future__ import annotations

# Verified against Irodori PDF worksheets + starter audio transcripts.
FILL_CATALOG: dict[tuple[str, str], tuple[int, list[dict]]] = {
    ("L06", "A4"): (
        162,
        [
            {
                "prompt_jp": "ホットコーヒー、＿。",
                "answers": ["お願いします"],
                "full_jp": "ホットコーヒー、お願いします。",
                "answer_alts": ["ください"],
            },
            {
                "prompt_jp": "Sサイズ、＿。",
                "answers": ["お願いします"],
                "full_jp": "Sサイズ、お願いします。",
                "answer_alts": ["ください"],
            },
            {
                "prompt_jp": "チーズバーガーと、てりやきバーガーと、フィッシュバーガー、＿。",
                "answers": ["ください"],
                "full_jp": "チーズバーガーと、てりやきバーガーと、フィッシュバーガー、ください。",
                "answer_alts": ["お願いします"],
            },
            {
                "prompt_jp": "これ、＿。",
                "answers": ["ください"],
                "full_jp": "これ、ください。",
                "answer_alts": ["お願いします"],
            },
        ],
    ),
    ("L06", "A9"): (
        165,
        [
            {"prompt_jp": "何＿か？", "answers": ["にします"], "full_jp": "何にしますか？"},
            {"prompt_jp": "私は、うどん＿。", "answers": ["にします"], "full_jp": "私は、うどんにします。"},
            {"prompt_jp": "私は、カレー＿。", "answers": ["にします"], "full_jp": "私は、カレーにします。"},
        ],
    ),
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
    ),
    ("L07", "A9"): (
        187,
        [
            {
                "prompt_jp": "電子レンジは＿？",
                "answers": ["ありますか"],
                "full_jp": "電子レンジはありますか？",
            },
            {"prompt_jp": "＿。", "answers": ["あります"], "full_jp": "あります。"},
            {
                "prompt_jp": "トースターは＿？",
                "answers": ["ありますか"],
                "full_jp": "トースターはありますか？",
            },
            {
                "prompt_jp": "トースターは＿。",
                "answers": ["ありません"],
                "full_jp": "トースターはありません。",
            },
            {
                "prompt_jp": "ベッドは＿。",
                "answers": ["ないです"],
                "full_jp": "ベッドはないです。",
                "answer_alts": ["ありません"],
            },
            {
                "prompt_jp": "＿。",
                "answers": ["ないです"],
                "full_jp": "ないです。",
                "answer_alts": ["ありません"],
            },
        ],
    ),
    ("L07", "A19"): (
        191,
        [
            {"prompt_jp": "ちょっと＿です。", "answers": ["せまい"], "full_jp": "ちょっとせまいです。",
             "answer_alts": ["狭い"]},
            {
                "prompt_jp": "ちょっと＿です。でも、＿です。",
                "answers": ["ふるい", "広い"],
                "full_jp": "ちょっとふるいです。でも、広いです。",
                "answer_alts": ["古い"],
            },
            {"prompt_jp": "とても＿です。", "answers": ["きれい"], "full_jp": "とてもきれいです。",
             "answer_alts": ["綺麗"]},
            {"prompt_jp": "＿です。", "answers": ["しずか"], "full_jp": "しずかです。",
             "answer_alts": ["静か"]},
        ],
    ),
    ("L07", "A25"): (
        195,
        [
            {"prompt_jp": "いえ、＿です。", "answers": ["広くない"], "full_jp": "いえ、広くないです。"},
            {
                "prompt_jp": "あまり＿です。",
                "answers": ["静かじゃない"],
                "full_jp": "あまり静かじゃないです。",
                "answer_alts": ["しずかじゃない"],
            },
            {
                "prompt_jp": "（家は）＿です。",
                "answers": ["大きくない"],
                "full_jp": "（家は）大きくないです。",
            },
            {
                "prompt_jp": "いえ、＿です。",
                "answers": ["新しくない"],
                "full_jp": "いえ、新しくないです。",
            },
        ],
    ),
    ("L08", "A7"): (
        217,
        [
            {
                "prompt_jp": "ここは男性の更衣室です。ここ＿着替えます。",
                "answers": ["で"],
                "full_jp": "ここは男性の更衣室です。ここで着替えます。",
            },
            {
                "prompt_jp": "ここは給湯室です。ここ＿お茶をいれます。",
                "answers": ["で"],
                "full_jp": "ここは給湯室です。ここでお茶をいれます。",
            },
            {
                "prompt_jp": "ここは会議室です。ここ＿打ち合わせをします。",
                "answers": ["で"],
                "full_jp": "ここは会議室です。ここで打ち合わせをします。",
            },
            {
                "prompt_jp": "ここは食堂です。ここ＿ご飯を食べます。",
                "answers": ["で"],
                "full_jp": "ここは食堂です。ここでご飯を食べます。",
            },
        ],
    ),
    ("L11", "A7"): (
        286,
        [
            {"prompt_jp": "趣味は、＿ですか？", "answers": ["何"], "full_jp": "趣味は、何ですか？"},
            {"prompt_jp": "ゲーム＿。", "answers": ["です"], "full_jp": "ゲームです。"},
            {
                "prompt_jp": "アニメ＿。",
                "answers": ["が好きです"],
                "full_jp": "アニメが好きです。",
            },
            {"prompt_jp": "読書と映画＿。", "answers": ["です"], "full_jp": "読書と映画です。"},
            {
                "prompt_jp": "スポーツ＿。あと、料理＿。",
                "answers": ["です", "も好きです"],
                "full_jp": "スポーツです。あと、料理も好きです。",
            },
        ],
    ),
    ("L11", "A11"): (
        290,
        [
            {
                "prompt_jp": "＿スポーツが好きですか？",
                "answers": ["どんな"],
                "full_jp": "どんなスポーツが好きですか？",
            },
            {
                "prompt_jp": "＿マンガが好きですか？",
                "answers": ["どんな"],
                "full_jp": "どんなマンガが好きですか？",
            },
            {
                "prompt_jp": "スポーツは、＿好き＿です。",
                "answers": ["あまり", "じゃない"],
                "full_jp": "スポーツは、あまり好きじゃないです。",
            },
            {
                "prompt_jp": "「ドラゴンボール」が＿です。",
                "answers": ["大好き"],
                "full_jp": "「ドラゴンボール」が大好きです。",
            },
        ],
    ),
    ("L14", "A7"): (
        371,
        [
            {
                "prompt_jp": "トイレは、＿か？",
                "answers": ["どこです"],
                "full_jp": "トイレは、どこですか？",
                "answer_alts": ["どこ"],
            },
            {
                "prompt_jp": "コインロッカーは、＿か？",
                "answers": ["どこにあります"],
                "full_jp": "コインロッカーは、どこにありますか？",
                "answer_alts": ["どこです"],
            },
            {
                "prompt_jp": "この近く＿、コンビニは＿か？",
                "answers": ["に", "あります"],
                "full_jp": "この近くに、コンビニはありますか？",
            },
            {
                "prompt_jp": "この近く＿、ATMは＿か？",
                "answers": ["に", "あります"],
                "full_jp": "この近くに、ATMはありますか？",
            },
        ],
    ),
    ("L14", "A17"): (
        375,
        [
            {
                "prompt_jp": "今、＿にいますか？",
                "answers": ["どこ"],
                "full_jp": "今、どこにいますか？",
            },
            {
                "prompt_jp": "改札の＿にいます。",
                "answers": ["前"],
                "full_jp": "改札の前にいます。",
            },
            {
                "prompt_jp": "コンビニの＿にいます。",
                "answers": ["中"],
                "full_jp": "コンビニの中にいます。",
            },
            {
                "prompt_jp": "インフォメーションの＿です。",
                "answers": ["横"],
                "full_jp": "インフォメーションの横です。",
            },
            {
                "prompt_jp": "エスカレーターの＿にいます。",
                "answers": ["下"],
                "full_jp": "エスカレーターの下にいます。",
            },
        ],
    ),
    ("L15", "A16"): (
        402,
        [
            {
                "prompt_jp": "ドライヤーは、＿ですか？",
                "answers": ["どこ"],
                "full_jp": "ドライヤーは、どこですか？",
            },
            {
                "prompt_jp": "カメラは、＿ですか？",
                "answers": ["何階"],
                "full_jp": "カメラは、何階ですか？",
                "answer_alts": ["なんがい"],
            },
            {
                "prompt_jp": "スマホケースがほしいんですが、＿ありますか？",
                "answers": ["どこに"],
                "full_jp": "スマホケースがほしいんですが、どこにありますか？",
            },
            {
                "prompt_jp": "延長コードが＿……。",
                "answers": ["ほしいんですが"],
                "full_jp": "延長コードがほしいんですが……。",
                "answer_alts": ["欲しいんですが"],
            },
        ],
    ),
    ("L15", "A29"): (
        407,
        [
            {
                "prompt_jp": "（この傘、）＿ですね。",
                "answers": ["おもしろい"],
                "full_jp": "（この傘、）おもしろいですね。",
            },
            {
                "prompt_jp": "（この帽子、）＿ですね。",
                "answers": ["かっこいい"],
                "full_jp": "（この帽子、）かっこいいですね。",
            },
            {
                "prompt_jp": "このバッグ、＿！",
                "answers": ["かわいい"],
                "full_jp": "このバッグ、かわいい！",
                "answer_alts": ["可愛い"],
            },
            {
                "prompt_jp": "本当！＿ですね。",
                "answers": ["かわいい"],
                "full_jp": "本当！かわいいですね。",
                "answer_alts": ["可愛い"],
            },
            {
                "prompt_jp": "このコート、＿！",
                "answers": ["すてき"],
                "full_jp": "このコート、すてき！",
                "answer_alts": ["素敵"],
            },
            {
                "prompt_jp": "＿ですね。でも、＿ですね。",
                "answers": ["おしゃれ", "高い"],
                "full_jp": "おしゃれですね。でも、高いですね。",
            },
        ],
    ),
    ("L18", "A15"): (
        489,
        [
            {
                "prompt_jp": "＿、景色もきれいでした。",
                "answers": ["それに"],
                "full_jp": "それに、景色もきれいでした。",
            },
            {
                "prompt_jp": "＿、温泉の近くで、鶏の天ぷらを食べました。",
                "answers": ["それから"],
                "full_jp": "それから、温泉の近くで、鶏の天ぷらを食べました。",
            },
            {
                "prompt_jp": "おいしかったです。＿、ちょっと高かったです。",
                "answers": ["でも"],
                "full_jp": "おいしかったです。でも、ちょっと高かったです。",
            },
        ],
    ),
    ("L09", "A6"): (
        242,
        [
            {
                "prompt_jp": "朝、何時＿起きますか？",
                "answers": ["に"],
                "full_jp": "朝、何時に起きますか？",
            },
            {
                "prompt_jp": "5時＿起きます。",
                "answers": ["に"],
                "full_jp": "5時に起きます。",
            },
            {
                "prompt_jp": "私は、だいたい、7時＿起きます。",
                "answers": ["に"],
                "full_jp": "私は、だいたい、7時に起きます。",
            },
            {
                "prompt_jp": "夜は、何時＿寝ますか？",
                "answers": ["に"],
                "full_jp": "夜は、何時に寝ますか？",
            },
            {
                "prompt_jp": "10時半＿寝ます。",
                "answers": ["に"],
                "full_jp": "10時半に寝ます。",
            },
            {
                "prompt_jp": "11時＿寝ます。",
                "answers": ["に"],
                "full_jp": "11時に寝ます。",
                "answer_alts": ["ごろ"],
            },
        ],
    ),
    ("L09", "A10"): (
        245,
        [
            {
                "prompt_jp": "仕事は、毎朝9時＿です。",
                "answers": ["から"],
                "full_jp": "仕事は、毎朝9時からです。",
            },
            {
                "prompt_jp": "12時＿1時＿、昼休みです。",
                "answers": ["から", "まで"],
                "full_jp": "12時から1時まで、昼休みです。",
            },
            {
                "prompt_jp": "3時＿3時半＿、休み時間です。",
                "answers": ["から", "まで"],
                "full_jp": "3時から3時半まで、休み時間です。",
            },
            {
                "prompt_jp": "仕事は、6時＿です。",
                "answers": ["まで"],
                "full_jp": "仕事は、6時までです。",
            },
        ],
    ),
    ("L09", "A16"): (
        249,
        [
            {
                "prompt_jp": "＿が＿ですか？",
                "answers": ["いつ", "いい"],
                "full_jp": "いつがいいですか？",
            },
            {
                "prompt_jp": "私は、土曜日が＿です。ヌンさんは？",
                "answers": ["いい"],
                "full_jp": "私は、土曜日がいいです。ヌンさんは？",
            },
            {
                "prompt_jp": "すみません、土曜日は＿……。",
                "answers": ["ちょっと"],
                "full_jp": "すみません、土曜日はちょっと……。",
            },
            {
                "prompt_jp": "私は、日曜日が＿です。",
                "answers": ["いい"],
                "full_jp": "私は、日曜日がいいです。",
            },
            {
                "prompt_jp": "私は、日曜日は＿です。すみません。",
                "answers": ["だめ"],
                "full_jp": "私は、日曜日はだめです。すみません。",
                "answer_alts": ["ダメ"],
            },
        ],
    ),
    ("L10", "A10"): (
        261,
        [
            {
                "prompt_jp": "ちょっと、手伝っ＿。",
                "answers": ["てください"],
                "full_jp": "ちょっと、手伝ってください。",
            },
            {
                "prompt_jp": "段ボール、そこに置い＿。",
                "answers": ["てください"],
                "full_jp": "段ボール、そこに置いてください。",
            },
            {
                "prompt_jp": "これ、鈴木さんに持って行っ＿。",
                "answers": ["てください"],
                "full_jp": "これ、鈴木さんに持って行ってください。",
            },
            {
                "prompt_jp": "テーブルの上、片付け＿。",
                "answers": ["てください"],
                "full_jp": "テーブルの上、片付けてください。",
            },
            {
                "prompt_jp": "そこのドライバー、取っ＿。",
                "answers": ["てください"],
                "full_jp": "そこのドライバー、取ってください。",
            },
            {
                "prompt_jp": "ごみ、捨て＿。",
                "answers": ["てください"],
                "full_jp": "ごみ、捨ててください。",
            },
            {
                "prompt_jp": "いす、並べ＿。",
                "answers": ["てください"],
                "full_jp": "いす、並べてください。",
            },
            {
                "prompt_jp": "窓、閉め＿？",
                "answers": ["てくれる"],
                "full_jp": "窓、閉めてくれる？",
                "answer_alts": ["てくれますか", "てください"],
            },
            {
                "prompt_jp": "プロジェクタとリモコン、持って来＿？",
                "answers": ["てくれる"],
                "full_jp": "プロジェクタとリモコン、持って来てくれる？",
                "answer_alts": ["てくれますか", "てください"],
            },
        ],
    ),
    ("L13", "A8"): (
        338,
        [
            {
                "prompt_jp": "＿バスは、空港＿か？",
                "answers": ["この", "に行きます"],
                "full_jp": "このバスは、空港に行きますか？",
            },
            {
                "prompt_jp": "＿電車は、大阪駅＿か？",
                "answers": ["この", "に行きます"],
                "full_jp": "この電車は、大阪駅に行きますか？",
            },
            {
                "prompt_jp": "＿船は、黒島＿か？",
                "answers": ["この", "に行きます"],
                "full_jp": "この船は、黒島に行きますか？",
            },
        ],
    ),
    ("L13", "A16"): (
        341,
        [
            {
                "prompt_jp": "＿は、さきやま新都心ですか？",
                "answers": ["ここ"],
                "full_jp": "ここは、さきやま新都心ですか？",
            },
            {
                "prompt_jp": "＿は、どこですか？",
                "answers": ["ここ"],
                "full_jp": "ここは、どこですか？",
            },
            {
                "prompt_jp": "＿、どこですか？",
                "answers": ["今"],
                "full_jp": "今、どこですか？",
            },
            {
                "prompt_jp": "＿は、どこですか？",
                "answers": ["次"],
                "full_jp": "次は、どこですか？",
            },
            {
                "prompt_jp": "＿は、浦田ですか？",
                "answers": ["次"],
                "full_jp": "次は、浦田ですか？",
            },
        ],
    ),
    ("L14", "A28"): (
        379,
        [
            {
                "prompt_jp": "＿公園ですね。",
                "answers": ["広い"],
                "full_jp": "広い公園ですね。",
            },
            {
                "prompt_jp": "＿お寺がありますね。",
                "answers": ["古い"],
                "full_jp": "古いお寺がありますね。",
            },
            {
                "prompt_jp": "＿ビルがたくさんありますね。",
                "answers": ["高い"],
                "full_jp": "高いビルがたくさんありますね。",
            },
            {
                "prompt_jp": "＿通りですね。",
                "answers": ["にぎやかな"],
                "full_jp": "にぎやかな通りですね。",
            },
            {
                "prompt_jp": "＿水ですね。",
                "answers": ["きれいな"],
                "full_jp": "きれいな水ですね。",
            },
            {
                "prompt_jp": "＿建物ですね。",
                "answers": ["大きな"],
                "full_jp": "大きな建物ですね。",
            },
            {
                "prompt_jp": "＿ですね。",
                "answers": ["大きい"],
                "full_jp": "大きいですね。",
            },
        ],
    ),
    ("L15", "A9"): (
        397,
        [
            {
                "prompt_jp": "電池が＿、どこ＿買えますか？",
                "answers": ["欲しいんですが", "で"],
                "full_jp": "電池が欲しいんですが、どこで買えますか？",
                "answer_alts": ["ほしいんですが"],
            },
            {
                "prompt_jp": "コンビニ＿買えますよ。",
                "answers": ["で"],
                "full_jp": "コンビニで買えますよ。",
            },
            {
                "prompt_jp": "100円ショップ＿ありますよ。",
                "answers": ["に"],
                "full_jp": "100円ショップにありますよ。",
            },
        ],
    ),
    ("L16", "A23"): (
        431,
        [
            {
                "prompt_jp": "たい焼き8＿、ください。",
                "answers": ["つ"],
                "full_jp": "たい焼き8つ、ください。",
            },
            {
                "prompt_jp": "コロッケ4＿と、シュウマイ10＿、ください。",
                "answers": ["つ", "個"],
                "full_jp": "コロッケ4つと、シュウマイ10個、ください。",
            },
            {
                "prompt_jp": "ひき肉200＿、ください。",
                "answers": ["g"],
                "full_jp": "ひき肉200g、ください。",
                "answer_alts": ["グラム"],
            },
            {
                "prompt_jp": "昆布2＿、たらこ1＿、梅3＿、ください。",
                "answers": ["つ", "つ", "つ"],
                "full_jp": "昆布2つ、たらこ1つ、梅3つ、ください。",
            },
            {
                "prompt_jp": "チョコレートケーキとチーズケーキ、2個＿お願いします。",
                "answers": ["ずつ"],
                "full_jp": "チョコレートケーキとチーズケーキ、2個ずつお願いします。",
            },
        ],
    ),
    ("L17", "A7"): (
        453,
        [
            {
                "prompt_jp": "休みは、何をし＿か？",
                "answers": ["ました"],
                "full_jp": "休みは、何をしましたか？",
            },
            {
                "prompt_jp": "お風呂と台所を掃除し＿。",
                "answers": ["ました"],
                "full_jp": "お風呂と台所を掃除しました。",
            },
            {
                "prompt_jp": "オーケストラのコンサートに行き＿。",
                "answers": ["ました"],
                "full_jp": "オーケストラのコンサートに行きました。",
            },
            {
                "prompt_jp": "服を買い＿。",
                "answers": ["ました"],
                "full_jp": "服を買いました。",
            },
            {
                "prompt_jp": "昼まで寝＿。",
                "answers": ["ました"],
                "full_jp": "昼まで寝ました。",
            },
            {
                "prompt_jp": "ネットで、家族と話し＿。",
                "answers": ["ました"],
                "full_jp": "ネットで、家族と話しました。",
            },
            {
                "prompt_jp": "何＿し＿。",
                "answers": ["も", "ませんでした"],
                "full_jp": "何もしませんでした。",
            },
            {
                "prompt_jp": "家でゆっくりし＿。",
                "answers": ["ました"],
                "full_jp": "家でゆっくりしました。",
            },
        ],
    ),
}

# Breakfast katachi (p.140 形に注目) — also in katachi_fix_catalog.py
FILL_CATALOG[("L05", "A33")] = (
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
)
FILL_CATALOG[("L05", "A34")] = (
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
)
FILL_CATALOG[("L08", "A12")] = (
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
)
FILL_CATALOG[("L16", "A15")] = (
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
)
FILL_CATALOG[("L18", "A12")] = (
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
)

# L05 drink offer patterns (p.133 形に注目)
FILL_CATALOG[("L05", "A24")] = (
    133,
    [
        {"prompt_jp": "お茶、＿か？", "answers": ["飲みます"], "full_jp": "お茶、飲みますか？"},
        {"prompt_jp": "お酒、＿？", "answers": ["飲む"], "full_jp": "お酒、飲む？"},
        {"prompt_jp": "何、＿か？", "answers": ["飲みます"], "full_jp": "何、飲みますか？"},
        {"prompt_jp": "何、＿？", "answers": ["飲む"], "full_jp": "何、飲む？"},
    ],
)
FILL_CATALOG[("L05", "A25")] = (
    133,
    [
        {
            "prompt_jp": "お茶、飲みますか？ — はい、＿。",
            "answers": ["お願いします"],
            "full_jp": "はい、お願いします。",
        },
        {
            "prompt_jp": "お茶、飲みますか？ — いいえ、＿。",
            "answers": ["けっこうです"],
            "answer_alts": ["結構です"],
            "full_jp": "いいえ、けっこうです。",
        },
    ],
)
FILL_CATALOG[("L05", "A26")] = (
    133,
    [
        {"prompt_jp": "何、＿か？", "answers": ["飲みます"], "full_jp": "何、飲みますか？"},
        {
            "prompt_jp": "じゃあ、＿、お願いします。",
            "answers": ["ビール"],
            "full_jp": "じゃあ、ビール、お願いします。",
        },
    ],
)

# OCR/heuristic junk — demote to listen_repeat_all.
DEMOTE: list[tuple[str, str]] = [
    ("L11", "A21"),
    ("L18", "A11"),
]
