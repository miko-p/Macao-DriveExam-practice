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

> 依賴：`rich`（介面）、`click`（命令列），無瀏覽器/網路依賴。

## 🚀 使用

```
用法：python -m trainer.main [選項]

選項：
  --subject 章節     只練某個章節（如 第一冊）
  --mode 模式        循序 sequential(預設) | 隨機 random | 錯題 wrong
                     | 統計 stats | 模擬考 exam
  --count 數量       題數（預設全部）
  --view-image 方式   auto(預設,kitty彩圖) | ascii | <外部程式>
```

### 常用指令

```bash
python -m trainer.main                          # 全部，循序刷題
python -m trainer.main --subject 第一冊         # 只練第一冊
python -m trainer.main --mode random --count 20 # 隨機抽 20 題
python -m trainer.main --mode wrong             # 錯題重練
python -m trainer.main --mode stats             # 成績統計
python -m trainer.main --mode exam --count 40   # 模擬考 40 題
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
trainer/    互動練習端（main.py）
database/   SQLite 資料存取層（schema.sql + store.py）
data/       題庫 questions.db + 題目圖片 images/（隨專案發佈）
doc/        進度文件
```

## ⚡ 一鍵啟動（可選)

把下面這行加進 `~/.config/fish/config.fish`，之後在 kitty 裡輸入 `drive` 即可刷題：

```fish
function drive
    cd ~/Program_Project/drive-lesson-practice
    source .venv/bin/activate.fish
    python -m trainer.main $argv
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
