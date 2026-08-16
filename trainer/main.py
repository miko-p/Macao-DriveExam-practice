"""M3 练习端：交互式 CLI 刷题（rich）。

用法：
  python -m trainer
  python -m trainer --subject 第一冊
  python -m trainer --mode random --count 20

模式：
  顺序 sequential  从题库按序
  随机 random      随机抽题
  错题 wrong       只练答错的题（错题本）
  统计 stats       显示成绩/章节正确率
  模拟考 exam      随机 N 题，交卷统一批改看总分
（章节通过 --subject 指定）

图片题：题干含 [img:相对路径] 标记。
默认 --view-image auto：在 kitty 终端自动用 icat 真彩内嵌显示，
否则仅提示本地路径。也可用 --view-image ascii(img2txt)、
或指定查看器程序(如 viu/qview)。
"""
from __future__ import annotations

import os
import random
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import ROOT
from database.store import (connect, init_db, get_questions_with_stats,
                            get_wrong_questions, overall_stats,
                            stats_by_subject, subjects)
from trainer.tui import run_question

console = Console()


def _split_img(text: str) -> tuple[str | None, str]:
    """从题干提取 [img:...] 标记，返回 (图片绝对路径, 纯题干)。"""
    m = re.match(r"^\[img:([^\]]+)\]\s*(.*)$", text, re.S)
    if m:
        p = (ROOT / m.group(1))
        return (str(p) if p.exists() else None), m.group(2)
    return None, text


def _in_kitty() -> bool:
    """是否运行在 kitty 终端（真彩内嵌可达）。"""
    if "KITTY_WINDOW_ID" in os.environ:
        return True
    return "kitty" in os.environ.get("TERM", "").lower()


def _show_image(path: str, viewer: str) -> None:
    """显示图片，按 viewer 策略：
    auto  → kitty 真彩内嵌，否则仅提示路径
    kitty → 强制 kitty 内嵌
    ascii → img2txt 内嵌 ASCII
    其他  → 当作外部查看器命令启动"""
    if not path:
        return
    if viewer == "auto":
        if _in_kitty():
            _kitty_icat(path)
        # 非 kitty：仅提示路径（已在上层显示）
        return
    if viewer == "kitty":
        _kitty_icat(path)
        return
    if viewer == "ascii":
        try:
            subprocess.run(["img2txt", "-W", "50", "-H", "15", path])
        except FileNotFoundError:
            console.print(f"[dim]img2txt 不可用，请手动查看: {path}[/dim]")
        return
    # 外部查看器
    try:
        subprocess.Popen(viewer.split() + [path], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        console.print(f"[dim]图片查看器不可用，请手动查看: {path}[/dim]")


def _kitty_icat(path: str) -> None:
    """kitty 内嵌真彩显示（stream 传输，默认按终端宽度缩放）。"""
    # 真实 kitty 交互终端里 /dev/tty 可用，icat 会把真彩图画进终端。
    # stdout/stderr 交给终端即可；文件缺失等硬错误再提示。
    if not Path(path).exists():
        console.print(f"[dim]图片文件不存在: {path}[/dim]")
        return
    try:
        subprocess.run(
            ["kitty", "+kitten", "icat", "--transfer-mode=stream", path])
    except FileNotFoundError:
        console.print(f"[dim]kitty+icat 不可用，请手动查看: {path}[/dim]")


def _print_question(q) -> None:
    img, stem = _split_img(q["stem"])
    header = f"[bold cyan]{q['subject']}[/bold cyan] · {q['source_id']}"
    lines = [f"[bold]{stem}[/bold]"]
    if img:
        lines.append(f"[dim](图片: {img})[/dim]")
    lines.append("")
    import json
    for ch, txt in json.loads(q["choices"]).items():
        lines.append(f"  [bold]{ch}.[/bold] {txt}")
    console.print(Panel("\n".join(lines), title=header, title_align="left",
                        border_style="cyan", padding=(1, 2)))


def _record(conn, q, correct: int, mode: str) -> None:
    conn.execute(
        "INSERT INTO practice_log (qid, correct, mode) VALUES (?,?,?)",
        (q["id"], correct, mode))
    conn.commit()


def _qid_from_user(subject: str, qid: int) -> str:
    """把 (册名, 题号) 转成 source_id，如 ("第一冊", 50) -> "book1_q50"。
    优雅回退：找不到对应册号时返回 book1_q<qid>。"""
    BOOK_N = {"第一冊": 1, "第二冊": 2, "第三冊": 3, "第四冊": 4, "第五冊": 5}
    for cn, n in BOOK_N.items():
        if cn in subject:
            return f"book{n}_q{qid}"
    return f"book1_q{qid}"


def run(subject: str | None, mode: str, count: int | None, viewer: str,
        start_qid: int | None = None) -> None:
    conn = connect()
    init_db(conn)

    # kitty 环境检查：刷题类模式依赖 kitty 真彩显示题目图片
    if mode != "stats" and not _in_kitty():
        console.print("[bold yellow]⚠ 当前不在 kitty 终端。[/bold yellow]")
        console.print("[yellow]本工具面向 kitty 终端设计：题目图片靠 kitty 真彩内嵌\n"
                      "(kitty +kitten icat) 来显示交通标志。其他终端看不到标志图，\n"
                      "仅给出图片路径，做题体验不完整。建议用 kitty 终端运行。[/yellow]")
        if mode == "exam" or not viewer or viewer == "auto":
            console.print("[dim]继续运行（图片题仅提示本地路径）。[/dim]\n")

    # 统计模式
    if mode == "stats":
        show_stats(conn, subject)
        conn.close()
        return

    # 模拟考模式
    if mode == "exam":
        run_exam(conn, subject, count, viewer)
        conn.close()
        return

    # 抽题
    if mode == "random":
        allq = get_questions_with_stats(conn, subject)
        n = min(count, len(allq)) if count else len(allq)
        questions = random.sample(list(allq), n)
    elif mode == "wrong":
        questions = get_wrong_questions(conn, subject)
        if count:
            questions = questions[:count]
    else:  # sequential / practice / learn（册内顺序）
        questions = list(get_questions_with_stats(conn, subject))
        # 题号跳转：从指定 source_id 那题开始（如 practice book 1 50 → 从 book1_q50）
        if start_qid and subject:
            target = _qid_from_user(subject, start_qid)
            for i, q in enumerate(questions):
                if str(q["source_id"]) == target:
                    questions = questions[i:] + questions[:i]  # 从该题开始，继续后面的
                    break
        if count:
            questions = questions[:count]

    if not questions:
        console.print("[yellow]没有可练习的题。[/yellow]")
        if mode == "wrong":
            console.print("[dim]错题重练需要先有答错的记录。[/dim]")
        else:
            console.print("[red]题库为空，请确认 data/questions.db 已就绪。[/red]")
        subj = subjects(conn)
        if subj:
            console.print(f"现有章节: {', '.join(subj)}")
        conn.close()
        sys.exit(1 if mode != "wrong" else 0)

    console.print(f"[bold]开始{f'学习' if mode=='learn' else '练习'}[/bold] · {len(questions)} 题 · 模式 {mode}"
                  + (f" · {subject}" if subject else ""))
    if mode == "learn":
        console.print("[dim]Enter 下一题 · r 上一题 · q 退出 · 正确答案绿色高亮[/dim]\n")
    else:
        console.print("[dim]↑↓ 选择选项 · Enter 确认 · q 退出 · 答错可重答一次[/dim]\n")

    correct = 0
    try:
        if mode == "learn":
            # 学习模式：enter 下一 / r 上一
            i = 0
            n = len(questions)
            while 0 <= i < n:
                res = run_question(questions[i], learn=True)
                if res["quit"]:
                    console.print("\n[dim]已退出学习[/dim]")
                    break
                if res["nav"] == "prev":
                    i -= 1
                else:  # next
                    i += 1
        else:
            for q in questions:
                res = run_question(q)                  # 全屏箭头选择（含错题重答）
                if res["quit"]:
                    console.print("\n[dim]已退出练习[/dim]")
                    break
                ok = 1 if res["correct"] else 0
                _record(conn, q, ok, mode)
                correct += ok
    except KeyboardInterrupt:
        console.print("\n[dim]中断中止[/dim]")

    console.print(Panel(
        f"[bold]完成: {len(questions)} 题, 答对 {correct} ({correct/len(questions)*100:.0f}%)[/bold]",
        border_style="green"))

    conn.close()


def run_exam(conn, subject=None, count=None, viewer="auto") -> None:
    """模拟考：随机抽题、不即时批改、最后统一交卷看总分。"""
    import time
    allq = get_questions_with_stats(conn, subject)
    n = count or min(40, len(allq))
    if n > len(allq):
        n = len(allq)
    questions = random.sample(list(allq), n)
    if not questions:
        console.print("[yellow]题库为空，无法模拟考。[/yellow]")
        return

    console.print(Panel(f"[bold]模拟考试[/bold] · {n} 题"
                        f"{' · '+subject if subject else ''}\n"
                        "[dim]作答后不提示对错，交卷统一批改。[/dim]",
                        border_style="magenta"))
    console.print("[dim]↑↓ 选择选项 · Enter 确认 · q 交卷 · 作答不显示答案[/dim]\n")
    answers: list[tuple] = []
    start = time.time()
    try:
        for q in questions:
            res = run_question(q, exam=True)     # 全屏箭头选择，不显示答案
            if res["quit"]:
                console.print("[dim]提前交卷[/dim]")
                break
            answers.append((q, res["choice"]))
    except KeyboardInterrupt:
        console.print("\n[dim]模拟考中断，按已答部分批改[/dim]")

    elapsed = time.time() - start
    correct = sum(1 for q, a in answers if a == q["answer"])
    total = len(answers)
    # 记录作答（模式 exam）
    for q, a in answers:
        _record(conn, q, 1 if a == q["answer"] else 0, "exam")
    pct = (correct / total * 100) if total else 0
    console.print(Panel(
        f"[bold]交卷[/bold] · 作答 {total}/{n} 题 · 用时 {int(elapsed//60)}分{int(elapsed%60)}秒\n"
        f"[bold]答对 {correct} 题，正确率 {pct:.0f}%[/bold]"
        + (f"\n[dim]通过线 85%（参考正式考试）[/dim]" if pct < 85 else "\n[green]达到 85% 合格线 👍[/green]"),
        border_style="green" if pct >= 85 else "red"))


def show_stats(conn, subject=None) -> None:
    """显示整体/分章节统计。"""
    s = overall_stats(conn, subject)
    header = "成绩统计" + (f" · {subject}" if subject else " · 全部章节")
    table = Table(title=header, expand=True)
    table.add_column("题数", justify="right")
    table.add_column("已作答", justify="right")
    table.add_column("正确率", justify="right")
    table.add_column("错题占比", justify="right")
    got = s["total"] - s["answered"]
    table.add_row(str(s["total"]), str(s["answered"]),
                  f"{s['correct_pct']}%" if s["correct_pct"] is not None else "—",
                  f"{s['wrong_pct']}%" if s["wrong_pct"] is not None else "—")
    console.print(table)

    if not subject:
        console.print("\n[bold]分章节统计[/bold]")
        subj_table = Table(expand=True)
        subj_table.add_column("章节")
        subj_table.add_column("题数", justify="right")
        subj_table.add_column("已作答", justify="right")
        subj_table.add_column("正确率", justify="right")
        for row in stats_by_subject(conn):
            subj_table.add_row(
                row["subject"], str(row["total"]), str(row["answered"]),
                f"{row['accuracy']}%" if row["accuracy"] is not None else "—")
        console.print(subj_table)


@click.command()
@click.option("--subject", type=str, default=None,
              help="章节（空=全部）")
@click.option("--mode", type=click.Choice(["sequential", "random", "wrong", "stats", "exam"]),
              default="sequential", help="练习模式")
@click.option("--count", type=int, default=None, help="题数（默认全部）")
@click.option("--view-image", type=str, default="auto",
              help="图片显示: auto(kitty真彩自动,默认)/kitty/ascii(img2txt)/外部程序")
def main(subject, mode, count, view_image):
    run(subject, mode, count, view_image)


if __name__ == "__main__":
    main()
