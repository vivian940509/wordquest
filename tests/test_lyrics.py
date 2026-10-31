import ai_teacher
from app import app


def test_local_lyrics_fallback_includes_romaji_and_trusted_translation(monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)

    lines, source = ai_teacher.explain_lyrics("かっこいいから好きなんじゃない")

    assert source == "local"
    assert lines == [{
        "japanese": "かっこいいから好きなんじゃない",
        "romaji": "ka kko ii ka ra suki nan ja na i",
        "translation": "我不是因為你很酷才喜歡你",
        "vocabulary": [],
        "grammar": "",
    }]


def test_lyrics_translation_endpoint_validates_and_returns_line_notes(monkeypatch):
    monkeypatch.setattr("app.explain_lyrics", lambda text: ([{"japanese":"君が好き","translation":"我喜歡你","vocabulary":["好き（すき）：喜歡"],"grammar":"が標示主語"}], "ai"))
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.post("/api/japanese/lyrics", data={"lyrics":"君が好き"})
        assert response.status_code == 200
        assert response.json["lines"][0]["translation"] == "我喜歡你"
        assert client.post("/api/japanese/lyrics", data={"lyrics":""}).status_code == 400
        assert client.post("/api/japanese/lyrics", data={"lyrics":"a" * 5001}).status_code == 413


def test_japanese_page_includes_lyrics_study_form():
    app.config["TESTING"] = True
    with app.test_client() as client:
        html = client.get("/japanese").data.decode("utf-8")
    assert "貼上歌詞" in html
    assert "data-lyrics-form" in html
    assert "data-lyrics-results" in html


def test_lyrics_results_render_optional_romaji_line():
    javascript = (app.root_path + "/static/js/app.js")
    with open(javascript, encoding="utf-8") as source:
        content = source.read()
    assert "lyrics-romaji" in content
    assert "if(romaji)" in content
    with open(app.root_path + "/static/css/style.css", encoding="utf-8") as source:
        assert ".lyrics-romaji" in source.read()
