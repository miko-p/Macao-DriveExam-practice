<div align="center">

# 🚗 澳門駕考題庫練習工具

**在終端機裡刷澳門駕考筆試題庫**

內建五冊 **647 題** + **242 幅** 交通標誌/圖表圖片，循序、隨機、錯題、模擬考一站搞定，全程離線。

[简体中文](README.zh-CN.md) · **繁體中文**（預設）

</div>

---

## ✨ 特色

| | |
|---|---|
| 📚 **內建題庫** | 五冊（第一冊~第五冊）647 題，按冊分類 |
| 🖼️ **圖片顯示** | 交通標誌圖以 kitty icat 真彩原圖顯示在題目上方 | 
| 🎯 **多種模式** | 循序 / 隨機 / 章節 / 錯題重練 |
| 📝 **模擬考試** | 隨機抽題、統一交卷、85% 及格線提示 |
| 📊 **成績統計** | 整體與分章節正確率、錯題本 |
| ⌨️ **互動體驗** | 上下箭頭選擇、圖片與題目並排、答錯可重答
一次 |
| ⚡ **全離線** | 資料在本地，無網路依賴 |

## ⚠️ 終端機要求

本工具面向 **kitty 終端機** 設計：題目圖片用 kitty 的 `icat` 以**真彩原圖**顯示在題目上方，這樣才能看清交通標誌。

- 僅支援 **kitty 終端機**（非 kitty 無法顯示圖片）。

## 📦 安裝

需要 Python 3.10+。

```bash
# 於 kitty 終端機執行
python3 -m venv .venv
source .venv/bin/activate.fish        # bash: source .venv/bin/activate
pip install -r requirements.txt
```

> 依賴：`rich`（介面）、`click`（命令列）、`prompt_toolkit`（互動介面）。圖片渲染用 kitty 自帶的 `icat`，無需額外安裝。

## 🚀 使用

### 啟動互動式介面

在 kitty 終端機輸入 `MDrivePractice`（fish 已配置）：

```bash
MDrivePractice
# 或 python -m trainer.shell
```

進入全螢幕介面：**顯示標題 + 底部命令輸入框**，輸入命令按 Enter 進入對應模式。
輸入時支援 **fuzzy 下拉補全**（Tab / 方向鍵選取）。完成一次練習後自動返回命令介面。

### 命令

| 命令 | 說明 |
|------|------|
| `start [N]` | 循序刷 N 題（預設全部） |
| `random [--count N]` | 隨機抽 N 題（預設全部） |
| `wrong [--count N]` | 錯題重練 N 題 |
| `exam [--count N]` | 模擬考 N 題（預設 40），統一交卷批改 |
| `stats` | 成績統計（整體 + 分章節） |
| `practice book 1 [題號]` | 練習第一冊（可指定題號從該題開始） |
| `learn book 1 [題號]` | 瀏覽第一冊：正確答案綠色高亮，Enter 下一題 / r 上一題 |
| `help` | 顯示幫助 |
| `clear` | 重顯標題 |
| `quit` | 退出 |

也支援**命令列直通**（跳過互動介面，直接刷題）：

```bash
python -m trainer.main --mode exam --count 40   # 模擬考 40 題
python -m trainer.main --subject 第一冊         # 只練第一冊
python -m trainer.main --mode stats             # 成績統計
```

### 作答交互（訓練模式）

進入模式後，每題以一排呈現：**交通標誌圖以真彩原圖顯示在上方**，下方為題目與選項。

| 按鍵 | 作用 |
|------|------|
| `↑` / `↓` | 上下移動選擇選項 |
| `Enter` | 確認作答 |
| `q` | 退出 |

錯題處理（練習模式）：**答錯時顯示「答錯」並給一次重答機會**（正確答案會高亮），再答錯才進入下一題。

模擬考（`exam`）模式：作答後**不顯示對錯、不重答**，交卷統一批改看總分。

學習瀏覽（`learn`）模式：**不須作答**，正確答案以**綠色背景高亮**直接顯示，`Enter` 下一題、`r` 上一題、`q` 退出。可配合題號跳轉（如 `learn book 2 30`）從特定題開始瀏覽。

## 🧱 目錄結構

```
trainer/    互動練習端（shell.py 命令介面 + tui.py 全螢幕刷題 + main.py 核心 + logger.py 日誌）
database/   SQLite 資料存取層（schema.sql + store.py）
data/       題庫 questions.db + 題目圖片 images/ + 日誌 logs/（隨專案發佈）
doc/        進度文件
```

## ⚡ 一鍵啟動（可選)

以下已加進你的 `~/.config/fish/config.fish`，在 kitty 終端機輸入 `MDrivePractice` 即可啟動：

```fish
function MDrivePractice
    cd ~/Program_Project/drive-lesson-practice
    source .venv/bin/activate.fish
    python -m trainer.shell $argv
end
```

## 📊 資料

- 題庫：`data/questions.db`（`questions` 題目表 + `practice_log` 作答流水表）。
- 圖片：`data/images/`（242 幅，隨專案發佈）。
- 正確率、錯題本、分章節統計均基於 `practice_log` 作答流水。

## 📝 日誌

運行時的資訊、警告與錯誤會寫入 `data/logs/drive_practice.log`（自動建立）。若遇到異常，可將該檔案內容提供出來，有助於排查。放大後的圖片快取在 `data/images_cache/`（可刪除重建）。

## 🧭 進度

- 架構：`BLUEPRINT.md`
- 更新紀錄：`CHANGELOG.md`
- 授權：`LICENSE`（MIT）
- 階段記錄：`doc/`

---

<div align="center">

<sub>本工具仍在演進中，歡迎回饋 · MIT Licence</sub>

</div>
