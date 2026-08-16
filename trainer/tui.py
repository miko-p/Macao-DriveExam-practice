"""TUI 刷题界面：图片居中在上(icat真彩) + 题目选项靠左(蓝色边框) + 箭头增量高亮。

可靠性：图片只渲染一次；箭头移动时**只增量重写**当前/新选中选项行（绝对行号），
绝不整页重建 → 图片不动、文字不乱。
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

DISPLAY_H = 30          # 内容区总高（题目+选项框架高度估算，容纳最多选项）

# 图片
IMG_H = 12            # 图片渲染高度（字符行）

# ANSI
_C = "\x1b["
_RST = f"{_C}0m"
_SEL = f"{_C}48;2;68;68;170;38;2;255;255;255m"
_OKT = f"{_C}32m"
_ERRBG = f"{_C}48;2;136;34;34;38;2;255;255;255m"
_GRAY = f"{_C}90m"
_TTL = f"{_C}1;36m"
_FRAME = f"{_C}36m"     # 边框：青色


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


# ---------- 图片（居中渲染一次） ----------

def _render_img_centered(path: str) -> None:
    if not path or not Path(path).exists():
        return
    tw = _term_width()
    IMG_W = 26                     # 图片渲染宽度（字符）
    left = max(1, (tw - IMG_W) // 2)   # 水平居中
    try:
        subprocess.run(
            ["kitty", "+kitten", "icat", "--transfer-mode=stream",
             "--place", f"{IMG_W}x{IMG_H}@{left}x1", str(path)],
            check=False)
    except FileNotFoundError:
        pass


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _vis(t: str) -> str:
    return _ANSI_RE.sub("", t)


def _pad(t: str, w: int) -> str:
    d = w - len(_vis(t))
    return t + " " * max(0, d)


# ---------- 边框/行 ----------

def _top_border(width: int) -> str:
    return f"{_FRAME}┌{'─'*width}┐{_RST}"


def _mid_line(text: str, width: int) -> str:
    return f"{_FRAME}│{_RST}{_pad(text, width)}{_FRAME}│{_RST}"


def _bottom_border(width: int) -> str:
    return f"{_FRAME}└{'─'*width}┘{_RST}"


def _draw_at(row: int, text: str, col: int = 0) -> None:
    sys.stdout.write(f"{_C}{row};{col+1}H{text}")
    sys.stdout.flush()


def _erase_from(row: int, col: int = 0) -> None:
    sys.stdout.write(f"{_C}{row};{col+1}H{_C}0J")
    sys.stdout.flush()


def _clear_scr() -> None:
    sys.stdout.write(_clr())
    sys.stdout.flush()


# ---------- 键盘 ----------
_SAVED_ATTR = None


def _enter_raw():
    import termios, tty
    global _SAVED_ATTR
    _SAVED_ATTR = termios.tcgetattr(sys.stdin.fileno())
    tty.setraw(sys.stdin.fileno())


def _exit_raw():
    import termios
    global _SAVED_ATTR
    if _SAVED_ATTR:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, _SAVED_ATTR)


def _read_key() -> str:
    ch = sys.stdin.read(1)
    if ch == "\x1b":
        nxt = sys.stdin.read(2)
        return {"[A": "up", "[B": "down", "[C": "right", "[D": "left"}.get(nxt, "esc")
    return ch


# ---------- 主逻辑 ----------

def run_question(q, exam: bool = False) -> dict:
    result = {"correct": False, "first_wrong": False, "quit": False, "choice": ""}
    img, _ = _split_img(q["stem"])
    choices = _choices_dict(q)
    letters = list(choices.keys())
    if not letters:
        return result

    tw = _term_width()
    box_w = min(50, tw - 8)          # 题目/选项框内容宽
    correct = q["answer"] or ""
    _, stem = _split_img(q["stem"])

    # 布局位置记录
    # 图片区: 1..IMG_H
    # 题目框: 从 TITLE_TOP 开始, 高度 3 (上框|题干+标题|下框)  -- 简化合并
    TITLE_TOP = IMG_H + 2
    # 选项框起始行
    OPT_TOP = TITLE_TOP + 4
    opt_rows = {}   # letter -> 行号(选项框内首行)
    FEEDBACK_ROW = OPT_TOP + len(letters) + 3
    HELP_ROW = FEEDBACK_ROW + 2

    # 全清, 渲染图片(居中,一次)
    _clear_scr()
    if img and _in_kitty():
        _render_img_centered(img)

    def draw_frames():
        """画题目框+选项框+帮助(只画一次)。返回每个选项的行号。"""
        # 题目框（标题+题干+下框）-- 合并: 上框 | 标题+题干 | 下框
        _erase_from(TITLE_TOP)
        _draw_at(TITLE_TOP, _top_border(box_w))
        _draw_at(TITLE_TOP+1, _mid_line(f"{_TTL}{q['subject']} · {q['source_id']}{_RST}", box_w))
        _draw_at(TITLE_TOP+2, _mid_line(stem, box_w))
        _draw_at(TITLE_TOP+3, _bottom_border(box_w))

        # 选项框
        _draw_at(OPT_TOP, _top_border(box_w))
        rowa = {}
        for idx, ch in enumerate(letters):
            rr = OPT_TOP + 1 + idx
            rowa[ch] = rr
        for idx, ch in enumerate(letters):
            _draw_at(OPT_TOP+1+idx, _opt_line(idx, None))
        _draw_at(OPT_TOP+len(letters)+1, _bottom_border(box_w))
        return rowa, OPT_TOP + len(letters) + 2   # 返回选项行映射和框底后行

    FEEDBACK_ROW = OPT_TOP + len(letters) + 3
    HELP_ROW = FEEDBACK_ROW + 2

    def _opt_line(idx: int, tone) -> str:
        """生成一个选项行：带边框 + 内容高亮。tone: 'sel'/'ok'/'err'/'gray'/None。"""
        ch = letters[idx]
        txt = choices[ch]
        cell = None
        if tone == "sel":
            cell = _SEL
        elif tone == "ok":
            cell = _OKT
        elif tone == "err":
            cell = _ERRBG
        elif tone == "gray":
            cell = _GRAY
        inner = f"{cell if cell else ''}{ch}. {txt}{_RST}"
        return f"{_FRAME}│{_RST}{_pad(inner, box_w)}{_FRAME}│{_RST}"

    # ---- 状态 ----
    sel = 0
    answered = False
    final_correct = False
    first_wrong = False

    rowa, _after_opt = draw_frames()
    # 给初始选中项上高亮
    _draw_at(rowa[letters[sel]], _opt_line(sel, "sel"))

    def fmt_feedback() -> str:
        if not exam and answered:
            return f"{_OKT}✓ 正确{_RST}" if final_correct else f"{_ERRBG}✗ 答错（请重答）{_RST}"
        if exam and answered:
            return f"{_TTL}已作答{_RST}"
        return ""

    def fmt_help() -> str:
        if exam:
            return "↑↓ 选择 · Enter 确认 · q 交卷" if not answered else "← 继续"
        if answered and not final_correct:
            return "↑↓ 选择重答选项 · Enter 确认 · q 退出（正确答案已高亮）"
        return "↑↓ 选择 · Enter 确认 · q 退出"

    def paint_feedback():
        _erase_from(FEEDBACK_ROW)
        _draw_at(FEEDBACK_ROW, fmt_feedback())
        _draw_at(HELP_ROW, fmt_help())

    def highlight_option(idx, tone):
        _draw_at(rowa[letters[idx]], _opt_line(idx, tone))

    paint_feedback()

    try:
        _enter_raw()
        while True:
            key = _read_key()
            if key == "up" and not final_correct:
                highlight_option(sel, None)
                sel = (sel - 1) % len(letters)
                highlight_option(sel, "sel")
            elif key == "down" and not final_correct:
                highlight_option(sel, None)
                sel = (sel + 1) % len(letters)
                highlight_option(sel, "sel")
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
                        final_correct = True; answered = True
                        result["correct"] = True
                        # 正确项标绿, 结束
                        for idx, ch in enumerate(letters):
                            highlight_option(idx, "ok" if ch == correct else "gray")
                        paint_feedback()
                        break
                    else:
                        first_wrong = True; answered = True
                        result["first_wrong"] = True
                        # 正确答案标绿, 选中错项红底
                        for idx, ch in enumerate(letters):
                            highlight_option(idx, "ok" if ch == correct else None)
                        highlight_option(sel, "err")
                        paint_feedback()
                else:
                    # 重答
                    if letter == q["answer"]:
                        result["first_wrong"] = True
                        result["correct"] = False
                        for idx, ch in enumerate(letters):
                            highlight_option(idx, "ok" if ch == correct else None)
                    break
    except (KeyboardInterrupt, EOFError):
        result["quit"] = True
    finally:
        _exit_raw()
        sys.stdout.write("\n")
        sys.stdout.flush()
    return result


def _clr() -> str:
    return f"{_C}H{_C}2J"
