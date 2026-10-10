import json, os, random, string, uuid
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, text
from battle_engine import next_review_time
from word_data import ACHIEVEMENTS, CHAPTERS

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_URL = f"sqlite:///{(BASE_DIR / 'database' / 'wordquest.local.db').as_posix()}"
_initialized_sqlite_urls = set()
APP_TZ = ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Taipei"))

def app_today(): return datetime.now(APP_TZ).date()

def get_database_url():
    url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    if url.startswith("postgres://"): return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"): return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

@lru_cache(maxsize=4)
def _build_engine(url):
    if url.startswith("sqlite:///"):
        p = Path(url.replace("sqlite:///", "", 1)); p = p if p.is_absolute() else BASE_DIR / p; p.parent.mkdir(parents=True, exist_ok=True); url=f"sqlite:///{p.as_posix()}"
    return create_engine(url, pool_pre_ping=True, future=True)

def get_engine(): return _build_engine(get_database_url())

def _initialize_sqlite(engine):
    url=str(engine.url)
    if engine.dialect.name != "sqlite" or url in _initialized_sqlite_urls: return
    schema=(BASE_DIR/"database"/"schema_sqlite.sql").read_text(encoding="utf-8")
    with engine.begin() as c:
        for stmt in [x.strip() for x in schema.split(";") if x.strip()]: c.execute(text(stmt))
        # forward-compatible columns for older local db
        cols={r[1] for r in c.execute(text("PRAGMA table_info(users_profile)")).all()}
        for name, ddl in {"auth_user_id":"TEXT","streak_freezes":"INTEGER DEFAULT 0","unlocked_chapter":"INTEGER DEFAULT 1","equipped_gear":"TEXT DEFAULT ''","created_at":"TEXT"}.items():
            if name not in cols: c.execute(text(f"ALTER TABLE users_profile ADD COLUMN {name} {ddl}"))
        c.execute(text("UPDATE users_profile SET created_at=CURRENT_TIMESTAMP WHERE created_at IS NULL"))
    _initialized_sqlite_urls.add(url)

@contextmanager
def db_connection():
    e=get_engine(); _initialize_sqlite(e)
    with e.begin() as c: yield c

def ensure_guest_profile(user_id=None, username="勇者"):
    user_id=user_id or str(uuid.uuid4())
    with db_connection() as c:
        r=c.execute(text("SELECT * FROM users_profile WHERE id=:id"),{"id":user_id}).mappings().first()
        if r: return dict(r)
        c.execute(text("INSERT INTO users_profile(id,username,level,exp,hp,coins,current_streak,last_login) VALUES(:id,:u,1,0,100,0,1,:today)"),{"id":user_id,"u":username,"today":app_today().isoformat()})
    return fetch_profile(user_id)



def ensure_auth_profile(auth_user_id, username="勇者", guest_user_id=None):
    """Return the profile linked to a Supabase Auth user, preserving a guest profile when possible."""
    with db_connection() as c:
        existing=c.execute(text("SELECT * FROM users_profile WHERE auth_user_id=:a"),{"a":auth_user_id}).mappings().first()
        if existing: return dict(existing)
        if guest_user_id:
            guest=c.execute(text("SELECT * FROM users_profile WHERE id=:id"),{"id":guest_user_id}).mappings().first()
            if guest and not guest.get("auth_user_id"):
                c.execute(text("UPDATE users_profile SET auth_user_id=:a, username=:u WHERE id=:id"),{"a":auth_user_id,"u":username or guest.get("username") or "勇者","id":guest_user_id})
                return dict(c.execute(text("SELECT * FROM users_profile WHERE id=:id"),{"id":guest_user_id}).mappings().first())
        new_id=str(uuid.uuid4())
        c.execute(text("INSERT INTO users_profile(id,auth_user_id,username,level,exp,hp,coins,current_streak,last_login) VALUES(:id,:a,:u,1,0,100,0,1,:today)"),{"id":new_id,"a":auth_user_id,"u":username or "勇者","today":app_today().isoformat()})
    return fetch_profile(new_id)

def update_username(user_id, username):
    username=(username or "").strip()[:24]
    if not username: return False
    with db_connection() as c:
        c.execute(text("UPDATE users_profile SET username=:n WHERE id=:u"),{"n":username,"u":user_id})
    return True

def touch_login(user_id):
    """Update login streak. One missed day can consume a streak freeze."""
    with db_connection() as c:
        row=c.execute(text("SELECT current_streak,streak_freezes,last_login FROM users_profile WHERE id=:u"),{"u":user_id}).mappings().first()
        if not row: return
        raw=row["last_login"]
        if isinstance(raw,str):
            try: last=date.fromisoformat(raw[:10])
            except ValueError: last=app_today()
        else: last=raw or app_today()
        today=app_today(); gap=(today-last).days
        streak=int(row["current_streak"] or 1); freezes=int(row["streak_freezes"] or 0)
        if gap<=0: return
        if gap==1: streak+=1
        elif gap==2 and freezes>0: freezes-=1; streak+=1
        else: streak=1
        if streak>1 and streak%7==0: freezes+=1
        c.execute(text("UPDATE users_profile SET current_streak=:s,streak_freezes=:f,last_login=:today WHERE id=:u"),{"s":streak,"f":freezes,"today":today.isoformat(),"u":user_id})

def fetch_profile(user_id):
    with db_connection() as c:
        r=c.execute(text("SELECT * FROM users_profile WHERE id=:id"),{"id":user_id}).mappings().first(); return dict(r) if r else None

def apply_battle_result(user_id, word, correct, exp, coins, hp_delta=0, question=None, selected="", response_ms=0, speech_score=None):
    with db_connection() as c:
        c.execute(text("UPDATE users_profile SET exp=exp+:e, coins=coins+:co, hp=CASE WHEN hp+:hp < 0 THEN 0 WHEN hp+:hp > 100 THEN 100 ELSE hp+:hp END, level=1+((exp+:e)/100) WHERE id=:u"),{"u":user_id,"e":exp,"co":coins,"hp":hp_delta})
        was_review=False
        if word:
            row=c.execute(text("SELECT proficiency_level,mistake_count FROM user_vocabulary WHERE user_id=:u AND word=:w"),{"u":user_id,"w":word}).mappings().first()
            was_review=bool(row and int(row.get("mistake_count",0) or 0)>0); old=int(row["proficiency_level"]) if row else 0; new=min(5, old+1) if correct else max(0, old-1); due=next_review_time(new if correct else 0).isoformat()
            c.execute(text("""INSERT INTO user_vocabulary(user_id,word,proficiency_level,next_review_time,mistake_count,correct_count,last_seen_at)
            VALUES(:u,:w,:p,:due,:m,:ok,CURRENT_TIMESTAMP) ON CONFLICT(user_id,word) DO UPDATE SET proficiency_level=:p,next_review_time=:due,mistake_count=user_vocabulary.mistake_count+:m,correct_count=user_vocabulary.correct_count+:ok,last_seen_at=CURRENT_TIMESTAMP"""),{"u":user_id,"w":word,"p":new,"due":due,"m":0 if correct else 1,"ok":1 if correct else 0})
        if question:
            c.execute(text("""INSERT INTO answer_history(user_id,chapter_id,stage_id,difficulty,mode,prompt,selected_answer,correct_answer,is_correct,response_ms,speech_score)
            VALUES(:u,:ch,:st,:d,:mo,:p,:s,:a,:ok,:ms,:ss)"""),{"u":user_id,"ch":question.get("chapter_id"),"st":question.get("stage_id"),"d":question.get("difficulty"),"mo":question.get("mode"),"p":question.get("prompt"),"s":selected,"a":question.get("answer"),"ok":bool(correct),"ms":response_ms,"ss":speech_score})
            st=question.get("stage_id")
            if st:
                limit_ms=max(1000,int(question.get("time_limit",12))*1000)
                stars=(3 if response_ms and response_ms<=limit_ms*0.4 else 2 if response_ms and response_ms<=limit_ms*0.75 else 1) if correct else 0
                score=max(40,100-min(int(response_ms/max(limit_ms/35,1)),35)) if correct else 0
                c.execute(text("""INSERT INTO stage_progress(user_id,stage_id,stars,best_score,completed,attempts) VALUES(:u,:s,:stars,:score,:done,1)
                ON CONFLICT(user_id,stage_id) DO UPDATE SET stars=CASE WHEN stage_progress.stars>:stars THEN stage_progress.stars ELSE :stars END,best_score=CASE WHEN stage_progress.best_score>:score THEN stage_progress.best_score ELSE :score END,completed=(stage_progress.completed OR :done),attempts=stage_progress.attempts+1,updated_at=CURRENT_TIMESTAMP"""),{"u":user_id,"s":st,"stars":stars,"score":score,"done":bool(correct)})
                if correct and int(st)%100==len(next((c["stages"] for c in CHAPTERS if c["id"]==int(st)//100), [])):
                    next_ch=min(len(CHAPTERS),int(st)//100+1)
                    c.execute(text("UPDATE users_profile SET unlocked_chapter=CASE WHEN unlocked_chapter>:n THEN unlocked_chapter ELSE :n END WHERE id=:u"),{"n":next_ch,"u":user_id})
        metric="review_attempts" if question and question.get("is_review") else "speech_attempts" if question and question.get("mode")=="speech" else "correct_answers" if correct else None
        if metric:
            c.execute(text(f"""INSERT INTO daily_progress(user_id,progress_date,{metric}) VALUES(:u,:today,1)
            ON CONFLICT(user_id,progress_date) DO UPDATE SET {metric}=daily_progress.{metric}+1"""),{"u":user_id,"today":app_today().isoformat()})

    # Achievement checks are idempotent; rewards are granted only on first unlock.
    return refresh_achievements(user_id)


def fetch_vocabulary(user_id):
    with db_connection() as c:
        rows=c.execute(text("SELECT word,proficiency_level,next_review_time,mistake_count,correct_count,last_seen_at FROM user_vocabulary WHERE user_id=:u ORDER BY last_seen_at DESC"),{"u":user_id}).mappings().all(); return [dict(x) for x in rows]

def fetch_stage_progress(user_id):
    with db_connection() as c:
        return {int(r["stage_id"]):dict(r) for r in c.execute(text("SELECT * FROM stage_progress WHERE user_id=:u"),{"u":user_id}).mappings().all()}

def fetch_daily(user_id):
    with db_connection() as c:
        r=c.execute(text("SELECT * FROM daily_progress WHERE user_id=:u AND progress_date=:today"),{"u":user_id,"today":app_today().isoformat()}).mappings().first()
        return dict(r) if r else {"correct_answers":0,"speech_attempts":0,"review_attempts":0,"claimed_json":"[]"}

def fetch_items(user_id):
    with db_connection() as c:
        return [dict(x) for x in c.execute(text("SELECT * FROM user_items WHERE user_id=:u"),{"u":user_id}).mappings().all()]

def buy_item(user_id,item_key,price):
    with db_connection() as c:
        coins=c.execute(text("SELECT coins FROM users_profile WHERE id=:u"),{"u":user_id}).scalar_one()
        if coins < price: return False
        c.execute(text("UPDATE users_profile SET coins=coins-:p WHERE id=:u"),{"u":user_id,"p":price})
        c.execute(text("INSERT INTO user_items(user_id,item_key) VALUES(:u,:i) ON CONFLICT(user_id,item_key) DO UPDATE SET quantity=quantity+1"),{"u":user_id,"i":item_key}); return True

def has_item(user_id,item_key):
    """Return True only when the owned item is currently equipped."""
    with db_connection() as c:
        return bool(c.execute(text("SELECT 1 FROM user_items WHERE user_id=:u AND item_key=:i AND equipped=:yes"),{"u":user_id,"i":item_key,"yes":True}).first())

def create_challenge(user_id, chapter_id, stage_id=None):
    code=''.join(random.choices(string.ascii_uppercase+string.digits,k=6)); seed=random.randint(100000,999999999)
    with db_connection() as c: c.execute(text("INSERT INTO challenges(code,creator_user_id,chapter_id,stage_id,seed) VALUES(:c,:u,:ch,:s,:seed)"),{"c":code,"u":user_id,"ch":chapter_id,"s":stage_id,"seed":seed})
    return code

def fetch_challenge(code):
    with db_connection() as c:
        r=c.execute(text("SELECT * FROM challenges WHERE code=:c"),{"c":code.upper()}).mappings().first(); return dict(r) if r else None


def record_challenge_result(code,user_id,username,correct,elapsed_ms,combo=0):
    with db_connection() as c:
        c.execute(text("INSERT INTO challenge_results(code,user_id,username,correct_count,total_questions,elapsed_ms,max_combo) VALUES(:c,:u,:n,:ok,1,:ms,:combo)"),{"c":code,"u":user_id,"n":username,"ok":1 if correct else 0,"ms":elapsed_ms,"combo":combo if correct else 0})

def clear_challenge_results(code,user_id):
    with db_connection() as c:
        c.execute(text("DELETE FROM challenge_results WHERE code=:c AND user_id=:u"),{"c":code.upper(),"u":user_id})

def challenge_leaderboard(code):
    with db_connection() as c:
        rows=c.execute(text("SELECT username,SUM(correct_count) correct_count,SUM(total_questions) total_questions,SUM(elapsed_ms) elapsed_ms,MAX(max_combo) max_combo FROM challenge_results WHERE code=:c GROUP BY username ORDER BY correct_count DESC,elapsed_ms ASC"),{"c":code.upper()}).mappings().all()
        return [dict(x) for x in rows]

def _decode_claimed(value):
    if isinstance(value, list): return value
    if value is None: return []
    try: return json.loads(value)
    except (TypeError, json.JSONDecodeError): return []


def claim_daily_mission(user_id, mission):
    """Claim a completed daily mission once. Returns (ok, message)."""
    metric=mission["metric"]; key=mission["key"]; target=int(mission["target"]); reward=int(mission["reward"])
    allowed={"correct_answers","speech_attempts","review_attempts"}
    if metric not in allowed: return False,"任務設定錯誤。"
    with db_connection() as c:
        today=app_today().isoformat()
        row=c.execute(text("SELECT * FROM daily_progress WHERE user_id=:u AND progress_date=:today"),{"u":user_id,"today":today}).mappings().first()
        if not row or int(row.get(metric,0) or 0)<target: return False,"任務還沒完成。"
        claimed=_decode_claimed(row.get("claimed_json"))
        if key in claimed: return False,"今天已經領過這個獎勵。"
        claimed.append(key)
        payload=json.dumps(claimed,ensure_ascii=False)
        if c.dialect.name=="postgresql":
            c.execute(text("UPDATE daily_progress SET claimed_json=CAST(:j AS jsonb) WHERE user_id=:u AND progress_date=:today"),{"j":payload,"u":user_id,"today":today})
        else:
            c.execute(text("UPDATE daily_progress SET claimed_json=:j WHERE user_id=:u AND progress_date=:today"),{"j":payload,"u":user_id,"today":today})
        c.execute(text("UPDATE users_profile SET coins=coins+:r WHERE id=:u"),{"r":reward,"u":user_id})
    return True,f"任務完成！獲得 {reward} 金幣。"


def fetch_due_vocabulary(user_id, limit=20):
    # Filter in Python so SQLite ISO timestamps with a T/+00:00 compare correctly,
    # while PostgreSQL timestamptz values continue to work unchanged.
    now=datetime.now(timezone.utc)
    with db_connection() as c:
        rows=c.execute(text("""SELECT word,proficiency_level,next_review_time,mistake_count,correct_count,last_seen_at
            FROM user_vocabulary WHERE user_id=:u AND mistake_count>0
            ORDER BY next_review_time ASC"""),{"u":user_id}).mappings().all()
    due=[]
    for raw in rows:
        item=dict(raw); value=item.get("next_review_time")
        if isinstance(value,str):
            try: value=datetime.fromisoformat(value.replace("Z","+00:00"))
            except ValueError: value=now
        if isinstance(value,datetime) and value.tzinfo is None: value=value.replace(tzinfo=timezone.utc)
        if not value or value<=now: due.append(item)
        if len(due)>=limit: break
    return due


def equip_item(user_id,item_key):
    with db_connection() as c:
        owned=c.execute(text("SELECT 1 FROM user_items WHERE user_id=:u AND item_key=:i"),{"u":user_id,"i":item_key}).first()
        if not owned: return False
        c.execute(text("UPDATE user_items SET equipped=0 WHERE user_id=:u"),{"u":user_id})
        c.execute(text("UPDATE user_items SET equipped=1 WHERE user_id=:u AND item_key=:i"),{"u":user_id,"i":item_key})
        c.execute(text("UPDATE users_profile SET equipped_gear=:i WHERE id=:u"),{"u":user_id,"i":item_key})
        return True


def unequip_item(user_id):
    with db_connection() as c:
        c.execute(text("UPDATE user_items SET equipped=0 WHERE user_id=:u"),{"u":user_id})
        c.execute(text("UPDATE users_profile SET equipped_gear='' WHERE id=:u"),{"u":user_id})



def fetch_achievements(user_id):
    with db_connection() as c:
        rows=c.execute(text("SELECT achievement_key,earned_at FROM user_achievements WHERE user_id=:u ORDER BY earned_at DESC"),{"u":user_id}).mappings().all()
        return [dict(x) for x in rows]


def achievement_metrics(user_id):
    with db_connection() as c:
        completed=int(c.execute(text("SELECT COUNT(*) FROM stage_progress WHERE user_id=:u AND completed=:yes"),{"u":user_id,"yes":True}).scalar() or 0)
        stars=int(c.execute(text("SELECT COALESCE(SUM(stars),0) FROM stage_progress WHERE user_id=:u"),{"u":user_id}).scalar() or 0)
        chapter1=int(c.execute(text("SELECT COUNT(*) FROM stage_progress WHERE user_id=:u AND completed=:yes AND stage_id BETWEEN 101 AND 107"),{"u":user_id,"yes":True}).scalar() or 0)
        tamed=int(c.execute(text("SELECT COUNT(*) FROM user_vocabulary WHERE user_id=:u AND proficiency_level>=5"),{"u":user_id}).scalar() or 0)
    return {"completed_stages":completed,"total_stars":stars,"chapter1_completed":chapter1,"tamed_words":tamed}


def refresh_achievements(user_id):
    metrics=achievement_metrics(user_id); newly=[]
    with db_connection() as c:
        earned={r[0] for r in c.execute(text("SELECT achievement_key FROM user_achievements WHERE user_id=:u"),{"u":user_id}).all()}
        for a in ACHIEVEMENTS:
            if a["key"] in earned or int(metrics.get(a["metric"],0)) < int(a["target"]):
                continue
            c.execute(text("INSERT INTO user_achievements(user_id,achievement_key) VALUES(:u,:k) ON CONFLICT(user_id,achievement_key) DO NOTHING"),{"u":user_id,"k":a["key"]})
            c.execute(text("UPDATE users_profile SET coins=coins+:r WHERE id=:u"),{"r":int(a.get("reward",0)),"u":user_id})
            newly.append(a)
    return newly

def fetch_recent_mistakes(user_id, limit=10):
    with db_connection() as c:
        rows=c.execute(text("""SELECT prompt,selected_answer,correct_answer,difficulty,mode,created_at
            FROM answer_history WHERE user_id=:u AND is_correct=:wrong
            ORDER BY created_at DESC LIMIT :lim"""),{"u":user_id,"wrong":False,"lim":limit}).mappings().all()
        return [dict(x) for x in rows]
