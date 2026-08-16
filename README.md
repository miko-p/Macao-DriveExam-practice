# 驾考题库练习工具

一个本地的驾考笔试题库练习工具：内置题库（五册共 647 题 + 242 幅标志/图表图片），在终端里交互式刷题、统计成绩、模拟考试。全程离线，无网络依赖。

> 说明：仅作个人练习使用。

## 功能

- **本地题库**：内置五册驾考笔试题库（647 题），按册分类（第一冊~第五冊），含 242 幅题目图片。
- **终端刷题**：顺序 / 随机 / 章节 / 错题重练。
- **模拟考**：随机抽题、统一交卷批改、及格线提示。
- **成绩统计**：整体与分章节正确率、错题本。

## 环境要求

- Python 3.10+（在 3.14 上开发测试）

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate.fish          # bash: source .venv/bin/activate
pip install -r requirements.txt
```

## 使用

```
用法：python -m trainer.main [选项]

选项：
  --subject 章节     只练某个章节（如 第一冊）
  --mode 模式        sequential(顺序,默认) | random(随机) | wrong(错题重练)
                     | stats(成绩统计) | exam(模拟考)
  --count 数量       题数（默认全部）
  --view-image 方式   auto(默认)/kitty/ascii/<外部程序>
```

示例：

```bash
python -m trainer.main                            # 全部，顺序刷题
python -m trainer.main --subject 第一冊           # 只练第一册
python -m trainer.main --mode random --count 20   # 随机抽 20 题
python -m trainer.main --mode wrong               # 错题重练
python -m trainer.main --mode stats               # 成绩统计
python -m trainer.main --mode exam --count 40     # 模拟考 40 题
```

作答键：
- 输入 `A` / `B` / `C` / `D` 作答 → 立即显示对错与正确答案。
- `s` 跳过（计入错题）。
- `q` / `quit` 退出，进度自动保存。

图片题显示：默认 `--view-image auto`——在 **kitty 终端**自动用真彩内嵌显示标志图；
非 kitty 终端仅提示本地图片路径。也可 `--view-image ascii` 用 img2txt，或指定外部程序（如 `viu`/`qview`）。

## 数据

- 题库：`data/questions.db`（SQLite，`questions` 题目表 + `practice_log` 作答流水表）。
- 题目图片：`data/images/`。
- 正确率、错题本、分章节统计均基于 `practice_log`。

## 目录结构

```
database/   SQLite 数据访问层（schema + store）
trainer/    交互练习端
doc/        进度文档
data/       题库数据库与图片（随项目发布）
```

## 快捷方式（可选）

fish 中一键启动刷题，可加进 `~/.config/fish/config.fish`：

```fish
alias drive "cd ~/Program_Project/drive-lesson-practice; and source .venv/bin/activate.fish; and python -m trainer.main"
```

## 进度

- 架构：`BLUEPRINT.md`
- 阶段记录：`doc/M3-status.md` ~ `doc/M5-status.md`

本工具仍在演进中，欢迎反馈；代码以 MIT 许可开源。
