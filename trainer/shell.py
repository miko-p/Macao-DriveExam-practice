"""MDrivePractice 交互式命令界面（类 Hermes 全屏 TUI）。

启动后清屏显示标题，底部输入框可输入命令（fuzzy 下拉补全），
输入命令进入对应练习模式，完成后返回此界面。

用法：
  python -m trainer.shell
  （或 fish alias MDrivePractice）
"""
from __future__ import annotations

import sys
from typing import Optional

from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings

from trainer.main import run, Console  # noqa: F401
from config import IMAGE_DIR

console = Console()

# 命令集（含常用的中文别名和选项，用于 fuzzy 补全）
COMMANDS = [
    # 模式命令
    "start", "顺序",
    "random", "随机",
    "exam", "模拟考", "考试",
    "wrong", "错题",
    "stats", "统计",
    # 章节
    "book 第一冊", "book 第二冊", "book 第三冊", "book 第四冊", "book 第五冊",
    "第一冊", "第二冊", "第三冊", "第四冊", "第五冊",
    "chapter",
    # 其他
    "help", "帮助", "说明",
    "clear", "清屏",
    "quit", "exit", "退出",
]

BANNER = r"""
  __  __   _____     _            _      _____                     _       _
 |  \/  | |  __ \   (_)          | |    |  __ \                   (_)     (_)
 | \  / | | |  | |   _  _ _   __ _| |    | |  | |  __ _  _ __ ___  _  ___  _  ___
 | |\/| | | |  | |  | || | | / _` | |    | |  | | / _` || '_ ` _ \| |/ __|| |/ _ \
 | |  | | | |__/ |  | || | | | (_| | |    | |__| /| (_| || | | | | | |\__ \| |  __/
 |_|  |_| |_____/   |_||_|  |_|\__,_|_|    |_____/ \__,_||_| |_| |_||_||___/|_|\___|
  澳門駕考題庫練習工具 · Macao Drive Exam Practice
"""


def _clear() -> None:
    console.clear()


def _show_banner() -> None:
    _clear()
    console.print(BANNER, style="bold cyan")

    console.print("[bold]在底部输入命令开始刷题[/bold] "
                  "(Tab/方向键 补全，输入 'help' 查看全部命令)\n")


def _get_modes_help() -> str:
    return """\
[bold cyan]MDrivePractice 命令[/bold cyan]

[bold cyan]模式[/bold]
  start | 顺序 [N]           顺序刷 N 题（默认全部）
  random | 随机 [--count N]   随机抽 N 题（默认全部）
  wrong | 错题 [--count N]    错题重练 N 题
  exam | 模拟考 [--count N]   模拟考 N 题（默认40），统一批改
  stats | 统计                查看成绩统计

[bold cyan]章节[/bold]
  book 第一冊                只练某一册
  也可直接输入册名：第一冊 / 第二冊 ...

[bold cyan]其他[/bold]
  help | 帮助                 显示帮助
  clear | 清屏                 重显标题
  quit | exit | 退出           退出程序
"""


def _make_completer() -> FuzzyCompleter:
    return FuzzyCompleter(WordCompleter(COMMANDS, ignore_case=True,
                                        match_middle=True))


def _parse_command(raw: str):
    """解析命令，返回 (mode, subject, count)；无法识别的返回 None。"""
    raw = raw.strip()
    if not raw:
        return None
    parts = raw.split()

    # 提取数量参数：--count N 或 结尾数字
    count = None
    for i, p in enumerate(parts):
        if p.lower() == "--count" and i + 1 < len(parts) and parts[i + 1].isdigit():
            count = int(parts[i + 1])
            parts = parts[:i] + parts[i + 2:]
            break
    if count is None and parts and parts[-1].isdigit():
        count = int(parts[-1])
        parts = parts[:-1]

    if not parts:
        return None
    cmd = parts[0].lower()
    subject = parts[1] if len(parts) > 1 else None

    # 模式命令
    if cmd in ("start", "顺序"):
        return ("sequential", None, count)
    if cmd in ("random", "随机"):
        return ("random", None, count)
    if cmd in ("wrong", "错题"):
        return ("wrong", None, count)
    if cmd in ("exam", "模拟考", "考试"):
        return ("exam", None, count)
    if cmd in ("stats", "统计"):
        return ("stats", None, None)

    # 章节命令：book 第一冊 / 直接册名
    if cmd in ("book", "chapter") and subject:
        cn = _normalize_book(subject) or subject
        return ("sequential", cn, count)
    if subject:  # 如: 第X册 作为 book 的主题
        cn = _normalize_book(subject)
        if cn:
            return ("sequential", cn, count)
    # 直接用册名做命令 (第一冊 单独)
    cn = _normalize_book(parts[0])
    if cn:
        return ("sequential", cn, count)

    # 控制命令
    if cmd in ("help", "帮助", "说明"):
        return ("__help__", None, None)
    if cmd in ("clear", "清屏"):
        return ("__clear__", None, None)
    if cmd in ("quit", "exit", "退出"):
        return ("__quit__", None, None)

    return None  # 未知


def _normalize_book(s: str) -> Optional[str]:
    """把 第一冊/第一册/第 X 冊 等统一成 繁體冊名；非册名返回 None。"""
    for cn in ("第一冊", "第二冊", "第三冊", "第四冊", "第五冊"):
        if cn in s or cn.replace("冊", "册") in s:
            return cn
    return None


def run_shell() -> None:
    """启动交互式命令界面。"""
    _show_banner()
    history = InMemoryHistory()
    completer = _make_completer()

    while True:
        try:
            raw = prompt(
                HTML("<b><ansicyan>MDrivePractice></ansicyan></b> "),
                completer=completer,
                history=history,
                style=None,
                key_bindings=None,
                bottom_toolbar="MDrivePractice · 输入命令刷题  |  Tab 补全 · quit 退出",
            )
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]再见！[/dim]")
            break

        cmd = _parse_command(raw)
        if cmd is None:
            if raw.strip():
                console.print("[yellow]未识别的命令，输入 [bold]help[/bold] 查看帮助。[/yellow]")
            continue

        action, subject, count = cmd
        if action == "__help__":
            console.print(_get_modes_help())
            continue
        if action == "__clear__":
            _show_banner()
            continue
        if action == "__quit__":
            console.print("[bold green]✋ 再见，刷题愉快！[/bold green]")
            break

        # 进入模式：先清屏
        _clear()
        try:
            run(subject=subject, mode=action, count=count, viewer="auto")
        except SystemExit:
            pass
        # 刷题结束返回命令界面
        console.print("\n[bold cyan]┌──────────────────────────────────┐[/bold cyan]")
        console.print("[bold cyan]│ 已完成本次练习，返回命令界面     │[/bold cyan]")
        console.print("[bold cyan]└──────────────────────────────────┘[/bold cyan]")
        _show_banner()


def main() -> None:
    run_shell()


if __name__ == "__main__":
    main()
