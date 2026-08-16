<div align="center">

# 🚗 澳门驾考题库练习工具

**在终端里刷澳门驾考笔试题库**

内置五册 **647 题** + **242 幅** 交通标志/图表图片，顺序、随机、错题、模拟考一站搞定，全程离线。

**简体中文** · [繁体中文](README.md)（预设）

</div>

---

## ✨ 特性

| | |
|---|---|
| 📚 **内置题库** | 五册（第一冊~第五冊）647 题，按册分类 |
| 🖼️ **图片显示** | 交通标志图以 kitty icat 真彩原图显示在题目上方 | 
| 🎯 **多种模式** | 顺序 / 随机 / 章节 / 错题重练 |
| 📝 **模拟考试** | 随机抽题、统一交卷、85% 及格线提示 |
| 📊 **成绩统计** | 整体与分章节正确率、错题本 |
| ⌨️ **交互体验** | 上下箭头选择、图片与题目并排、答错可重答一次 |
| ⚡ **全离线** | 数据在本地，无网络依赖 |

## ⚠️ 终端要求

本工具面向 **kitty 终端** 设计：题目图片用 kitty 的 `icat` 以**真彩原图**显示在题目上方，这样才能看清交通标志。

- 仅支持 **kitty 终端**（非 kitty 无法显示图片）。

## 📦 安装

需要 Python 3.10+。

```bash
# 在 kitty 终端里执行
python3 -m venv .venv
source .venv/bin/activate.fish        # bash: source .venv/bin/activate
pip install -r requirements.txt
```

> 依赖：`rich`（界面）、`click`（命令行）、`prompt_toolkit`（交互界面）。图片渲染用 kitty 自带的 `icat`，无需额外安装。

## 🚀 使用

### 启动交互式界面

在 kitty 终端输入 `MDrivePractice`（fish 已配置）：

```bash
MDrivePractice
# 或 python -m trainer.shell
```

进入全屏界面：**显示标题 + 底部命令输入框**，输入命令按 Enter 进入对应模式。
输入时支持**两级补全**：先输入/补全主命令，按空格键后再按 Tab 补子选项（如 `practice` + 空格→ `book 1..5`）。完成一次练习后自动返回命令界面。

### 命令

| 命令 | 说明 |
|------|------|
| `start [N]` | 顺序刷 N 题（默认全部） |
| `random [--count N]` | 随机抽 N 题（默认全部） |
| `wrong [--count N]` | 错题重练 N 题 |
| `exam [--count N]` | 模拟考 N 题（默认 40），统一交卷批改 |
| `stats` | 成绩统计（整体 + 分章节） |
| `practice book 1 [题号]` | 练习第一册（可指定题号从该题开始） |
| `learn book 1 [题号]` | 浏览第一册：正确答案绿色高亮，Enter 下一题 / r 上一题 |
| `help` | 显示帮助 |
| `clear` | 重显标题 |
| `quit` | 退出 |
| `edata 2026-08-18` | 考试倒计时：输入未来日期，大字显示剩余天数 |

也支持**命令行直通**（跳过交互界面，直接刷题）：

```bash
python -m trainer.main --mode exam --count 40   # 模拟考 40 题
python -m trainer.main --subject 第一冊         # 只练第一册
python -m trainer.main --mode stats             # 成绩统计
```

### 作答交互（训练模式）

进入模式后，每题以一排呈现：**交通标志图以真彩原图显示在上方**，下方为题目与选项。

| 按键 | 作用 |
|------|------|
| `↑` / `↓` | 上下移动选择选项 |
| `Enter` | 确认作答 |
| `q` | 退出 |

错题处理（练习模式）：**答错时显示「答错」并给一次重答机会**（正确答案会高亮），再答错才进入下一题。

模拟考（`exam`）模式：作答后**不显示对错、不重答**，交卷统一批改看总分。

学习浏览（`learn`）模式：**无需作答**，正确答案以**绿色背景高亮**直接显示，`Enter` 下一题、`r` 上一题、`q` 退出。可配合题号跳转（如 `learn book 2 30`）从特定题开始浏览。

## 🧱 目录结构

```
trainer/    交互练习端（shell.py 命令界面 + tui.py 全屏刷题 + main.py 核心 + logger.py 日志）
database/   SQLite 数据访问层（schema.sql + store.py）
data/       题库 questions.db + 题目图片 images/ + 日志 logs/（随项目发布）
doc/        进度文档
```

## ⚡ 一键启动（可选)

以下已加进你的 `~/.config/fish/config.fish`，在 kitty 终端输入 `MDrivePractice` 即可启动：

```fish
function MDrivePractice
    cd ~/Program_Project/drive-lesson-practice
    source .venv/bin/activate.fish
    python -m trainer.shell $argv
end
```

## 📊 数据

- 题库：`data/questions.db`（`questions` 题目表 + `practice_log` 作答流水表）。
- 图片：`data/images/`（242 幅，随项目发布）。
- 正确率、错题本、分章节统计均基于 `practice_log` 作答流水。

## 📝 日志

运行时的信息、警告与错误会写入 `data/logs/drive_practice.log`（自动创建）。若遇到异常，可将该文件内容提供出来，有助于排查。放大后的图片缓存位于 `data/images_cache/`（可删除重建）。

## 🧭 进度

- 架构：`BLUEPRINT.md`
- 更新记录：`CHANGELOG.md`
- 授权：`LICENSE`（MIT）
- 阶段记录：`doc/`

---

<div align="center">

<sub>本工具仍在演进中，欢迎反馈 · MIT Licence</sub>

</div>
