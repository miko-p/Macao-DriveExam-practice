"""MDrivePractice 交互式命令界面（类 Hermes 全屏 TUI）。

启动后清屏显示标题，底部输入框可输入命令（两级补全：先主命令，主命令 + 空格后再 Tab 补子选项），
输入命令进入对应练习模式，完成后返回此界面。

用法：
  python -m trainer.shell
  （或 fish alias MDrivePractice）
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, date
from typing import Optional

from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory

from trainer.main import run, Console  # noqa: F401
from trainer.logger import get_logger
from config import IMAGE_DIR, EXAM_DATE_FILE

console = Console()
log = get_logger("shell")

# 主命令（仅英文）
MAIN_COMMANDS = [
    "start", "random", "wrong", "exam", "stats",
    "practice", "learn",
    "help", "clear", "quit", "edata",
]

# 子选项：主命令 + 空格 后再 Tab 可补全的参数
SUB_OPTIONS = {
    "practice": ["book 1", "book 2", "book 3", "book 4", "book 5"],
    "learn":    ["book 1", "book 2", "book 3", "book 4", "book 5"],
    "edata":    ["<2026-12-31>"],
}

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

    cl = _exam_countdown_line()          # 启动标题下方显示考试倒计时
    if cl is not None:
        console.print(cl)
        console.print("[bold cyan]──────────────────────────────[/bold cyan]")

    console.print("[bold]在底部输入命令开始刷题[/bold] "
                  "(输入主命令后按空格再 Tab 补子选项，help 查看全部命令)\n")


def _get_modes_help() -> str:
    return """\
[bold cyan]MDrivePractice 命令[/bold cyan]

[bold cyan]模式[/bold cyan]
  start [N]               顺序刷 N 题（默认全部）
  random [--count N]      随机抽 N 题（默认全部）
  wrong [--count N]       错题重练 N 题
  exam [--count N]        模拟考 N 题（默认40），统一批改
  stats                   查看成绩统计

[bold cyan]答题练习[/bold cyan]
  practice book 1 [题号]   练习第一册（可指定题号开始）
  practice book 2 [题号]   （1-5 册）

[bold cyan]学习浏览[/bold cyan]
  learn book 1 [题号]      浏览第一册：正确答案绿色高亮，
                           Enter 下一题 · r 上一题

[bold cyan]其他[/bold cyan]
  help                    显示帮助
  clear                   重显标题
  quit                    退出程序
  edata 2026-08-18        考试倒计时：输入未来日期，大字显示剩余天数
"""


class _TwoLevelCompleter(Completer):
    """两级补全：先补主命令，主命令 + 空格后再补子选项。"""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        parts = text.split()
        word = parts[-1] if parts else ""
        # 已输入主命令 + 空格 → 补该命令的子选项
        if parts:
            main = parts[0].lower()
            if len(parts) >= 2 or text.endswith(" "):
                subs = SUB_OPTIONS.get(main)
                if subs:
                    for s in subs:
                        yield Completion(s, start_position=-len(word))
                    return
        # 否则补主命令（前缀匹配）
        for c in sort_main():
            if c.startswith(word):
                yield Completion(c, start_position=-len(word))


def sort_main() -> list[str]:
    """主命令排序：练习模式在前，其余按字母序。"""
    return sorted(MAIN_COMMANDS,
                  key=lambda x: (0 if x in ("start", "random", "wrong",
                                            "exam", "stats") else 1, x))


def _make_completer() -> Completer:
    return _TwoLevelCompleter()


def _parse_date(s: str):
    """解析 YYYY-MM-DD 且须为未来日期(>今天)；否则返回 None。"""
    try:
        d = datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None
    if d <= date.today():
        return None
    return d


def _parse_command(raw: str):
    """解析命令，返回 (action, subject, count, start_qid)；无法识别的返回 None。"""
    raw = raw.strip()
    if not raw:
        return None
    parts = raw.split()
    cmd0 = parts[0].lower()

    # edata：倒计时命令 edata YYYY-MM-DD（要求未来日期）
    if cmd0 == "edata":
        if len(parts) >= 2:
            d = _parse_date(parts[1])
            if d:
                return ("__edata__", parts[1], None, None)
            return ("__edata_err__", "日期格式应为 YYYY-MM-DD，且需大于今天（如 2026-08-18）", None, None)
        return ("__edata_err__", "用法：edata YYYY-MM-DD（如 edata 2026-08-18）", None, None)

    # 答题/学习：practice/learn book <册> [题号]（不能先做 count 提取，会误吞题号）
    if cmd0 in ("practice", "learn"):
        mode = "practice" if cmd0 == "practice" else "learn"
        # 期望: practice book <N> [qid]
        if len(parts) >= 3 and parts[1].lower() == "book":
            book = _normalize_book(parts[2])
            if book:
                start_qid = None
                if len(parts) >= 4 and parts[3].isdigit():
                    start_qid = int(parts[3])
                return (mode, book, None, start_qid)
        # 也可: practice <N> [qid]
        if len(parts) >= 2:
            book = _normalize_book(parts[1])
            if book:
                start_qid = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else None
                return (mode, book, None, start_qid)
        return None

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

    # 模式命令（仅英文）
    if cmd == "start":
        return ("sequential", None, count, None)
    if cmd == "random":
        return ("random", None, count, None)
    if cmd == "wrong":
        return ("wrong", None, count, None)
    if cmd == "exam":
        return ("exam", None, count, None)
    if cmd == "stats":
        return ("stats", None, None, None)

    # 控制命令
    if cmd in ("help", "clear", "quit"):
        return (f"__{cmd}__", None, None, None)

    return None  # 未知


def _normalize_book(s: str) -> Optional[str]:
    """把 1/第一冊/第一册 等统一成 繁體冊名；非册名返回 None。"""
    NUM = {"1": "第一冊", "2": "第二冊", "3": "第三冊",
           "4": "第四冊", "5": "第五冊", "一": "第一冊", "二": "第二冊",
           "三": "第三冊", "四": "第四冊", "五": "第五冊"}
    S = s.strip()
    if S in NUM:
        return NUM[S]
    for cn in ("第一冊", "第二冊", "第三冊", "第四冊", "第五冊"):
        if cn in S or cn.replace("冊", "册") in S:
            return cn
    return None


# ---------- 倒计时 edata ----------

_BIG_DIGITS = {
    "0": ["███", "█ █", "█ █", "█ █", "███"],
    "1": [" █ ", "██ ", " █ ", " █ ", "███"],
    "2": ["███", "  █", "███", "█  ", "███"],
    "3": ["███", "  █", "███", "  █", "███"],
    "4": ["█ █", "█ █", "███", "  █", "  █"],
    "5": ["███", "█  ", "███", "  █", "███"],
    "6": ["███", "█  ", "███", "█ █", "███"],
    "7": ["███", "  █", "  █", "  █", "  █"],
    "8": ["███", "█ █", "███", "█ █", "███"],
    "9": ["███", "█ █", "███", "  █", "███"],
}


def _big_num(n: int) -> list[str]:
    """把天数渲染成 5 行块状大字，返回行列表。"""
    s = str(max(0, n))
    lines = ["" for _ in range(5)]
    for i, ch in enumerate(s):
        d = _BIG_DIGITS.get(ch)
        if not d:
            continue
        for r in range(5):
            lines[r] += d[r] + "  "      # 数字间隔
    return lines


def _load_exam_date():
    """读取持久化的考试日期；无效/无则返回 None。"""
    try:
        s = EXAM_DATE_FILE.read_text(encoding="utf-8").strip()
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _save_exam_date(date_str: str) -> None:
    try:
        EXAM_DATE_FILE.parent.mkdir(exist_ok=True)
        EXAM_DATE_FILE.write_text(date_str, encoding="utf-8")
    except Exception:
        pass


def _exam_countdown_line():
    """生成启动标题下方的紧凑倒计时行(数字黄色粗体突出)；无显示返回 None。"""
    d = _load_exam_date()
    if not d or d <= date.today():
        return None
    days = (d - date.today()).days
    from rich.text import Text as _T
    t = _T()
    t.append("  🗓  距离考试还有 ", style="bold")
    t.append(str(days), style="bold yellow")
    t.append(" 天", style="bold")
    t.append(f"  （考试日 {d.isoformat()}）", style="dim")
    return t


def _countdown_text(days: int, date_str: str | None = None):
    """生成倒计时渲染对象（rich Text，分段着色，避免 markup 配对问题）。

    date_str 为 None 时不附日期行（供启动标题下方用）。
    """
    from rich.text import Text as _T
    bw = max(30, shutil.get_terminal_size().columns or 80)

    text = _T()
    text.append("\n")
    text.append("═" * min(bw, 56) + "\n\n", style="bold cyan")
    text.append("距 离 考 试 还 有\n\n", style="bold")
    # 大字数字（居中，黄底白字粗体突出）
    big = _big_num(days)
    for row in big:
        pad = max(0, (bw - len(row)) // 2)
        cell = row.ljust(24)
        text.append(" " * pad)
        text.append(f"  {cell}  ", style="bold white on yellow")
        text.append("\n")
    text.append("\n")
    if date_str:
        text.append(f"  考试日期：{date_str}  ·  剩余 {days} 天\n", style="cyan")
        text.append("＝" * min(bw, 56) + "\n", style="bold cyan")
    return text


def _show_countdown(date_str: str) -> None:
    """清屏居中显示倒计时大字，按键后返回（edata 命令）。"""
    from datetime import datetime as _dt
    target = _dt.strptime(date_str, "%Y-%m-%d").date()
    days = (target - date.today()).days

    _clear()
    t = _countdown_text(days, date_str)
    t.append("\n按任意键返回命令界面…", style="dim")
    console.print(t)

    # 等待按键返回
    try:
        import termios, tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        raw = sys.stdin.read(1)
        if raw == "\x1b":
            sys.stdin.read(2)
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        input()


def run_shell() -> None:
    """启动交互式命令界面。"""
    log.info("MDrivePractice 命令界面启动")
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
        except Exception:
            log.exception("命令界面运行异常")
            break

        cmd = _parse_command(raw)
        if cmd is None:
            if raw.strip():
                log.info("未识别命令: %r", raw)
                console.print("[yellow]未识别的命令，输入 [bold]help[/bold] 查看帮助。[/yellow]")
            continue

        action, subject, count, start_qid = cmd
        if action == "__help__":
            console.print(_get_modes_help())
            continue
        if action == "__clear__":
            _show_banner()
            continue
        if action == "__quit__":
            console.print("[bold green]✋ 再见，刷题愉快！[/bold green]")
            break
        if action == "__edata__":
            ds = subject or ""
            _save_exam_date(ds)               # 持久化考试日期，启动时在标题下显示
            _show_countdown(ds)
            _show_banner()
            continue
        if action == "__edata_err__":
            console.print(f"[yellow]{subject}[/yellow]")
            continue

        # stats 简单输出：不清屏、直接空一行显示统计，保留命令界面上下文
        if action == "stats":
            console.print("")
            run(subject=None, mode="stats", count=None, viewer="auto")
            console.print("")
            continue

        # 进入模式：先清屏
        _clear()
        log.info("执行命令 action=%s subject=%r count=%r start_qid=%r", action, subject, count, start_qid)
        try:
            run(subject=subject, mode=action, count=count,
                start_qid=start_qid, viewer="auto")
        except SystemExit:
            pass
        except Exception:
            log.exception("模式执行异常 action=%s", action)
        # 刷题结束返回命令界面
        console.print("\n[bold cyan]┌──────────────────────────────────┐[/bold cyan]")
        console.print("[bold cyan]│ 已完成本次练习，返回命令界面     │[/bold cyan]")
        console.print("[bold cyan]└──────────────────────────────────┘[/bold cyan]")
        _show_banner()


def main() -> None:
    run_shell()


if __name__ == "__main__":
    main()
