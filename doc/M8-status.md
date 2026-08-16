# M8 狀態報告：應用完善（日誌 / 倒計時 / 繁體 / 及格線 / 安全）

> 日期：2026-08-16
> 階段：M8 使用體驗與工程完善 — 已完成

## 1. 目標

在功能齊全的基礎上，補齊應用層的工程細節與使用者體驗：日誌、考試倒計時、介面繁體化、模擬考及格線對齊實際標準、安全掃描修復，以及 GitHub 文件完備。

## 2. 實現

### 2.1 應用日誌系統（`trainer/logger.py`）
- 運行時資訊/警告/錯誤寫入 `data/logs/drive_practice.log`（控制台僅顯示 WARNING+，避免干擾互動介面）。
- 記錄練習開始/抽題/完成、命令執行、使用者中斷、**異常 traceback**、圖片處理失敗等。
- 5MB 自動滾動歸檔；`data/logs/` 入 `.gitignore` 不入版控。

### 2.2 考試倒計時（`edata` 命令）
- `edata YYYY-MM-DD`：設定考試日期並全螢幕大字顯示剩餘天數（塊狀數字 + 黃底突出）。
- 日期須為未來日期，格式錯誤給提示。
- 考試日期持久化至 `data/exam_date`（入 `.gitignore`）；**重啟 MDrivePractice 時在標題下方自動顯示倒計時**。用 rich `Text` 分段著色，修正早期 markup 標籤不配對的崩潰。

### 2.3 兩級命令補全
- `start/random/wrong/exam/stats/practice/learn/help/clear/quit/edata` 主命令 + 子選項兩級補全，參數不再預先塞入候選。

### 2.4 介面繁體化
- 全部使用者可見文案（tui 回饋/幫助、main 統計/模擬考提示、shell 命令介面/幫助/倒計時/toolbar）改為繁體中文。
- README 以繁體為預設（`README.md`），另附簡體 `README.zh-CN.md`。

### 2.5 模擬考及格線對齊實際標準
- 及格線由 85% 改為**總錯 ≤ 8（正確率 ≥ 84%）且每冊錯 ≤ 2** 的雙標準判斷。
- 新增分冊錯題統計與「超冊」提示。

### 2.6 退出顯示統計
- `quit` / `Ctrl+C` 退出前先顯示一次成績統計，再道別。

### 2.7 安全掃描與 GitHub 文件
- 用 ai-sec-scan 掃描，修正 `overall_stats` 的 SQL 字串插值（改參數化），消除潛在注入風險。
- 新增 LICENSE（MIT）、CHANGELOG.md、`trainer/logger.py`。

## 3. 驗證

- 日誌正確寫入（INFO/WARNING），控制台僅 WARNING+。
- 倒計時 `_countdown_text` 無 markup 崩潰，顯示「距 離 考 試 還 有 N 天」與啟動標題下倒數行。
- 及格判斷四場景（全對 / 分冊超 2 / 總數超 8 / 各冊合規）全數正確。
- 退出流程輸出「最後統計 + 成績統計 + 再見」。
- ai-sec-scan：critical 消除（SQL 誤報修復後退出碼 0），剩餘 medium 為抽題用途誤報。

## 4. 交付物

- `trainer/logger.py`、`trainer/shell.py`（edata/補全/繁體/退出統計）。
- `LICENSE`、`CHANGELOG.md`、`doc/M6~M8-status.md`。
- config 加 `LOGS_DIR` / `EXAM_DATE_FILE`。

## 5. 說明 / 遺留

- 排行榜/作答時間維度統計尚未加入（見 BLUEPRINT 後續可選）。
- 安全掃描剩餘的 INSECURE_RANDOM 為隨機抽題的正常用途，未改動。
