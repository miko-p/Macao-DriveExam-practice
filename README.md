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
| 🖼️ **彩圖顯示** | 交通標誌圖在終端機內嵌顯示（kitty 終端機） |
| 🎯 **多種模式** | 循序 / 隨機 / 章節 / 錯題重練 |
| 📝 **模擬考試** | 隨機抽題、統一交卷、85% 及格線提示 |
| 📊 **成績統計** | 整體與分章節正確率、錯題本 |
| ⚡ **全離線** | 資料在本地，無網路依賴 |

## ⚠️ 終端機要求

本工具面向 **kitty 終端機** 設計：題目圖片依靠 kitty 的 `icat` 協定在終端機內嵌**彩圖顯示**，這樣才能看清交通標誌。

- **kitty 終端機**：完整體驗（標誌圖彩圖內嵌）。
- 其他終端機：可以執行，但圖片題只能看到本地路徑提示，**作答體驗不完整**。

## 📦 安裝

需要 Python 3.10+。

```bash
# 於 kitty 終端機執行
python3 -m venv .venv
source .venv/bin/activate.fish        # bash: source .venv/bin/activate
pip install -r requirements.txt
```

> 依賴：`rich`（介面）、`click`（命令列）、`prompt_toolkit`（互動命令介面），無瀏覽器/網路依賴。

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
| `start [N]` / `顺序` | 循序刷題（N 題，預設全部） |
| `random [--count N]` | 隨機抽 N 題（預設全部） |
| `wrong [--count N]` | 錯題重練 N 題 |
| `exam [--count N]` | 模擬考 N 題（預設 40），統一交卷批改 |
| `stats` / `统计` | 成績統計（整體 + 分章節） |
| `book 第一冊` / `第一冊` | 只練某一冊 |
| `help` | 顯示幫助 |
| `clear` | 重顯標題 |
| `quit` / `exit` | 退出 |

也支援**命令列直通**（跳過互動介面，直接刷題）：

```bash
python -m trainer.main --mode exam --count 40   # 模擬考 40 題
python -m trainer.main --subject 第一冊         # 只練第一冊
python -m trainer.main --mode stats             # 成績統計
```

### 作答鍵

| 按鍵 | 作用 |
|------|------|
| `A` / `B` / `C` / `D` | 作答，即時顯示對錯與正確答案 |
| `s` | 跳過（計入錯題） |
| `q` / `quit` | 離開，進度自動儲存 |

### 圖片題顯示

預設 `--view-image auto`：在 **kitty 終端機** 自動用 `icat` 彩圖內嵌顯示標誌圖。
也可以：

```bash
python -m trainer.main --mode random --view-image ascii   # img2txt ASCII 圖
python -m trainer.main --view-image viu                    # 外接檢視器
```

## 🧱 目錄結構

```
trainer/    互動練習端（shell.py 命令介面 + main.py 刷題核心）
database/   SQLite 資料存取層（schema.sql + store.py）
data/       題庫 questions.db + 題目圖片 images/（隨專案發佈）
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

## 🧭 進度

- 架構：`BLUEPRINT.md`
- 階段記錄：`doc/`

---

<div align="center">

<sub>本工具仍在演進中，歡迎回饋 · MIT Licence</sub>

</div>
