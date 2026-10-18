import os
import requests


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
    fallback=[{"japanese":line,"translation":"尚未設定 AI 翻譯服務","vocabulary":[],"grammar":""} for line in lines]
    api_key=os.getenv("AI_API_KEY","").strip()
    if not api_key: return fallback, "local"
    base=os.getenv("AI_BASE_URL","https://api.openai.com/v1").rstrip("/")
    model=os.getenv("AI_MODEL","gpt-4o-mini")
    prompt=("你是日文學習老師。請把以下日文歌詞逐行翻成自然的繁體中文，並幫助初學者學習。"
            "只回傳 JSON 陣列，每個元素包含 japanese、translation、vocabulary（最多 3 個，格式為單字、讀音、中文）、grammar。"
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
