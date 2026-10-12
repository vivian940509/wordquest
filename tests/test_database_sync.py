import database


def use_temp_database(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'wordquest.test.db'}")
    database._build_engine.cache_clear()
    database._initialized_database_urls.clear()


def test_existing_auth_profile_merges_guest_progress_on_login(monkeypatch, tmp_path):
    use_temp_database(monkeypatch, tmp_path)

    guest = database.ensure_guest_profile(username="Computer")
    with database.db_connection() as conn:
        conn.execute(
            database.text(
                "INSERT INTO users_profile(id, auth_user_id, username, level, exp, hp, coins, current_streak, last_login) "
                "VALUES('auth-profile', 'auth-123', 'Phone', 1, 0, 100, 0, 1, '2026-10-12')"
            )
        )
        conn.execute(
            database.text(
                "INSERT INTO stage_progress(user_id, stage_id, stars, best_score, completed, attempts) "
                "VALUES(:u, 101, 3, 95, 1, 2)"
            ),
            {"u": guest["id"]},
        )
        conn.execute(
            database.text(
                "INSERT INTO user_vocabulary(user_id, word, proficiency_level, mistake_count, correct_count, weak_word) "
                "VALUES(:u, 'starving', 4, 1, 5, 0)"
            ),
            {"u": guest["id"]},
        )

    profile = database.ensure_auth_profile("auth-123", "Phone", guest["id"])

    assert profile["id"] == "auth-profile"
    assert database.fetch_stage_progress("auth-profile")[101]["completed"]
    assert database.fetch_stage_progress("auth-profile")[101]["stars"] == 3
    vocab = {row["word"]: row for row in database.fetch_vocabulary("auth-profile")}
    assert vocab["starving"]["proficiency_level"] == 4
    with database.db_connection() as conn:
        assert conn.execute(database.text("SELECT 1 FROM users_profile WHERE id=:id"), {"id": guest["id"]}).first() is None


def test_stage_completion_can_store_five_stars(monkeypatch, tmp_path):
    use_temp_database(monkeypatch, tmp_path)
    profile = database.ensure_guest_profile(username="Nova")

    database.record_stage_completion(profile["id"], 101, stars=5, score=100, completed=True)

    progress = database.fetch_stage_progress(profile["id"])
    assert progress[101]["stars"] == 5


def test_battle_result_can_skip_achievement_refresh(monkeypatch, tmp_path):
    use_temp_database(monkeypatch, tmp_path)
    profile = database.ensure_guest_profile(username="Nova")

    def forbidden_refresh(user_id):
        raise AssertionError("intermediate campaign answers should not run achievement aggregation")

    monkeypatch.setattr(database, "refresh_achievements", forbidden_refresh)

    result = database.apply_battle_result(
        profile["id"],
        "careful",
        True,
        exp=10,
        coins=3,
        question={"chapter_id": 1, "stage_id": 101, "difficulty": "beginner", "mode": "shield", "prompt": "p", "answer": "careful", "defer_stage_progress": True},
        selected="careful",
        check_achievements=False,
    )

    assert result == []
