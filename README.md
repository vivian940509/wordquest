# WordQuest

WordQuest 是 Flask + SQLAlchemy 製作的英文學習 RPG。這版把學習流程做成「闖關 → 錯題解析 → 排程複習 → 熟練度 → 裝備/每日任務 → 朋友對戰」的循環，資料庫可直接切換到 Supabase PostgreSQL。

## 目前功能

- ✅ 錯題解析：顯示「你選了什麼」、正確答案、錯因、生活化記法與例句
- ✅ 初級 / 中級 / 高級：預習頁先看中文、英文與發音；練習頁不直接顯示中文提示
- ✅ 國小 / 國中 / 高中 / 大學 4 章 × 12 關關卡地圖，章內逐關解鎖、完成章尾解鎖下一章
- ✅ 關卡 1–3 星：正確率與作答速度會影響星等
- ✅ SRS 單字複習：0–5 星熟練度、錯題到期回鍋、5 星顯示「已馴服」
- ✅ 錯題中心：查看近期錯題與目前到期複習項目
- ✅ 每日任務：答對 5 題、唸 3 題、複習 3 個錯題，可實際領金幣
- ✅ 角色/裝備：發音魔杖、記憶護符、外觀收藏；購買後需穿上才生效
- ✅ 7 日連勝：每連續 7 天送 1 張復活卡；只漏 1 天時可自動消耗一張保 streak
- ✅ 朋友對戰：6 碼挑戰碼、固定 5 題同題組、答對數/時間/最高連擊排行榜
- ✅ AI 老師：錯題頁可要求再解釋；無 API key 使用本機白話解說，有 key 可走 OpenAI-compatible API
- ✅ 語音練習：瀏覽器 Speech Recognition、相似度與練習提示；發音魔杖提供 +10 判定容錯
- ✅ SQLite 本機開發 + Supabase PostgreSQL 正式環境

> 語音評分目前是「語音辨識文字與目標句的相似度」，不是聲學/音素級評分。因此「th / r / v」提示屬練習建議，不應當作專業發音檢測結果。

## 本機啟動

```powershell
py -m pip install -r requirements.txt
copy .env.example .env
py app.py
```

瀏覽器開啟 `http://127.0.0.1:5001`。

## 連接 Supabase

1. 建立 Supabase project。
2. 在 Supabase SQL Editor 執行 `database/schema_supabase.sql`。
3. 到 Project Settings > Database 複製 PostgreSQL connection string。
4. `.env` 將 `DATABASE_URL` 改成該 connection string，建議加 `sslmode=require`。
5. 設定一組新的 `SECRET_KEY`。
6. 重新啟動 Flask。

目前 Flask 後端直接用 PostgreSQL connection string 存取資料，因此資料庫密碼只放伺服器 `.env`。不要把 PostgreSQL 密碼或 Supabase `service_role` key 寫進前端 JavaScript。

部署到 Vercel 與 Supabase 的完整步驟請看 `DEPLOYMENT.md`。

## AI 老師（選用）

完全不設定也能使用內建白話解說。若要使用 OpenAI-compatible API，在 `.env` 設：

```text
AI_API_KEY=你的金鑰
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
```

也可以把 `AI_BASE_URL` / `AI_MODEL` 換成其他相容服務。

## Supabase Auth

目前已支援 Supabase Email / Password 註冊與登入：

- 訪客可以先玩，註冊時會把目前 guest profile 綁到 `auth.users`，保留關卡、星星、錯題、熟練度、金幣與道具。
- 登入後可從「我的帳號」查看學習統計與修改勇者名稱。
- 導覽列會依登入狀態顯示登入 / 註冊或帳號 / 登出。
- 登入狀態由 Flask 簽名 session 保存 30 天；Supabase 負責 Email/Password 身分驗證。

若 Supabase 專案開啟 **Confirm email**，新使用者註冊後需先到信箱完成驗證再登入；若關閉則可註冊後直接登入。

## 測試

```powershell
py -m pytest
```

若只想快速檢查 Python 語法：

```powershell
py -m compileall .
```

## Phase 3+：錯題解析與關卡地圖

- 錯題解析採四段式介面：你的答案 → 正確答案 → 錯誤原因 → 生活化例句。
- 答錯自動加入 SRS 複習排程，可從結果頁立即回鍋練習。
- 關卡地圖共 4 章 × 12 關（48 關），從國小基礎一路到大學學術英文。
- 點關卡會先進入預習頁，先看中文意思、英文單字、例句並聽發音，再開始練習。
- 關卡依作答速度與正確性保留 0–3 星最佳成績，地圖顯示章節完成率與累積星星。
- 新增 `user_achievements`，成就首次解鎖會自動發放金幣。
- Supabase 使用者請重新執行 `database/schema_supabase.sql`，其中 `CREATE TABLE IF NOT EXISTS` 與防重複 policy block 可安全補上新表。


### 快速答題與手機發音
- 一般題限時：初級 8 秒、中級 6 秒、高級 4 秒；語音題 8 秒。
- 「聽發音」會優先播放字典 API 的真人音檔，無音檔時才使用瀏覽器 TTS，提升 Android 手機與內建瀏覽器相容性。
