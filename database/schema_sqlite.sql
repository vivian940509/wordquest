CREATE TABLE IF NOT EXISTS users_profile (
    id TEXT PRIMARY KEY, username TEXT NOT NULL, level INTEGER DEFAULT 1, exp INTEGER DEFAULT 0,
    hp INTEGER DEFAULT 100, coins INTEGER DEFAULT 0, current_streak INTEGER DEFAULT 1,
    streak_freezes INTEGER DEFAULT 0, last_login TEXT DEFAULT CURRENT_DATE, unlocked_chapter INTEGER DEFAULT 1,
    equipped_gear TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS user_vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, word TEXT NOT NULL,
    proficiency_level INTEGER DEFAULT 0, next_review_time TEXT DEFAULT CURRENT_TIMESTAMP,
    mistake_count INTEGER DEFAULT 0, correct_count INTEGER DEFAULT 0, last_seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, word)
);
CREATE TABLE IF NOT EXISTS answer_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, chapter_id INTEGER, stage_id INTEGER,
    difficulty TEXT, mode TEXT, prompt TEXT, selected_answer TEXT, correct_answer TEXT, is_correct INTEGER,
    response_ms INTEGER DEFAULT 0, speech_score INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS stage_progress (
    user_id TEXT NOT NULL, stage_id INTEGER NOT NULL, stars INTEGER DEFAULT 0, best_score INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0, attempts INTEGER DEFAULT 0, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, stage_id)
);
CREATE TABLE IF NOT EXISTS daily_progress (
    user_id TEXT NOT NULL, progress_date TEXT NOT NULL, correct_answers INTEGER DEFAULT 0,
    speech_attempts INTEGER DEFAULT 0, review_attempts INTEGER DEFAULT 0, claimed_json TEXT DEFAULT '[]',
    PRIMARY KEY(user_id, progress_date)
);
CREATE TABLE IF NOT EXISTS user_items (
    user_id TEXT NOT NULL, item_key TEXT NOT NULL, quantity INTEGER DEFAULT 1, equipped INTEGER DEFAULT 0,
    acquired_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id, item_key)
);
CREATE TABLE IF NOT EXISTS challenges (
    code TEXT PRIMARY KEY, creator_user_id TEXT NOT NULL, chapter_id INTEGER NOT NULL, stage_id INTEGER,
    seed INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, expires_at TEXT
);
CREATE TABLE IF NOT EXISTS challenge_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT NOT NULL, user_id TEXT NOT NULL, username TEXT NOT NULL,
    correct_count INTEGER DEFAULT 0, total_questions INTEGER DEFAULT 0, elapsed_ms INTEGER DEFAULT 0,
    max_combo INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS battle_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, dungeon_title TEXT NOT NULL,
    score INTEGER DEFAULT 0, exp_gained INTEGER DEFAULT 0, coins_gained INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS user_achievements (
    user_id TEXT NOT NULL, achievement_key TEXT NOT NULL, earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, achievement_key)
);
