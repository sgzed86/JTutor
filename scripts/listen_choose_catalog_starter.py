"""Curated listen_choose fixes for Starter OCR mega-strings.

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
    # --- L05 ---
    ("L05", "A4"): {
        "prompt_en": "Listen (CD 05-04). What does Sasaki like and dislike?",
        "picture_hint_en": "Likes / dislikes for food.",
        "key_phrases": [
            "私は魚が好きです。",
            "野菜も好きです。",
            "肉は好きじゃないです。",
        ],
        "choices": [
            ch("a", "魚と野菜が好きで、肉は好きじゃない", "likes fish & vegetables; not meat"),
            ch("b", "お茶が好きですか", "Do you like tea?"),
            ch("c", "コーヒーをお願いします", "Coffee, please"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "私は魚が好きです。野菜も好きです。肉は好きじゃないです。",
    },
    # --- L06 ---
    ("L06", "A2"): {
        "prompt_en": "Listen (CD 06-02). Do they eat here or take out?",
        "picture_hint_en": "Fast-food order — here or takeout.",
        "key_phrases": [
            "チーズバーガーとテリヤキバーガーとフィッシュバーガーください。",
            "こちらでお召し上がりですか。",
            "いえ、テイクアウトで。お持ち帰りですね。",
        ],
        "choices": [
            ch("a", "ここで食べます", "eat here"),
            ch("b", "テイクアウト／お持ち帰りです", "takeout"),
            ch("c", "マヨネーズはありますか", "Do you have mayonnaise?"),
        ],
        "correct_ids": ["b"],
        "choose_mode": "any",
        "transcript": "チーズバーガーとテリヤキバーガーとフィッシュバーガーください。こちらでお召し上がりですか。いえ、テイクアウトで。お持ち帰りですね。ありがとうございます。",
    },
    ("L06", "A3"): {
        "prompt_en": "Listen (CD 06-03). What do they order, and where do they eat?",
        "picture_hint_en": "Burger set + drink; eat in or take out.",
        "key_phrases": [
            "これください。チキンバーガーのセットですね。",
            "ドリンクは何になりますか。",
            "じゃあウーロン茶お願いします。",
            "はい、ここで。",
        ],
        "choices": [
            ch("a", "チキンバーガーのセットとウーロン茶で、ここで食べます", "chicken burger set + oolong; eat here"),
            ch("b", "フィッシュバーガーをテイクアウトします", "fish burger takeout"),
            ch("c", "コーヒーをください", "coffee please"),
            ch("d", "マヨネーズはありますか", "mayonnaise?"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "いらっしゃいませ。はい、えーと、これください。チキンバーガーのセットですね。ドリンクは何になりますか。じゃあウーロン茶お願いします。こちらでお召し上がりですか。はい、ここで。",
    },
    # --- L07 ---
    ("L07", "A22"): {
        "prompt_en": "Listen (CD 07-22). Where does Bisal live, and how is the place?",
        "picture_hint_en": "Home size / quiet or not.",
        "key_phrases": [
            "ビサルさんはどこに住んでいますか。",
            "会社の近くに住んでいます。",
            "広くないです。でも、とても静かです。",
        ],
        "choices": [
            ch("a", "会社の近く。広くないけど静かです", "near work; not big but quiet"),
            ch("b", "とても広いマンションです", "very spacious condo"),
            ch("c", "駅の隣に住んでいます", "lives next to the station"),
            ch("d", "ベッドはありません", "no bed"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "ビサルさんはどこに住んでいますか。会社の近くに住んでいます。広いですか。え、広くないです。でも、とても静かです。近くに公園があります。そうですか。",
    },
    ("L07", "A24"): {
        "prompt_en": "Listen (CD 07-24). What kind of home does Maeda have?",
        "picture_hint_en": "Condo vs house; new/old; size.",
        "key_phrases": [
            "前田さんはマンションですか。",
            "うちは一戸建てです。でも大きくないです。",
            "新しくないです。とても古いです。",
        ],
        "choices": [
            ch("a", "一戸建てで、大きくなくて古いです", "detached house; not big; old"),
            ch("b", "新しいマンションです", "new condo"),
            ch("c", "会社の近くのアパートです", "apartment near work"),
            ch("d", "とても綺麗で広いです", "very clean and spacious"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "前田さんはマンションですか。うちは一戸建てです。すごいですね。でも大きくないです。新しいですか。いやー、新しくないです。とても古いです。地下にエレベーターがあります。エレベーターもとても古いです。へぇ。",
    },
    # --- L08 ---
    ("L08", "A4"): {
        "prompt_en": "Listen (CD 08-04). What room is this, and what do they do there?",
        "picture_hint_en": "Office rooms tour.",
        "key_phrases": [
            "ここは給湯室です。",
            "ここでお茶を入れます。",
        ],
        "choices": [
            ch("a", "給湯室でお茶を入れます", "tea room — make tea"),
            ch("b", "ガムテープはどこですか", "Where is the tape?"),
            ch("c", "のりはどこにありますか", "Where is the glue?"),
            ch("d", "ここは会議室です", "This is a meeting room"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "ここは給湯室です。ここでお茶を入れます。",
    },
    ("L08", "A6"): {
        "prompt_en": "Listen (CD 08-06). What room is this?",
        "picture_hint_en": "Office rooms tour.",
        "key_phrases": [
            "ここは食堂です。",
            "ここでご飯を食べます。",
            "おいしいですよ。",
        ],
        "choices": [
            ch("a", "ここは食堂です。ここでご飯を食べます", "cafeteria — eat here"),
            ch("b", "ここは給湯室です", "tea room"),
            ch("c", "ここは会議室です", "meeting room"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "えっと、ここは食堂です。ここでご飯を食べます。はい、おいしいですよ。",
    },
    # --- L09 ---
    ("L09", "A5"): {
        "prompt_en": "Listen (CD 09-05). When does Murakami sleep and wake up?",
        "picture_hint_en": "Daily schedule times.",
        "key_phrases": [
            "村上さんは何時に寝ますか。",
            "2時ごろです。",
            "朝は何時に起きますか。",
            "8時15分です。",
        ],
        "choices": [
            ch("a", "2時ごろ寝て、8時15分に起きます", "sleeps ~2:00; wakes 8:15"),
            ch("b", "9時に寝て、6時に起きます", "sleeps 9; wakes 6"),
            ch("c", "土曜日にプールに行きます", "goes to the pool on Saturday"),
            ch("d", "仕事は毎朝9時からです", "work starts at 9"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "村上さんは何時に寝ますか。2時ごろです。午前2時？遅いですね。夜はゲームをします。へぇ。朝は何時に起きますか。8時15分です。遅い！",
    },
    # --- L10 ---
    ("L10", "A12"): {
        "prompt_en": "Listen (CD 10-12). What do they ask you to do?",
        "picture_hint_en": "Workplace request.",
        "key_phrases": [
            "隣の部屋、10時までに片付けてください。",
            "はい、10時ですね。",
        ],
        "choices": [
            ch("a", "隣の部屋を10時までに片付けてください", "tidy the next room by 10"),
            ch("b", "スマホの充電器ありますか", "Do you have a phone charger?"),
            ch("c", "ダンボールをそこに置いてください", "Put the boxes there"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "隣の部屋、10時までに片付けてください。はい、10時ですね。",
    },
    ("L10", "A13"): {
        "prompt_en": "Listen (CD 10-13). What do they ask you to do?",
        "picture_hint_en": "Workplace request — chairs.",
        "key_phrases": [
            "会議室にいすを8つ並べてくれる？",
            "すみません、いくつですか。",
            "8つです。",
            "はい、分かりました。",
        ],
        "choices": [
            ch("a", "会議室にいすを8つ並べてください", "line up 8 chairs in the meeting room"),
            ch("b", "コピーを30枚お願いします", "30 copies please"),
            ch("c", "続きを3人持っていってください", "take the sequel to three people"),
            ch("d", "スマホを充電してください", "charge the phone"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "会議室にいすを8つ並べてくれる？すみません。いくつですか。8つです。はい、分かりました。",
    },
    ("L10", "A14"): {
        "prompt_en": "Listen (CD 10-14). Where and when should Lindsay go?",
        "picture_hint_en": "Phone message / appointment.",
        "key_phrases": [
            "もしもし、リンジーさん。",
            "あとで14番の面接室に来てください。",
            "何時ですか。",
            "午後2時半です。",
        ],
        "choices": [
            ch("a", "14番の面接室に午後2時半に来てください", "come to interview room 14 at 2:30 p.m."),
            ch("b", "ダンボールをそこに置いてください", "put the boxes there"),
            ch("c", "ごみを捨ててください", "throw away the trash"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "もしもし、リンジーさん。はい。あとで14番の面接室に来てください。すみません、何時ですか。午後2時半です。分かりました。",
    },
    ("L10", "A25"): {
        "prompt_en": "Listen (CD 10-25). What do they borrow?",
        "picture_hint_en": "Borrowing something at work.",
        "key_phrases": [
            "すみません、辞書ありますか。",
            "あるよ。",
            "じゃあちょっと借ります。",
        ],
        "choices": [
            ch("a", "辞書を借ります", "borrows a dictionary"),
            ch("b", "鉛筆ありますか", "Do you have a pencil?"),
            ch("c", "コピーを30枚お願いします", "30 copies please"),
            ch("d", "隣の部屋を片付けてください", "tidy the next room"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "すみません、辞書ありますか。辞書？あるよ。はい、じゃあちょっと借ります。",
    },
    # --- L11 ---
    ("L11", "A3"): {
        "prompt_en": "Listen (CD 11-03). What is their hobby?",
        "picture_hint_en": "Hobby question.",
        "key_phrases": [
            "趣味は何ですか。",
            "アニメが好きです。",
        ],
        "choices": [
            ch("a", "趣味はアニメです", "hobby is anime"),
            ch("b", "公園でテニスをします", "plays tennis in the park"),
            ch("c", "休みの日は掃除をします", "cleans on days off"),
            ch("d", "バスケットボールが好きです", "likes basketball"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "趣味は何ですか。んー、アニメが好きです。ああ、アニメ。",
    },
    ("L11", "A17"): {
        "prompt_en": "Listen (CD 11-17). What does Nigel do on days off?",
        "picture_hint_en": "Weekend / day-off activities.",
        "key_phrases": [
            "ニゲルさん、休みの日はいつも何をしますか。",
            "いつも掃除と洗濯をします。",
            "あとよく友達と話します。",
        ],
        "choices": [
            ch("a", "掃除と洗濯をして、よく友達と話します", "cleaning/laundry; often talks with friends"),
            ch("b", "漫画が好きです", "likes manga"),
            ch("c", "うちでゆっくりします", "relaxes at home"),
            ch("d", "スポーツをします", "does sports"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "ニゲルさん、休みの日はいつも何をしますか。そうですね。私はいつも掃除と洗濯をします。あとよく友達と話します。そうですか。",
    },
    ("L11", "A19"): {
        "prompt_en": "Listen (CD 11-19). What does Morita do on days off?",
        "picture_hint_en": "Weekend sports.",
        "key_phrases": [
            "森田さんは休みの日は何をしますか。",
            "外でスポーツをします。",
            "友達と公園でテニスをします。",
            "時々一人でジョギングをします。",
        ],
        "choices": [
            ch("a", "公園でテニスやジョギングをします", "tennis / jogging in the park"),
            ch("b", "よく友達と買い物します", "often shops with friends"),
            ch("c", "ゲームをします", "plays games"),
            ch("d", "音楽を聞きます", "listens to music"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "森田さんは休みの日は何をしますか。外でスポーツをします。スポーツ、いいですね。どんなスポーツをしますか。友達と公園でテニスをします。あと時々一人でジョギングをします。へぇ、いいですね。",
    },
    ("L11", "A20"): {
        "prompt_en": "Listen (CD 11-20). What does Ishikawa do on days off?",
        "picture_hint_en": "Weekend habits.",
        "key_phrases": [
            "石川さんは休みの日はうちでゴロゴロします。",
            "時々パチンコするかな。",
            "スポーツは全然しないね。",
        ],
        "choices": [
            ch("a", "うちでゴロゴロ。時々パチンコ。スポーツはしない", "lounges at home; sometimes pachinko; no sports"),
            ch("b", "外でスポーツをします", "does sports outside"),
            ch("c", "掃除と洗濯をします", "cleaning and laundry"),
            ch("d", "アニメが好きです", "likes anime"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "石川さんは？休みの日はうちでゴロゴロ。布団でゆっくり。時々パチンコするかな。パチンコ？なんですか。日本のゲーム。そうですか。スポーツは？スポーツは全然しないね。",
    },
    # --- L12 ---
    ("L12", "A8"): {
        "prompt_en": "Listen (CD 12-08). Are they going to the match?",
        "picture_hint_en": "Invitation / plans.",
        "key_phrases": [
            "アントニオさん、今週の金曜日、サッカーの試合に行きますか。",
            "もちろん行きます。私も行きます。",
            "楽しみですね。",
        ],
        "choices": [
            ch("a", "金曜日のサッカーの試合に行きます", "going to Friday's soccer match"),
            ch("b", "一時半から映画に行きます", "movie at 1:30"),
            ch("c", "行きません。残念です", "not going; too bad"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "アントニオさん、今週の金曜日、サッカーの試合に行きますか。もちろん行きます。私も行きます。楽しみですね。そうですね。",
    },
    ("L12", "A9"): {
        "prompt_en": "Listen (CD 12-09). Who is going to the year-end party?",
        "picture_hint_en": "Invitation — going or not.",
        "key_phrases": [
            "業さん、明日の忘年会に行きますか。",
            "ごめんなさい。",
            "私は行きます。",
            "そうですか、残念です。",
        ],
        "choices": [
            ch("a", "一人は行って、一人は行きません", "one goes, one doesn't"),
            ch("b", "二人とも行きます", "both go"),
            ch("c", "タイフェスティバルに行きます", "going to a Thai festival"),
            ch("d", "日曜日に焼肉に行きます", "yakiniku on Sunday"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "ごめんなさい。業さん、明日の忘年会に行きますか。あぁ、私は行きます。そうですか、残念です。",
    },
    ("L12", "A16"): {
        "prompt_en": "Listen (CD 12-16). What plans do they make?",
        "picture_hint_en": "Movie invitation.",
        "key_phrases": [
            "アニタさん、明日の夜、サクラプラザで映画があります。一緒に見に行きませんか。",
            "いいですね。何の映画ですか。",
            "男はつらいよ、です。",
            "一時半からです。じゃあ一緒に行きましょう。",
        ],
        "choices": [
            ch("a", "明日の夜、一時半から映画を見に行きます", "movie tomorrow night at 1:30"),
            ch("b", "サッカーの試合に行きます", "going to a soccer match"),
            ch("c", "忘年会に行きます", "year-end party"),
            ch("d", "行きません。残念です", "not going"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "アニタさん、明日の夜、サクラプラザで映画があります。一緒に見に行きませんか。いいですね。何の映画ですか。男はつらいようです。うーん、何時からですか。一時半からです。一時半、大丈夫です。じゃあ一緒に行きましょう。",
    },
    # --- L13 ---
    ("L13", "A4"): {
        "prompt_en": "Listen (CD 13-04). Which bus goes to City Hospital?",
        "picture_hint_en": "Asking about a bus route.",
        "key_phrases": [
            "すみません、このバスは市民病院に行きますか。",
            "このバスは行きません。",
            "市民病院は23番のバスです。",
        ],
        "choices": [
            ch("a", "市民病院は23番のバスです", "City Hospital is bus 23"),
            ch("b", "この電車は東新宿に行きますか", "Does this train go to Higashi-Shinjuku?"),
            ch("c", "このバスで空港に行きます", "This bus goes to the airport"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "あのー、すみません。このバスは市民病院に行きますか。このバスは行きません。市民病院は23番のバスです。23番ですね。分かりました。",
    },
    ("L13", "A5"): {
        "prompt_en": "Listen (CD 13-05). How do they get to Osaka Station?",
        "picture_hint_en": "Wrong platform / track.",
        "key_phrases": [
            "すみません、この電車は大阪駅に行きますか。",
            "大阪駅は反対側です。7番線です。",
            "7番線ですか。ありがとうございます。",
        ],
        "choices": [
            ch("a", "大阪駅は反対側の7番線です", "Osaka Station is track 7 on the other side"),
            ch("b", "このバスで行きます", "take this bus"),
            ch("c", "水族館まで電車で行きます", "train to the aquarium"),
            ch("d", "10分ぐらいです", "about 10 minutes"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "すみません、この電車は大阪駅に行きますか。大阪駅は反対側です。7番線です。7番線ですか。7番線です。ありがとうございます。",
    },
    ("L13", "A11"): {
        "prompt_en": "Listen (CD 13-11). Are they at the right station?",
        "picture_hint_en": "Confirming the place name.",
        "key_phrases": [
            "先山セントラルステーションです。",
            "すみません、ここは先山セントラルステーションですか。",
            "はい、そうです。",
        ],
        "choices": [
            ch("a", "ここは先山セントラルステーションです", "This is Sakiyama Central Station"),
            ch("b", "市役所までどうやって行きますか", "How do I get to City Hall?"),
            ch("c", "次は浦田ですか", "Is next Urata?"),
            ch("d", "家から会社まで何で行きますか", "How do you get from home to work?"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "先山セントラルステーションです。すみません、ここは先山セントラルステーションですか。はい、そうです。ありがとうございます。",
    },
    ("L13", "A13"): {
        "prompt_en": "Listen (CD 13-13). Where is the passenger now?",
        "picture_hint_en": "Lost-item / location call.",
        "key_phrases": [
            "終点、本宮です。",
            "すみません、今どこですか。",
            "本宮です。終点ですよ。",
        ],
        "choices": [
            ch("a", "今、本宮の終点にいます", "now at Hongu terminal"),
            ch("b", "東新宿に止まります", "stops at Higashi-Shinjuku"),
            ch("c", "下に乗ってください", "please get on below"),
            ch("d", "次はどこですか", "Where is next?"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "終点、本宮です。お忘れ物の内容をお願いします。すみません、今どこですか。本宮です。終点ですよ。ありがとうございました。",
    },
    ("L13", "A25"): {
        "prompt_en": "Listen (CD 13-25). How does Tokui commute?",
        "picture_hint_en": "How they get to work.",
        "key_phrases": [
            "徳井さんは？",
            "バスで来ます。15分ぐらいです。",
            "時々、歩いて来ます。1時間ぐらいかかります。",
        ],
        "choices": [
            ch("a", "バスで15分。時々歩いて1時間", "bus ~15 min; sometimes walk ~1 hour"),
            ch("b", "この電車は大阪駅に行きます", "this train to Osaka Station"),
            ch("c", "空港行きのバスです", "airport bus"),
            ch("d", "7番線です", "track 7"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "徳井さんは？バスで来ます。15分ぐらいです。そうですか。時々、歩いて来ます。1時間ぐらいかかります。うーん、大変ですね。",
    },
    ("L13", "A30"): {
        "prompt_en": "Listen (CD 13-30). How do they get to Aquarium No.1?",
        "picture_hint_en": "Directions — train and bus.",
        "key_phrases": [
            "すみません、水族館一番までどうやって行きますか。",
            "新港まで電車に乗ります。",
            "マリンシティまでバスに乗ります。",
            "それから歩いて5分ぐらいです。",
        ],
        "choices": [
            ch("a", "電車とバスに乗って、歩いて行きます", "train + bus, then walk"),
            ch("b", "このバスは空港に行きますか", "Does this bus go to the airport?"),
            ch("c", "ここは先山セントラルステーションですか", "Is this Sakiyama Central?"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "すみません、水族館一番までどうやって行きますか。はい、水族館一番ですね。ここから新港まで電車に乗ります。新港からマリンシティまでバスに乗ります。マリンシティから歩いて5分ぐらいです。ありがとうございます。",
    },
    ("L13", "A31"): {
        "prompt_en": "Listen (CD 13-31). How do they get to City Hall?",
        "picture_hint_en": "Directions — bus transfer.",
        "key_phrases": [
            "すみません、市役所までどうやって行きますか。",
            "12番のバスに乗ります。",
            "バスセンターで乗リ換えます。",
            "5番のバスに乗ります。市役所は終点です。",
        ],
        "choices": [
            ch("a", "12番バス→バスセンターで5番に乗り換え", "bus 12, transfer to bus 5 at the bus center"),
            ch("b", "この電車は東新宿に行きますか", "Does this train go to Higashi-Shinjuku?"),
            ch("c", "10分ぐらい歩きます", "walk about 10 minutes"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "すみません、市役所までどうやって行きますか。市役所はここから12番のバスに乗ります。バスセンターでバスを降ります。5番のバスに乗り換えてください。市役所は終点です。分かりました。",
    },
    ("L13", "A32"): {
        "prompt_en": "Listen (CD 13-32). How do they get to Sakura Mall?",
        "picture_hint_en": "Directions — subway then bus.",
        "key_phrases": [
            "すみません、サクラモールまでどうやって行きますか。",
            "モミジ駅からサクラ駅まで南北線に乗ります。",
            "サクラ駅で東西線に乗り換えて、新サクラ駅で降ります。",
            "新サクラ駅からバスがあります。",
        ],
        "choices": [
            ch("a", "南北線と東西線に乗って、バスで行きます", "Nanboku + Tozai lines, then bus"),
            ch("b", "本宮の終点にいます", "at Hongu terminal"),
            ch("c", "10分ぐらいです", "about 10 minutes"),
            ch("d", "タクシーに乗ってください", "please take a taxi"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "すみません、サクラモールまでどうやって行きますか。サクラモールですか。えっと、モミジ駅からサクラ駅まで南北線に乗ります。サクラ駅で東西線に乗り換えて、新サクラ駅で降ります。新サクラ駅からバスがあります。ありがとうございます。",
    },
    # --- L14 ---
    ("L14", "A15"): {
        "prompt_en": "Listen (CD 14-15). Where is Lilian now?",
        "picture_hint_en": "Phone — current location.",
        "key_phrases": [
            "もしもし、リリアンさん。",
            "今どこ？",
            "今、インフォメーションの横です。",
        ],
        "choices": [
            ch("a", "インフォメーションの横にいます", "beside the information desk"),
            ch("b", "コンビニの中にいます", "inside the convenience store"),
            ch("c", "ピセットさんのところにいます", "at Pisset's place"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "もしもし、もしもし、リリアンさん。はい。今どこ？えー、今インフォメーションの横です。インフォメーションね。分かった、すぐ行く。",
    },
    ("L14", "A27"): {
        "prompt_en": "Listen (CD 14-27). What are they looking at?",
        "picture_hint_en": "City buildings.",
        "key_phrases": [
            "見て。",
            "あれはセンタービル。あれは住友ビル。あれは三井ビル。",
            "高いビルがたくさんありますね。",
        ],
        "choices": [
            ch("a", "高いビルがたくさんあります", "there are many tall buildings"),
            ch("b", "この近くにATMはありますか", "Is there an ATM nearby?"),
            ch("c", "あっちにやりますよ", "I'll do it over there"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "見て。あれはセンタービル。あれは住友ビル。あれは三井ビル。高いビルがたくさんありますね。そうだね。",
    },
    # --- L15 ---
    ("L15", "A4"): {
        "prompt_en": "Listen (CD 15-04). Where can they buy bandages?",
        "picture_hint_en": "Where to buy something.",
        "key_phrases": [
            "絆創膏が欲しいんですが、どこで買えますか。",
            "ドラッグストアで買えますよ。",
        ],
        "choices": [
            ch("a", "絆創膏はドラッグストアで買えます", "bandages at a drugstore"),
            ch("b", "電池が欲しいんですが、どこで買えますか", "Where can I buy batteries?"),
            ch("c", "ゆかたはデパートで買えます", "yukata at a department store"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "絆創膏が欲しいんですが、どこで買えますか。ドラッグストアで買えますよ。分かりました。ありがとうございます。",
    },
    ("L15", "A5"): {
        "prompt_en": "Listen (CD 15-05). Where can they buy a yukata?",
        "picture_hint_en": "Where to buy something.",
        "key_phrases": [
            "ゆかたが欲しいんですが、どこで買えますか。",
            "駅前のショッピングセンターで買えますよ。",
            "2階におみせがあります。",
        ],
        "choices": [
            ch("a", "駅前のショッピングセンターの2階で買えます", "2F of the station shopping center"),
            ch("b", "このバッグ、かわいい", "This bag is cute"),
            ch("c", "カメラは何階ですか", "Which floor for cameras?"),
            ch("d", "100円ショップにあります", "at a 100-yen shop"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "ゆかたが欲しいんですが、どこで買えますか。駅前のショッピングセンターで買えますよ。2階におみせがあります。そうですか。",
    },
    ("L15", "A7"): {
        "prompt_en": "Listen (CD 15-07). Where can they buy a bento box?",
        "picture_hint_en": "Where to buy something.",
        "key_phrases": [
            "お弁当箱が欲しいんですが、どこで買えますか。",
            "100円ショップにありますよ。",
            "お弁当箱もおはしもあります。",
        ],
        "choices": [
            ch("a", "お弁当箱は100円ショップにあります", "bento box at a 100-yen shop"),
            ch("b", "カメラは何階ですか", "Which floor for cameras?"),
            ch("c", "ドライヤーはどこですか", "Where are the hair dryers?"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "お弁当箱が欲しいんですが、どこで買えますか。100円ショップにありますよ。お弁当箱もおはしもあります。ありがとうございます。",
    },
    ("L15", "A8"): {
        "prompt_en": "Listen (CD 15-08). Where can they buy coconut milk?",
        "picture_hint_en": "Where to buy something.",
        "key_phrases": [
            "ココナッツミルクが欲しいんですが、どこで買えますか。",
            "ああ、大きいスーパーにあるよ。",
            "ニコニコスーパーとか。",
        ],
        "choices": [
            ch("a", "大きいスーパー（ニコニコスーパーなど）にあります", "at a big supermarket"),
            ch("b", "延長コードが欲しいです", "I want an extension cord"),
            ch("c", "この傘、面白いですね", "This umbrella is interesting"),
            ch("d", "2階です", "2nd floor"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "ココナッツミルクが欲しいんですが、どこで買えますか。ああ、大きいスーパーにあるよ。ニコニコスーパーとか。そうですか。ありがとうございます。",
    },
    ("L15", "A15"): {
        "prompt_en": "Listen (CD 15-15). What does the customer want?",
        "picture_hint_en": "Store help — item request.",
        "key_phrases": [
            "すみません、延長コードが欲しいんですが。",
            "ご案内します。こちらになります。",
        ],
        "choices": [
            ch("a", "延長コードが欲しいです（こちらになります）", "wants an extension cord — this way"),
            ch("b", "コンビニで買えますよ", "You can buy it at a convenience store"),
            ch("c", "あちらでございます", "It's over there"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "すみません、延長コードが欲しいんですが。ご案内します。こちらになります。はい、ありがとうございます。",
    },
    ("L15", "A27"): {
        "prompt_en": "Listen (CD 15-27). What do they say about the jacket?",
        "picture_hint_en": "Shopping comments.",
        "key_phrases": [
            "このジャケット、いいね。",
            "そうですね。それに安いですね。",
        ],
        "choices": [
            ch("a", "ジャケットがいいし、安いです", "the jacket looks good and is cheap"),
            ch("b", "延長コードが欲しいです", "wants an extension cord"),
            ch("c", "ドライヤーは2階です", "hair dryers are on 2F"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "このジャケット、いいね。そうですね。それに安いですね。",
    },
    # --- L16 ---
    ("L16", "A8"): {
        "prompt_en": "Listen (CD 16-08). How much is it?",
        "picture_hint_en": "Asking the price.",
        "key_phrases": [
            "すみません、これいくらですか。",
            "1980円です。",
        ],
        "choices": [
            ch("a", "1980円です", "1,980 yen"),
            ch("b", "よろしくお願いします", "please treat me well"),
            ch("c", "ありがとうございます", "thank you"),
            ch("d", "3万4千500円です", "¥34,500"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "すみません、これいくらですか。これ？1980円です。",
    },
    ("L16", "A10"): {
        "prompt_en": "Listen (CD 16-10). How much is it?",
        "picture_hint_en": "Asking the price.",
        "key_phrases": [
            "すみません、これいくらですか。",
            "3万4千500円です。",
        ],
        "choices": [
            ch("a", "3万4千500円です", "¥34,500"),
            ch("b", "1980円です", "¥1,980"),
            ch("c", "ありがとうございます", "thank you"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "あのー、すみません。これいくらですか。はい、これですね。えっと、3万4千500円です。",
    },
    ("L16", "A11"): {
        "prompt_en": "Listen (CD 16-11). What do they buy, and for how much?",
        "picture_hint_en": "Price + purchase.",
        "key_phrases": [
            "すみません、そのカレンダーいくらですか。",
            "あ、これは240円です。",
            "じゃあそれください。",
        ],
        "choices": [
            ch("a", "カレンダーは240円。それください", "calendar ¥240 — I'll take it"),
            ch("b", "ケーキを二つお願いします", "two cakes please"),
            ch("c", "これいくらですか", "How much is this?"),
            ch("d", "お菓子は230円です", "snacks are ¥230"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "すみません、そのカレンダーいくらですか。あ、これは240円です。じゃあそれください。",
    },
    ("L16", "A12"): {
        "prompt_en": "Listen (CD 16-12). How much are the snacks?",
        "picture_hint_en": "Price check + another item.",
        "key_phrases": [
            "このお菓子、いくらですか。",
            "230円です。",
            "じゃあこれもお願いします。",
        ],
        "choices": [
            ch("a", "お菓子は230円です。これもお願いします", "snacks ¥230; this too please"),
            ch("b", "1個2個3個…", "counting pieces"),
            ch("c", "カレンダーは240円です", "calendar ¥240"),
            ch("d", "はい、ありがとうございます", "thank you"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "このお菓子、いくらですか。230円です。じゃあこれもお願いします。",
    },
    ("L16", "A13"): {
        "prompt_en": "Listen (CD 16-13). Do they buy it?",
        "picture_hint_en": "Price / made-in — buy or not.",
        "key_phrases": [
            "あの、これいくらですか。",
            "あ、それね。猫？えっと、それはパキスタン製です。",
            "そうですか。じゃあいいです。",
        ],
        "choices": [
            ch("a", "パキスタン製なので、買いません", "made in Pakistan — won't buy"),
            ch("b", "1個ください", "one please"),
            ch("c", "お菓子は230円です", "snacks ¥230"),
            ch("d", "じゃああれください", "I'll take that one"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "あの、これいくらですか。あ、それね。猫？えっと、それはパキスタン製です。そうですか。じゃあいいです。",
    },
    ("L16", "A14"): {
        "prompt_en": "Listen (CD 16-14). How much is the T-shirt?",
        "picture_hint_en": "Price + purchase.",
        "key_phrases": [
            "すみません、あのTシャツいくらですか。",
            "あれは1990円です。",
            "じゃああれください。",
        ],
        "choices": [
            ch("a", "Tシャツは1990円。あれください", "T-shirt ¥1990 — I'll take it"),
            ch("b", "たこ焼きをください", "takoyaki please"),
            ch("c", "ありがとうございます", "thank you"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "すみません、あのTシャツいくらですか。あ、あれは1990円です。じゃああれください。",
    },
    ("L16", "A18"): {
        "prompt_en": "Listen (CD 16-18). What do they order?",
        "picture_hint_en": "Food stall order.",
        "key_phrases": [
            "いらっしゃいませ。",
            "たこ焼きください。",
            "はい、たこ焼き。ありがとうございます。",
        ],
        "choices": [
            ch("a", "たこ焼きをください", "takoyaki please"),
            ch("b", "袋はどうしますか", "bag?"),
            ch("c", "頼むやつください", "the requested one please"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "いらっしゃいませ。たこ焼きください。はい、たこ焼き。ありがとうございます。",
    },
    ("L16", "A20"): {
        "prompt_en": "Listen (CD 16-20). What do they buy?",
        "picture_hint_en": "Butcher / meat counter.",
        "key_phrases": [
            "いらっしゃいませ。",
            "このひき肉、200gください。",
            "はい、200gですね。",
        ],
        "choices": [
            ch("a", "ひき肉を200gください", "200g ground meat"),
            ch("b", "これは240円です", "this is ¥240"),
            ch("c", "パキスタン製です", "made in Pakistan"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "いらっしゃいませ。このひき肉、200gください。はい、200gですね。",
    },
    ("L16", "A22"): {
        "prompt_en": "Listen (CD 16-22). What do they order?",
        "picture_hint_en": "Market stall — several items.",
        "key_phrases": [
            "いらっしゃいませ。",
            "こんぶ2つ、たらこ1つ、うめ3つください。",
            "はい、こんぶが2つ、たらこが1つ、うめが3つですね。",
        ],
        "choices": [
            ch("a", "こんぶ2つ、たらこ1つ、うめ3つ", "2 kombu, 1 tarako, 3 ume"),
            ch("b", "たこ焼きをください", "takoyaki please"),
            ch("c", "袋はどうしますか", "bag?"),
        ],
        "correct_ids": ["a"],
        "choose_mode": "any",
        "transcript": "いらっしゃいませ。えーっと、こんぶ2つ、たらこ1つ、うめ3つください。はい、こんぶが2つ、たらこが1つ、うめが3つですね。",
    },
}
