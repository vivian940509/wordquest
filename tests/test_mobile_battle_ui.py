from pathlib import Path

from app import app


def test_battle_template_keeps_four_choices_compact_on_mobile():
    css = Path("static/css/style.css").read_text(encoding="utf-8")
    js = Path("static/js/app.js").read_text(encoding="utf-8")
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in css
    assert ".monster-stage {\n        min-height: 128px" in css
    assert "['pointerup','touchend','click']" not in js
    assert "form.addEventListener('click',handleAnswerPress)" in js


def test_battle_page_still_renders_four_answer_buttons():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/battle?chapter=1&stage=1&difficulty=beginner")
    assert response.status_code == 200
    assert response.data.decode().count('class="word-card"') == 4
