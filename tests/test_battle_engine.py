from datetime import datetime, timezone

from battle_engine import build_battle, build_vocab_question, grade_answer, next_review_time
from word_data import STARTER_WORDS


def test_vocab_question_uses_two_options_after_mistakes():
    question = build_vocab_question(seed=1, weak_mode=True)
    assert len(question["options"]) == 2
    assert question["answer"] in question["options"]


def test_vocab_question_explains_options_for_beginners():
    question = build_vocab_question(seed=1)
    assert question["instruction"] == "選出符合情境的英文"
    assert question["option_details"][question["answer"]]


def test_grade_answer_rewards_correct_choice():
    question = build_battle(seed=1, mistake_streak=0)
    result = grade_answer(question, question["answer"])
    assert result["correct"] is True
    assert result["exp"] > 0
    assert result["damage"] > 0


def test_next_review_time_clamps_level():
    now = datetime(2026, 10, 8, tzinfo=timezone.utc)
    assert next_review_time(99, now=now).day == 7


def test_starter_words_have_study_card_fields():
    first_word = STARTER_WORDS[0]
    assert first_word["word"]
    assert first_word["zh"]
    assert first_word["context"]
    assert first_word["example"]
