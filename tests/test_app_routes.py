from pathlib import Path

from app import app
from word_data import CHAPTERS


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


def test_map_page_uses_single_fast_snapshot(monkeypatch):
    app.config["TESTING"] = True
    calls = {"snapshot": 0, "progress": 0, "achievements": 0, "metrics": 0}

    def fake_user():
        return {"id": "profile-123", "username": "Nova", "unlocked_chapter": 4}

    def fake_snapshot(user_id):
        calls["snapshot"] += 1
        return {
            "progress": {},
            "earned": set(),
            "metrics": {"completed_stages": 0, "total_stars": 0, "total_stages": 48, "max_stars": 144},
        }

    def forbidden(*args, **kwargs):
        raise AssertionError("map page should use fetch_map_snapshot instead of extra progress/stat queries")

    monkeypatch.setattr("app.current_user", fake_user)
    monkeypatch.setattr("app.fetch_map_snapshot", fake_snapshot)
    monkeypatch.setattr("app.fetch_stage_progress", forbidden)
    monkeypatch.setattr("app.fetch_achievements", forbidden)
    monkeypatch.setattr("app.achievement_metrics", forbidden)

    with app.test_client() as client:
        response = client.get("/map")

    assert response.status_code == 200
    assert calls["snapshot"] == 1
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
    assert "delighted".encode("utf-8") in response.data
    assert "confident".encode("utf-8") in response.data
    assert b'data-speak-word="starving"' in response.data
    assert b"/battle?chapter=1&amp;stage=101&amp;difficulty=beginner" in response.data


def test_stage_lesson_has_mobile_single_card_preview_flow():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/lesson?chapter=1&stage=101&difficulty=beginner")
    html = response.data.decode("utf-8")
    assert response.status_code == 200
    assert 'class="lesson-carousel"' in html
    assert 'data-lesson-carousel' in html
    assert 'data-card-total="5"' in html
    assert "1 / 5" in html
    assert 'class="lesson-progress-bar"' in html
    assert 'data-lesson-prev' in html
    assert 'data-lesson-next' in html
    assert "下一個" in html
    assert "開始挑戰" in html
    assert "展開" in html


def test_battle_page_uses_question_time_limit_after_preview():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/battle?chapter=1&stage=101&difficulty=beginner")
    assert response.status_code == 200
    assert b'data-countdown="8"' in response.data
    assert b'data-answer-form' in response.data


def test_pronounce_falls_back_to_same_origin_tts_when_dictionary_has_no_audio(monkeypatch):
    app.config["TESTING"] = True

    def fake_lookup(word):
        return {"word": word, "phonetic": "", "audio": "", "definition": ""}

    monkeypatch.setattr("app.lookup_word", fake_lookup)
    with app.test_client() as client:
        response = client.get("/api/pronounce?word=starving")

    assert response.status_code == 200
    assert response.get_json()["audio"] == "/api/pronounce/audio?word=starving"


def test_tts_proxy_returns_same_origin_audio(monkeypatch):
    app.config["TESTING"] = True
    app.config["PRONUNCIATION_CACHE"].clear()

    class FakeTtsResponse:
        ok = True
        content = b"x" * 300
        headers = {"Content-Type": "audio/mpeg"}

        def raise_for_status(self):
            return None

    def fake_get(url, headers=None, timeout=None):
        assert "translate_tts" in url
        assert "starving" in url
        return FakeTtsResponse()

    monkeypatch.setattr("app.requests.get", fake_get)
    with app.test_client() as client:
        response = client.get("/api/tts?word=starving")

    assert response.status_code == 200
    assert response.data == b"x" * 300
    assert response.content_type == "audio/mpeg"


def test_register_logs_in_without_email_verification(monkeypatch):
    app.config["TESTING"] = True

    def fake_auth(path, payload=None, access_token=None):
        return {"user": {"id": "11111111-1111-4111-8111-111111111111", "user_metadata": {"username": "Nova"}}}, None

    def fake_profile(auth_user_id, username="勇者", guest_user_id=None):
        return {"id": "profile-123", "username": username}

    monkeypatch.setattr("app.supabase_auth_request", fake_auth)
    monkeypatch.setattr("app.ensure_auth_profile", fake_profile)
    with app.test_client() as client:
        response = client.post(
            "/register",
            data={"username": "Nova", "email": "nova@example.com", "password": "secret1"},
        )
        with client.session_transaction() as session:
            auth_email = session.get("auth_email")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert auth_email == "nova@example.com"


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


def test_custom_practice_page_lists_all_requested_modes():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/practice")
    html=response.data.decode("utf-8")
    assert response.status_code == 200
    for text in ["只練錯題","只練弱點","未馴服單字","指定章節","10 題快速練習","30 題挑戰","無限模式"]:
        assert text in html


def test_forgot_password_and_google_login_controls_exist():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response=client.get("/login")
    html=response.data.decode("utf-8")
    assert "忘記密碼" in html
    assert "使用 Google 登入" in html
    assert 'class="google-action polished-google-action"' in html
    assert "不用另外記密碼" in html


def test_register_page_has_google_signup_control():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response=client.get("/register")
    html=response.data.decode("utf-8")
    assert response.status_code == 200
    assert "使用 Google 建立帳號" in html
    assert 'href="/login/google"' in html
    assert 'class="google-action polished-google-action"' in html
    assert "原本的訪客進度會一起保留" in html


def test_campaign_battle_has_five_question_progress():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response=client.get("/battle?chapter=1&stage=101&difficulty=beginner&restart=1")
    html=response.data.decode("utf-8")
    assert response.status_code == 200
    assert "第 1/5 題" in html
    assert 'data-countdown="8"' in html


def test_pronounce_audio_falls_back_to_google_when_dictionary_audio_fails(monkeypatch):
    app.config["TESTING"] = True
    app.config["PRONUNCIATION_CACHE"].clear()

    monkeypatch.setattr("app.lookup_word", lambda word: {"word": word, "phonetic": "", "audio": "https://bad.example/audio.mp3"})

    class BadResponse:
        ok = False
        content = b""
        headers = {}

    class GoodResponse:
        ok = True
        content = b"x" * 300
        headers = {"Content-Type": "audio/mpeg"}

    def fake_get(url, headers=None, timeout=None):
        return BadResponse() if "bad.example" in url else GoodResponse()

    monkeypatch.setattr("app.requests.get", fake_get)
    with app.test_client() as client:
        response = client.get("/api/pronounce/audio?word=starving")

    assert response.status_code == 200
    assert response.mimetype == "audio/mpeg"
    assert response.headers["X-Pronunciation-Source"] == "google-tts"
    assert "s-maxage" in response.headers["Cache-Control"]


def test_pronounce_audio_uses_fast_timeouts(monkeypatch):
    app.config["TESTING"] = True
    app.config["PRONUNCIATION_CACHE"].clear()
    observed_lookup_timeouts = []
    observed_audio_timeouts = []

    def fake_lookup(word, timeout=None):
        observed_lookup_timeouts.append(timeout)
        return {"word": word, "phonetic": "", "audio": "https://bad.example/audio.mp3"}

    class BadResponse:
        ok = False
        content = b""
        headers = {}

    class GoodResponse:
        ok = True
        content = b"x" * 300
        headers = {"Content-Type": "audio/mpeg"}

    def fake_get(url, headers=None, timeout=None):
        observed_audio_timeouts.append(timeout)
        return BadResponse() if "bad.example" in url else GoodResponse()

    monkeypatch.setattr("app.lookup_word", fake_lookup)
    monkeypatch.setattr("app.requests.get", fake_get)
    with app.test_client() as client:
        response = client.get("/api/pronounce/audio?word=starving")

    assert response.status_code == 200
    assert observed_lookup_timeouts
    assert observed_audio_timeouts
    assert all(timeout is not None and timeout <= 1.2 for timeout in observed_lookup_timeouts)
    assert all(timeout is not None and timeout <= 1.2 for timeout in observed_audio_timeouts)


def test_pronounce_audio_serves_cached_success_without_external_calls(monkeypatch):
    app.config["TESTING"] = True
    app.config["PRONUNCIATION_CACHE"].clear()
    calls = {"lookup": 0, "audio": 0}

    def fake_lookup(word, timeout=None):
        calls["lookup"] += 1
        return {"word": word, "phonetic": "", "audio": ""}

    class GoodResponse:
        ok = True
        content = b"cached-audio" * 30
        headers = {"Content-Type": "audio/mpeg"}

    def fake_get(url, headers=None, timeout=None):
        calls["audio"] += 1
        return GoodResponse()

    monkeypatch.setattr("app.lookup_word", fake_lookup)
    monkeypatch.setattr("app.requests.get", fake_get)
    with app.test_client() as client:
        first = client.get("/api/pronounce/audio?word=starving")
        second = client.get("/api/pronounce/audio?word=starving")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.data == first.data
    assert calls == {"lookup": 1, "audio": 1}


def test_frontend_pronunciation_falls_back_within_two_seconds():
    js = (Path(app.root_path) / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert "PRONUNCIATION_AUDIO_START_TIMEOUT_MS=1500" in js
    assert "audio timeout" in js
    assert "7000" not in js
