def _make_stages(chapter_id, titles):
    difficulties = ["beginner"] * 4 + ["intermediate"] * 4 + ["advanced"] * 4
    return [{"id": chapter_id * 100 + i + 1, "title": title, "difficulty": difficulties[i]} for i, title in enumerate(titles)]


CHAPTERS = [
    {
        "id": 1,
        "title": "國小基礎",
        "icon": "🎒",
        "description": "生活、情緒、動作與簡單句子",
        "stages": _make_stages(1, ["餓肚子警報", "累到不行", "快樂與生氣", "大小與安靜", "自信 vs 緊張", "生活小對話", "身體感受", "日常聽說", "基礎克漏字", "圖片情境", "綜合複習", "國小 Boss"]),
    },
    {
        "id": 2,
        "title": "國中進階",
        "icon": "🏫",
        "description": "校園、借還、活動、比較與常見文法",
        "stages": _make_stages(2, ["借筆小任務", "課堂指令", "社團活動", "考前準備", "相似字陷阱", "報告前夕", "校園小對話", "比較與感受", "動名詞克漏字", "時態判斷", "閱讀小測", "國中 Boss"]),
    },
    {
        "id": 3,
        "title": "高中核心",
        "icon": "📚",
        "description": "旅行、社會議題、抽象形容詞與閱讀句型",
        "stages": _make_stages(3, ["點餐入門", "問路任務", "旅館入住", "交通與目的地", "旅行干擾字", "觀點表達", "原因結果", "閱讀推論", "高中克漏字", "轉折語氣", "長句理解", "高中 Boss"]),
    },
    {
        "id": 4,
        "title": "大學學術",
        "icon": "🎓",
        "description": "學術閱讀、研究、論證、摘要與正式用語",
        "stages": _make_stages(4, ["學術單字入門", "研究方法", "資料與證據", "論文摘要", "立場與反駁", "因果推論", "正式語氣", "簡報問答", "學術克漏字", "段落邏輯", "批判閱讀", "大學 Boss"]),
    },
]

ACHIEVEMENTS = [
    {"key":"first_clear","icon":"⚔️","title":"初次勝利","description":"完成第一個關卡","metric":"completed_stages","target":1,"reward":20},
    {"key":"chapter_one","icon":"🏠","title":"日常生活達人","description":"完成第一章全部 7 關","metric":"chapter1_completed","target":7,"reward":50},
    {"key":"ten_stars","icon":"⭐","title":"星星收藏家","description":"累積獲得 10 顆關卡星星","metric":"total_stars","target":10,"reward":40},
    {"key":"word_tamer","icon":"🐉","title":"第一隻馴服單字","description":"把任一單字練到 5 星","metric":"tamed_words","target":1,"reward":50},
    {"key":"world_explorer","icon":"🗺️","title":"世界探索者","description":"完成 15 個關卡","metric":"completed_stages","target":15,"reward":80},
    {"key":"wordquest_master","icon":"👑","title":"WordQuest 大師","description":"完成三章共 21 關","metric":"completed_stages","target":21,"reward":120},
]


STARTER_WORDS = [
    {"word":"starving","pos":"adjective","zh":"餓到不行","chapter":1,"context":"我很餓，我現在真的需要吃點東西。","example":"I am starving after class.","memory":"想像肚子餓到咕嚕叫：不是普通 hungry，是餓爆的 starving。","distractors":["exhausted","furious","delighted"],"similar":["hungry","thirsty","exhausted"]},
    {"word":"exhausted","pos":"adjective","zh":"累癱了","chapter":1,"context":"我今天讀了一整天，現在只想躺平。","example":"She felt exhausted after practice.","memory":"手機只剩 1% 電，就像人 exhausted：幾乎沒電。","distractors":["starving","delighted","tiny"],"similar":["tired","sleepy","starving"]},
    {"word":"furious","pos":"adjective","zh":"非常生氣","chapter":1,"context":"有人插隊還裝沒事，我氣到快冒煙。","example":"He was furious about the mistake.","memory":"普通生氣是 angry；氣到像火山爆發才是 furious。","distractors":["calm","delighted","hungry"],"similar":["angry","annoyed","delighted"]},
    {"word":"delighted","pos":"adjective","zh":"很開心","chapter":1,"context":"朋友準備了驚喜生日派對，我覺得超開心。","example":"I was delighted to see you.","memory":"收到超想要的禮物，那種『太開心了！』就是 delighted。","distractors":["furious","exhausted","afraid"],"similar":["pleased","excited","furious"]},
    {"word":"confident","pos":"adjective","zh":"有自信的","chapter":1,"context":"我練習很多次，所以上台報告時不太害怕。","example":"Be confident when you speak.","memory":"你上台不怕、相信自己做得到，就是 confident，不是 nervous。","distractors":["nervous","hungry","silent"],"similar":["nervous","anxious","proud"]},
    {"word":"nervous","pos":"adjective","zh":"緊張的","chapter":1,"context":"輪到我上台報告前，我手心一直冒汗。","example":"I feel nervous before presentations.","memory":"考試前手心冒汗、心跳快，就是 nervous。","distractors":["confident","calm","delighted"],"similar":["anxious","confident","calm"]},
    {"word":"borrow","pos":"verb","zh":"借入","chapter":2,"context":"我忘了帶筆，所以想跟同學借一支。","example":"Can I borrow your pen?","memory":"borrow = 借進來；東西往我這邊移。lend = 借出去。","distractors":["lend","buy","sell"],"similar":["lend","rent","take"]},
    {"word":"lend","pos":"verb","zh":"借出","chapter":2,"context":"同學忘了帶橡皮擦，我把我的借給他。","example":"I can lend you my eraser.","memory":"lend = 我把東西借出去；方向跟 borrow 相反。","distractors":["borrow","buy","keep"],"similar":["borrow","give","rent"]},
    {"word":"reservation","pos":"noun","zh":"預約／訂位","chapter":3,"context":"去熱門餐廳前先打電話訂位。","example":"I have a reservation for two.","memory":"餐廳或飯店先留一個位置給你，就是 reservation。","distractors":["direction","receipt","menu"],"similar":["appointment","booking","receipt"]},
    {"word":"receipt","pos":"noun","zh":"收據","chapter":3,"context":"結帳後店員給我一張付款證明。","example":"Could I have the receipt, please?","memory":"付完錢拿到的小紙條，就是 receipt。","distractors":["reservation","passport","menu"],"similar":["recipe","reservation","ticket"]},
    {"word":"destination","pos":"noun","zh":"目的地","chapter":3,"context":"我們搭車最後要到達的地方。","example":"Taipei is our final destination.","memory":"旅行最後『要到哪裡』，那個地方就是 destination。","distractors":["departure","direction","station"],"similar":["direction","departure","location"]},
    {"word":"solution","pos":"noun","zh":"解決方法","chapter":2,"context":"這題很難，但老師給了我們一個好方法。","example":"We found a solution to the problem.","memory":"solve 是解決；solution 就是解決方法。","distractors":["question","mistake","report"],"similar":["answer","method","problem"]},
    {"word":"improve","pos":"verb","zh":"改善／進步","chapter":2,"context":"我每天練習，所以英文慢慢變好了。","example":"Practice can improve your English.","memory":"improve 像把能力往上推，代表變更好。","distractors":["forget","borrow","break"],"similar":["develop","practice","review"]},
    {"word":"prepare","pos":"verb","zh":"準備","chapter":2,"context":"明天要報告，我今晚先整理資料。","example":"I need to prepare for the test.","memory":"pre- 有提前的感覺，prepare 就是提前做好準備。","distractors":["arrive","forget","lend"],"similar":["plan","review","practice"]},
    {"word":"compare","pos":"verb","zh":"比較","chapter":2,"context":"老師要我們看兩篇文章哪裡相同、哪裡不同。","example":"Compare these two pictures.","memory":"compare 是把兩個東西放一起看差異。","distractors":["complete","borrow","listen"],"similar":["contrast","check","describe"]},
    {"word":"opinion","pos":"noun","zh":"意見／看法","chapter":3,"context":"我覺得學生應該有更多閱讀時間，這是我的看法。","example":"What is your opinion about this issue?","memory":"opinion 不是事實，是你的想法與立場。","distractors":["receipt","direction","ticket"],"similar":["idea","view","fact"]},
    {"word":"evidence","pos":"noun","zh":"證據","chapter":3,"context":"寫作文時不能只說我覺得，要拿資料支持。","example":"Use evidence to support your answer.","memory":"evidence 是讓別人相信你的證明。","distractors":["emotion","destination","menu"],"similar":["proof","support","reason"]},
    {"word":"significant","pos":"adjective","zh":"重要的／顯著的","chapter":3,"context":"這個改變很大，會影響很多人。","example":"The result was significant.","memory":"significant 比 important 更正式，常用在閱讀和研究。","distractors":["tiny","silent","ordinary"],"similar":["important","major","meaningful"]},
    {"word":"contrast","pos":"verb","zh":"對比","chapter":3,"context":"文章把城市生活和鄉村生活放在一起比較差異。","example":"The article contrasts city life with country life.","memory":"contrast 重點在差異，compare 可以看同也看異。","distractors":["complete","order","borrow"],"similar":["compare","differ","separate"]},
    {"word":"analyze","pos":"verb","zh":"分析","chapter":4,"context":"教授要我們拆開資料，找出背後的原因。","example":"We need to analyze the data carefully.","memory":"analyze 就是把複雜東西拆開看。","distractors":["memorize","guess","arrive"],"similar":["examine","study","interpret"]},
    {"word":"hypothesis","pos":"noun","zh":"假設","chapter":4,"context":"做研究前，我們先提出一個可以驗證的想法。","example":"The experiment tested our hypothesis.","memory":"hypothesis 是研究一開始拿來測的假設。","distractors":["receipt","destination","emotion"],"similar":["assumption","theory","claim"]},
    {"word":"methodology","pos":"noun","zh":"研究方法","chapter":4,"context":"論文要說明你怎麼收集和分析資料。","example":"The methodology explains how the study was conducted.","memory":"method 是方法；methodology 是整套研究方法。","distractors":["vocabulary","reservation","direction"],"similar":["method","approach","procedure"]},
    {"word":"interpret","pos":"verb","zh":"詮釋／解讀","chapter":4,"context":"同一組數據可能有不同解讀，所以要說明你的理由。","example":"How do you interpret these findings?","memory":"interpret 是說明你怎麼理解資料或文字。","distractors":["translate","borrow","order"],"similar":["explain","analyze","understand"]},
    {"word":"credible","pos":"adjective","zh":"可信的","chapter":4,"context":"寫報告時要找可靠來源，不要只看隨便的貼文。","example":"Use credible sources in your essay.","memory":"credible 跟 credit 都有信任感，代表值得相信。","distractors":["furious","tiny","hungry"],"similar":["reliable","trustworthy","valid"]},
    {"word":"synthesize","pos":"verb","zh":"整合","chapter":4,"context":"讀完多篇文章後，要把共同觀點整理成自己的結論。","example":"The essay synthesizes several studies.","memory":"synthesize 是把很多來源融合成一個完整想法。","distractors":["separate","forget","guess"],"similar":["combine","integrate","summarize"]},
    {"word":"subsequent","pos":"adjective","zh":"後續的","chapter":4,"context":"第一次實驗後，後續研究修正了方法。","example":"Subsequent studies reached a different conclusion.","memory":"subsequent 是正式說法，指後來接著發生的。","distractors":["previous","tiny","calm"],"similar":["following","later","next"]},
    {"word":"framework","pos":"noun","zh":"架構","chapter":4,"context":"寫研究時，我們需要一個架構來整理想法。","example":"This framework helps explain the results.","memory":"framework 像房子的骨架，幫想法站起來。","distractors":["ticket","menu","receipt"],"similar":["structure","model","system"]},
]

WORD_HINTS = {item["word"]: item["zh"] for item in STARTER_WORDS}
WORD_HINTS.update({
    "calm":"冷靜的","hungry":"餓的","thirsty":"口渴的","tired":"累的","sleepy":"想睡的",
    "afraid":"害怕的","tiny":"很小的","silent":"安靜的","anxious":"焦慮的","proud":"驕傲的",
    "angry":"生氣的","annoyed":"惱怒的","pleased":"愉快的","excited":"興奮的","rent":"租借",
    "take":"拿取","give":"給","keep":"保留","buy":"購買","sell":"賣出","direction":"方向",
    "receipt":"收據","menu":"菜單","appointment":"預約","booking":"訂位","passport":"護照",
    "recipe":"食譜","ticket":"票","departure":"出發","station":"車站","location":"位置",
    "see":"看見","seeing":"看見，V-ing","saw":"see 的過去式","seen":"see 的過去分詞",
    "tell":"說","telling":"說，V-ing","told":"tell 的過去式","to tell":"to 加原形",
    "order":"點餐","ordering":"點餐，V-ing","ordered":"order 的過去式","to order":"to + 原形",
    "question":"問題","mistake":"錯誤","report":"報告","answer":"答案","method":"方法","problem":"問題",
    "develop":"發展","practice":"練習","review":"複習","arrive":"抵達","plan":"計畫","complete":"完成",
    "listen":"聽","fact":"事實","proof":"證明","support":"支持","reason":"理由","emotion":"情緒",
    "ordinary":"普通的","major":"主要的","meaningful":"有意義的","differ":"不同","separate":"分開",
    "memorize":"記憶","guess":"猜測","examine":"檢查","study":"研究","assumption":"假定",
    "theory":"理論","claim":"主張","approach":"方法","procedure":"程序","vocabulary":"字彙",
    "translate":"翻譯","understand":"理解","reliable":"可靠的","trustworthy":"可信的","valid":"有效的",
    "combine":"結合","integrate":"整合","summarize":"摘要","previous":"先前的","following":"接下來的",
    "later":"較晚的","next":"下一個","structure":"結構","model":"模型","system":"系統",
})

CLOZE_TRAPS = [
    {"chapter":2,"prompt":"I look forward to _____ you soon.","answer":"seeing","options":["see","seeing","saw","seen"],"explanation":"look forward to 後面的 to 是介系詞，所以要接名詞或 V-ing；因此選 seeing。","memory":"看到 look forward to，直接想到後面接 V-ing。"},
    {"chapter":2,"prompt":"She is good at _____ stories.","answer":"telling","options":["tell","telling","told","to tell"],"explanation":"be good at 的 at 是介系詞，後面接 V-ing，所以是 telling stories。","memory":"介系詞 at 後面遇到動詞，通常變成 V-ing。"},
    {"chapter":3,"prompt":"We decided _____ dinner near the hotel.","answer":"to order","options":["order","ordering","ordered","to order"],"explanation":"decide 後面常接 to + 原形，所以是 decided to order。","memory":"decide to do = 決定去做某事。"},
    {"chapter":4,"prompt":"The researcher tried _____ the data from multiple sources.","answer":"to synthesize","options":["synthesize","synthesizing","synthesized","to synthesize"],"explanation":"try to do 表示試著去做某事；正式學術句中可用 tried to synthesize。","memory":"try to do = 試著做；try doing = 試做看看效果。"},
    {"chapter":4,"prompt":"The article provides evidence _____ the hypothesis.","answer":"supporting","options":["support","supporting","supported","to support"],"explanation":"evidence supporting the hypothesis 是分詞片語，表示支持假設的證據。","memory":"名詞後面用 V-ing 可以補充說明它正在做的功能。"},
]

DAILY_MISSIONS = [
    {"key":"correct_5","title":"今天答對 5 題","target":5,"metric":"correct_answers","reward":20},
    {"key":"speak_3","title":"今天唸 3 個單字","target":3,"metric":"speech_attempts","reward":15},
    {"key":"review_3","title":"今天複習 3 個錯題","target":3,"metric":"review_attempts","reward":20},
]

SHOP_ITEMS = [
    {"key":"pronunciation_wand","name":"發音魔杖","price":120,"type":"gear","description":"語音題判定容錯 +10%。"},
    {"key":"memory_amulet","name":"記憶護符","price":150,"type":"gear","description":"答錯時少扣 4 HP。"},
    {"key":"mint_cape","name":"薄荷斗篷","price":80,"type":"cosmetic","description":"角色外觀收藏品。"},
]
