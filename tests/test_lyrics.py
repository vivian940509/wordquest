from app import app


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
