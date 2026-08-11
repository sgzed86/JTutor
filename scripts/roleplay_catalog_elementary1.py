"""Curated Can-do role-play scenarios for Elementary 1 (EL01–EL18)."""

from __future__ import annotations

ELEMENTARY1: dict[str, list[dict]] = {
    "CD_EL01_01": [
        {
            "setup_en": "You meet a friend after a long time. Exchange a greeting.",
            "goal_en": "Learner uses a 'long time no see' greeting.",
            "partner_jp": "あ、久しぶり！",
            "expected": ["久しぶり", "お久しぶりです", "元気"],
        },
        {
            "setup_en": "Yuki greets you after a long time. Reply.",
            "goal_en": "Learner returns the reunion greeting.",
            "partner_jp": "お久しぶりです。お元気ですか？",
            "expected": ["お久しぶりです", "おかげさまで", "元気です"],
        },
    ],
    "CD_EL01_02": [
        {
            "setup_en": "A close friend asks how you've been. Answer simply.",
            "goal_en": "Learner talks simply about recent life.",
            "partner_jp": "最近、どう？元気？",
            "expected": ["元気です", "おかげさまで", "忙しい", "です"],
        },
        {
            "setup_en": "Ask Yuki how she has been lately.",
            "goal_en": "Learner asks about someone's recent life.",
            "partner_jp": "久しぶりですね。",
            "expected": ["元気ですか", "最近どう", "どうですか"],
        },
    ],
    "CD_EL01_03": [
        {
            "setup_en": "Someone asks about your work in Japan. Answer simply.",
            "goal_en": "Learner talks simply about their work in Japan.",
            "partner_jp": "日本では、どんな仕事をしていますか？",
            "expected": ["働いています", "仕事", "です"],
        },
        {
            "setup_en": "Say what kind of work you do.",
            "goal_en": "Learner describes their job simply.",
            "partner_jp": "仕事、大変ですか？",
            "expected": ["です", "働いて", "工場", "会社"],
        },
    ],
    "CD_EL02_04": [
        {
            "setup_en": "Talk about your hobbies and favorite things to do.",
            "goal_en": "Learner talks about hobbies/favorites.",
            "partner_jp": "趣味は何ですか？",
            "expected": ["趣味", "好きです", "すること"],
        },
        {
            "setup_en": "Yuki shares her hobby. Share yours.",
            "goal_en": "Learner responds with their own hobby.",
            "partner_jp": "私の趣味は料理をすることです。",
            "expected": ["趣味", "好き", "です"],
        },
    ],
    "CD_EL02_05": [
        {
            "setup_en": "Ask and answer about how you spend days off.",
            "goal_en": "Learner discusses days off.",
            "partner_jp": "休みの日は何をしますか？",
            "expected": ["休み", "します", "です"],
        },
        {
            "setup_en": "Ask Yuki what she does on weekends.",
            "goal_en": "Learner asks about days off.",
            "partner_jp": "私はよく散歩します。",
            "expected": ["何をしますか", "休み", "どうしますか"],
        },
    ],
    "CD_EL02_06": [
        {
            "setup_en": "Yuki reads a staff intro card. Say what hobbies you heard.",
            "goal_en": "Learner shows they understood family/hobby info from a description.",
            "partner_jp": "田中さんです。趣味は写真です。家族は妻と子ども二人です。",
            "expected": ["写真", "趣味", "家族", "子ども"],
        },
        {
            "setup_en": "From the staff card, who likes games?",
            "goal_en": "Learner extracts info from a short description.",
            "partner_jp": "リーさんの趣味はゲームをすることです。休日は家で過ごします。",
            "expected": ["リー", "ゲーム", "趣味"],
        },
    ],
    "CD_EL02_07": [
        {
            "setup_en": "Say a short staff-intro style line about your hobby and days off.",
            "goal_en": "Learner produces a simple self blurb for a staff board.",
            "partner_jp": "自己紹介カードを書いてください。趣味と休みの日のことです。",
            "expected": ["趣味", "好き", "休み"],
        },
        {
            "setup_en": "Dictate a short intro: hobby + weekend.",
            "goal_en": "Learner writes/says hobby and free-day info simply.",
            "partner_jp": "じゃあ、あなたのカードをお願いします。",
            "expected": ["趣味は", "です", "します"],
        },
    ],
    "CD_EL03_08": [
        {
            "setup_en": "Yuki describes Japanese seasons. Which season did she mention for cherry blossoms?",
            "goal_en": "Learner shows they understood seasonal characteristics.",
            "partner_jp": "春は桜の花が咲きます。夏はとても暑いです。冬は寒くて雪が降る所もあります。",
            "expected": ["春", "桜", "夏", "冬"],
        },
        {
            "setup_en": "Summarize one seasonal fact you heard.",
            "goal_en": "Learner restates a seasonal characteristic.",
            "partner_jp": "秋は紅葉がきれいです。食べ物もおいしい季節です。",
            "expected": ["秋", "紅葉", "おいしい"],
        },
    ],
    "CD_EL03_09": [
        {
            "setup_en": "Talk about seasons in your country.",
            "goal_en": "Learner describes seasonal characteristics of their country.",
            "partner_jp": "あなたの国には、どんな季節がありますか？",
            "expected": ["季節", "暑い", "寒い", "です"],
        },
        {
            "setup_en": "Compare winter in your country to Japan.",
            "goal_en": "Learner talks simply about their country's seasons.",
            "partner_jp": "日本の冬は寒いです。あなたの国は？",
            "expected": ["冬", "です", "暑い", "寒い"],
        },
    ],
    "CD_EL03_10": [
        {
            "setup_en": "Say your favorite season and why.",
            "goal_en": "Learner states favorite season with a reason.",
            "partner_jp": "好きな季節は何ですか？どうしてですか？",
            "expected": ["好き", "から", "季節", "です"],
        },
        {
            "setup_en": "Yuki likes summer. Share your favorite and a reason.",
            "goal_en": "Learner gives favorite season + reason.",
            "partner_jp": "私は夏が好きです。海に行けるからです。",
            "expected": ["好き", "から", "です"],
        },
    ],
    "CD_EL04_11": [
        {
            "setup_en": "Greet Yuki while mentioning the weather.",
            "goal_en": "Learner greets and mentions weather.",
            "partner_jp": "おはようございます。",
            "expected": ["暑い", "寒い", "いい天気", "ですね"],
        },
        {
            "setup_en": "Yuki comments on the heat. Reply with a weather greeting.",
            "goal_en": "Learner exchanges a weather-related greeting.",
            "partner_jp": "朝から暑いですね。",
            "expected": ["ですね", "暑い", "本当"],
        },
    ],
    "CD_EL04_12": [
        {
            "setup_en": "Yuki gives a short forecast. What weather is coming?",
            "goal_en": "Learner shows they understood a weather forecast.",
            "partner_jp": "明日は雨です。午後から風が強くなります。",
            "expected": ["雨", "風", "明日"],
        },
        {
            "setup_en": "Restate today's weather from the forecast.",
            "goal_en": "Learner understands spoken weather info.",
            "partner_jp": "今日は晴れのち曇りです。気温は二十五度です。",
            "expected": ["晴れ", "曇り", "二十五"],
        },
    ],
    "CD_EL04_13": [
        {
            "setup_en": "Yuki reads a weather post. What does it say?",
            "goal_en": "Learner shows they understood a simple weather post.",
            "partner_jp": "SNSです。「今日は雪！寒い！」って書いてあります。",
            "expected": ["雪", "寒い"],
        },
        {
            "setup_en": "Summarize the weather comment you heard.",
            "goal_en": "Learner understands social-media style weather text.",
            "partner_jp": "『台風、近いです。気をつけて』という投稿です。",
            "expected": ["台風", "気をつけて"],
        },
    ],
    "CD_EL05_14": [
        {
            "setup_en": "Give your impressions of your town.",
            "goal_en": "Learner talks about impressions of their town.",
            "partner_jp": "住んでいる町は、どうですか？",
            "expected": ["便利", "にぎやか", "静か", "です"],
        },
        {
            "setup_en": "Yuki says her town is busy. Share your impression.",
            "goal_en": "Learner gives a town impression.",
            "partner_jp": "私の町はとてもにぎやかで便利です。",
            "expected": ["です", "便利", "静か", "好き"],
        },
    ],
    "CD_EL05_15": [
        {
            "setup_en": "Ask for a recommended place around town.",
            "goal_en": "Learner asks for recommendations.",
            "partner_jp": "この辺、詳しいですよ。",
            "expected": ["おすすめ", "どこ", "ありますか"],
        },
        {
            "setup_en": "Ask where a good café is.",
            "goal_en": "Learner asks about recommended places and shows understanding.",
            "partner_jp": "何か聞きたいことがありますか？",
            "expected": ["カフェ", "おすすめ", "どこ"],
        },
    ],
    "CD_EL05_16": [
        {
            "setup_en": "Yuki describes the map. Where is the station?",
            "goal_en": "Learner gets info about spots from a map description.",
            "partner_jp": "駅は真ん中です。公園は駅の北です。コンビニは駅の前です。",
            "expected": ["駅", "公園", "コンビニ", "北"],
        },
        {
            "setup_en": "From the map talk, name one famous spot.",
            "goal_en": "Learner extracts place info.",
            "partner_jp": "有名なのは旧寺と市場です。市場は日曜がおすすめです。",
            "expected": ["寺", "市場", "日曜"],
        },
    ],
    "CD_EL06_17": [
        {
            "setup_en": "Ask where the bus stop is.",
            "goal_en": "Learner asks for directions.",
            "partner_jp": "はい、どうしましたか？",
            "expected": ["どこですか", "バス停", "すみません"],
        },
        {
            "setup_en": "Yuki gives directions. Confirm the next step.",
            "goal_en": "Learner shows they understood directions.",
            "partner_jp": "次の角を右に曲がってください。まっすぐです。",
            "expected": ["右", "まっすぐ", "わかりました"],
        },
    ],
    "CD_EL06_18": [
        {
            "setup_en": "On the phone. Ask how to get to the meeting place.",
            "goal_en": "Learner asks for directions by phone.",
            "partner_jp": "もしもし。いまどこですか？",
            "expected": ["どうやって", "行き方", "どこ"],
        },
        {
            "setup_en": "Phone directions: confirm which exit.",
            "goal_en": "Learner understands phone directions.",
            "partner_jp": "東口を出て、コンビニの前で待ってください。",
            "expected": ["東口", "コンビニ", "わかりました"],
        },
    ],
    "CD_EL06_19": [
        {
            "setup_en": "You're in a car. Tell the driver where to turn.",
            "goal_en": "Learner gives simple directions by car.",
            "partner_jp": "次、どっちですか？",
            "expected": ["右", "左", "まっすぐ", "曲がって"],
        },
        {
            "setup_en": "Guide Yuki to the station entrance.",
            "goal_en": "Learner gives destination directions.",
            "partner_jp": "駅、近いですか？案内してください。",
            "expected": ["まっすぐ", "右", "左", "です"],
        },
    ],
    "CD_EL07_20": [
        {
            "setup_en": "Ask what time and where you will meet.",
            "goal_en": "Learner asks meeting time and place.",
            "partner_jp": "じゃあ、あした会いましょう。",
            "expected": ["何時", "どこ", "待ち合わせ"],
        },
        {
            "setup_en": "Confirm the meeting details Yuki said.",
            "goal_en": "Learner understands meeting time/place.",
            "partner_jp": "駅の改札前で、三時に待ち合わせしましょう。",
            "expected": ["三時", "改札", "駅"],
        },
    ],
    "CD_EL07_21": [
        {
            "setup_en": "Decide a meeting time and place with Yuki.",
            "goal_en": "Learner proposes/agrees on meeting details.",
            "partner_jp": "いつ、どこがいいですか？",
            "expected": ["時", "駅", "ましょう", "いいです"],
        },
        {
            "setup_en": "Suggest meeting at the café at 1:00.",
            "goal_en": "Learner helps decide time and place.",
            "partner_jp": "私は午後なら大丈夫です。",
            "expected": ["一時", "カフェ", "どうですか", "ましょう"],
        },
    ],
    "CD_EL07_22": [
        {
            "setup_en": "Yuki reads a late message. What does it say?",
            "goal_en": "Learner understands a 'I'll be late' message.",
            "partner_jp": "メッセージです。「すみません。十分くらい遅れます。」",
            "expected": ["遅れ", "十分", "すみません"],
        },
        {
            "setup_en": "Summarize the late notice.",
            "goal_en": "Learner understands lateness info.",
            "partner_jp": "『電車が遅れて、四時になります』とのことです。",
            "expected": ["四時", "遅れ", "電車"],
        },
    ],
    "CD_EL07_23": [
        {
            "setup_en": "You're running late. Say a short message you would send.",
            "goal_en": "Learner produces a simple late message.",
            "partner_jp": "友だち、待っていますよ。連絡してください。",
            "expected": ["遅れます", "すみません", "分"],
        },
        {
            "setup_en": "Write/say: you'll be 15 minutes late.",
            "goal_en": "Learner communicates lateness.",
            "partner_jp": "いま、どこですか？",
            "expected": ["遅れます", "十五分", "すみません"],
        },
    ],
    "CD_EL08_24": [
        {
            "setup_en": "Invite Yuki out while asking if she's been to the new mall.",
            "goal_en": "Learner invites while checking experience/interest.",
            "partner_jp": "最近、どう？",
            "expected": ["行きませんか", "行きましたか", "一緒"],
        },
        {
            "setup_en": "Ask if they like festivals, then invite them.",
            "goal_en": "Learner invites with interest check.",
            "partner_jp": "週末、ひまです。",
            "expected": ["好きですか", "行きませんか", "どうですか"],
        },
    ],
    "CD_EL08_25": [
        {
            "setup_en": "You're already out. Suggest what to do next.",
            "goal_en": "Learner discusses next place/activity while out.",
            "partner_jp": "次、どこに行きましょうか？",
            "expected": ["ましょう", "どうですか", "行きたい"],
        },
        {
            "setup_en": "After shopping. Propose coffee or going home.",
            "goal_en": "Learner discusses the next step.",
            "partner_jp": "そろそろお腹すきました。",
            "expected": ["食べ", "ましょう", "どう"],
        },
    ],
    "CD_EL08_26": [
        {
            "setup_en": "After an event, give your impressions to Yuki.",
            "goal_en": "Learner shares impressions of the outing.",
            "partner_jp": "今日のイベント、どうでしたか？",
            "expected": ["楽しかった", "よかった", "でした"],
        },
        {
            "setup_en": "Comment on the place you visited together.",
            "goal_en": "Learner gives impressions to their companion.",
            "partner_jp": "アウトレット、初めてでしたね。",
            "expected": ["ですね", "楽しかった", "また"],
        },
    ],
    "CD_EL09_27": [
        {
            "setup_en": "Talk about your experience learning Japanese.",
            "goal_en": "Learner talks about Japanese learning experience.",
            "partner_jp": "どこで日本語を勉強しましたか？",
            "expected": ["勉強", "日本語", "です"],
        },
        {
            "setup_en": "Say how long you've studied Japanese.",
            "goal_en": "Learner describes learning background simply.",
            "partner_jp": "日本語、どのくらい勉強していますか？",
            "expected": ["勉強", "年", "月", "です"],
        },
    ],
    "CD_EL09_28": [
        {
            "setup_en": "Give your impressions of learning Japanese.",
            "goal_en": "Learner comments on studying Japanese.",
            "partner_jp": "日本語の勉強、どうですか？",
            "expected": ["難しい", "楽しい", "です", "でも"],
        },
        {
            "setup_en": "Say what is hard or fun about Japanese.",
            "goal_en": "Learner gives learning impressions.",
            "partner_jp": "漢字は難しいですか？",
            "expected": ["難しい", "楽しい", "好き", "です"],
        },
    ],
    "CD_EL09_29": [
        {
            "setup_en": "You don't understand a word. Ask for help.",
            "goal_en": "Learner asks for help with Japanese.",
            "partner_jp": "はい、何ですか？",
            "expected": ["教えて", "わかりません", "何ですか", "読み方"],
        },
        {
            "setup_en": "Ask how to read this kanji.",
            "goal_en": "Learner requests help with Japanese.",
            "partner_jp": "このメニュー、見てください。",
            "expected": ["読み方", "教えて", "何と読みますか"],
        },
    ],
    "CD_EL09_30": [
        {
            "setup_en": "Yuki summarizes a study forum tip. What method was recommended?",
            "goal_en": "Learner understands a recommended study method.",
            "partner_jp": "フォーラムでは『毎日、短い会話を聞く』がおすすめだそうです。",
            "expected": ["聞く", "毎日", "会話", "おすすめ"],
        },
        {
            "setup_en": "Restate one study tip you heard.",
            "goal_en": "Learner shows understanding of online study advice.",
            "partner_jp": "『単語は例文で覚えるといい』と書いてありました。",
            "expected": ["単語", "例文", "覚える"],
        },
    ],
    "CD_EL10_31": [
        {
            "setup_en": "Yuki reads a class flyer. When and where is the lesson?",
            "goal_en": "Learner finds place/date/time from class info.",
            "partner_jp": "書道教室です。公民館で、土曜の午前十時からです。",
            "expected": ["公民館", "土曜", "十時", "書道"],
        },
        {
            "setup_en": "Say the day of the Japanese class you heard.",
            "goal_en": "Learner extracts schedule info.",
            "partner_jp": "日本語教室は毎週水曜日、七時から九時、会議室Aです。",
            "expected": ["水曜", "七時", "会議室"],
        },
    ],
    "CD_EL10_32": [
        {
            "setup_en": "At city hall. Ask about a class you're interested in.",
            "goal_en": "Learner asks about a lesson and understands answers.",
            "partner_jp": "市民課です。どうしましたか？",
            "expected": ["教室", "ありますか", "申し込み", "日本語"],
        },
        {
            "setup_en": "Ask if beginners can join.",
            "goal_en": "Learner asks a question about the lesson.",
            "partner_jp": "書道教室の案内です。",
            "expected": ["初心者", "できますか", "いくら", "いつ"],
        },
    ],
    "CD_EL10_33": [
        {
            "setup_en": "A friend asks about local Japanese classes. Answer simply.",
            "goal_en": "Learner talks about community Japanese classes.",
            "partner_jp": "近くに日本語のクラス、ある？",
            "expected": ["あります", "教室", "公民館", "です"],
        },
        {
            "setup_en": "Ask a friend if they go to a Japanese class.",
            "goal_en": "Learner asks/answers about local classes.",
            "partner_jp": "日本語、どこで勉強していますか？",
            "expected": ["教室", "どこ", "勉強"],
        },
    ],
    "CD_EL10_34": [
        {
            "setup_en": "For class registration: say your goal in learning Japanese.",
            "goal_en": "Learner answers about goals/experience for joining a class.",
            "partner_jp": "どうして日本語を勉強したいですか？",
            "expected": ["から", "仕事", "話したい", "たい"],
        },
        {
            "setup_en": "Say briefly about your Japanese level/experience.",
            "goal_en": "Learner talks about learning experience/goals.",
            "partner_jp": "日本語の経験を教えてください。",
            "expected": ["勉強", "です", "少し"],
        },
    ],
    "CD_EL11_35": [
        {
            "setup_en": "BBQ planning. Say what you will bring.",
            "goal_en": "Learner discusses who brings what.",
            "partner_jp": "バーベキュー、だれが何を持って行きますか？",
            "expected": ["持って行きます", "買って", "肉", "私"],
        },
        {
            "setup_en": "Offer to buy meat and vegetables.",
            "goal_en": "Learner assigns/offers an item for BBQ.",
            "partner_jp": "私は炭を持って行きます。",
            "expected": ["肉", "野菜", "持って", "行きます"],
        },
    ],
    "CD_EL11_36": [
        {
            "setup_en": "House party. Discuss what to buy.",
            "goal_en": "Learner discusses shopping for a party.",
            "partner_jp": "パーティーの買い物、何が必要ですか？",
            "expected": ["買います", "ください", "飲み物", "必要"],
        },
        {
            "setup_en": "Suggest what to buy for snacks.",
            "goal_en": "Learner proposes party purchases.",
            "partner_jp": "お菓子と飲み物、どうしますか？",
            "expected": ["買いましょう", "どうですか", "ください"],
        },
    ],
    "CD_EL11_37": [
        {
            "setup_en": "Ask staff about ingredients or expiration date.",
            "goal_en": "Learner asks store staff about food details.",
            "partner_jp": "はい、どの商品ですか？",
            "expected": ["原材料", "賞味期限", "入っていますか", "アレルギー"],
        },
        {
            "setup_en": "Ask if this has milk/egg.",
            "goal_en": "Learner asks about ingredients.",
            "partner_jp": "このパンですよ。",
            "expected": ["入っていますか", "ミルク", "卵", "アレルギー"],
        },
    ],
    "CD_EL11_38": [
        {
            "setup_en": "Yuki reads a label. Does it contain peanuts?",
            "goal_en": "Learner shows they understood a food label.",
            "partner_jp": "原材料名：小麦、砂糖、落花生。アレルギー：落花生。",
            "expected": ["落花生", "アレルギー", "小麦"],
        },
        {
            "setup_en": "From the label, name one allergen you heard.",
            "goal_en": "Learner checks labels for things they cannot eat.",
            "partner_jp": "この表示に『卵』と書いてあります。乳は入っていません。",
            "expected": ["卵", "乳", "入って"],
        },
    ],
    "CD_EL12_39": [
        {
            "setup_en": "Looking at food. Give an impression from appearance.",
            "goal_en": "Learner comments on how food looks (〜そう).",
            "partner_jp": "この料理、見てください。",
            "expected": ["そう", "おいしそう", "辛そう"],
        },
        {
            "setup_en": "Comment on Yuki's bento appearance.",
            "goal_en": "Learner gives a look-based impression.",
            "partner_jp": "駅前のコンビニで買ったお弁当です。",
            "expected": ["おいしそう", "そうですね", "かっこいい"],
        },
    ],
    "CD_EL12_40": [
        {
            "setup_en": "After tasting a recommended dish, comment.",
            "goal_en": "Learner comments after eating recommended food.",
            "partner_jp": "おすすめのカレーです。どうですか？",
            "expected": ["おいしい", "辛い", "です", "けど"],
        },
        {
            "setup_en": "Share your impression after eating.",
            "goal_en": "Learner gives a post-eating comment.",
            "partner_jp": "食べてみてください。",
            "expected": ["おいしい", "でした", "甘い"],
        },
    ],
    "CD_EL12_41": [
        {
            "setup_en": "Ask about the taste or ingredients.",
            "goal_en": "Learner asks/answers about taste or ingredients.",
            "partner_jp": "このスープ、飲んでみて。",
            "expected": ["何が入っていますか", "辛いですか", "味"],
        },
        {
            "setup_en": "Answer: is it spicy? What's in it?",
            "goal_en": "Learner talks about taste/ingredients.",
            "partner_jp": "辛いですか？何の肉ですか？",
            "expected": ["辛い", "肉", "です", "から"],
        },
    ],
    "CD_EL12_42": [
        {
            "setup_en": "Yuki reads instant-food instructions. What do you do first?",
            "goal_en": "Learner understands cooking instructions.",
            "partner_jp": "お湯を入れて、三分待ってください。よくかき混ぜます。",
            "expected": ["お湯", "三分", "かき混ぜ"],
        },
        {
            "setup_en": "Restate one step from the instructions.",
            "goal_en": "Learner shows they understood instant-food steps.",
            "partner_jp": "ふたを少し開けて、レンジで六百ワット二分です。",
            "expected": ["レンジ", "二分", "ふた"],
        },
    ],
    "CD_EL13_43": [
        {
            "setup_en": "Something went wrong at work. Tell your supervisor.",
            "goal_en": "Learner reports a workplace problem.",
            "partner_jp": "どうしましたか？",
            "expected": ["んですが", "困って", "わかりません", "なくなった"],
        },
        {
            "setup_en": "Report that toilet paper ran out.",
            "goal_en": "Learner explains a simple workplace issue.",
            "partner_jp": "何かあった？",
            "expected": ["トイレットペーパー", "んですが", "なく"],
        },
    ],
    "CD_EL13_44": [
        {
            "setup_en": "Your boss asks about work status. Answer briefly.",
            "goal_en": "Learner briefly reports work status.",
            "partner_jp": "仕事、どうですか？終わりそう？",
            "expected": ["終わりそうです", "分", "やってます", "です"],
        },
        {
            "setup_en": "Say about how long until you finish.",
            "goal_en": "Learner answers a status question.",
            "partner_jp": "いま、どのくらい？",
            "expected": ["分ぐらい", "終わり", "です"],
        },
    ],
    "CD_EL13_45": [
        {
            "setup_en": "Ask how to use a machine at work.",
            "goal_en": "Learner asks how to use equipment.",
            "partner_jp": "コピー機、使えますよ。",
            "expected": ["どうやって", "使い方", "教えて"],
        },
        {
            "setup_en": "Ask what this button does.",
            "goal_en": "Learner asks for machine instructions.",
            "partner_jp": "この機械です。",
            "expected": ["何ですか", "どうしますか", "教えて"],
        },
    ],
    "CD_EL13_46": [
        {
            "setup_en": "Yuki explains a task. Confirm what you should do.",
            "goal_en": "Learner understands work instructions.",
            "partner_jp": "まず電源を入れて、次にスタートを押してください。",
            "expected": ["電源", "スタート", "わかりました"],
        },
        {
            "setup_en": "Restate the instruction you heard.",
            "goal_en": "Learner shows understanding of task directions.",
            "partner_jp": "箱を倉庫に運んで、空の箱は折ってください。",
            "expected": ["倉庫", "箱", "折って"],
        },
    ],
    "CD_EL13_47": [
        {
            "setup_en": "Yuki reads a short work email. What is the request?",
            "goal_en": "Learner understands a simple work email.",
            "partner_jp": "メールです。『明日の会議資料を十五時までに送ってください』。",
            "expected": ["会議", "十五時", "送って"],
        },
        {
            "setup_en": "Summarize the email.",
            "goal_en": "Learner shows they understood email content.",
            "partner_jp": "『本日は在宅勤務です。急ぎの連絡はチャットでお願いします』。",
            "expected": ["在宅", "チャット", "連絡"],
        },
    ],
    "CD_EL14_48": [
        {
            "setup_en": "Call work to say you'll be late.",
            "goal_en": "Learner phones in late/absent.",
            "partner_jp": "はい、〇〇商店です。",
            "expected": ["遅れます", "休みます", "すみません"],
        },
        {
            "setup_en": "Call to take the day off (you're sick).",
            "goal_en": "Learner makes an absence call.",
            "partner_jp": "もしもし、人事です。",
            "expected": ["休みます", "具合が悪い", "すみません"],
        },
    ],
    "CD_EL14_49": [
        {
            "setup_en": "Ask a coworker if you can step out briefly.",
            "goal_en": "Learner asks permission to leave briefly.",
            "partner_jp": "いま、忙しい？",
            "expected": ["いいですか", "ちょっと", "行ってきます"],
        },
        {
            "setup_en": "Ask permission to go to the bathroom/convenience store.",
            "goal_en": "Learner requests brief leave permission.",
            "partner_jp": "何か用？",
            "expected": ["いいですか", "コンビニ", "トイレ"],
        },
    ],
    "CD_EL14_50": [
        {
            "setup_en": "Ask in advance for a day off next week.",
            "goal_en": "Learner asks permission for planned leave.",
            "partner_jp": "来週のシフト、確認したいことがありますか？",
            "expected": ["休みたい", "いいですか", "お願いします"],
        },
        {
            "setup_en": "Request Friday off.",
            "goal_en": "Learner requests advance time off.",
            "partner_jp": "何か相談ですか？",
            "expected": ["金曜日", "休み", "いいですか"],
        },
    ],
    "CD_EL14_51": [
        {
            "setup_en": "Ask how to fill out a vacation form.",
            "goal_en": "Learner asks how to complete a leave form.",
            "partner_jp": "休暇届ですね。",
            "expected": ["書き方", "どこに", "教えて", "ですか"],
        },
        {
            "setup_en": "Yuki explains the form. What do you write in the reason box?",
            "goal_en": "Learner understands form instructions.",
            "partner_jp": "理由欄に『私用』と書いて、日付を入れて提出してください。",
            "expected": ["私用", "日付", "提出"],
        },
    ],
    "CD_EL15_52": [
        {
            "setup_en": "At the hospital. Explain your symptoms simply.",
            "goal_en": "Learner describes symptoms.",
            "partner_jp": "今日はどうしましたか？",
            "expected": ["痛い", "熱", "のど", "んです"],
        },
        {
            "setup_en": "Say you have a fever and sore throat.",
            "goal_en": "Learner reports symptoms.",
            "partner_jp": "症状を教えてください。",
            "expected": ["熱", "のど", "痛い", "です"],
        },
    ],
    "CD_EL15_53": [
        {
            "setup_en": "The doctor gives advice. What should you do?",
            "goal_en": "Learner shows they understood the doctor.",
            "partner_jp": "今日は休んでください。薬を飲んで、たくさん水を飲んでください。",
            "expected": ["休んで", "薬", "水"],
        },
        {
            "setup_en": "Confirm what the doctor said about returning.",
            "goal_en": "Learner understands medical instructions.",
            "partner_jp": "熱が下がらなかったら、また来てください。",
            "expected": ["熱", "また", "来て"],
        },
    ],
    "CD_EL15_54": [
        {
            "setup_en": "Reception asks for form info. Say your symptoms and when they started.",
            "goal_en": "Learner provides questionnaire info orally.",
            "partner_jp": "問診票です。いつからですか？",
            "expected": ["昨日から", "今日", "痛い", "熱"],
        },
        {
            "setup_en": "Answer allergy and medicine questions simply.",
            "goal_en": "Learner fills key reception info.",
            "partner_jp": "アレルギーはありますか？いま薬を飲んでいますか？",
            "expected": ["ありません", "あります", "薬", "いいえ"],
        },
    ],
    "CD_EL15_55": [
        {
            "setup_en": "Pharmacist explains medicine use. How often do you take it?",
            "goal_en": "Learner understands medicine directions.",
            "partner_jp": "この薬は食後に一日三回飲んでください。",
            "expected": ["食後", "三回", "一日"],
        },
        {
            "setup_en": "Restate one precaution you heard.",
            "goal_en": "Learner understands usage precautions.",
            "partner_jp": "お酒は飲まないでください。眠くなることがあります。",
            "expected": ["お酒", "眠く", "飲まない"],
        },
    ],
    "CD_EL15_56": [
        {
            "setup_en": "Yuki reads the medicine label. What's the dosage?",
            "goal_en": "Learner understands written dosage directions.",
            "partner_jp": "用法：一日二回、一回一錠。朝と夜。",
            "expected": ["二回", "一錠", "朝", "夜"],
        },
        {
            "setup_en": "From the label, when do you take it?",
            "goal_en": "Learner reads medicine instructions.",
            "partner_jp": "『食前に飲んでください』と書いてあります。",
            "expected": ["食前", "飲んで"],
        },
    ],
    "CD_EL16_57": [
        {
            "setup_en": "Yuki feels unwell. Give simple advice.",
            "goal_en": "Learner gives or understands health advice.",
            "partner_jp": "頭が痛いんです…",
            "expected": ["休んで", "薬", "ほうがいい", "水"],
        },
        {
            "setup_en": "Listen to advice and say what you should do.",
            "goal_en": "Learner understands advice for feeling unwell.",
            "partner_jp": "熱があるときは、無理しないで休んだほうがいいですよ。",
            "expected": ["休む", "無理", "熱"],
        },
    ],
    "CD_EL16_58": [
        {
            "setup_en": "Talk about what you do to stay healthy.",
            "goal_en": "Learner talks about health habits.",
            "partner_jp": "健康のために、何か気をつけていますか？",
            "expected": ["しています", "ように", "運動", "睡眠"],
        },
        {
            "setup_en": "Share one healthy habit.",
            "goal_en": "Learner describes mindfulness for health.",
            "partner_jp": "私は野菜を食べるようにしています。",
            "expected": ["しています", "ように", "です"],
        },
    ],
    "CD_EL16_59": [
        {
            "setup_en": "Yuki summarizes epidemic news. Name / symptom / prevention?",
            "goal_en": "Learner understands epidemic news basics.",
            "partner_jp": "ニュースです。インフルエンザが流行しています。熱とせきが出ます。手洗いが大切です。",
            "expected": ["インフルエンザ", "熱", "手洗い"],
        },
        {
            "setup_en": "What prevention method was mentioned?",
            "goal_en": "Learner extracts prevention info.",
            "partner_jp": "マスクをして、人混みを避けてください、とのことです。",
            "expected": ["マスク", "人混み", "避け"],
        },
    ],
    "CD_EL16_60": [
        {
            "setup_en": "Yuki reads a hospital poster. What symptoms are listed?",
            "goal_en": "Learner understands a health poster.",
            "partner_jp": "ポスターです。症状：発熱、せき、のどの痛み。予防：手洗い、うがい。",
            "expected": ["発熱", "せき", "手洗い"],
        },
        {
            "setup_en": "Name one prevention method from the poster.",
            "goal_en": "Learner understands poster prevention tips.",
            "partner_jp": "『うがいと換気をしましょう』と書いてあります。",
            "expected": ["うがい", "換気"],
        },
    ],
    "CD_EL17_61": [
        {
            "setup_en": "You visit someone's house. Give a basic greeting.",
            "goal_en": "Learner uses visiting greetings.",
            "partner_jp": "はい、どうぞ。",
            "expected": ["ごめんください", "おじゃまします", "はじめまして"],
        },
        {
            "setup_en": "Enter the home politely.",
            "goal_en": "Learner greets when visiting.",
            "partner_jp": "あ、来てくれた！上がって。",
            "expected": ["おじゃまします", "ありがとう", "ごめんください"],
        },
    ],
    "CD_EL17_62": [
        {
            "setup_en": "Give a simple explanation about the gift you brought.",
            "goal_en": "Learner explains a gift simply.",
            "partner_jp": "これ、何ですか？",
            "expected": ["お土産", "です", "母が", "作った"],
        },
        {
            "setup_en": "Present a souvenir and say a bit about it.",
            "goal_en": "Learner explains their gift.",
            "partner_jp": "手みやげ、ありがとう！",
            "expected": ["です", "国の", "お菓子", "お土産"],
        },
    ],
    "CD_EL17_63": [
        {
            "setup_en": "Talk about an item — where you bought it or who gave it.",
            "goal_en": "Learner talks about belongings origin.",
            "partner_jp": "そのお守り、いいですね。どこで買いましたか？",
            "expected": ["兄が", "くれました", "買いました", "です"],
        },
        {
            "setup_en": "Explain your decoration/amulet.",
            "goal_en": "Learner explains an item's story.",
            "partner_jp": "それは何ですか？",
            "expected": ["です", "もらった", "買った", "から"],
        },
    ],
    "CD_EL17_64": [
        {
            "setup_en": "Say a short thank-you email after visiting.",
            "goal_en": "Learner produces a simple thank-you message.",
            "partner_jp": "昨日はありがとう。メール、書いてみて。",
            "expected": ["ありがとう", "楽しかった", "また"],
        },
        {
            "setup_en": "Thank them for inviting you.",
            "goal_en": "Learner writes/says thanks for the visit.",
            "partner_jp": "招待してくれて、どう感じましたか？メールで伝えて。",
            "expected": ["ありがとう", "おじゃま", "でした"],
        },
    ],
    "CD_EL18_65": [
        {
            "setup_en": "Congratulate someone on their birthday/wedding.",
            "goal_en": "Learner says congratulations.",
            "partner_jp": "今日、誕生日なんです。",
            "expected": ["おめでとう", "ございます"],
        },
        {
            "setup_en": "Congratulate a couple on their marriage.",
            "goal_en": "Learner offers congratulations.",
            "partner_jp": "来月、結婚します。",
            "expected": ["おめでとう", "ございます"],
        },
    ],
    "CD_EL18_66": [
        {
            "setup_en": "Discuss what gift to give.",
            "goal_en": "Learner discusses gift ideas.",
            "partner_jp": "プレゼント、何がいいと思う？",
            "expected": ["どうですか", "いい", "あげたら", "花"],
        },
        {
            "setup_en": "Suggest a gift for a newborn.",
            "goal_en": "Learner helps choose a gift.",
            "partner_jp": "赤ちゃんが生まれたんです。何を贈ろうかな。",
            "expected": ["どうですか", "服", "おもちゃ", "いい"],
        },
    ],
    "CD_EL18_67": [
        {
            "setup_en": "Someone gives you a gift. Thank them and comment.",
            "goal_en": "Learner thanks and comments on a gift.",
            "partner_jp": "これ、どうぞ。",
            "expected": ["ありがとう", "うれしい", "素敵"],
        },
        {
            "setup_en": "Receive a souvenir. Respond politely.",
            "goal_en": "Learner thanks + offers a short comment.",
            "partner_jp": "旅行のお土産です。",
            "expected": ["ありがとう", "ですね", "喜んで"],
        },
    ],
    "CD_EL18_68": [
        {
            "setup_en": "Yuki reads a birthday SNS post. What happened?",
            "goal_en": "Learner understands a birthday social post.",
            "partner_jp": "投稿です。『今日誕生日！友だちとケーキ』。",
            "expected": ["誕生日", "ケーキ", "友だち"],
        },
        {
            "setup_en": "Summarize the post.",
            "goal_en": "Learner shows understanding of the SNS message.",
            "partner_jp": "『三十歳になりました。メッセージありがとう！』とあります。",
            "expected": ["三十", "メッセージ", "ありがとう"],
        },
    ],
    "CD_EL18_69": [
        {
            "setup_en": "Write/say a short congratulations card message.",
            "goal_en": "Learner produces a card message of congratulations.",
            "partner_jp": "カードに一言、書いてください。結婚祝いです。",
            "expected": ["おめでとう", "幸せ", "ください"],
        },
        {
            "setup_en": "Say goodbye/congratulations on a farewell card.",
            "goal_en": "Learner writes a goodbye or congratulations message.",
            "partner_jp": "友だちが国へ帰ります。カードのメッセージをお願いします。",
            "expected": ["元気で", "また", "ありがとう", "おめでとう"],
        },
    ],
}
