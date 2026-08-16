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
| 🖼️ **真彩图片** | 交通标志图在终端内嵌显示（kitty 终端） |
| 🎯 **多种模式** | 顺序 / 随机 / 章节 / 错题重练 |
| 📝 **模拟考试** | 随机抽题、统一交卷、85% 及格线提示 |
| 📊 **成绩统计** | 整体与分章节正确率、错题本 |
| ⚡ **全离线** | 数据在本地，无网络依赖 |

## ⚠️ 终端要求

本工具面向 **kitty 终端** 设计：题目图片依靠 kitty 的 `icat` 协议在终端内嵌**真彩显示**，这样才能看清交通标志。

- **kitty 终端**：完整体验（标志图真彩内嵌）。
- 其他终端：可以运行，但图片题只能看到本地路径提示，**做题体验不完整**。

## 📦 安装

需要 Python 3.10+。

```bash
# kitty 终端里执行
python3 -m venv .venv
source .venv/bin/activate.fish        # bash: source .venv/bin/activate
pip install -r requirements.txt
```

> 依赖：`rich`（界面）、`click`（命令行）、`prompt_toolkit`（交互命令界面），无浏览器/网络依赖。

## 🚀 使用

### 启动交互式界面

在 kitty 终端输入 `MDrivePractice`（fish 已配置）：

```bash
MDrivePractice
# 或 python -m trainer.shell
```

进入全屏界面：**显示标题 + 底部命令输入框**，输入命令按 Enter 进入对应模式。
输入时支持 **fuzzy 下拉补全**（Tab / 方向键选取）。完成一次练习后自动返回命令界面。

### 命令

| 命令 | 说明 |
|------|------|
| `start [N]` / `顺序` | 顺序刷题（N 题，默认全部） |
| `random [--count N]` | 随机抽 N 题（默认全部） |
| `wrong [--count N]` | 错题重练 N 题 |
| `exam [--count N]` | 模拟考 N 题（默认 40），统一交卷批改 |
| `stats` / `统计` | 成绩统计（整体 + 分章节） |
| `book 第一冊` / `第一冊` | 只练某一册 |
| `help` | 显示帮助 |
| `clear` | 重显标题 |
| `quit` / `exit` | 退出 |

也支持**命令行直通**（跳过交互界面，直接刷题）：

```bash
python -m trainer.main --mode exam --count 40   # 模拟考 40 题
python -m trainer.main --subject 第一冊         # 只练第一册
python -m trainer.main --mode stats             # 成绩统计
```

### 作答键

| 按键 | 作用 |
|------|------|
| `A` / `B` / `C` / `D` | 作答，即时显示对错与正确答案 |
| `s` | 跳过（计入错题） |
| `q` / `quit` | 退出，进度自动保存 |

### 图片题显示

默认 `--view-image auto`：在 **kitty 终端** 自动用 `icat` 真彩内嵌显示标志图。
也可以：

```bash
python -m trainer.main --mode random --view-image ascii   # img2txt ASCII 图
python -m trainer.main --view-image viu                    # 外接查看器
```

## 🧱 目录结构

```
trainer/    交互练习端（shell.py 命令界面 + main.py 刷题核心）
database/   SQLite 数据访问层（schema.sql + store.py）
data/       题库 questions.db + 题目图片 images/（随项目发布）
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

## 🧭 进度

- 架构：`BLUEPRINT.md`
- 阶段记录：`doc/`

---

<div align="center">

<sub>本工具仍在演进中，欢迎反馈 · MIT Licence</sub>

</div>
