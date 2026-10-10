import os, time, requests
from datetime import timedelta
from urllib.parse import quote
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for, flash
from battle_engine import build_battle, build_review_question, grade_answer, build_wrong_answer_analysis
from database import (apply_battle_result, record_stage_completion, fetch_learning_analytics, fetch_mistake_words, fetch_unmastered_words, ensure_guest_profile, ensure_auth_profile, update_username, fetch_profile, fetch_vocabulary, fetch_stage_progress,
                      fetch_daily, fetch_items, buy_item, has_item, create_challenge, fetch_challenge, touch_login, record_challenge_result, challenge_leaderboard,
                      claim_daily_mission, fetch_due_vocabulary, equip_item, unequip_item, fetch_recent_mistakes, clear_challenge_results, fetch_achievements, achievement_metrics)
from dictionary_api import lookup_word
from word_data import STARTER_WORDS, WORD_HINTS, CHAPTERS, DAILY_MISSIONS, SHOP_ITEMS, ACHIEVEMENTS
from ai_teacher import explain as teacher_explain
load_dotenv()
app=Flask(__name__); app.config["SECRET_KEY"]=os.getenv("SECRET_KEY","dev-wordquest"); app.permanent_session_lifetime=timedelta(days=30)

def supabase_auth_request(path, payload=None, access_token=None):
    base=os.getenv("SUPABASE_URL","").rstrip("/"); key=os.getenv("SUPABASE_ANON_KEY","")
    if not base or not key: return None, "尚未設定 SUPABASE_URL / SUPABASE_ANON_KEY"
    headers={"apikey":key,"Content-Type":"application/json"}
    if access_token: headers["Authorization"]=f"Bearer {access_token}"
    try:
        r=requests.post(f"{base}/auth/v1/{path}",json=payload or {},headers=headers,timeout=10)
        data=r.json() if r.content else {}
    except Exception:
        return None, "登入服務暫時無法連線"
    if not r.ok: return None, data.get("msg") or data.get("message") or data.get("error_description") or "帳號驗證失敗"
    return data, None

def supabase_auth_get_user(access_token):
    base=os.getenv("SUPABASE_URL","").rstrip("/"); key=os.getenv("SUPABASE_ANON_KEY","")
    if not base or not key: return None,"尚未設定 SUPABASE_URL / SUPABASE_ANON_KEY"
    try:
        r=requests.get(f"{base}/auth/v1/user",headers={"apikey":key,"Authorization":f"Bearer {access_token}"},timeout=10)
        data=r.json() if r.content else {}
    except Exception: return None,"登入服務暫時無法連線"
    if not r.ok: return None,data.get("msg") or data.get("message") or "無法取得帳號資料"
    return data,None

def supabase_auth_update_user(access_token,password):
    base=os.getenv("SUPABASE_URL","").rstrip("/"); key=os.getenv("SUPABASE_ANON_KEY","")
    if not base or not key: return None,"尚未設定 SUPABASE_URL / SUPABASE_ANON_KEY"
    try:
        r=requests.put(f"{base}/auth/v1/user",json={"password":password},headers={"apikey":key,"Authorization":f"Bearer {access_token}","Content-Type":"application/json"},timeout=10)
        data=r.json() if r.content else {}
    except Exception: return None,"登入服務暫時無法連線"
    if not r.ok: return None,data.get("msg") or data.get("message") or "密碼更新失敗"
    return data,None

def run_summary(results,total=5):
    attempts=len(results); correct=sum(1 for x in results if x.get("correct")); elapsed=sum(int(x.get("elapsed_ms",0) or 0) for x in results)
    avg=round(elapsed/max(attempts,1)/1000,1); exp=sum(int(x.get("exp",0) or 0) for x in results); coins=sum(int(x.get("coins",0) or 0) for x in results)
    accuracy=round(100*correct/max(attempts,1)) if attempts else 0
    stars=3 if total and correct>=total else 2 if total and correct>=max(total-1,1) else 1 if correct>=max(1,(total+1)//2) else 0
    wrong=[x for x in results if not x.get("correct")]
    counts={}
    for x in wrong:
        w=x.get("word") or x.get("answer") or ""
        if w: counts[w]=counts.get(w,0)+1
    weakest=max(counts,key=counts.get) if counts else None
    score=round((accuracy*0.8)+max(0,20-avg*2))
    return {"attempts":attempts,"correct":correct,"accuracy":accuracy,"avg_seconds":avg,"exp":exp,"coins":coins,"stars":stars,"wrong":wrong,"weakest":weakest,"score":score}

def question_time_limit(question):
    # Keep rounds fast and game-like. Speech gets a little extra time for mic startup.
    if question.get("mode")=="speech": return 8
    return {"beginner":8,"intermediate":6,"advanced":4}.get(question.get("difficulty"),6)

def current_user():
    if "user_id" not in session:
        p=ensure_guest_profile(username="見習勇者"); session["user_id"]=p["id"]
    p=ensure_guest_profile(session["user_id"],username="見習勇者"); touch_login(p["id"]); return fetch_profile(p["id"])

def enrich_dictionary(word,dictionary=None):
    if not word:return None
    dictionary=dictionary or {}; hint=WORD_HINTS.get(word,""); definition=dictionary.get("definition") or ""
    if "暫時無法連線字典 API" in definition or not definition: definition=hint or "先用遊戲內建情境練習。"
    return {"word":dictionary.get("word") or word,"phonetic":dictionary.get("phonetic") or "","audio":dictionary.get("audio") or "","definition":definition,"local_hint":hint}

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower(); password=request.form.get("password","")
        data,err=supabase_auth_request("token?grant_type=password",{"email":email,"password":password})
        if err: flash(err); return render_template("login.html")
        user=data.get("user") or {}; guest_id=session.get("user_id")
        profile=ensure_auth_profile(user.get("id"), (user.get("user_metadata") or {}).get("username") or email.split("@")[0], guest_id)
        session["user_id"]=profile["id"]; session["auth_email"]=email; session.permanent=True
        flash("登入成功，學習進度已同步。")
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        username=request.form.get("username","").strip(); email=request.form.get("email","").strip().lower(); password=request.form.get("password","")
        if len(password)<6: flash("密碼至少需要 6 個字元。") ; return render_template("register.html")
        data,err=supabase_auth_request("signup",{"email":email,"password":password,"data":{"username":username or "勇者"}})
        if err: flash(err); return render_template("register.html")
        user=data.get("user") or {}; profile=ensure_auth_profile(user.get("id"),username or email.split("@")[0],session.get("user_id"))
        session["user_id"]=profile["id"]
        session["auth_email"]=email; session.permanent=True; flash("註冊完成，原本的訪客進度已保留。")
        return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/forgot-password",methods=["GET","POST"])
def forgot_password():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower()
        redirect_to=url_for("reset_password",_external=True)
        _,err=supabase_auth_request(f"recover?redirect_to={quote(redirect_to,safe=':/')}",{"email":email})
        flash(err or "重設密碼連結已寄出，請到信箱查看。")
        if not err: return redirect(url_for("login"))
    return render_template("forgot_password.html")

@app.route("/reset-password",methods=["GET","POST"])
def reset_password():
    if request.method=="POST":
        token=request.form.get("access_token",""); password=request.form.get("password","")
        if len(password)<6: flash("密碼至少需要 6 個字元。")
        elif not token: flash("重設連結已失效，請重新申請。")
        else:
            _,err=supabase_auth_update_user(token,password); flash(err or "密碼已更新，請重新登入。")
            if not err: return redirect(url_for("login"))
    return render_template("reset_password.html")

@app.get("/login/google")
def login_google():
    base=os.getenv("SUPABASE_URL","").rstrip("/")
    if not base: flash("尚未設定 Supabase，無法使用 Google 登入。"); return redirect(url_for("login"))
    callback=url_for("google_callback",_external=True)
    return redirect(f"{base}/auth/v1/authorize?provider=google&redirect_to={quote(callback,safe=':/')}")

@app.get("/auth/google/callback")
def google_callback(): return render_template("auth_callback.html")

@app.post("/auth/google/complete")
def google_complete():
    token=(request.get_json(silent=True) or {}).get("access_token","")
    user,err=supabase_auth_get_user(token)
    if err: return jsonify({"ok":False,"error":err}),400
    email=user.get("email",""); profile=ensure_auth_profile(user.get("id"),(user.get("user_metadata") or {}).get("full_name") or email.split("@")[0] or "勇者",session.get("user_id"))
    session["user_id"]=profile["id"]; session["auth_email"]=email; session.permanent=True
    return jsonify({"ok":True,"redirect":url_for("index")})

@app.post("/logout")
def logout():
    session.clear(); flash("已登出。")
    return redirect(url_for("index"))

@app.get("/account")
def account():
    p=current_user(); vocab=fetch_vocabulary(p["id"]); progress=fetch_stage_progress(p["id"]); mistakes=fetch_recent_mistakes(p["id"],5)
    stats={"words":len(vocab),"completed":sum(1 for x in progress.values() if x.get("completed")),"stars":sum(int(x.get("stars",0) or 0) for x in progress.values()),"mistakes":len(mistakes),"due":len(fetch_due_vocabulary(p["id"]))}
    analytics=fetch_learning_analytics(p["id"])
    return render_template("account.html",profile=p,stats=stats,analytics=analytics,auth_email=session.get("auth_email"))

@app.post("/account/username")
def account_username():
    if not session.get("auth_email"): flash("請先登入再修改名稱。") ; return redirect(url_for("login"))
    flash("名稱已更新。" if update_username(current_user()["id"],request.form.get("username")) else "名稱不可為空。")
    return redirect(url_for("account"))

@app.get("/")
def index():
    p=current_user(); daily=fetch_daily(p["id"]); claimed=daily.get("claimed_json",[])
    if isinstance(claimed,str):
        import json
        try: claimed=json.loads(claimed)
        except Exception: claimed=[]
    return render_template("index.html",profile=p,daily=daily,missions=DAILY_MISSIONS,claimed=set(claimed),due_count=len(fetch_due_vocabulary(p["id"])))
@app.get("/study")
def study(): return render_template("study.html",profile=current_user(),words=STARTER_WORDS)

def stage_words(chapter, stage=None):
    words=[w for w in STARTER_WORDS if int(w.get("chapter",0))==int(chapter)]
    if not words:
        return []
    chapter_data=next((c for c in CHAPTERS if c["id"]==int(chapter)),None)
    stage_ids=[s["id"] for s in chapter_data["stages"]] if chapter_data else []
    stage_index=stage_ids.index(stage) if stage in stage_ids else 0
    return [words[(stage_index+i)%len(words)] for i in range(min(5,len(words)))]

@app.get("/map")
def map_page():
    p=current_user(); progress=fetch_stage_progress(p["id"]); earned_rows=fetch_achievements(p["id"]); earned={x["achievement_key"] for x in earned_rows}
    chapter_stats={}
    total_stages=sum(len(chapter["stages"]) for chapter in CHAPTERS)
    max_stars=total_stages*3
    for chapter in CHAPTERS:
        ids=[s["id"] for s in chapter["stages"]]
        done=sum(1 for sid in ids if progress.get(sid,{}).get("completed"))
        stars=sum(int(progress.get(sid,{}).get("stars",0) or 0) for sid in ids)
        chapter_stats[chapter["id"]]={"done":done,"total":len(ids),"stars":stars,"max_stars":len(ids)*3,"percent":round(100*done/max(len(ids),1))}
    metrics=achievement_metrics(p["id"]); metrics.update({"total_stages":total_stages,"max_stars":max_stars})
    return render_template("map.html",profile=p,chapters=CHAPTERS,progress=progress,chapter_stats=chapter_stats,achievements=ACHIEVEMENTS,earned=earned,metrics=metrics)
@app.get("/lesson")
def lesson():
    p=current_user(); difficulty=request.args.get("difficulty","beginner"); chapter=int(request.args.get("chapter",1)); stage=request.args.get("stage",type=int)
    chapter_data=next((c for c in CHAPTERS if c["id"]==chapter),None)
    stage_data=next((s for s in chapter_data["stages"] if s["id"]==stage),None) if chapter_data and stage else None
    if not chapter_data:
        flash("找不到這個章節。"); return redirect(url_for("map_page"))
    return render_template("lesson.html",profile=p,chapter=chapter_data,stage=stage_data,stage_id=stage,difficulty=difficulty,words=stage_words(chapter,stage))
@app.get("/battle")
def battle():
    p=current_user(); difficulty=request.args.get("difficulty","beginner"); chapter=int(request.args.get("chapter",1)); stage=request.args.get("stage",type=int)
    if chapter>int(p.get("unlocked_chapter",1) or 1): flash("先完成前一章才能解鎖這裡。"); return redirect(url_for("map_page"))
    challenge_code=request.args.get("challenge","").upper(); challenge=fetch_challenge(challenge_code) if challenge_code else None
    if stage and not challenge:
        chapter_data=next((c for c in CHAPTERS if c["id"]==chapter),None); ids=[x["id"] for x in chapter_data["stages"]] if chapter_data else []
        if stage in ids and ids.index(stage)>0:
            prev=ids[ids.index(stage)-1]; prog=fetch_stage_progress(p["id"])
            if not (prog.get(prev) and prog[prev].get("completed")):
                flash("先完成上一關才能挑戰這一關。"); return redirect(url_for("map_page"))
    if challenge:
        round_no=max(1,min(5,request.args.get("round",1,type=int))); seed=int(challenge["seed"])+round_no*9973
    elif stage:
        run=session.get("campaign_run")
        if request.args.get("restart")=="1" or not run or run.get("stage_id")!=stage or run.get("difficulty")!=difficulty:
            run={"stage_id":stage,"chapter_id":chapter,"difficulty":difficulty,"results":[],"seed":int(time.time()*1000)}; session["campaign_run"]=run
        round_no=len(run.get("results",[]))+1
        if round_no>5: return redirect(url_for("level_summary"))
        seed=int(run.get("seed",int(time.time())))+round_no*9973
    else:
        round_no=1; seed=int(time.time())
    q=build_battle(seed=seed,mistake_streak=int(session.get("mistake_streak",0)),difficulty=difficulty,chapter_id=chapter,stage_id=stage)
    q["challenge_code"]=challenge_code if challenge else ""; q["challenge_round"]=round_no if challenge else 0
    if stage and not challenge:
        q.update({"campaign_round":round_no,"campaign_total":5,"campaign_mode":True,"defer_stage_progress":True})
    q["time_limit"]=question_time_limit(q); session["question"]=q; session["question_started_ms"]=int(time.time()*1000)
    return render_template("battle.html",profile=p,question=q)
@app.post("/answer")
def answer():
    p=current_user(); q=session.pop("question",None)
    if not q:return redirect(url_for("map_page"))
    selected=request.form.get("selected",""); speech_score=request.form.get("speech_score",type=int); protect=4 if has_item(p["id"],"memory_amulet") else 0
    speech_score=min(100,(speech_score or 0)+10) if q["mode"]=="speech" and has_item(p["id"],"pronunciation_wand") else speech_score
    result=grade_answer(q,selected,speech_score=speech_score,hp_protection=protect); session["mistake_streak"]=0 if result["correct"] else int(session.get("mistake_streak",0))+1
    word=q["answer"].split()[0] if q["mode"] in {"shield","speech","review"} else q.get("answer","")
    elapsed=max(0,int(time.time()*1000)-int(session.get("question_started_ms",int(time.time()*1000))))
    newly=apply_battle_result(p["id"],word,result["correct"],result["exp"],result["coins"],result["hp_delta"],q,selected,elapsed,result.get("speech_score"))
    for a in newly or []: flash(f"成就解鎖：{a['icon']} {a['title']}，獲得 {a['reward']} 金幣！")
    if q.get("challenge_code"):
        combo=int(session.get("challenge_combo",0)); combo=combo+1 if result["correct"] else 0; session["challenge_combo"]=combo
        record_challenge_result(q["challenge_code"],p["id"],p["username"],result["correct"],elapsed,combo=combo)
    analysis=build_wrong_answer_analysis(q,selected); dictionary=enrich_dictionary(word,lookup_word(word) if word else None)
    item={"correct":bool(result["correct"]),"elapsed_ms":elapsed,"exp":result["exp"],"coins":result["coins"],"word":word,"answer":q.get("answer"),"selected":selected,"prompt":q.get("prompt")}
    if q.get("campaign_mode"):
        run=session.get("campaign_run") or {"results":[]}; run.setdefault("results",[]).append(item); session["campaign_run"]=run
        if len(run["results"])>=5:
            summary=run_summary(run["results"],5); summary.update({"stage_id":run.get("stage_id"),"chapter_id":run.get("chapter_id"),"difficulty":run.get("difficulty")})
            achievements=record_stage_completion(p["id"],run.get("stage_id"),summary["stars"],summary["score"],completed=summary["correct"]>=3)
            for a in achievements or []: flash(f"成就解鎖：{a['icon']} {a['title']}，獲得 {a['reward']} 金幣！")
            session["level_summary"]=summary; session.pop("campaign_run",None); session.pop("last_result",None)
            return redirect(url_for("level_summary"))
    if q.get("practice_mode"):
        run=session.get("practice_run") or {"results":[]}; run.setdefault("results",[]).append(item); session["practice_run"]=run
        limit=run.get("limit")
        if limit and len(run["results"])>=int(limit):
            session["practice_summary"]=run_summary(run["results"],int(limit)); session.pop("practice_run",None)
            return redirect(url_for("practice_summary"))
    session["last_result"]={"question":q,"selected":selected,"result":result,"dictionary":dictionary,"analysis":analysis}
    return redirect(url_for("result"))

@app.get("/result")
def result():
    p=current_user(); x=session.get("last_result")
    if not x:return redirect(url_for("map_page"))
    return render_template("result.html",profile=fetch_profile(p["id"]),**x)
@app.get("/level-summary")
def level_summary():
    summary=session.get("level_summary")
    if not summary: return redirect(url_for("map_page"))
    return render_template("level_summary.html",profile=current_user(),summary=summary)

@app.get("/practice")
def practice():
    p=current_user(); return render_template("practice.html",profile=p,chapters=CHAPTERS,weak_count=len(fetch_mistake_words(p["id"],weak_only=True)))

@app.post("/practice/start")
def practice_start():
    p=current_user(); mode=request.form.get("mode","quick10"); difficulty=request.form.get("difficulty","intermediate"); chapter=request.form.get("chapter",type=int) or 1
    limit={"quick10":10,"challenge30":30}.get(mode)
    words=[]
    if mode in {"wrong","weak"}: words=[x["word"] for x in fetch_mistake_words(p["id"],sort="count",weak_only=(mode=="weak"))]
    elif mode=="unmastered":
        mastered={x["word"] for x in fetch_vocabulary(p["id"]) if int(x.get("proficiency_level",0) or 0)>=5}; words=[x["word"] for x in STARTER_WORDS if x["word"] not in mastered]
    elif mode=="chapter": words=[x["word"] for x in STARTER_WORDS if int(x.get("chapter",0))==chapter]
    if mode in {"wrong","weak","unmastered","chapter"} and not words:
        flash("目前沒有符合這個模式的單字。"); return redirect(url_for("practice"))
    if mode in {"wrong","weak","unmastered","chapter"}: limit=len(words)
    session["practice_run"]={"mode":mode,"difficulty":difficulty,"chapter_id":chapter,"limit":limit,"words":words,"results":[],"seed":int(time.time()*1000)}
    return redirect(url_for("practice_battle"))

@app.get("/practice/battle")
def practice_battle():
    run=session.get("practice_run")
    if not run: return redirect(url_for("practice"))
    idx=len(run.get("results",[])); words=run.get("words") or []
    if words:
        word=words[idx%len(words)]; q=build_review_question(word,seed=int(run.get("seed",0))+idx); q["difficulty"]=run.get("difficulty","intermediate"); q["difficulty_label"]={"beginner":"初級","intermediate":"中級","advanced":"高級"}.get(q["difficulty"],"練習")
    else:
        q=build_battle(seed=int(run.get("seed",0))+idx*9973,mistake_streak=int(session.get("mistake_streak",0)),difficulty=run.get("difficulty","intermediate"),chapter_id=run.get("chapter_id",1),stage_id=None)
    q.update({"practice_mode":run.get("mode"),"practice_round":idx+1,"practice_total":run.get("limit"),"defer_stage_progress":True,"time_limit":question_time_limit(q)})
    session["question"]=q; session["question_started_ms"]=int(time.time()*1000)
    return render_template("battle.html",profile=current_user(),question=q)

@app.post("/practice/exit")
def practice_exit():
    run=session.get("practice_run")
    if not run: return redirect(url_for("practice"))
    session["practice_summary"]=run_summary(run.get("results",[]),len(run.get("results",[])) or 1); session.pop("practice_run",None)
    return redirect(url_for("practice_summary"))

@app.get("/practice/summary")
def practice_summary():
    summary=session.get("practice_summary")
    if not summary: return redirect(url_for("practice"))
    return render_template("practice_summary.html",profile=current_user(),summary=summary)

@app.post("/daily/claim/<mission_key>")
def daily_claim(mission_key):
    mission=next((m for m in DAILY_MISSIONS if m["key"]==mission_key),None)
    if not mission: flash("找不到這個任務。"); return redirect(url_for("index"))
    ok,msg=claim_daily_mission(current_user()["id"],mission); flash(msg); return redirect(url_for("index"))

@app.get("/review")
def review():
    p=current_user(); due=fetch_due_vocabulary(p["id"])
    if not due:
        flash("目前沒有到期錯題，先去闖新關卡！"); return redirect(url_for("vocabulary"))
    word=request.args.get("word") or due[0]["word"]
    q=build_review_question(word,seed=int(time.time())); q["time_limit"]=question_time_limit(q); session["question"]=q; session["question_started_ms"]=int(time.time()*1000)
    return render_template("battle.html",profile=p,question=q)

@app.post("/shop/equip/<item_key>")
def shop_equip(item_key):
    p=current_user(); flash("裝備完成！" if equip_item(p["id"],item_key) else "你還沒有這個道具。")
    return redirect(url_for("shop"))

@app.post("/shop/unequip")
def shop_unequip():
    unequip_item(current_user()["id"]); flash("已卸下裝備。")
    return redirect(url_for("shop"))


def _valid_audio_response(response):
    content_type=(response.headers.get("Content-Type") or "").lower()
    return response.ok and len(response.content or b"") > 256 and ("audio" in content_type or "mpeg" in content_type or "mp3" in content_type or "octet-stream" in content_type)

def _audio_response(content, content_type="audio/mpeg", source="fallback"):
    response=Response(content,mimetype=(content_type or "audio/mpeg").split(";")[0])
    # Stable same-origin URL lets browsers/Vercel cache successful pronunciation bytes.
    response.headers["Cache-Control"]="public, max-age=86400, s-maxage=604800, stale-while-revalidate=86400"
    response.headers["X-Pronunciation-Source"]=source
    response.headers["Accept-Ranges"]="bytes"
    return response

@app.get("/api/pronounce")
def api_pronounce():
    """Return a same-origin playback URL plus phonetic metadata.

    Keeping playback same-origin avoids intermittent mobile failures caused by
    third-party audio hosts, CORS, and in-app WebView network policies.
    """
    word=(request.args.get("word") or "").strip()
    if not word:
        return jsonify({"audio":"","error":"缺少單字"}),400
    item=lookup_word(word) or {}
    return jsonify({"audio":url_for("api_pronounce_audio",word=word),"phonetic":item.get("phonetic") or ""})

@app.get("/api/pronounce/audio")
def api_pronounce_audio():
    """Proxy pronunciation audio with server-side fallback.

    Order: dictionary audio -> Google Translate TTS. The browser only talks to
    this HTTPS same-origin endpoint, so mobile playback is much more reliable.
    """
    word=(request.args.get("word") or "").strip()
    if not word:
        return jsonify({"error":"缺少單字"}),400

    headers={"User-Agent":"Mozilla/5.0 (WordQuest pronunciation)","Accept":"audio/mpeg,audio/*;q=0.9,*/*;q=0.1"}
    item=lookup_word(word) or {}
    dictionary_audio=(item.get("audio") or "").strip()
    if dictionary_audio.startswith("//"):
        dictionary_audio="https:"+dictionary_audio
    if dictionary_audio.startswith("https://"):
        try:
            r=requests.get(dictionary_audio,headers=headers,timeout=5)
            if _valid_audio_response(r):
                return _audio_response(r.content,r.headers.get("Content-Type") or "audio/mpeg","dictionary")
        except Exception:
            pass

    google_url=f"https://translate.google.com/translate_tts?ie=UTF-8&q={quote(word)}&tl=en&client=tw-ob"
    try:
        r=requests.get(google_url,headers=headers,timeout=7)
        if _valid_audio_response(r):
            return _audio_response(r.content,r.headers.get("Content-Type") or "audio/mpeg","google-tts")
    except Exception:
        pass
    return jsonify({"error":"暫時無法取得發音"}),502

@app.get("/api/tts")
def api_tts():
    # Backwards-compatible alias used by older clients/bookmarks.
    return api_pronounce_audio()

@app.post("/api/teacher/explain")
def api_teacher_explain():
    x=session.get("last_result")
    if not x: return jsonify({"error":"沒有可解釋的錯題"}),400
    text,source=teacher_explain(x["question"],x.get("selected",""))
    return jsonify({"explanation":text,"source":source})

@app.get("/mistakes")
def mistakes():
    p=current_user(); sort=request.args.get("sort","recent"); weak=request.args.get("weak")=="1"
    return render_template("mistakes.html",profile=p,items=fetch_recent_mistakes(p["id"]),words=fetch_mistake_words(p["id"],sort=sort,weak_only=weak),due=fetch_due_vocabulary(p["id"]),sort=sort,weak=weak)

@app.get("/vocabulary")
def vocabulary(): return render_template("vocabulary.html",profile=current_user(),words=fetch_vocabulary(current_user()["id"]))
@app.get("/shop")
def shop():
    p=current_user(); rows=fetch_items(p["id"]); return render_template("shop.html",profile=p,items=SHOP_ITEMS,owned={x["item_key"] for x in rows},equipped=p.get("equipped_gear","") or "")
@app.post("/shop/buy/<item_key>")
def shop_buy(item_key):
    item=next((x for x in SHOP_ITEMS if x["key"]==item_key),None)
    if item: flash("購買成功！" if buy_item(current_user()["id"],item_key,item["price"]) else "金幣不足。")
    return redirect(url_for("shop"))
@app.get("/friends")
def friends():
    code=request.args.get("code","").upper(); return render_template("friends.html",profile=current_user(),challenge=code or None,leaderboard=challenge_leaderboard(code) if code else [])
@app.post("/friends/create")
def friends_create():
    ch=int(request.form.get("chapter",1)); session["challenge_combo"]=0; code=create_challenge(current_user()["id"],ch); return redirect(url_for("friends",code=code))
@app.post("/friends/join")
def friends_join():
    ch=fetch_challenge(request.form.get("code","").strip())
    if not ch: flash("找不到這個挑戰碼。"); return redirect(url_for("friends"))
    session["challenge_combo"]=0; clear_challenge_results(ch["code"],current_user()["id"])
    return redirect(url_for("battle",chapter=ch["chapter_id"],stage=ch.get("stage_id") or "",difficulty="intermediate",challenge=ch["code"],round=1))
@app.get("/api/question")
def api_question(): return jsonify(build_battle(seed=int(time.time()),mistake_streak=int(session.get("mistake_streak",0))))
if __name__=="__main__": app.run(debug=True,port=5001)
