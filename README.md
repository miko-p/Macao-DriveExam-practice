<div align="center">

# 🚗 澳门驾考题库练习工具

**在终端里刷澳门驾考笔试题库**

内置五册 **647 题** + **242 幅** 交通标志/图表图片，顺序、随机、错题、模拟考一站搞定，全程离线。

**简体中文** · [繁体中文](README.zh-TW.md)

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

> 依赖：`rich`（界面）、`click`（命令行），无浏览器/网络依赖。

## 🚀 使用

```
用法：python -m trainer.main [选项]

选项：
  --subject 章节     只练某个章节（如 第一冊）
  --mode 模式        顺序 sequential(默认) | 随机 random | 错题 wrong
                     | 统计 stats | 模拟考 exam
  --count 数量       题数（默认全部）
  --view-image 方式   auto(默认,kitty真彩) | ascii | <外部程序>
```

### 常用命令

```bash
python -m trainer.main                          # 全部，顺序刷题
python -m trainer.main --subject 第一冊         # 只练第一册
python -m trainer.main --mode random --count 20 # 随机抽 20 题
python -m trainer.main --mode wrong             # 错题重练
python -m trainer.main --mode stats             # 成绩统计
python -m trainer.main --mode exam --count 40   # 模拟考 40 题
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
trainer/    交互练习端（main.py）
database/   SQLite 数据访问层（schema.sql + store.py）
data/       题库 questions.db + 题目图片 images/（随项目发布）
doc/        进度文档
```

## ⚡ 一键启动（可选)

把下面这行加进 `~/.config/fish/config.fish`，之后在 kitty 里输入 `drive` 即可刷题：

```fish
alias drive "cd ~/Program_Project/drive-lesson-practice; and source .venv/bin/activate.fish; and python -m trainer.main"
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
