# M6 狀態報告：互動式命令介面（MDrivePractice）

> 日期：2026-08-16
> 階段：M6 互動命令介面 + 命令體系 — 已完成

## 1. 目標

在 M5 的 CLI 刷題之上，新增一個**互動式命令介面**，讓使用者不用記命令行參數，直接在介面底部輸入簡短命令即可進入對應模式。

## 2. 實現

### 2.1 互動命令介面（`trainer/shell.py`）
- prompt_toolkit 實作底部輸入框 + 標題 banner，啟動即清屏顯示。
- 輸入命令按 Enter 進入對應模式，完成一次練習自動返回命令介面。

### 2.2 命令體系（僅英文）
- 模式命令：`start`（順序）/ `random`（隨機）/ `exam`（模擬考）/ `wrong`（錯題）/ `stats`（統計）。
- 答題練習：`practice book <冊> [題號]`（取代原本的 `book`），可指定題號從某題開始。
- 學習瀏覽：`learn book <冊> [題號]`，正確答案綠色高亮，`Enter` 下一題 / `r` 上一題。
- 其他：`help`（幫助）/ `clear`（重顯標題）/ `quit`（退出）。
- 移除中文別名，命令統一為英文。

### 2.3 兩級補全
- 自訂 `_TwoLevelCompleter`：先補主命令（前綴匹配），輸入主命令 + 空白鍵後再按 `Tab` 補子選項（如 `practice` → `book 1..5`、`edata` → 日期佔位）。

## 3. 使用者互動

```
MDrivePractice> practice book 3 20   ← 從第三冊第 20 題開始練習
MDrivePractice> learn book 1         ← 瀏覽第一冊
MDrivePractice> stats                ← 成績統計
MDrivePractice> quit                 ← 退出
```

## 4. 驗證

- 命令解析：`practice book 1 50` 正確定位到 `book1_q50`；`learn book 1 55` → 題號 55。
- 兩級補全：空輸入列出主命令、`prac`→`practice`、`practice `→`book 1..5`、`edata `→日期佔位。
- import / shell 冒煙通過。

## 5. 交付物

- `trainer/shell.py`：互動命令介面 + 命令解析 + 兩級補全。
- `trainer/main.py`：新增 practice/learn 模式與題號跳轉。

## 6. 說明 / 遺留

- learn 模式的上一題原用 `Ctrl+Enter`，因部分終端辨識不可靠，改為 `r` 鍵。
- 題號跳轉基於 `source_id`（如 `book1_q50`），超出該冊題數時自動退回冊內順序。
