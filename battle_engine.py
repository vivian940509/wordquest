import random
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from word_data import CLOZE_TRAPS, STARTER_WORDS, WORD_HINTS

SRS_INTERVAL_DAYS = [0, 1, 3, 7, 14, 30]
DIFFICULTY_LABELS = {"beginner": "初級", "intermediate": "中級", "advanced": "高級"}


def _cards_for_chapter(chapter_id):
    cards = [x for x in STARTER_WORDS if x.get("chapter") == chapter_id]
    return cards or STARTER_WORDS


def build_vocab_question(seed=None, weak_mode=False, difficulty="beginner", chapter_id=1, stage_id=None):
    rng = random.Random(seed)
    card = rng.choice(_cards_for_chapter(chapter_id))
    if difficulty == "intermediate":
        distractors = card.get("similar", card["distractors"])[:3]
    else:
        distractors = card["distractors"][:3]
    options = [card["word"], *distractors]
    if weak_mode and difficulty == "beginner":
        options = [card["word"], distractors[0]]
    rng.shuffle(options)
    prompt = card["context"] if difficulty != "advanced" else card["example"].replace(card["word"], "_____")
    instruction = "選出符合情境的英文" if difficulty != "advanced" else "Choose the best word for the sentence"
    show_hints = difficulty == "beginner"
    return {
        "mode": "shield",
        "difficulty": difficulty,
        "difficulty_label": DIFFICULTY_LABELS.get(difficulty, difficulty),
        "chapter_id": chapter_id,
        "stage_id": stage_id,
        "monster": "情境守衛",
        "instruction": instruction,
        "prompt": prompt,
        "answer": card["word"],
        "answer_zh": card["zh"],
        "options": options,
        "show_hints": show_hints,
        "option_details": {option: WORD_HINTS.get(option, "相似干擾字") for option in options},
        "example": card["example"],
        "memory_tip": card.get("memory", card["example"]),
        "explanation": f"{card['word']} 是「{card['zh']}」。{card.get('memory', '')}",
    }


def build_cloze_question(seed=None, chapter_id=2, stage_id=None):
    rng = random.Random(seed)
    traps = [x for x in CLOZE_TRAPS if x.get("chapter") == chapter_id] or CLOZE_TRAPS
    trap = rng.choice(traps)
    options = list(trap["options"])
    rng.shuffle(options)
    return {
        "mode": "trap", "difficulty": "advanced", "difficulty_label": "高級",
        "chapter_id": chapter_id, "stage_id": stage_id, "monster": "文法寶箱",
        "instruction": "選出正確的填空答案", "prompt": trap["prompt"], "answer": trap["answer"],
        "answer_zh": WORD_HINTS.get(trap["answer"], ""), "options": options, "show_hints": False,
        "option_details": {option: WORD_HINTS.get(option, "文法選項") for option in options},
        "example": trap["prompt"].replace("_____", trap["answer"]),
        "memory_tip": trap.get("memory", "先抓固定搭配，再判斷動詞形式。"), "explanation": trap["explanation"],
    }


def build_speech_challenge(seed=None, chapter_id=1, stage_id=None, difficulty="intermediate"):
    rng = random.Random(seed)
    card = rng.choice(_cards_for_chapter(chapter_id))
    return {
        "mode":"speech", "difficulty":difficulty, "difficulty_label":DIFFICULTY_LABELS.get(difficulty, difficulty),
        "chapter_id":chapter_id, "stage_id":stage_id, "monster":"回音法師", "instruction":"跟著唸出這句英文",
        "prompt":card["example"], "answer":card["example"], "answer_zh":card["zh"], "options":[], "show_hints":False,
        "option_details":{}, "example":card["example"], "memory_tip":"先慢慢唸清楚，再追求速度。",
        "explanation":"系統會依瀏覽器辨識結果估算相似度，並給你發音練習建議。",
    }


def build_battle(seed=None, mistake_streak=0, difficulty="beginner", chapter_id=1, stage_id=None):
    rng = random.Random(seed)
    if difficulty == "advanced":
        return build_cloze_question(seed=seed, chapter_id=chapter_id, stage_id=stage_id)
    mode = rng.choice(["shield", "shield", "speech"] if difficulty == "intermediate" else ["shield"])
    if mode == "speech":
        return build_speech_challenge(seed=seed, chapter_id=chapter_id, stage_id=stage_id, difficulty=difficulty)
    return build_vocab_question(seed=seed, weak_mode=mistake_streak >= 2, difficulty=difficulty, chapter_id=chapter_id, stage_id=stage_id)



def build_review_question(word, seed=None):
    rng = random.Random(seed)
    card = next((x for x in STARTER_WORDS if x["word"] == word), None)
    if not card:
        card = rng.choice(STARTER_WORDS)
    distractors = list(card.get("similar", card.get("distractors", [])))[:3]
    options = [card["word"], *distractors]
    rng.shuffle(options)
    return {
        "mode":"review", "difficulty":"intermediate", "difficulty_label":"錯題複習",
        "chapter_id":card.get("chapter",1), "stage_id":None, "monster":"記憶幽靈",
        "instruction":"把這個錯題重新打贏", "prompt":card["context"], "answer":card["word"],
        "answer_zh":card["zh"], "options":options, "show_hints":False,
        "option_details":{option:WORD_HINTS.get(option,"相似干擾字") for option in options},
        "example":card["example"], "memory_tip":card.get("memory",card["example"]),
        "explanation":f"{card['word']} 是「{card['zh']}」。{card.get('memory','')}", "is_review":True,
    }

def speech_similarity(target, transcript):
    target = " ".join((target or "").casefold().split())
    transcript = " ".join((transcript or "").casefold().split())
    return int(round(100 * SequenceMatcher(None, target, transcript).ratio())) if target and transcript else 0


def speech_feedback(score):
    if score >= 90: return "很接近！節奏和單字都很穩。"
    if score >= 75: return "很接近，再慢一點會更清楚。"
    if score >= 55: return "有抓到大部分內容，先把每個單字分開唸清楚。"
    return "先慢慢跟讀一次，特別注意 th、r、v 等容易混淆的音。"


def grade_answer(question, selected, speech_score=None, hp_protection=0):
    if question["mode"] == "speech":
        score = speech_score if speech_score is not None else speech_similarity(question["answer"], selected)
        correct = score >= 75
        hp_loss = max(0, 6 - hp_protection)
        return {"correct":correct,"damage":34 if correct else 12,"hp_delta":0 if correct else -hp_loss,
                "exp":18 if correct else 8,"coins":5 if correct else 2,
                "message":"咒語共鳴成功，攻擊力加倍！" if correct else "這次還沒完全命中，但有完成口說練習。",
                "speech_score":score,"speech_feedback":speech_feedback(score)}
    correct = (selected or "").strip().casefold() == question["answer"].strip().casefold()
    hp_loss = max(0, 12 - hp_protection)
    return {"correct":correct,"damage":28 if correct else 0,"hp_delta":0 if correct else -hp_loss,
            "exp":15 if correct else 6,"coins":4 if correct else 1,
            "message":"破盾成功！這張單字卡開始發光。" if correct else "被干擾字騙到了，看看差異就會更牢。"}


def build_wrong_answer_analysis(question, selected):
    return {
        "selected": selected or "（未作答）",
        "correct_answer": question["answer"],
        "why_wrong": f"「{selected}」和題目情境不吻合。{question['explanation']}" if selected else question["explanation"],
        "memory_tip": question.get("memory_tip", question.get("example", "")),
        "example": question.get("example", ""),
    }


def next_review_time(proficiency_level, now=None):
    now = now or datetime.now(timezone.utc)
    level = max(0, min(int(proficiency_level), len(SRS_INTERVAL_DAYS) - 1))
    return now + timedelta(days=SRS_INTERVAL_DAYS[level])
