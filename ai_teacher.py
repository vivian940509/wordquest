import os
import requests

LOCAL_LYRICS_NOTES = {
    "かっこいいから好きなんじゃない": ("ka kko ii ka ra suki nan ja na i", "我不是因為你很酷才喜歡你"),
    "好きだからかっこいいんだよ": ("suki da ka ra ka kko ii n da yo", "我覺得你很酷，是因為我喜歡你"),
    "だれかにばかにされてもなんともない": ("da re ka ni ba ka ni sa re te mo nan to mo na i", "就算被別人嘲笑也沒關係"),
    "忘れないでほしい": ("wa su re na i de ho shi i", "希望你不要忘記"),
    "ずっと隣にいてくれませんか": ("zu tto to na ri ni i te ku re ma se n ka", "可以一直陪在我身邊嗎"),
    "貴方が好きなの": ("a na ta ga suki na no", "我喜歡你"),
    "君を愛おしく思うよ": ("ki mi o i to o shi ku o mo u yo", "我覺得你很令人珍愛"),
    "今日もシミュレーション": ("kyo u mo shi myu re e sho n", "今天也在反覆模擬"),
    "君との恋は": ("ki mi to no ko i wa", "和你的戀愛"),
    "甘いムスクの香りがしたんだ": ("a ma i mu su ku no ka o ri ga shi ta n da", "帶著甜甜麝香的氣味"),
}

KANA_ROMAJI = {
    "あ":"a","い":"i","う":"u","え":"e","お":"o","か":"ka","き":"ki","く":"ku","け":"ke","こ":"ko",
    "さ":"sa","し":"shi","す":"su","せ":"se","そ":"so","た":"ta","ち":"chi","つ":"tsu","て":"te","と":"to",
    "な":"na","に":"ni","ぬ":"nu","ね":"ne","の":"no","は":"ha","ひ":"hi","ふ":"fu","へ":"he","ほ":"ho",
    "ま":"ma","み":"mi","む":"mu","め":"me","も":"mo","や":"ya","ゆ":"yu","よ":"yo","ら":"ra","り":"ri","る":"ru","れ":"re","ろ":"ro","わ":"wa","を":"o","ん":"n",
    "が":"ga","ぎ":"gi","ぐ":"gu","げ":"ge","ご":"go","ざ":"za","じ":"ji","ず":"zu","ぜ":"ze","ぞ":"zo","だ":"da","ぢ":"ji","づ":"zu","で":"de","ど":"do","ば":"ba","び":"bi","ぶ":"bu","べ":"be","ぼ":"bo","ぱ":"pa","ぴ":"pi","ぷ":"pu","ぺ":"pe","ぽ":"po",
    "きゃ":"kya","きゅ":"kyu","きょ":"kyo","しゃ":"sha","しゅ":"shu","しょ":"sho","ちゃ":"cha","ちゅ":"chu","ちょ":"cho","にゃ":"nya","にゅ":"nyu","にょ":"nyo","ひゃ":"hya","ひゅ":"hyu","ひょ":"hyo","みゃ":"mya","みゅ":"myu","みょ":"myo","りゃ":"rya","りゅ":"ryu","りょ":"ryo","ぎゃ":"gya","ぎゅ":"gyu","ぎょ":"gyo","じゃ":"ja","じゅ":"ju","じょ":"jo","びゃ":"bya","びゅ":"byu","びょ":"byo","ぴゃ":"pya","ぴゅ":"pyu","ぴょ":"pyo",
}


def kana_to_romaji(text):
    normalized="".join(chr(ord(char)-0x60) if "ァ" <= char <= "ヶ" else char for char in (text or ""))
    tokens=[]; index=0; geminate=False
    while index<len(normalized):
        char=normalized[index]
        if char=="っ": geminate=True; index+=1; continue
        if char=="ー":
            if tokens and tokens[-1][-1:] in "aeiou": tokens[-1]+=tokens[-1][-1]
            index+=1; continue
        pair=normalized[index:index+2]
        romaji=KANA_ROMAJI.get(pair) or KANA_ROMAJI.get(char)
        if romaji:
            if geminate and romaji[0:1] not in {"a","i","u","e","o","n"}: romaji=romaji[0]+romaji
            tokens.append(romaji); geminate=False; index+=2 if pair in KANA_ROMAJI else 1; continue
        if char.isspace(): tokens.append("")
        else: tokens.append(char)
        geminate=False; index+=1
    return " ".join(token for token in tokens if token)


def local_lyrics_note(line):
    known=LOCAL_LYRICS_NOTES.get(line)
    if known:
        romaji,translation=known
    else:
        romaji=kana_to_romaji(line)
        translation="本機字典尚未收錄這句；設定 AI 後可取得自然繁中翻譯。"
    return {"japanese":line,"romaji":romaji,"translation":translation,"vocabulary":[],"grammar":""}


def local_explanation(question, selected):
    answer=question.get("answer","")
    answer_zh=question.get("answer_zh","")
    memory=question.get("memory_tip","")
    explanation=question.get("explanation","")
    if question.get("mode")=="speech":
        return f"這題重點不是一次唸得很快，而是先把句子分段唸清楚。先慢速跟讀「{answer}」，再逐漸加快。{memory}"
    if selected:
        return f"你剛剛選了「{selected}」，但這個情境真正要表達的是「{answer}（{answer_zh}）」。{explanation} 記法：{memory}"
    return f"正確答案是「{answer}（{answer_zh}）」。{explanation} 記法：{memory}"


def explain(question, selected):
    """Use an OpenAI-compatible endpoint when configured; otherwise return a deterministic local teacher explanation."""
    fallback=local_explanation(question, selected)
    api_key=os.getenv("AI_API_KEY","").strip()
    base=os.getenv("AI_BASE_URL","https://api.openai.com/v1").rstrip("/")
    model=os.getenv("AI_MODEL","gpt-4o-mini")
    if not api_key:
        return fallback, "local"


def explain_lyrics(lyrics):
    """Translate Japanese lyrics into compact study notes, with a safe local fallback."""
    lines=[line.strip() for line in lyrics.splitlines() if line.strip()]
    fallback=[local_lyrics_note(line) for line in lines]
    api_key=os.getenv("AI_API_KEY","").strip()
    if not api_key: return fallback, "local"
    base=os.getenv("AI_BASE_URL","https://api.openai.com/v1").rstrip("/")
    model=os.getenv("AI_MODEL","gpt-4o-mini")
    prompt=("你是日文學習老師。請把以下日文歌詞逐行翻成自然的繁體中文，並幫助初學者學習。"
            "只回傳 JSON 陣列，每個元素包含 japanese、romaji、translation、vocabulary（最多 3 個，格式為單字、讀音、中文）、grammar。"
            "不要補寫原文沒有的句子。\n歌詞：\n"+"\n".join(lines))
    try:
        r=requests.post(f"{base}/chat/completions",headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
                        json={"model":model,"messages":[{"role":"user","content":prompt}],"temperature":0.2,"max_tokens":1800},timeout=20)
        r.raise_for_status()
        import json
        raw=r.json()["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"): raw=raw.split("\n",1)[1].rsplit("```",1)[0].strip()
        result=json.loads(raw)
        if not isinstance(result,list): raise ValueError("lyrics response is not a list")
        for item in result:
            if not isinstance(item,dict): raise ValueError("lyrics item is not an object")
            item["romaji"]=item.get("romaji") or kana_to_romaji(item.get("japanese", ""))
        return result, "ai"
    except Exception:
        return fallback, "local"
    prompt=("你是 WordQuest 英文老師。請用繁體中文、國中生也懂的白話，最多 120 字解釋錯題。"
            "一定要包含：使用者為何容易選錯、正確答案與錯誤選項差異、一個生活化記法。\n"
            f"題目：{question.get('prompt','')}\n使用者答案：{selected or '未作答'}\n"
            f"正確答案：{question.get('answer','')}\n既有說明：{question.get('explanation','')}")
    try:
        r=requests.post(f"{base}/chat/completions",headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
                        json={"model":model,"messages":[{"role":"user","content":prompt}],"temperature":0.4,"max_tokens":220},timeout=12)
        r.raise_for_status()
        text=r.json()["choices"][0]["message"]["content"].strip()
        return text or fallback, "ai"
    except Exception:
        return fallback, "local"
