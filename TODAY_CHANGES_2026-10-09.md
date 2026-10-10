# WordQuest 今日工作紀錄（2026-10-09）

## 完成摘要

今天把 WordQuest 從本機 Flask 專案整理成可連接 Supabase、可部署到 Vercel 的版本，並補上英文學習流程、關卡數量、課前單字學習頁，以及多個部署與資料庫錯誤修正。

目前主要網址：

- GitHub Repository：https://github.com/vivian940509/wordquest.git
- Vercel Production：https://wordquest-hann18.vercel.app/
- 本機測試：http://127.0.0.1:5001/

## GitHub 與 Git 設定

- 建立並推送 WordQuest 專案到 GitHub。
- 設定 Git 使用者資料：
  - `user.name`：`vivian940509`
  - `user.email`：`C112156105@nkust.edu.tw`
- 修正先前 commit author 資訊，讓 GitHub 紀錄對應到正確帳號。
- 目前主要分支為 `main`。

## Supabase 連接

- 建立並連接 Supabase 專案。
- Supabase URL：
  - `https://eivbcznrihjfttpabvdq.supabase.co`
- 已執行 `database/schema_supabase.sql` 建立資料表與 RLS 基礎設定。
- 本機 `.env` 已設定：
  - `DATABASE_URL`
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
- 密碼與 API secret 只放在 `.env` 或 Vercel Environment Variables，沒有寫進 GitHub。
- 已確認 Flask / SQLAlchemy 可以連接 Supabase PostgreSQL。

## Vercel 部署

- 已將專案部署到 Vercel。
- Production URL：
  - `https://wordquest-hann18.vercel.app/`
- Vercel Environment Variables 已設定：
  - `DATABASE_URL`
  - `SECRET_KEY`
  - `APP_TIMEZONE`
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `AI_BASE_URL`
  - `AI_MODEL`
- 修正 Vercel 初始 404 問題：
  - 移除自訂 `vercel.json` rewrite。
  - 移除不需要的 `api/index.py`。
  - 改用 Vercel zero-config Flask entrypoint，直接從 `app.py` 啟動。
- 修正 Vercel 500 問題：
  - 補上 Production 環境變數。
  - 修正 PostgreSQL upsert 欄位衝突。

## 遊戲內容修改

- 擴充成四個學習等級：
  - 國小基礎
  - 國中進階
  - 高中核心
  - 大學學術
- 關卡數量擴充為：
  - 每章 12 關
  - 共 4 章
  - 總共 48 關
  - 總星數 144 顆
- 地圖統計改成動態計算，不再固定顯示 21 關 / 63 星。
- 補充更多大學程度單字，例如：
  - `analyze`
  - `hypothesis`
  - `methodology`
  - `interpret`
  - `significant`
  - `framework`
  - `derive`
  - `synthesize`

## 學習流程修改

- 新增課前單字學習頁。
- 現在點選關卡後，會先看到：
  - 中文意思
  - 英文單字
  - 英文例句
  - 發音按鈕
- 使用者可以先學單字與聽發音，再開始正式練習。
- 正式練習頁已移除中文提示，避免答題時直接看到答案。
- 課前頁原本只顯示 3 個單字，已修正為顯示該章節完整單字。

## 錯誤修正

- 修正答題時倒數尚未結束就按下答案，可能出現 Internal Server Error 的問題。
- 修正 Supabase PostgreSQL `ON CONFLICT DO UPDATE` 造成的 ambiguous column 問題。
- 已修正的資料表流程包含：
  - `user_vocabulary`
  - `daily_progress`
  - `stage_progress`
- 修正 Vercel 部署後根路徑顯示 Not Found 的問題。
- 修正 Production 缺少 `DATABASE_URL` 時無法啟動的問題。

## 測試結果

今天完成後已執行測試：

```text
15 passed
```

測試涵蓋重點：

- Flask route 基本頁面可開啟。
- 地圖資料可正常載入。
- 關卡流程可進入學習與答題。
- Supabase / SQLite 相容資料流程。
- SRS 複習與 battle engine 相關流程。
- PostgreSQL upsert 修正後不再因欄位名稱衝突失敗。

## 目前狀態

- 本機可以用 `py app.py` 啟動。
- 本機網址：http://127.0.0.1:5001/
- Production 已部署到 Vercel。
- Supabase 資料庫已接上。
- GitHub main 分支已推送。

## 後續建議

- 補上真正帳號登入系統，使用 Supabase Auth。
- 將每一關改成完整 5 到 10 題流程，並加入關卡結算畫面。
- 擴充更多國小、國中、高中、大學程度題庫。
- 增加音素級發音評分。
- 補上角色外觀、裝備換裝與更完整商店頁。
- 在 Vercel 上確認 Production 每個主要頁面都能正常操作。

## 晚間更新：登入註冊與答題節奏

- 新增 Supabase Auth Email/Password 註冊、登入、登出。
- 註冊時會把目前瀏覽器的 guest profile 綁到新帳號，保留關卡、星星、錯題、熟練度、金幣與道具。
- 新增「我的帳號」頁，可查看完成關卡、總星數、學過單字與待複習數量，並可修改勇者名稱。
- 導覽列會依登入狀態顯示「登入 / 註冊」或「我的帳號 / 登出」。
- 答題倒數再加速：初級 8 秒、中級 6 秒、高級 4 秒；語音題 8 秒。倒數歸零會自動交卷。
- 倒數歸零現在會自動交卷，不再只是視覺倒數；最後 5 秒會進入警示狀態。
- 星等速度門檻改為依題目限時比例計算，避免縮短時間後仍沿用舊 7 / 15 秒門檻。


## 2026-10-10 補充修改
- 答題時間調整為：初級 8 秒、中級 6 秒、高級 4 秒、語音題 8 秒。
- 改善手機「聽發音」：按下按鈕時優先取得字典真人語音檔播放；若沒有音檔，再退回瀏覽器 TTS。
- Android / 內建 WebView 若 speechSynthesis 有介面但無聲音，不再只依賴它。
- 播放失敗時，按鈕會提示檢查手機媒體音量。

## 2026-10-10 — 六大功能擴充

### 1. 一般關卡改為 5 題完整流程
- 一般 stage 現在固定 5 題，題目頁會顯示「第 n/5 題」進度。
- 每題仍使用現有難度倒數：初級 8 秒、中級 6 秒、高級 4 秒、語音 8 秒。
- 關卡完成後才一次寫入 stage progression，避免單題答對就直接通關。
- POST /answer 會消耗當前 question session，避免重新整理/重送造成重複獎勵。

### 2. 關卡結算頁
新增 `/level-summary`：
- 正確率、平均答題時間、星星、EXP、金幣、關卡分數。
- 本關錯題與最弱單字。
- 再挑戰一次與回地圖。

### 3. 個人學習 Dashboard
`/account` 新增：
- 最近 7 天答題數。
- 總正確率、平均答題時間、總答題數。
- 最容易錯的 5 個單字。
- 初級/中級/高級正確率。
- 7 天學習連續圖與目前 streak。

### 4. 忘記密碼 + Google 登入
新增：
- `/forgot-password`
- `/reset-password`
- `/login/google`
- `/auth/google/callback`
- `/auth/google/complete`

Supabase 後台需另外設定：
1. Authentication > Providers > Google 啟用 Google provider，填入 Google OAuth Client ID / Secret。
2. Authentication > URL Configuration 將正式網址加入 Redirect URLs，例如：
   - `https://wordquest-sandy-gamma.vercel.app/auth/google/callback`
   - `https://wordquest-sandy-gamma.vercel.app/reset-password`
3. Google Cloud OAuth Authorized redirect URI 需包含 Supabase 提供的 callback URL（通常為 `https://<project-ref>.supabase.co/auth/v1/callback`）。

### 5. 錯題中心升級
- `user_vocabulary` 新增 `weak_word`、`last_wrong_at`。
- 累積答錯達 3 次會自動成為弱點單字。
- 錯題中心可切換「最近又錯 / 最常錯 / 弱點單字」。
- 新增「一鍵只練弱點」。

### 6. 自訂學習模式
新增 `/practice`：
- 只練錯題。
- 只練弱點。
- 只練未馴服單字（包含尚未練過的字）。
- 指定章節。
- 10 題快速練習。
- 30 題挑戰。
- 無限模式，可隨時結束並查看本次統計。

### 資料庫更新
- SQLite 會自動補上 `weak_word` 與 `last_wrong_at` 欄位。
- Supabase/PostgreSQL 請重新執行 `database/schema_supabase.sql` 最後的 migration 段落。

## 手機發音穩定性修正（2026-10-10）
- 發音改成瀏覽器只播放同源 `/api/pronounce/audio`，不再直接連第三方音檔網址。
- 後端發音來源依序為：字典真人音檔 → Google TTS；會驗證回應狀態、內容大小與音訊 Content-Type。
- 音訊成功後加上 CDN/瀏覽器快取標頭，降低同一單字重複抓取失敗機率。
- 手機點擊時直接建立 Audio 並呼叫 `play()`，避免等待 `fetch()` 後失去 iOS/Android 的 user-gesture 播放權限。
- 遠端音訊失敗後再退回 Web Speech API，會等待 voices、優先 en-US/en-GB、取消舊朗讀並避免重疊播放。
- 新增載入、切換備援、完全失敗等按鈕狀態。
