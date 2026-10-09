from pathlib import Path
import json

from app import app
from word_data import CHAPTERS


def test_vercel_routes_to_python_serverless_entrypoint():
    config = json.loads((Path(app.root_path) / "vercel.json").read_text(encoding="utf-8"))
    assert config["rewrites"] == [{"source": "/(.*)", "destination": "/api/index.py"}]
    entrypoint = (Path(app.root_path) / "api" / "index.py").read_text(encoding="utf-8")
    assert "from app import app" in entrypoint


def test_curriculum_map_has_four_school_levels_and_many_stages():
    assert [chapter["title"] for chapter in CHAPTERS] == ["國小基礎", "國中進階", "高中核心", "大學學術"]
    assert [len(chapter["stages"]) for chapter in CHAPTERS] == [12, 12, 12, 12]


def test_map_summary_uses_expanded_curriculum_totals():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/map")
    assert response.status_code == 200
    assert b"/48" in response.data
    assert b"/144" in response.data


def test_home_points_to_study_before_battle():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/")
    assert response.status_code == 200
    assert b"/study" in response.data
    assert "先背單字".encode("utf-8") in response.data


def test_study_page_renders_word_cards_and_start_button():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/study")
    assert response.status_code == 200
    assert "starving".encode("utf-8") in response.data
    assert "開始破關".encode("utf-8") in response.data


def test_study_page_has_pronunciation_buttons():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/study")
    assert response.status_code == 200
    assert b'data-speak-word="starving"' in response.data
    assert "聽發音".encode("utf-8") in response.data


def test_stage_lesson_shows_meaning_pronunciation_before_practice():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/lesson?chapter=1&stage=101&difficulty=beginner")
    assert response.status_code == 200
    assert "starving".encode("utf-8") in response.data
    assert "餓到不行".encode("utf-8") in response.data
    assert b'data-speak-word="starving"' in response.data
    assert b"/battle?chapter=1&amp;stage=101&amp;difficulty=beginner" in response.data


def test_answer_redirects_to_get_result_page():
    app.config["TESTING"] = True
    with app.test_client() as client:
        client.get("/battle")
        with client.session_transaction() as session:
            question = session["question"]
        response = client.post("/answer", data={"selected": question["answer"]})
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/result")

        result_response = client.get("/result")
        assert result_response.status_code == 200
        assert "回關卡地圖".encode("utf-8") in result_response.data


def test_battle_page_uses_clear_learning_instruction():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/battle")
    assert response.status_code == 200
    assert "選出符合情境的英文".encode("utf-8") in response.data
    assert "中文提示".encode("utf-8") not in response.data


def test_result_page_uses_local_word_explanation_when_dictionary_is_unavailable(monkeypatch):
    app.config["TESTING"] = True

    def fake_lookup(word):
        return {
            "word": word,
            "phonetic": "",
            "audio": "",
            "definition": "暫時無法連線字典 API，先用遊戲內建情境練習。",
        }

    monkeypatch.setattr("app.lookup_word", fake_lookup)
    with app.test_client() as client:
        client.get("/battle")
        with client.session_transaction() as session:
            session["question"] = {
                "mode": "shield",
                "monster": "情境守衛",
                "instruction": "選出符合情境的英文",
                "prompt": "我練習很多次，所以上台報告時不太害怕。",
                "answer": "confident",
                "options": ["confident", "nervous"],
                "option_details": {"confident": "有自信的", "nervous": "緊張的"},
                "example": "Be confident when you speak.",
                "explanation": "confident 是「有自信的」。",
            }
        client.post("/answer", data={"selected": "confident"})
        response = client.get("/result")

    assert response.status_code == 200
    assert "有自信的".encode("utf-8") in response.data
    assert b'data-speak-word="confident"' in response.data


def test_styles_include_game_motion():
    css = (Path(app.root_path) / "static" / "css" / "style.css").read_text(encoding="utf-8")
    assert "@keyframes monsterFloat" in css
    assert "@keyframes rewardPop" in css
    assert "prefers-reduced-motion" in css
