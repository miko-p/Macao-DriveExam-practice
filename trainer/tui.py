"""TUI 刷题界面：图片在上(kitty icat 真彩) + 题目选项在下(箭头选择)。

布局：三区各带边框，垂直堆叠，全部居中：
  ┌──────────图片区──────────┐
  │      (icat 真彩标志图)    │
  └──────────────────────────┘
  ┌──────────题目区──────────┐
  │  第一冊 · book1_q5       │
  │  圖五標誌表示:            │
  └──────────────────────────┘
  ┌──────────选项区──────────┐
  │   A. 禁止駛入   ← 高亮     │
  │   B. 十字交叉            │
  │   C. 禁止停車            │
  │   D. 施工               │
  └──────────────────────────┘
    ↑↓ 选择 · Enter 确认 · q 退出
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from config import ROOT

IMG_W = 24      # 图片渲染目标宽（字符）
IMG_H = 14      # 图片渲染目标高（字符）
BOX_W = 44      # 题目/选项边框内容宽度（居中后实际更宽）

# ---------- 图片 ----------

def _in_kitty() -> bool:
    return "KITTY_WINDOW_ID" in os.environ or "kitty" in os.environ.get("TERM", "").lower()


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


def _term_width() -> int:
    try:
        return shutil.get_terminal_size().columns or 80
    except Exception:
        return 80


def _render_image_centered(path: str) -> int:
    """居中渲染真彩图片，返回图片占行数（含上下留白）。"""
    if not path or not Path(path).exists():
        return 0
    tw = _term_width()
    left = max(1, (tw - IMG_W) // 2)     # 水平居中 col
    top = 1                               # 顶部行
    try:
        subprocess.run(
            ["kitty", "+kitten", "icat", "--transfer-mode=stream",
             "--place", f"{IMG_W}x{IMG_H}@{left}x{top}", str(path)],
            check=False)
    except FileNotFoundError:
        return 0
    return IMG_H


# ---------- 键盘 ----------

_TERMIOS_SAVED = None


def _enter_raw():
    import termios, tty
    global _TERMIOS_SAVED
    _TERMIOS_SAVED = termios.tcgetattr(sys.stdin.fileno())
    tty.setraw(sys.stdin.fileno())


def _exit_raw():
    import termios
    global _TERMIOS_SAVED
    if _TERMIOS_SAVED:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, _TERMIOS_SAVED)


def _read_key() -> str:
    ch = sys.stdin.read(1)
    if ch == "\x1b":
        nxt = sys.stdin.read(2)
        return {"[A": "up", "[B": "down", "[C": "right", "[D": "left"}.get(nxt, "esc")
    return ch


# ---------- ANSI ----------

_C = "\x1b["
_RST = f"{_C}0m"
_TITLE = f"{_C}1;36m"
_SEL = f"{_C}48;2;68;68;170;38;2;255;255;255m"
_OKTXT = f"{_C}32m"
_ERRBG = f"{_C}48;2;136;34;34;38;2;255;255;255m"
_GRAY = f"{_C}90m"
_BOX = f"{_C}36m"       # 边框青色
_FBOK = f"{_C}1;32m"
_FBERR = f"{_C}1;31m"


def _clr() -> str:
    return f"{_C}H{_C}2J"   # 清屏回家


def _center(text: str, width: int) -> str:
    """把文本居中到 width 宽。"""
    vis = len(text)
    if vis >= width:
        return text
    left = (width - vis) // 2
    return " " * left + text


def _box(lines: list[str], width: int) -> list[str]:
    """给若干行加边框，返回渲染行。"""
    # 内容行宽校正（取最宽）
    cw = max(len(l) for l in lines) if lines else 0
    cw = min(cw, width)
    out = ["┌" + "─" * (cw + 2) + "┐"]
    for l in lines:
        out.append("│ " + l.ljust(cw) + " │")
    out.append("└" + "─" * (cw + 2) + "┘")
    return out


# ---------- 渲染 ----------

def _render_all(q, sel, answered, final_correct, first_wrong, exam,
                box_w: int):
    """生成题目+选项区文字行（居中）。返回行列表。"""
    correct = q["answer"] or ""
    choices = _choices_dict(q)
    letters = list(choices.keys())

    # 题目区
    subj = f"{_TITLE}{q['subject']} · {q['source_id']}{_RST}"
    _, stem = _split_img(q["stem"])
    title_lines = _box([subj, stem, ""], box_w)

    # 选项区
    opt_lines = []
    for idx, ch in enumerate(letters):
        txt = choices[ch]
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
        opt_lines.append(f"{cell}{ch}. {txt}{_RST}")
    opt_box = _box(opt_lines, box_w)

    # 反馈与帮助
    fb = ""
    if not exam and answered:
        fb = f"{_FBOK}✓ 正确{_RST}" if final_correct else f"{_FBERR}✗ 答错（请重答）{_RST}"
    elif exam and answered:
        fb = f"{_C}1;36m已作答{_RST}"
    help_txt = (" ↑↓ 选择 · Enter 确认 · q 退出") if not exam else " ↑↓ 选择 · Enter 确认 · q 交卷"
    if not exam and answered and not final_correct:
        help_txt = " ↑↓ 选择要重答的选项 · Enter 确认 · q 退出"

    # 组装全部文字行（每行居中到满宽）
    tw = _term_width()
    all_lines = []
    for blk in (title_lines, opt_box):
        for ln in blk:
            all_lines.append(_center(ln, tw))
    if fb:
        all_lines.append(_center(fb, tw))
    all_lines.append(_center(help_txt, tw))
    return all_lines


# 简化：把"是否首绘"交给 run_question，这里只生成行

def _draw_text(lines: list[str], first: bool) -> None:
    """绘制文字。first=True 时直接写（光标在图片底）；否则先回卷清屏再写。"""
    n = len(lines)
    if not first:
        sys.stdout.write(f"{_C}{n}A")       # 回卷到文字区顶部
        sys.stdout.write(f"{_C}0J")          # 清文字区
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    sys.stdout.flush()


def run_question(q, exam: bool = False) -> dict:
    result = {"correct": False, "first_wrong": False, "quit": False, "choice": ""}

    img, _ = _split_img(q["stem"])
    letters = list(_choices_dict(q).keys())
    if not letters:
        return result

    sys.stdout.write(_clr())
    sys.stdout.flush()
    img_rows = 0
    if img and _in_kitty():
        img_rows = _render_image_centered(img)   # 图片居中在上
        # 图片下方留白
        sys.stdout.write("\n" * (img_rows - 1))
        sys.stdout.flush()

    sel, answered, final_correct, first_wrong = 0, False, False, False
    box_w = IMG_W + 8
    first = True

    def redraw(force_first=False):
        nonlocal first
        lines = _render_all(q, sel, answered, final_correct, first_wrong,
                            exam, box_w)
        _draw_text(lines, first or force_first)
        first = False

    redraw(force_first=True)

    try:
        _enter_raw()
        while True:
            key = _read_key()
            if key == "up" and not final_correct:
                sel = (sel - 1) % len(letters); redraw()
            elif key == "down" and not final_correct:
                sel = (sel + 1) % len(letters); redraw()
            elif key == "q":
                result["quit"] = True; break
            elif key in ("\r", "\n"):
                letter = letters[sel]
                if not answered:
                    if exam:
                        result["choice"] = letter
                        result["correct"] = (letter == q["answer"])
                        break
                    if letter == q["answer"]:
                        final_correct = True; answered = True
                        result["correct"] = True
                        redraw(); break
                    else:
                        first_wrong = True; answered = True
                        result["first_wrong"] = True
                        redraw()
                else:
                    if letter != q["answer"]:
                        result["first_wrong"] = True
                    result["correct"] = False
                    break
    except (KeyboardInterrupt, EOFError):
        result["quit"] = True
    finally:
        _exit_raw()
        sys.stdout.write("\n\x1b[?25h")
        sys.stdout.flush()
    return result
