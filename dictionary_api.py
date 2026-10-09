import requests


API_ROOT = "https://api.dictionaryapi.dev/api/v2/entries/en"


def lookup_word(word, timeout=5):
    clean_word = (word or "").strip().lower()
    if not clean_word:
        return None
    try:
        response = requests.get(f"{API_ROOT}/{clean_word}", timeout=timeout)
        response.raise_for_status()
        payload = response.json()[0]
    except Exception:
        return {
            "word": clean_word,
            "phonetic": "",
            "audio": "",
            "definition": "暫時無法連線字典 API，先用遊戲內建情境練習。",
        }

    phonetic = payload.get("phonetic") or ""
    audio = ""
    for item in payload.get("phonetics", []):
        phonetic = phonetic or item.get("text") or ""
        audio = audio or item.get("audio") or ""
        if phonetic and audio:
            break

    definition = ""
    meanings = payload.get("meanings") or []
    if meanings and meanings[0].get("definitions"):
        definition = meanings[0]["definitions"][0].get("definition", "")

    return {
        "word": payload.get("word", clean_word),
        "phonetic": phonetic,
        "audio": audio,
        "definition": definition,
    }
