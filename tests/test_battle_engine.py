from datetime import datetime, timezone

from battle_engine import build_battle, build_speech_challenge, build_vocab_question, grade_answer, next_review_time
from word_data import STARTER_WORDS


def test_vocab_question_uses_two_options_after_mistakes():
    question = build_vocab_question(seed=1, weak_mode=True)
    assert len(question["options"]) == 2
    assert question["answer"] in question["options"]


def test_vocab_question_explains_options_for_beginners():
    question = build_vocab_question(seed=1)
    assert question["instruction"] == "選出符合情境的英文"
    assert question["option_details"][question["answer"]]


def test_stage_question_excludes_words_already_seen_in_level():
    seen = {"starving", "exhausted", "furious", "delighted", "confident", "nervous", "family", "friend", "school"}
    answers = {
        build_vocab_question(seed=seed, chapter_id=1, stage_id=101, excluded_words=seen)["answer"]
        for seed in range(20)
    }
    assert answers == {"teacher"}


def test_intermediate_battle_keeps_speech_out_of_regular_rounds():
    modes = {build_battle(seed=seed, difficulty="intermediate")["mode"] for seed in range(30)}
    assert modes == {"shield"}


def test_speech_challenge_includes_cloze_hint_with_chinese_and_prefix():
    question = build_speech_challenge(seed=1)
    assert question["mode"] == "speech"
    assert question["answer_zh"]
    assert question["speech_cloze"]
    assert question["speech_prefix"] == question["word"][:2]
    assert question["speech_prefix"] in question["speech_cloze"]


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
