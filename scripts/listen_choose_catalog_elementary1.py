"""Curated listen_choose fixes for Elementary 1 OCR / instruction-junk.

Key: (lesson_id, activity_id) -> patch dict:
  prompt_en, picture_hint_en?, key_phrases, choices, correct_ids, choose_mode
  transcript?  (optional cleaned string for audio_transcripts.json)
"""

from __future__ import annotations


def ch(cid: str, jp: str, en: str | None = None) -> dict:
    d: dict = {"id": cid, "label_jp": jp}
    if en:
        d["label_en"] = en
    return d


LISTEN_CHOOSE: dict[tuple[str, str], dict] = {
    # --- EL03 seasons ---
    ("EL03", "A5"): {
        "prompt_en": "Listen (CD 03-05). What seasons does Joey's country have?",
        "picture_hint_en": "Seasons — summer all year.",
        "key_phrases": [
            "一年中夏です。",
            "ずっと暑いです。",
        ],
        "choices": [
            ch("a", "一年中夏です。ずっと暑いです。", "summer all year; always hot"),
            ch("b", "雨季と乾季があります", "rainy and dry seasons"),
            ch("c", "冬はとても寒くなります", "winter gets very cold"),
            ch("d", "秋が好きです", "likes autumn"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "ジョーイさんの国にはどんな季節がありますか。"
            "一年中夏です。ずっと暑いです。"
            "そうですか。"
        ),
    },
    ("EL03", "A6"): {
        "prompt_en": "Listen (CD 03-06). What seasons does Tam's country have?",
        "picture_hint_en": "Seasons — rainy season and dry season.",
        "key_phrases": [
            "雨季と乾季があります。",
            "雨季はとても暑いです。",
            "乾季は少し涼しくなります。",
        ],
        "choices": [
            ch("a", "雨季と乾季があります", "rainy and dry seasons"),
            ch("b", "一年中夏です。ずっと暑いです。", "summer all year"),
            ch("c", "冬はとても寒くなります", "winter is very cold"),
            ch("d", "秋が好きです", "likes autumn"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "タムさんの国にはどんな季節がありますか。"
            "雨季と乾季があります。"
            "そうですか。"
            "雨季はとても暑いです。"
            "ええ、でも乾季は少し涼しくなります。"
            "雨がたくさん降ります。"
        ),
    },
    ("EL03", "A7"): {
        "prompt_en": "Listen (CD 03-07). What are summers and winters like in Vyal's country?",
        "picture_hint_en": "Four seasons — very hot summers, very cold winters.",
        "key_phrases": [
            "日本と同じで四季があります。",
            "夏はとても暑いです。",
            "冬はとても寒いです。",
        ],
        "choices": [
            ch(
                "a",
                "四季があります。夏はとても暑くて、冬はとても寒いです",
                "four seasons; very hot summers, very cold winters",
            ),
            ch("b", "一年中夏です。ずっと暑いです。", "summer all year"),
            ch("c", "雨季と乾季があります", "rainy and dry seasons"),
            ch("d", "秋が好きです", "likes autumn"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "バイアルさんの国にはどんな季節がありますか。"
            "日本と同じです。四季があります。"
            "でも、夏はとても暑いです。冬はとても寒いです。"
            "そうですか。"
            "夏は40度、冬はマイナス40度になります。"
            "え？そうなんですか。"
        ),
    },
    ("EL03", "A8"): {
        "prompt_en": "Listen (CD 03-08). What is winter like in Xiao's country?",
        "picture_hint_en": "Four seasons — short summer, long cold winter.",
        "key_phrases": [
            "四季があります。",
            "夏はとても短いです。冬はとても長いです。",
            "雪がたくさん降ります。とても寒いです。",
        ],
        "choices": [
            ch("a", "冬はとても寒くなります", "winter gets very cold"),
            ch("b", "一年中夏です。ずっと暑いです。", "summer all year"),
            ch("c", "雨季と乾季があります", "rainy and dry seasons"),
            ch("d", "秋が好きです", "likes autumn"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "肖さんの国にはどんな季節がありますか。"
            "私の国にも四季があります。"
            "でも夏はとても短いです。冬はとても長いです。"
            "十月から五月まで冬です。"
            "そうですか。雪がたくさん降ります。とても寒いです。"
            "そうなんですか。"
        ),
    },
    # --- EL11 asking about ingredients ---
    # --- EL11 BBQ prep / ingredient questions ---
    ("EL11", "A4"): {
        "prompt_en": "Listen (CD 11-04). What will Marco buy for the barbecue?",
        "picture_hint_en": "Drinks for a barbecue — alcohol vs tea.",
        "key_phrases": [
            "マルコさんは飲み物をお願いします。",
            "すみません、私はお酒がダメですから。",
            "じゃあ、お茶も買っていきますね。",
        ],
        "choices": [
            ch("a", "お茶も買っていきます", "will also buy tea"),
            ch("b", "肉と野菜は私が買って行きます", "I'll buy meat and vegetables"),
            ch("c", "バナナを持っていきます", "will bring bananas"),
            ch("d", "おにぎりを作っていきます", "will make onigiri"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "じゃあ、マルコさんは飲み物をお願いします。"
            "いいですよ。ビールとワインでいいですか。"
            "あのう、すみません。私はお酒がダメですから。"
            "じゃあ、お茶も買っていきますね。"
            "ありがとうございます。"
        ),
    },
    ("EL11", "A5"): {
        "prompt_en": "Listen (CD 11-05). What will Hasegawa bring, and what about cups?",
        "picture_hint_en": "Barbecue prep — onigiri; cups at the site.",
        "key_phrases": [
            "私はおにぎりを作っていきますね。",
            "コップやお皿はどうしますか。",
            "それはバーベキュー場にありますから大丈夫です。",
        ],
        "choices": [
            ch("a", "おにぎりを作っていきます", "will make onigiri"),
            ch("b", "お茶も買っていきます", "will also buy tea"),
            ch("c", "バナナを持っていきます", "will bring bananas"),
            ch("d", "肉と野菜は私が買って行きます", "I'll buy meat and vegetables"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "じゃあ私はおにぎりを作っていきますね。"
            "いいですね。じゃあ長谷川さんはおにぎりをお願いします。"
            "コップやお皿はどうしますか。"
            "それはバーベキュー場にありますから大丈夫です。"
        ),
    },
    ("EL11", "A6"): {
        "prompt_en": "Listen (CD 11-06). What dessert will Noi bring?",
        "picture_hint_en": "Barbecue dessert — bananas to grill.",
        "key_phrases": [
            "ノイさん、デザートはどうですか。",
            "じゃあ、バナナを持っていきます。",
            "焼いて食べましょう。",
        ],
        "choices": [
            ch("a", "バナナを持っていきます", "will bring bananas"),
            ch("b", "お茶も買っていきます", "will also buy tea"),
            ch("c", "おにぎりを作っていきます", "will make onigiri"),
            ch("d", "肉と野菜は私が買って行きます", "I'll buy meat and vegetables"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "私は何を持っていきましょうか。"
            "じゃあ、ノイさん、デザートはどうですか。"
            "そうですね。じゃあ、バナナを持っていきます。焼いて食べましょう。"
            "え？バナナ？焼くんですか。"
            "はい、おいしいですよ。"
        ),
    },
    ("EL11", "A17"): {
        "prompt_en": "Listen (CD 11-17). What is the guest asking about?",
        "picture_hint_en": "Asking whether a dish contains egg.",
        "key_phrases": [
            "あのう、この料理、卵を使ってますか。",
            "いいえ、使ってませんよ。",
            "あ、じゃあ大丈夫です。いただきます。",
        ],
        "choices": [
            ch("a", "卵を使っているかどうか", "whether it uses egg"),
            ch("b", "よかったら、ピザ、どう？", "want some pizza?"),
            ch("c", "お茶", "tea"),
            ch("d", "チョコレートケーキとチーズケーキ、どっちがいいですか", "which cake?"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "さあ、どうぞ。"
            "あのう、この料理、卵を使ってますか。"
            "卵？いいえ、使ってませんよ。"
            "あ、じゃあ大丈夫です。いただきます。"
        ),
    },
    ("EL11", "A18"): {
        "prompt_en": "Listen (CD 11-18). Why won't the guest eat the pizza?",
        "picture_hint_en": "Pizza — shrimp allergy.",
        "key_phrases": [
            "よかったら、ピザ、どう？",
            "このピザ、エビが入ってますか。",
            "じゃあ私はダメです。エビのアレルギーですから。",
        ],
        "choices": [
            ch("a", "エビのアレルギーだから", "shrimp allergy"),
            ch("b", "卵を使っているかどうか", "whether it uses egg"),
            ch("c", "ハラルかどうか", "whether it is halal"),
            ch("d", "お茶も買っていきます", "will also buy tea"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "よかったら、ピザ、どう？"
            "このピザ、エビが入ってますか。"
            "エビ、入ってるよ。"
            "じゃあ私はダメです。エビのアレルギーですから。"
            "そうなんだ。"
        ),
    },
    ("EL11", "A19"): {
        "prompt_en": "Listen (CD 11-19). How long will the sashimi keep?",
        "picture_hint_en": "Asking about sashimi shelf life.",
        "key_phrases": [
            "すみません、このお刺身、明日までもちますか。",
            "お刺身は今日中に食べてください。",
            "明日はちょっと無理ですね。",
        ],
        "choices": [
            ch("a", "今日中に食べてください", "eat it today"),
            ch("b", "エビのアレルギーだから", "shrimp allergy"),
            ch("c", "ハラルかどうか", "whether it is halal"),
            ch("d", "バナナを持っていきます", "will bring bananas"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "すみません、このお刺身、明日までもちますか。"
            "あ、お刺身は今日中に食べてください。"
            "そうですか。明日は食べられますか。"
            "ちょっと無理ですね。"
        ),
    },
    ("EL11", "A20"): {
        "prompt_en": "Listen (CD 11-20). What is the guest asking about the ramen?",
        "picture_hint_en": "Asking whether ramen is halal.",
        "key_phrases": [
            "すみません、このラーメン、ハラルですか。",
            "そうですよ。このコーナーの商品は全部ハラルですよ。",
        ],
        "choices": [
            ch("a", "ハラルかどうか", "whether it is halal"),
            ch("b", "エビのアレルギーだから", "shrimp allergy"),
            ch("c", "今日中に食べてください", "eat it today"),
            ch("d", "卵を使っているかどうか", "whether it uses egg"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "すみません、このラーメン、ハラルですか。"
            "そうですよ。ああ、よかった。このコーナーの商品は全部ハラルですよ。"
            "へぇ、そうなんですか。"
        ),
    },
    # --- EL12 offering / reacting to food ---
    ("EL12", "A10"): {
        "prompt_en": "Listen (CD 12-10). What does the host say when offering food?",
        "picture_hint_en": "Offering tamagoyaki to try.",
        "key_phrases": [
            "よかったら、この卵焼き、食べてみてください。",
            "ありがとうございます。……あ、甘くておいしいですね。",
            "もう一つどうですか。",
        ],
        "choices": [
            ch("a", "よかったら、この卵焼き、食べてみてください。", "please try this tamagoyaki"),
            ch("b", "わー、それ、辛そうな料理ですね。", "that looks spicy"),
            ch("c", "それ、何ですか？", "what is that?"),
            ch("d", "へー。じゃ、今度、買ってみます。", "I'll buy some next time"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "よかったら、この卵焼き、食べてみてください。"
            "ありがとうございます。……あ、甘くておいしいですね。"
            "もう一つどうですか。"
            "じゃあ、もう一ついただきます。"
        ),
    },
    ("EL12", "A11"): {
        "prompt_en": "Listen (CD 12-11). How does the guest describe the okonomiyaki?",
        "picture_hint_en": "Comparing okonomiyaki to a dish from their country.",
        "key_phrases": [
            "お好み焼き、おいしい？",
            "はい、おいしいです。私の国のバインセオに似ています。",
            "もう少し食べる？あ、大丈夫です。もうお腹が一杯です。",
        ],
        "choices": [
            ch("a", "私の国の料理に似ています", "similar to food from my country"),
            ch("b", "よかったら、この卵焼き、食べてみてください。", "please try this tamagoyaki"),
            ch("c", "わー、それ、辛そうな料理ですね。", "that looks spicy"),
            ch("d", "すみません、酸っぱくてちょっと苦手です", "too sour for me"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "お好み焼き、おいしい？"
            "はい、おいしいです。私の国のバインセオに似ています。"
            "もう少し食べる？"
            "あ、大丈夫です。もうお腹が一杯です。"
        ),
    },
    ("EL12", "A12"): {
        "prompt_en": "Listen (CD 12-12). How does the guest react to the umeboshi?",
        "picture_hint_en": "Trying pickled plum — too sour.",
        "key_phrases": [
            "それ、何ですか。これ？梅干し。食べてみる？",
            "どう？",
            "すみません、酸っぱくてちょっと苦手です。",
        ],
        "choices": [
            ch("a", "すみません、酸っぱくてちょっと苦手です", "too sour; not my favorite"),
            ch("b", "よかったら、この卵焼き、食べてみてください。", "please try this tamagoyaki"),
            ch("c", "甘くておいしいですね", "sweet and delicious"),
            ch("d", "へー。じゃ、今度、買ってみます。", "I'll buy some next time"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "それ、何ですか。"
            "これ？梅干し。食べてみる？"
            "はい。"
            "どう？"
            "うん……すみません、酸っぱくてちょっと苦手です。"
            "あ、そう。"
        ),
    },
    ("EL12", "A13"): {
        "prompt_en": "Listen (CD 12-13). What can't the guest eat with the sukiyaki?",
        "picture_hint_en": "Sukiyaki — raw egg is a problem.",
        "key_phrases": [
            "すき焼き、おいしいですね。",
            "卵は使わないんですか。",
            "あ、生卵はちょっとダメです。すみません。",
        ],
        "choices": [
            ch("a", "生卵はちょっとダメです", "can't have raw egg"),
            ch("b", "よかったら、この卵焼き、食べてみてください。", "please try this tamagoyaki"),
            ch("c", "すみません、酸っぱくてちょっと苦手です", "too sour for me"),
            ch("d", "私の国の料理に似ています", "similar to food from my country"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": (
            "すき焼き、おいしいですね。"
            "よかった、どんどん食べてください。"
            "はい。卵は使わないんですか。"
            "あ、生卵はちょっとダメです。すみません。"
        ),
    },
}
