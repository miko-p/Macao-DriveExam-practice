"""TUI 刷题界面：图片在上(kitty icat 真彩整图) + 题目选项在下(箭头选择)。

纯终端方案（不切 alternate screen），保证 icat 真彩图片清晰且不被清除：
  · 先用 kitty icat 渲染真彩原图到屏幕顶部
  · 题目 + 选项打印在下方
  · ↑/↓ 移动选中项(ANSI 高亮)，Enter 确认，q 退出
  · 答错给一次重答机会（正确答案高亮），再错才下一题
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from config import ROOT

IMG_W = 32   # icat 渲染图片的目标字符宽（越宽越清晰）
IMG_H = 18   # 图片目标高


# ---------- 图片渲染 ----------

def _in_kitty() -> bool:
    if "KITTY_WINDOW_ID" in os.environ:
        return True
    return "kitty" in os.environ.get("TERM", "").lower()


def _split_img(text: str) -> tuple[str | None, str]:
    m = re.match(r"^\[img:([^\]]+)\]\s*(.*)$", text, re.S)
    if m:
        p = ROOT / m.group(1)
        return (str(p) if p.exists() else None), m.group(2)
    return None, text


def _choices_dict(q) -> dict:
    try:
        if hasattr(q, "keys") and "choices" in q.keys():
            ch = q["choices"]
        elif isinstance(q, dict) and "choices" in q:
            ch = q["choices"]
        else:
            ch = None
    except Exception:
        ch = None
    try:
        return json.loads(ch) if ch else {}
    except Exception:
        return {}


def _render_image(path: str) -> int:
    """用 kitty icat 渲染真彩图到当前屏幕，返回图片占用的行数。"""
    if not path or not Path(path).exists():
        return 0
    try:
        # 指定尺寸让图片不至于巨大，整宽渲染在当前屏幕（从顶部附近开始）
        subprocess.run(
            ["kitty", "+kitten", "icat", "--transfer-mode=stream",
             "--scale-up", "--place", f"{IMG_W}x{IMG_H}@3x1", str(path)],
            check=False)
        return IMG_H
    except FileNotFoundError:
        return 0


# ---------- 键盘读取 ----------

_TERMIOS_SAVED = None


def _enter_raw() -> None:
    import termios, tty
    global _TERMIOS_SAVED
    _TERMIOS_SAVED = termios.tcgetattr(sys.stdin.fileno())
    tty.setraw(sys.stdin.fileno())


def _exit_raw() -> None:
    import termios
    global _TERMIOS_SAVED
    if _TERMIOS_SAVED:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, _TERMIOS_SAVED)


def _read_key() -> str:
    """读取一个按键。返回 up/down/enter/m/ 或字符；ESC 序列解析。"""
    ch = sys.stdin.read(1)
    if ch == "\x1b":
        nxt = sys.stdin.read(2)
        return {"[A": "up", "[B": "down", "[C": "right", "[D": "left"}.get(nxt, "esc")
    return ch  # '\r'/'\n'->enter, 'q','a'...'


# ---------- ANSI ----------

_C = "\x1b["
_RST = f"{_C}0m"
_TITLE = f"{_C}1;36m"
_SEL = f"{_C}48;2;68;68;170;38;2;255;255;255m"
_OKTXT = f"{_C}32m"
_ERRBG = f"{_C}48;2;136;34;34;38;2;255;255;255m"
_GRAY = f"{_C}90m"


def _clear_screen() -> None:
    sys.stdout.write(f"{_C}2J{_C}H")
    sys.stdout.flush()


def _move(row: int, col: int = 1) -> None:
    sys.stdout.write(f"{_C}{row};{col}H")
    sys.stdout.flush()


# ---------- 渲染 ----------

def _render_all(q, sel: int, answered: bool, final_correct: bool,
                first_wrong: bool, exam: bool) -> int:
    """渲染整屏（题目+选项），返回选项区起始行。图片已由外部渲染在顶部不动。"""
    img, stem = _split_img(q["stem"])
    opt_start_row = IMG_H + 3          # 图片下方留几行
    _move(opt_start_row)
    sys.stdout.write(f"{_C}0J")        # 清空从当前位置到屏幕末尾（保留上方图片）
    sys.stdout.write(f"{_TITLE}{q['subject']} · {q['source_id']}{_RST}\n")
    sys.stdout.write(f"{stem}\n\n")
    correct = q["answer"] or ""
    choices = _choices_dict(q)
    letters = list(choices.keys())
    for idx, ch in enumerate(letters):
        txt = choices[ch]
        line = f"  {ch}. {txt}"
        cell = _RST
        if not final_correct:
            if idx == sel:
                cell = _SEL
            if answered and not exam and ch == correct:
                cell = _OKTXT
            if answered and first_wrong and idx == sel and ch != correct:
                cell = _ERRBG
        else:
            if ch == correct:
                cell = _OKTXT
            elif idx == sel:
                cell = _GRAY
        sys.stdout.write(f"{cell}{line}{_RST}\n")
    # 反馈
    sys.stdout.write("\n")
    if not exam and answered:
        if final_correct:
            sys.stdout.write(f"{_C}1;32m✓ 正确{_RST}\n")
        else:
            sys.stdout.write(f"{_C}1;31m✗ 答错（请重答，正确答案已高亮）{_RST}\n")
    elif exam and answered:
        sys.stdout.write(f"{_C}1;36m已作答{_RST}\n")
    # 帮助
    if exam:
        hint = " ↑↓ 选择 · Enter 确认 · q 交卷" if not answered else " ← 继续"
    else:
        hint = (" ↑↓ 选择要重答的选项 · Enter 确认 · q 退出"
                if answered and not final_correct else " ↑↓ 选择 · Enter 确认 · q 退出")
    sys.stdout.write(hint)
    sys.stdout.flush()
    return opt_start_row


def run_question(q, exam: bool = False) -> dict:
    """运行一题：图片在上(icat真彩) + 题目选项在下(箭头选择)。"""
    result = {"correct": False, "first_wrong": False, "quit": False, "choice": ""}

    img, _ = _split_img(q["stem"])
    letters = list(_choices_dict(q).keys())
    if not letters:
        return result

    _clear_screen()
    if img:
        _render_image(img)         # 真彩图（顶部，保持不动）

    sel = 0
    answered = False
    final_correct = False
    first_wrong = False
    _render_all(q, sel, answered, final_correct, first_wrong, exam)

    try:
        _enter_raw()
        while True:
            key = _read_key()
            if key == "up":
                if not final_correct:
                    sel = (sel - 1) % len(letters)
                    _render_all(q, sel, answered, final_correct, first_wrong, exam)
            elif key == "down":
                if not final_correct:
                    sel = (sel + 1) % len(letters)
                    _render_all(q, sel, answered, final_correct, first_wrong, exam)
            elif key == "q":
                result["quit"] = True
                break
            elif key in ("\r", "\n"):
                letter = letters[sel]
                if not answered:
                    if exam:
                        result["choice"] = letter
                        result["correct"] = (letter == q["answer"])
                        break
                    if letter == q["answer"]:
                        final_correct = True
                        answered = True
                        result["correct"] = True
                        _render_all(q, sel, answered, final_correct, first_wrong, exam)
                        break
                    else:
                        first_wrong = True
                        answered = True
                        result["first_wrong"] = True
                        _render_all(q, sel, answered, final_correct, first_wrong, exam)
                else:
                    # 重答
                    if letter != q["answer"]:
                        result["first_wrong"] = True
                    result["correct"] = False
                    break
    except (KeyboardInterrupt, EOFError):
        result["quit"] = True
    finally:
        _exit_raw()
        sys.stdout.write("\n\x1b[?25h")   # 恢复光标 + 换行
        sys.stdout.flush()
    return result
