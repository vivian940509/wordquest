import re
from pathlib import Path

import database
from app import app, run_summary
from word_data import CHAPTERS, CLOZE_TRAPS, STARTER_WORDS


def test_curriculum_map_has_four_school_levels_and_many_stages():
    assert [chapter["title"] for chapter in CHAPTERS] == ["國小基礎", "國中進階", "高中核心", "大學學術"]
    assert [len(chapter["stages"]) for chapter in CHAPTERS] == [20, 80, 100, 100]
    assert [chapter["words_per_stage"] for chapter in CHAPTERS] == [10, 15, 20, 25]


def test_map_summary_uses_expanded_curriculum_totals():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/map")
    assert response.status_code == 200
    assert b"/300" in response.data
    assert b"/1500" in response.data


def test_map_uses_numbered_stage_labels_instead_of_topic_titles():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/map")

    html = response.data.decode("utf-8")
    assert response.status_code == 200
    assert "第 1 關" in html
    assert "第 2 關" in html
    assert "餓肚子警報" not in html
    assert "累到不行" not in html


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
            "metrics": {"completed_stages": 0, "total_stars": 0, "total_stages": 300, "max_stars": 1500},
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
    assert b"/300" in response.data
    assert b"/1500" in response.data


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


def test_study_page_includes_distractor_word_cards():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/study")
    assert response.status_code == 200
    assert "afraid".encode("utf-8") in response.data
    assert "害怕的".encode("utf-8") in response.data
    assert b'data-speak-word="afraid"' in response.data


def test_study_cards_include_every_vocabulary_option_word():
    card_words = {item["word"] for item in STARTER_WORDS}
    option_words = set()
    for item in STARTER_WORDS:
        option_words.update(item.get("distractors", []))
        option_words.update(item.get("similar", []))

    assert option_words <= card_words


def test_study_cards_do_not_include_cloze_grammar_forms():
    card_words = {item["word"] for item in STARTER_WORDS}
    assert {"saw", "seen", "told", "ordered", "synthesized"}.isdisjoint(card_words)


def test_cloze_review_bank_has_complete_well_formed_questions():
    assert len(CLOZE_TRAPS) >= 20
    assert {item["chapter"] for item in CLOZE_TRAPS} == {1, 2, 3, 4}

    for item in CLOZE_TRAPS:
        assert set(item) >= {"chapter", "prompt", "answer", "options", "explanation", "memory"}
        assert item["prompt"].count("_____") == 1
        assert item["answer"] in item["options"]
        assert len(item["options"]) == 4
        assert len(set(item["options"])) == 4
        assert item["explanation"]
        assert item["memory"]


def test_each_chapter_has_at_least_ten_unique_word_cards():
    assert len({item["word"] for item in STARTER_WORDS}) >= 5000
    for chapter in CHAPTERS:
        words = [item["word"] for item in STARTER_WORDS if item.get("chapter") == chapter["id"]]
        assert len(words) == len(set(words))
        assert len(set(words)) >= chapter["words_per_stage"] * 2


def test_stage_lesson_shows_meaning_pronunciation_before_practice():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/lesson?chapter=1&stage=101&difficulty=beginner")
    assert response.status_code == 200
    assert "第 1 關".encode("utf-8") in response.data
    assert "餓肚子警報".encode("utf-8") not in response.data
    assert "starving".encode("utf-8") in response.data
    assert "餓到不行".encode("utf-8") in response.data
    assert b'data-speak-word="starving"' in response.data
    assert b"/battle?chapter=1&amp;stage=101&amp;difficulty=beginner" in response.data


def test_adjacent_stage_lessons_use_different_word_sets():
    app.config["TESTING"] = True
    with app.test_client() as client:
        first = client.get("/lesson?chapter=1&stage=101&difficulty=beginner")
        second = client.get("/lesson?chapter=1&stage=102&difficulty=beginner")

    first_html = first.data.decode("utf-8")
    second_html = second.data.decode("utf-8")
    first_words = set(re.findall(r'data-speak-word="([^"]+)"', first_html))
    second_words = set(re.findall(r'data-speak-word="([^"]+)"', second_html))
    assert first.status_code == 200
    assert second.status_code == 200
    assert len(first_words) == 10
    assert len(second_words) == 10
    assert first_words.isdisjoint(second_words)
    assert "starving" in first_words
    assert "student" in second_words


def test_lesson_word_count_scales_by_school_level():
    app.config["TESTING"] = True
    cases = [
        (1, 101, 10),
        (2, 201, 15),
        (3, 301, 20),
        (4, 401, 25),
    ]
    with app.test_client() as client:
        for chapter, stage, expected in cases:
            response = client.get(f"/lesson?chapter={chapter}&stage={stage}&difficulty=beginner")
            html = response.data.decode("utf-8")
            words = re.findall(r'data-speak-word="([^"]+)"', html)
            assert response.status_code == 200
            assert len(words) == expected
            assert len(set(words)) == expected
            assert f'data-card-total="{expected}"' in html


def test_stage_lesson_has_mobile_single_card_preview_flow():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/lesson?chapter=1&stage=101&difficulty=beginner")
    html = response.data.decode("utf-8")
    assert response.status_code == 200
    assert 'class="lesson-carousel"' in html
    assert 'data-lesson-carousel' in html
    assert 'data-card-total="10"' in html
    assert "1 / 10" in html
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
    assert b'data-correct-answer=' in response.data


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


def test_answer_uses_fast_dictionary_lookup_before_result(monkeypatch):
    app.config["TESTING"] = True
    observed_timeouts = []

    def fake_lookup(word, timeout=None):
        observed_timeouts.append(timeout)
        return {"word": word, "phonetic": "", "audio": "", "definition": ""}

    monkeypatch.setattr("app.lookup_word", fake_lookup)
    with app.test_client() as client:
        client.get("/battle")
        with client.session_transaction() as session:
            question = session["question"]
        response = client.post("/answer", data={"selected": question["answer"]})

    assert response.status_code == 302
    assert observed_timeouts
    assert all(timeout is not None and timeout <= 1.2 for timeout in observed_timeouts)


def test_final_campaign_answer_goes_to_summary_without_dictionary_lookup(monkeypatch):
    app.config["TESTING"] = True

    def forbidden_lookup(*args, **kwargs):
        raise AssertionError("final campaign answer should not wait for result-page dictionary lookup")

    monkeypatch.setattr("app.lookup_word", forbidden_lookup)
    with app.test_client() as client:
        client.get("/battle?chapter=1&stage=101&difficulty=beginner&restart=1")
        with client.session_transaction() as session:
            run = session["campaign_run"]
            run["results"] = [
                {"correct": True, "elapsed_ms": 500, "exp": 10, "coins": 3, "word": "starving", "answer": "starving", "selected": "starving", "prompt": "p"}
                for _ in range(9)
            ]
            session["campaign_run"] = run
        client.get("/battle?chapter=1&stage=101&difficulty=beginner")
        with client.session_transaction() as session:
            question = session["question"]
        response = client.post("/answer", data={"selected": question["answer"]})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/level-summary")


def test_campaign_question_totals_match_preview_count_for_all_school_levels(monkeypatch):
    profile = database.ensure_guest_profile(username="Test Runner")
    profile["unlocked_chapter"] = 4
    monkeypatch.setattr("app.current_user", lambda: profile)
    app.config["TESTING"] = True
    cases = [(1, 101, 10), (2, 201, 15), (3, 301, 20), (4, 401, 25)]

    with app.test_client() as client:
        for chapter, stage, expected in cases:
            lesson = client.get(f"/lesson?chapter={chapter}&stage={stage}&difficulty=beginner")
            words = re.findall(r'data-speak-word="([^"]+)"', lesson.data.decode("utf-8"))
            assert len(words) == expected
            assert len(set(words)) == expected

            client.get(f"/battle?chapter={chapter}&stage={stage}&difficulty=beginner&restart=1")
            with client.session_transaction() as session:
                run = session["campaign_run"]
                run["results"] = [
                    {"correct": True, "elapsed_ms": 500, "exp": 10, "coins": 3, "word": f"word-{i}", "answer": f"word-{i}", "selected": f"word-{i}", "prompt": "p"}
                    for i in range(expected - 2)
                ]
                session["campaign_run"] = run

            client.get(f"/battle?chapter={chapter}&stage={stage}&difficulty=beginner")
            with client.session_transaction() as session:
                question = session["question"]
                assert question["campaign_total"] == expected
            response = client.post("/answer", data={"selected": question["answer"]})
            assert response.status_code == 302
            assert response.headers["Location"].endswith(f"/battle?chapter={chapter}&stage={stage}&difficulty=beginner")

            client.get(f"/battle?chapter={chapter}&stage={stage}&difficulty=beginner")
            with client.session_transaction() as session:
                question = session["question"]
                assert question["campaign_total"] == expected
            response = client.post("/answer", data={"selected": question["answer"]})
            assert response.status_code == 302
            assert response.headers["Location"].endswith("/level-summary")


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
    for text in ["只練錯題","只練弱點","未馴服單字","指定章節","10 題快速練習","口說練習","30 題挑戰","無限模式"]:
        assert text in html


def test_speech_practice_starts_a_standalone_speech_question():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.post("/practice/start", data={"mode": "speech", "difficulty": "intermediate", "chapter": 1})
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/practice/battle")

        battle = client.get("/practice/battle")
        html = battle.data.decode("utf-8")

    assert battle.status_code == 200
    assert "口說練習" in html
    assert "中文：" in html
    assert "提示：" in html
    assert 'class="speech-button"' in html


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


def test_campaign_battle_uses_stage_word_count_progress():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response=client.get("/battle?chapter=1&stage=101&difficulty=beginner&restart=1")
    html=response.data.decode("utf-8")
    assert response.status_code == 200
    assert "第 1/10 題" in html
    assert 'data-countdown="8"' in html


def test_perfect_campaign_summary_awards_five_stars():
    results = [{"correct": True, "elapsed_ms": 500, "exp": 10, "coins": 3} for _ in range(10)]

    summary = run_summary(results, total=10)

    assert summary["stars"] == 5


def test_campaign_continues_until_stage_word_count():
    app.config["TESTING"] = True
    with app.test_client() as client:
        client.get("/battle?chapter=1&stage=101&difficulty=beginner&restart=1")
        for _ in range(5):
            with client.session_transaction() as session:
                question = session["question"]
            response = client.post("/answer", data={"selected": question["answer"]})
            assert response.status_code == 302
            assert response.headers["Location"].endswith("/battle?chapter=1&stage=101&difficulty=beginner")
            if _ < 4:
                client.get("/battle?chapter=1&stage=101&difficulty=beginner")

        with client.session_transaction() as session:
            assert len(session["campaign_run"]["results"]) == 5
            assert "level_summary" not in session


def test_campaign_practices_each_preview_word_once_before_summary():
    app.config["TESTING"] = True
    with app.test_client() as client:
        lesson = client.get("/lesson?chapter=1&stage=101&difficulty=beginner")
        preview_words = set(re.findall(r'data-speak-word="([^"]+)"', lesson.data.decode("utf-8")))
        client.get("/battle?chapter=1&stage=101&difficulty=beginner&restart=1")

        practiced_words = []
        for index in range(10):
            with client.session_transaction() as session:
                question = session["question"]
            practiced_words.append(question["word"])
            response = client.post("/answer", data={"selected": question["answer"]})
            assert response.status_code == 302
            if index < 9:
                assert response.headers["Location"].endswith("/battle?chapter=1&stage=101&difficulty=beginner")
                client.get("/battle?chapter=1&stage=101&difficulty=beginner")
            else:
                assert response.headers["Location"].endswith("/level-summary")

        assert set(practiced_words) == preview_words


def test_level_summary_shows_wrong_answers_in_dropdown():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as session:
            session["level_summary"] = {
                "stage_id": 101,
                "chapter_id": 1,
                "difficulty": "beginner",
                "stars": 1,
                "correct": 8,
                "attempts": 10,
                "accuracy": 80,
                "avg_seconds": 1.2,
                "exp": 80,
                "coins": 20,
                "score": 76,
                "weakest": "library",
                "wrong": [
                    {"answer": "library", "selected": "student", "prompt": "這是日常與課堂中很常遇到的字：圖書館。"}
                ],
            }
        response = client.get("/level-summary")

    html = response.data.decode("utf-8")
    assert response.status_code == 200
    assert "<details" in html
    assert "<summary" in html
    assert "本關錯題 1 題" in html
    assert "library" in html
    assert "student" in html


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


def test_frontend_answer_submit_shows_immediate_feedback():
    js = (Path(app.root_path) / "static" / "js" / "app.js").read_text(encoding="utf-8")
    css = (Path(app.root_path) / "static" / "css" / "style.css").read_text(encoding="utf-8")

    assert "答對，下一題載入中…" in js
    assert "答錯，解析載入中… 正確答案是" in js
    assert "dataset.correctAnswer" in js
    assert "answer-correct" in js
    assert "answer-wrong" in js
    assert "submitAnswer=chosen=>" in js
    assert "closest('button[name=\"selected\"]')" in js
    assert "handleAnswerPress" in js
    assert "pointerup" in js
    assert "touchend" in js
    assert "click" in js
    assert "form.submit()" in js
    assert "requestAnimationFrame(()=>form.submit())" not in js
    assert "setTimeout(()=>form.submit()" not in js
    assert "form.addEventListener('submit'" in js
    assert "form.querySelectorAll('button').forEach" in js
    assert "hiddenSelected.name='selected'" in js
    assert "hiddenSelected.value=chosen?.value||''" in js
    assert "touch-action: manipulation" in css
