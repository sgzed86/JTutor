"""Curated Can-do role-play scenarios for Starter + Elementary 1.

Each entry is a list of role-plays. Fields:
  setup_en  – what the learner should do (shown on stage)
  goal_en   – what success looks like (for the LLM judge)
  partner_jp – Yuki's opening line
  expected  – fallback phrase examples when Ollama is down
  hint_en   – optional short hint
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Starter (L01–L18). L04 kept here so the apply script can rewrite uniformly.
# ---------------------------------------------------------------------------

STARTER: dict[str, list[dict]] = {
    "CD_L01_01": [
        {
            "setup_en": "A coworker greets you in the morning. Greet them back.",
            "goal_en": "Learner returns a morning greeting (おはよう / おはようございます).",
            "partner_jp": "おはよう！",
            "expected": ["おはよう", "おはようございます"],
        },
        {
            "setup_en": "Someone says hello in the afternoon. Reply with a greeting.",
            "goal_en": "Learner replies with こんにちは.",
            "partner_jp": "こんにちは。",
            "expected": ["こんにちは"],
        },
        {
            "setup_en": "Evening — someone greets you. Respond in kind.",
            "goal_en": "Learner replies with こんばんは.",
            "partner_jp": "こんばんは。",
            "expected": ["こんばんは"],
        },
    ],
    "CD_L01_02": [
        {
            "setup_en": "Your classmate is leaving. Say goodbye the same way.",
            "goal_en": "Learner says a parting greeting (じゃあ、また / similar).",
            "partner_jp": "じゃあ、また。",
            "expected": ["じゃあ、また", "じゃあまた", "また"],
        },
        {
            "setup_en": "A senior colleague is leaving the office. Reply appropriately.",
            "goal_en": "Learner uses a workplace parting phrase (お疲れ / 失礼).",
            "partner_jp": "お先に失礼します。",
            "expected": ["お疲れさまです", "お疲れさまでした", "失礼します"],
        },
        {
            "setup_en": "Work is over for the day. Reply to their closing phrase.",
            "goal_en": "Learner replies to お疲れさまでした.",
            "partner_jp": "お疲れさまでした。",
            "expected": ["お疲れさまでした", "お疲れさまです", "お疲れ"],
        },
    ],
    "CD_L01_03": [
        {
            "setup_en": "Someone offers you something. Thank them.",
            "goal_en": "Learner thanks them (ありがとう).",
            "partner_jp": "どうぞ。",
            "expected": ["ありがとう", "ありがとうございます", "どうも"],
        },
        {
            "setup_en": "You bumped into someone. Apologize.",
            "goal_en": "Learner apologizes (すみません / ごめん).",
            "partner_jp": "あ！",
            "expected": ["すみません", "ごめんなさい", "ごめん"],
        },
        {
            "setup_en": "They thanked you. Give a short polite reply.",
            "goal_en": "Learner replies to thanks (どういたしまして / いいえ / どうも).",
            "partner_jp": "ありがとうございます。",
            "expected": ["どういたしまして", "いいえ", "どうも"],
        },
    ],
    "CD_L02_04": [
        {
            "setup_en": "The clerk said the room number too fast. Say you don't understand.",
            "goal_en": "Learner says they don't understand (わかりません).",
            "partner_jp": "部屋は213です。",
            "expected": ["よくわかりません", "わかりません", "わからない"],
        },
        {
            "setup_en": "Reception spoke quickly. Say you don't understand well.",
            "goal_en": "Learner communicates they didn't catch it.",
            "partner_jp": "ここは受付です。在留カードを見せてください。",
            "expected": ["よくわかりません", "わかりません"],
        },
    ],
    "CD_L02_05": [
        {
            "setup_en": "You missed the room number. Ask them to say it again.",
            "goal_en": "Learner asks for a repeat (もう一度).",
            "partner_jp": "部屋は213です。",
            "expected": ["もういちど、お願いします", "もう一度", "お願いします"],
        },
        {
            "setup_en": "They spoke too fast. Ask them to speak a little more slowly.",
            "goal_en": "Learner asks them to slow down (ゆっくり).",
            "partner_jp": "在留カードを見せてください。",
            "expected": ["もう少し、ゆっくり言ってください", "ゆっくり"],
        },
    ],
    "CD_L02_06": [
        {
            "setup_en": "Yuki says a number. Repeat it.",
            "goal_en": "Learner says the number they heard.",
            "partner_jp": "数字です。いち。",
            "expected": ["いち", "1", "一"],
        },
        {
            "setup_en": "Yuki says a number. Repeat it.",
            "goal_en": "Learner says the number they heard.",
            "partner_jp": "数字です。じゅう。",
            "expected": ["じゅう", "10", "十"],
        },
        {
            "setup_en": "Yuki asks you to say a number. Say 「さん」.",
            "goal_en": "Learner produces a number from the lesson.",
            "partner_jp": "数字を言ってください。さん。",
            "expected": ["さん", "3", "三"],
        },
    ],
    "CD_L03_07": [
        {
            "setup_en": "First meeting. Introduce yourself (name and where you're from).",
            "goal_en": "Learner gives a simple self-intro with name and country/hometown.",
            "partner_jp": "はじめまして。自己紹介をお願いします。",
            "expected": ["です", "から来ました", "はじめまして", "よろしくお願いします"],
        },
        {
            "setup_en": "Yuki introduces herself. Give your own short introduction.",
            "goal_en": "Learner replies with their own intro, not copying hers word-for-word only.",
            "partner_jp": "はじめまして。ユキです。日本から来ました。",
            "expected": ["です", "から来ました", "よろしくお願いします"],
        },
    ],
    "CD_L03_08": [
        {
            "setup_en": "You meet someone new. Ask their name and where they are from.",
            "goal_en": "Learner asks name and/or hometown (お名前 / どこ).",
            "partner_jp": "はじめまして。どうぞよろしくお願いします。",
            "expected": ["お名前は", "お名前", "どこから", "どちらから"],
        },
        {
            "setup_en": "Yuki says hello. Ask where she is from.",
            "goal_en": "Learner asks about origin/hometown.",
            "partner_jp": "こんにちは。ユキです。",
            "expected": ["どこから来ましたか", "どちらから", "どこ"],
        },
    ],
    "CD_L03_09": [
        {
            "setup_en": "First meeting. Use a set phrase like よろしくお願いします.",
            "goal_en": "Learner uses a first-meeting set phrase.",
            "partner_jp": "はじめまして。トンです。タイから来ました。",
            "expected": ["よろしく", "よろしくお願いします", "はじめまして"],
        },
        {
            "setup_en": "End a short first meeting politely.",
            "goal_en": "Learner closes with よろしく / similar.",
            "partner_jp": "今日はありがとうございました。",
            "expected": ["よろしく", "また", "失礼します"],
        },
    ],
    "CD_L04_12": [
        {
            "setup_en": "Yuki introduces her family. Listen, then say who you heard (father, mother, sister…).",
            "goal_en": "Learner shows they understood the family introduction.",
            "partner_jp": "紹介します。こちら、父と母と妹です。",
            "expected": ["父と母と妹です", "ちちとははといもうとです", "父", "母", "妹", "家族"],
        },
        {
            "setup_en": "Yuki introduces two people. Say who they are using と.",
            "goal_en": "Learner restates who was introduced (with と if possible).",
            "partner_jp": "紹介します。こちら、バトさんとミロさんです。",
            "expected": ["バトさんとミロさんです", "バトさん", "ミロさん"],
        },
    ],
    "CD_L04_13": [
        {
            "setup_en": "Yuki asks where you live. Answer with に住んでいます.",
            "goal_en": "Learner answers where they live using に住んでいます.",
            "partner_jp": "どこに住んでいますか？",
            "expected": ["東京に住んでいます", "赤羽に住んでいます", "住んでいます"],
        },
        {
            "setup_en": "Meet Miro. Ask how old she is.",
            "goal_en": "Learner asks someone's age.",
            "partner_jp": "こんにちは。ミロです。フィリピンから来ました。",
            "expected": ["何歳ですか", "いくつですか", "おいくつですか"],
        },
        {
            "setup_en": "Yuki asks your age. Answer with 〜歳です.",
            "goal_en": "Learner answers their age.",
            "partner_jp": "何歳ですか？",
            "expected": ["歳です", "さいです"],
        },
    ],
    "CD_L04_14": [
        {
            "setup_en": "Looking at a photo together. Ask who someone is.",
            "goal_en": "Learner asks who is in the photo.",
            "partner_jp": "このしゃしん、みてください。",
            "expected": ["これ誰ですか", "これ、だれですか", "だれですか"],
        },
        {
            "setup_en": "Yuki asks who is in the photo. Answer using の.",
            "goal_en": "Learner answers who someone is, ideally with の.",
            "partner_jp": "これ、だれですか？",
            "expected": ["私の母です", "あねの子どもです", "友だちのバトさんです", "の"],
        },
        {
            "setup_en": "Looking at a cute pet photo. React, then ask how old the pet is.",
            "goal_en": "Learner reacts and/or asks the pet's age.",
            "partner_jp": "みて。ペットのロッキーです。",
            "expected": ["かわいいですね", "何歳ですか", "いくつですか"],
        },
    ],
    "CD_L05_15": [
        {
            "setup_en": "Yuki asks if you like fish. Say what you like / don't like.",
            "goal_en": "Learner states likes/dislikes for food.",
            "partner_jp": "さかな、好きですか？",
            "expected": ["好きです", "好きじゃないです", "嫌いです"],
        },
        {
            "setup_en": "Talk about Japanese food. Say one food you like.",
            "goal_en": "Learner names a liked food with 好き.",
            "partner_jp": "日本の食べ物、何が好きですか？",
            "expected": ["好きです", "すしが好きです", "ラーメンが好きです"],
        },
    ],
    "CD_L05_16": [
        {
            "setup_en": "Ask Yuki what foods she likes.",
            "goal_en": "Learner asks about someone's food likes.",
            "partner_jp": "私はカレーが好きです。あなたは？",
            "expected": ["何が好きですか", "好きですか", "好きな"],
        },
        {
            "setup_en": "At lunch. Ask if they like meat.",
            "goal_en": "Learner asks a food preference question.",
            "partner_jp": "今日はお弁当です。",
            "expected": ["肉、好きですか", "好きですか", "何が好き"],
        },
    ],
    "CD_L05_17": [
        {
            "setup_en": "Chat about favorite foods. Say something you like and react to Yuki.",
            "goal_en": "Learner can talk simply about favorite foods.",
            "partner_jp": "私はラーメンが大好きです。",
            "expected": ["好きです", "いいですね", "私も"],
        },
        {
            "setup_en": "Yuki offers tea. Accept or decline politely.",
            "goal_en": "Learner responds to an offer in a food/drink chat.",
            "partner_jp": "お茶、飲みますか？",
            "expected": ["はい、お願いします", "結構です", "お願いします"],
        },
    ],
    "CD_L06_18": [
        {
            "setup_en": "At a café. Order a drink.",
            "goal_en": "Learner orders with ください / お願いします.",
            "partner_jp": "いらっしゃいませ。ご注文は？",
            "expected": ["ください", "お願いします", "コーヒー"],
        },
        {
            "setup_en": "Order a hamburger set and answer the drink question.",
            "goal_en": "Learner places an order and handles a follow-up.",
            "partner_jp": "チキンバーガーのセットですね。ドリンクは何になさいますか？",
            "expected": ["お願いします", "ください", "ウーロン茶"],
        },
    ],
    "CD_L06_19": [
        {
            "setup_en": "Looking at a menu. Ask a simple question about an item.",
            "goal_en": "Learner asks about the menu simply.",
            "partner_jp": "メニューです。どうぞ。",
            "expected": ["何ですか", "ありますか", "いくら", "おすすめ"],
        },
        {
            "setup_en": "Ask a friend what they will order.",
            "goal_en": "Learner asks what someone will have.",
            "partner_jp": "何にしますか？私はうどんにします。",
            "expected": ["何にしますか", "どうしますか", "うどん"],
        },
    ],
    "CD_L06_20": [
        {
            "setup_en": "Staff asks if you'll eat here. Answer appropriately.",
            "goal_en": "Learner understands and answers a staff question when ordering.",
            "partner_jp": "こちらでお召し上がりですか？",
            "expected": ["はい", "いいえ", "テイクアウト", "持ち帰り"],
        },
        {
            "setup_en": "Staff confirms your order. Respond.",
            "goal_en": "Learner shows they understood the confirmation.",
            "partner_jp": "ホットコーヒーですね。少々お待ちください。",
            "expected": ["はい", "お願いします", "ありがとう"],
        },
    ],
    "CD_L07_26": [
        {
            "setup_en": "Yuki gives a short house tour. Say what rooms you heard.",
            "goal_en": "Learner shows they understood the layout (rooms mentioned).",
            "partner_jp": "案内します。ここはリビングです。隣はキッチンです。二階に寝室があります。",
            "expected": ["リビング", "キッチン", "寝室", "二階"],
        },
        {
            "setup_en": "Yuki describes her apartment. Summarize where the bathroom is.",
            "goal_en": "Learner restates a location from the tour.",
            "partner_jp": "お風呂とトイレは一階です。ベランダもあります。",
            "expected": ["お風呂", "トイレ", "一階", "ベランダ"],
        },
    ],
    "CD_L07_27": [
        {
            "setup_en": "Looking at a room. Ask if there is a microwave.",
            "goal_en": "Learner asks whether something is there (ありますか).",
            "partner_jp": "私の部屋です。どうぞ。",
            "expected": ["ありますか", "電子レンジはありますか", "ありますか"],
        },
        {
            "setup_en": "Ask if the apartment has a washing machine.",
            "goal_en": "Learner checks for a needed item.",
            "partner_jp": "このアパートはどうですか？",
            "expected": ["洗濯機はありますか", "ありますか"],
        },
    ],
    "CD_L07_28": [
        {
            "setup_en": "Someone asks where you live. Answer simply.",
            "goal_en": "Learner describes where they live.",
            "partner_jp": "どこに住んでいますか？",
            "expected": ["住んでいます", "アパート", "に"],
        },
        {
            "setup_en": "Describe your place briefly (size/quiet is fine).",
            "goal_en": "Learner gives a simple description of their home.",
            "partner_jp": "おうちはどんなところですか？",
            "expected": ["住んで", "です", "静か", "狭い", "広い"],
        },
    ],
    "CD_L08_29": [
        {
            "setup_en": "At the office. Ask where Yamada-san is.",
            "goal_en": "Learner asks where someone is.",
            "partner_jp": "ちょっと、山田さんを探しています。",
            "expected": ["どこにいますか", "どこですか", "どこ"],
        },
        {
            "setup_en": "Ask where the scissors are.",
            "goal_en": "Learner asks where something is.",
            "partner_jp": "はさみ、使いたいんですけど…",
            "expected": ["どこですか", "どこにありますか", "どこ"],
        },
    ],
    "CD_L08_30": [
        {
            "setup_en": "Yuki asks where Miru is. Answer with a location word.",
            "goal_en": "Learner says where someone/something is.",
            "partner_jp": "ミロさんはどこにいますか？",
            "expected": ["にいます", "食堂にいます", "です", "ここ"],
        },
        {
            "setup_en": "Say where the tape is (on the desk / in the box is fine).",
            "goal_en": "Learner uses a location expression.",
            "partner_jp": "ガムテープはどこですか？",
            "expected": ["の上", "の中", "あそこ", "です"],
        },
    ],
    "CD_L08_31": [
        {
            "setup_en": "Yuki explains office rooms. Say which room is for meetings.",
            "goal_en": "Learner shows they understood a simple location explanation.",
            "partner_jp": "ここは会議室です。そこで打ち合わせをします。隣は食堂です。",
            "expected": ["会議室", "食堂", "打ち合わせ"],
        },
        {
            "setup_en": "Yuki says where Kenji is. Confirm you understood.",
            "goal_en": "Learner confirms understanding of a location.",
            "partner_jp": "ケンジさんは休憩室にいますよ。",
            "expected": ["わかりました", "休憩室", "はい"],
        },
    ],
    "CD_L09_32": [
        {
            "setup_en": "Say what time you wake up.",
            "goal_en": "Learner says a start time with 時.",
            "partner_jp": "朝、何時に起きますか？",
            "expected": ["時に", "時", "起きます"],
        },
        {
            "setup_en": "Say when you sleep / finish something.",
            "goal_en": "Learner says an end time.",
            "partner_jp": "夜は何時に寝ますか？",
            "expected": ["時", "寝ます", "頃"],
        },
    ],
    "CD_L09_33": [
        {
            "setup_en": "Ask Yuki what time she wakes up.",
            "goal_en": "Learner asks about a daily schedule.",
            "partner_jp": "私は毎朝ジョギングします。",
            "expected": ["何時に", "何時"],
        },
        {
            "setup_en": "Plan a movie. Ask when is good.",
            "goal_en": "Learner asks about schedule timing.",
            "partner_jp": "映画、行きたいですね。",
            "expected": ["いつ", "何時", "土曜日"],
        },
    ],
    "CD_L09_34": [
        {
            "setup_en": "Yuki says her schedule. Say what time she sleeps.",
            "goal_en": "Learner shows they understood spoken times.",
            "partner_jp": "朝は七時に起きます。夜は十一時に寝ます。",
            "expected": ["十一時", "7時", "七時", "寝ます"],
        },
        {
            "setup_en": "Yuki says the time. What time is it?",
            "goal_en": "Learner restates the time they heard.",
            "partner_jp": "今、十時半です。",
            "expected": ["十時半", "10時半", "半"],
        },
    ],
    "CD_L10_39": [
        {
            "setup_en": "Your supervisor gives a short instruction. Confirm what you should do.",
            "goal_en": "Learner shows they understood a simple work instruction.",
            "partner_jp": "隣の部屋、十時までに片付けてください。",
            "expected": ["十時", "片付け", "わかりました", "はい"],
        },
        {
            "setup_en": "Yuki asks you to arrange cups. Confirm how many.",
            "goal_en": "Learner understands and confirms the instruction.",
            "partner_jp": "コップを八つ並べてください。",
            "expected": ["八つ", "わかりました", "はい"],
        },
    ],
    "CD_L10_40": [
        {
            "setup_en": "You need a charger. Ask to borrow it.",
            "goal_en": "Learner asks to borrow something (貸して / 借りてもいい).",
            "partner_jp": "はい、何ですか？",
            "expected": ["貸してください", "借りてもいいですか", "ありますか"],
        },
        {
            "setup_en": "Ask to borrow a pen.",
            "goal_en": "Learner makes a lend-request.",
            "partner_jp": "すみません、ちょっと…",
            "expected": ["貸してください", "ペン", "いいですか"],
        },
    ],
    "CD_L10_41": [
        {
            "setup_en": "Make a simple request at work (copy / clean / bring).",
            "goal_en": "Learner makes a simple request with ください.",
            "partner_jp": "何か手伝いましょうか？",
            "expected": ["ください", "お願いします"],
        },
        {
            "setup_en": "Ask someone to wait a moment.",
            "goal_en": "Learner makes a short request.",
            "partner_jp": "いま、いいですか？",
            "expected": ["ちょっと待ってください", "ください", "お願いします"],
        },
    ],
    "CD_L11_44": [
        {
            "setup_en": "Yuki asks about your hobbies. Answer simply.",
            "goal_en": "Learner answers about hobbies.",
            "partner_jp": "趣味は何ですか？",
            "expected": ["趣味", "好きです", "です"],
        },
        {
            "setup_en": "Someone asks if you like sports. Answer.",
            "goal_en": "Learner answers a hobby/like question.",
            "partner_jp": "スポーツ、好きですか？",
            "expected": ["好きです", "好きじゃない", "あまり"],
        },
    ],
    "CD_L11_45": [
        {
            "setup_en": "Ask Yuki about her hobbies.",
            "goal_en": "Learner asks about hobbies/likes.",
            "partner_jp": "私の趣味は料理です。",
            "expected": ["趣味は何ですか", "何が好きですか", "好きですか"],
        },
        {
            "setup_en": "Ask what anime/manga they like.",
            "goal_en": "Learner asks about likes.",
            "partner_jp": "アニメ、よく見ます。",
            "expected": ["何が好きですか", "好きな", "好きですか"],
        },
    ],
    "CD_L11_46": [
        {
            "setup_en": "Say what you usually do on days off.",
            "goal_en": "Learner talks about days off.",
            "partner_jp": "休みの日はいつも何をしますか？",
            "expected": ["休み", "します", "ゆっくり"],
        },
        {
            "setup_en": "Yuki talks about her weekend. Say what you do.",
            "goal_en": "Learner describes their free-day activity.",
            "partner_jp": "私は休みの日に公園へ行きます。",
            "expected": ["休み", "します", "です"],
        },
    ],
    "CD_L12_47": [
        {
            "setup_en": "Invite Yuki to eat yakiniku together.",
            "goal_en": "Learner invites someone (ませんか / 一緒).",
            "partner_jp": "今週、ひまです。",
            "expected": ["行きませんか", "ませんか", "一緒"],
        },
        {
            "setup_en": "Invite a friend to a festival.",
            "goal_en": "Learner makes an invitation.",
            "partner_jp": "日曜日にタイフェスティバルがありますよ。",
            "expected": ["行きませんか", "一緒に", "ませんか"],
        },
    ],
    "CD_L12_48": [
        {
            "setup_en": "Yuki invites you. Accept.",
            "goal_en": "Learner accepts an invitation.",
            "partner_jp": "一緒に焼き肉を食べに行きませんか？",
            "expected": ["いいですね", "行きましょう", "はい"],
        },
        {
            "setup_en": "Yuki invites you, but you're busy. Decline politely.",
            "goal_en": "Learner declines simply and politely.",
            "partner_jp": "今度の土曜日、ハイキングに行きませんか？",
            "expected": ["ちょっと", "すみません", "また今度"],
        },
    ],
    "CD_L12_49": [
        {
            "setup_en": "Suggest a day for going out.",
            "goal_en": "Learner suggests a simple plan (day/time).",
            "partner_jp": "いつがいいですか？",
            "expected": ["土曜日", "日曜日", "ましょう", "いいです"],
        },
        {
            "setup_en": "Propose going to see a friend's match.",
            "goal_en": "Learner suggests a plan.",
            "partner_jp": "金曜の夜、ひまですか？",
            "expected": ["行きましょう", "どうですか", "ませんか"],
        },
    ],
    "CD_L13_52": [
        {
            "setup_en": "At the station. Ask if this train goes to Higashi-Shinjuku.",
            "goal_en": "Learner asks whether transit goes to their destination.",
            "partner_jp": "次の電車ですよ。",
            "expected": ["行きますか", "この電車は", "東新宿"],
        },
        {
            "setup_en": "Ask if this bus goes to the airport.",
            "goal_en": "Learner asks a destination question.",
            "partner_jp": "バス乗り場です。",
            "expected": ["行きますか", "空港", "このバス"],
        },
    ],
    "CD_L13_53": [
        {
            "setup_en": "The announcement was unclear. Ask where you are now.",
            "goal_en": "Learner asks where they are.",
            "partner_jp": "次は……（アナウンスが聞こえない）",
            "expected": ["ここはどこですか", "どこですか", "次は"],
        },
        {
            "setup_en": "Confirm the next stop.",
            "goal_en": "Learner asks/confirm location on the line.",
            "partner_jp": "まもなく、次の駅です。",
            "expected": ["次は", "どこですか", "ですか"],
        },
    ],
    "CD_L13_54": [
        {
            "setup_en": "Yuki explains the bus. Say which bus goes to the hospital.",
            "goal_en": "Learner shows they understood simple transit info.",
            "partner_jp": "このバスは行きません。市民病院は23番のバスです。",
            "expected": ["23番", "市民病院", "バス"],
        },
        {
            "setup_en": "Yuki says how she gets to work. How long does it take?",
            "goal_en": "Learner restates transit information.",
            "partner_jp": "家から会社まで電車で一時間半かかります。",
            "expected": ["一時間半", "電車", "かかります"],
        },
    ],
    "CD_L14_55": [
        {
            "setup_en": "Looking at a park. Make a simple comment.",
            "goal_en": "Learner comments with ですね / simple adjective.",
            "partner_jp": "ここは水元公園です。",
            "expected": ["ですね", "きれい", "広い", "いい"],
        },
        {
            "setup_en": "Looking at a tall building. React.",
            "goal_en": "Learner gives a simple impression.",
            "partner_jp": "みて、あのビル！",
            "expected": ["ですね", "高い", "すごい"],
        },
    ],
    "CD_L14_56": [
        {
            "setup_en": "Ask what this place is.",
            "goal_en": "Learner asks/confirm what a place is.",
            "partner_jp": "着きましたよ。",
            "expected": ["ここは何ですか", "何ですか", "どこ"],
        },
        {
            "setup_en": "Ask where the toilet is.",
            "goal_en": "Learner asks about a place nearby.",
            "partner_jp": "この建物、大きいですね。",
            "expected": ["トイレはどこですか", "どこですか"],
        },
    ],
    "CD_L14_57": [
        {
            "setup_en": "Describe the park simply (big/pretty/quiet).",
            "goal_en": "Learner uses a simple adjective description.",
            "partner_jp": "水元公園、どうですか？",
            "expected": ["きれい", "広い", "静か", "です"],
        },
        {
            "setup_en": "Yuki asks about a shop. Describe it.",
            "goal_en": "Learner describes appearance/size simply.",
            "partner_jp": "あのコンビニ、わかりますか？",
            "expected": ["小さい", "便利", "近い", "です"],
        },
    ],
    "CD_L15_58": [
        {
            "setup_en": "At a store. Say what you want.",
            "goal_en": "Learner says what they want/need (ほしい).",
            "partner_jp": "いらっしゃいませ。何かお探しですか？",
            "expected": ["ほしい", "が欲しい", "ください"],
        },
        {
            "setup_en": "You need batteries. Say so.",
            "goal_en": "Learner expresses a need.",
            "partner_jp": "どうぞ、見てください。",
            "expected": ["電池が欲しい", "ほしい", "電池"],
        },
    ],
    "CD_L15_59": [
        {
            "setup_en": "Ask staff where you can buy a phone case.",
            "goal_en": "Learner asks staff for a product/location.",
            "partner_jp": "はい、何でしょうか？",
            "expected": ["どこにありますか", "どこで買えますか", "ありますか"],
        },
        {
            "setup_en": "Ask which floor cameras are on.",
            "goal_en": "Learner asks staff about a product.",
            "partner_jp": "案内しますよ。",
            "expected": ["何階ですか", "どこですか", "カメラ"],
        },
    ],
    "CD_L15_60": [
        {
            "setup_en": "Staff says the dryer is on the 2nd floor. Confirm you understood.",
            "goal_en": "Learner shows they understood a staff reply.",
            "partner_jp": "ドライヤーは二階です。",
            "expected": ["二階", "わかりました", "ありがとう"],
        },
        {
            "setup_en": "Staff points to the item. Respond.",
            "goal_en": "Learner responds appropriately to staff.",
            "partner_jp": "こちらでございます。",
            "expected": ["ありがとう", "お願いします", "はい"],
        },
    ],
    "CD_L16_66": [
        {
            "setup_en": "Yuki says a price. How much is it?",
            "goal_en": "Learner shows they understood the price.",
            "partner_jp": "このTシャツは1990円です。",
            "expected": ["1990円", "円", "千円"],
        },
        {
            "setup_en": "At checkout. Restate the total you heard.",
            "goal_en": "Learner understands a spoken price.",
            "partner_jp": "お会計、825円になります。",
            "expected": ["825円", "円"],
        },
    ],
    "CD_L16_67": [
        {
            "setup_en": "Ask how much this is.",
            "goal_en": "Learner asks the price (いくら).",
            "partner_jp": "そのシャツ、いいですね。",
            "expected": ["いくらですか", "いくら"],
        },
        {
            "setup_en": "Ask the price of that cake.",
            "goal_en": "Learner asks staff for a price.",
            "partner_jp": "ケーキ、いろいろありますよ。",
            "expected": ["いくらですか", "いくら"],
        },
    ],
    "CD_L16_68": [
        {
            "setup_en": "At the meat counter. Say how much you want (e.g. 200g).",
            "goal_en": "Learner states amount/quantity when shopping.",
            "partner_jp": "いらっしゃいませ。何にしますか？",
            "expected": ["ください", "グラム", "お願いします"],
        },
        {
            "setup_en": "Order two cakes.",
            "goal_en": "Learner says a quantity.",
            "partner_jp": "ケーキですね。いくつですか？",
            "expected": ["二つ", "ください", "お願いします"],
        },
    ],
    "CD_L17_69": [
        {
            "setup_en": "Say what you did on your day off.",
            "goal_en": "Learner says past activities with ました.",
            "partner_jp": "休みは何をしましたか？",
            "expected": ["ました", "行きました", "しました"],
        },
        {
            "setup_en": "Yuki asks about Sunday. Answer.",
            "goal_en": "Learner reports past weekend activities.",
            "partner_jp": "日曜日は何をしましたか？",
            "expected": ["ました", "しませんでした"],
        },
    ],
    "CD_L17_70": [
        {
            "setup_en": "Ask how the festival was.",
            "goal_en": "Learner asks for an impression (どう).",
            "partner_jp": "国際フェスティバルに行きました。",
            "expected": ["どうでしたか", "どうだった", "どう"],
        },
        {
            "setup_en": "Ask if the movie was interesting.",
            "goal_en": "Learner asks how something was.",
            "partner_jp": "昨日、映画を見ました。",
            "expected": ["おもしろかったですか", "どうでしたか", "どう"],
        },
    ],
    "CD_L17_71": [
        {
            "setup_en": "Give a simple impression of your outing.",
            "goal_en": "Learner gives an impression (楽しかった / よかった).",
            "partner_jp": "休みはどうでしたか？",
            "expected": ["でした", "楽しかった", "よかった", "大変"],
        },
        {
            "setup_en": "Yuki went to a concert. React with a short impression question or comment.",
            "goal_en": "Learner comments on an event simply.",
            "partner_jp": "オーケストラのコンサートに行きました。",
            "expected": ["いいですね", "どうでしたか", "でした"],
        },
    ],
    "CD_L18_72": [
        {
            "setup_en": "Say what you want to do in Japan.",
            "goal_en": "Learner says what they want to do (たい).",
            "partner_jp": "日本で何がしたいですか？",
            "expected": ["たいです", "たい", "見たい", "行きたい"],
        },
        {
            "setup_en": "Talk about summer vacation plans — what do you want to do?",
            "goal_en": "Learner expresses a want/desire.",
            "partner_jp": "夏休み、どうしますか？",
            "expected": ["たいです", "行きたい", "したい"],
        },
    ],
    "CD_L18_73": [
        {
            "setup_en": "Yuki asks why. Give a simple reason with から.",
            "goal_en": "Learner gives a reason (どうして / から).",
            "partner_jp": "どうして広島に行きたいですか？",
            "expected": ["から", "友達", "住んで"],
        },
        {
            "setup_en": "Ask Yuki why she wants to go somewhere.",
            "goal_en": "Learner asks why.",
            "partner_jp": "温泉に入りたいです。",
            "expected": ["どうして", "なぜ"],
        },
    ],
    "CD_L18_74": [
        {
            "setup_en": "Talk about your next holiday plans.",
            "goal_en": "Learner talks about future holiday plans with たい / plans.",
            "partner_jp": "今度の休み、何をしますか？",
            "expected": ["たい", "行きます", "します"],
        },
        {
            "setup_en": "Long weekend coming. Say what you want to do.",
            "goal_en": "Learner describes upcoming holiday plans.",
            "partner_jp": "連休、どこか行きますか？",
            "expected": ["たい", "ゆっくり", "行きます", "うちで"],
        },
    ],
}
