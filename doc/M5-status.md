# M5 状态报告：模拟考 + 终端打磨 + 文档收尾

> 日期：2026-08-16
> 阶段：M5 模拟考 + 打磨 — 已完成

## 1. 目标

补齐模拟考模式、优化终端图片显示、完善 README 与使用说明，让工具达到可日常使用的完成度。

## 2. 实现

### 2.1 模拟考（`trainer/main.py` → `run_exam()`）
- `--mode exam --count N`：随机抽 N 题（默认 40）。
- 逐题作答**不即时批改**（更贴近真实考试），`q` 提前交卷。
- 交卷统一批改：显示作答数、用时、答对数、正确率，并提示正式考试参考及格线 85%。
- 作答以 mode='exam' 记入 `practice_log`（同样影响正确率/错题统计）。

### 2.2 终端图片显示（kitty 真彩）
- `--view-image auto`（默认）：自动检测 kitty 终端（`KITTY_WINDOW_ID` / `TERM=xterm-kitty`），用 `kitty +kitten icat --transfer-mode=stream` **真彩内嵌显示**交通标志图，缩放适配终端宽度。
- 非 kitty 终端：仅提示本地图片路径。
- `--view-image ascii`：用 img2txt 内嵌 ASCII 图。
- `--view-image <程序>`：启动任意外部查看器（如 viu/qview）。
- 练习与模拟考模式均支持图片显示。

### 2.3 进度持久化与文档
- 进度持久化：作答即写入 `practice_log`，退出/中断不丢失，重启后可查统计与错题。
- 新增 `README.md`（含使用指南）与各里程碑 status 文档。

## 3. 验证（真实数据）

- 模拟考：5 题抽题→作答→交卷，正确计算总分与用时，85% 及格线正确提示。
- 图片题在 kitty 终端 icat 命令构造正确、优雅降级；`_in_kitty()` 检测准确。
- 全量 smoke：trainer 各模式 `--help` / CLI 校验通过。

## 4. 交付物

- `trainer/main.py`：exam 模式 + kitty 真彩图片显示。
- `README.md`：完整项目简介、安装、使用指南、fish alias 建议。

## 5. 说明 / 遗留

- icat 的 `--place`/固定区域排版未做（当前按终端宽内嵌，够用）；如需右上角固定窗口可后续调。
- 暂无题目解析（explanation）字段展示——网站题库本身不带解析，属正常。
