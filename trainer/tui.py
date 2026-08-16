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

DISPLAY_H = 60          # 内容区总高（估算）

# 图片（加大）
IMG_H = 24            # 图片渲染高度（字符行）
IMG_W = 56            # 图片渲染宽度（字符）

# ANSI
_C = "\x1b["
_RST = f"{_C}0m"
_SEL = f"{_C}48;2;68;68;170;38;2;255;255;255m"
_OKT = f"{_C}32m"
_OKBG = f"{_C}48;2;0;150;0;38;2;255;255;255m"   # 正确项 绿底白字(learn)
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

def _term_height() -> int:
    try:
        return shutil.get_terminal_size().lines or 40
    except Exception:
        return 40


def _render_img_centered(path: str, height: int = IMG_H) -> int:
    """居中渲染真彩图片，返回实际占行数 height。"""
    if not path or not Path(path).exists():
        return 0
    tw = _term_width()
    left = max(1, (tw - IMG_W) // 2)   # 水平居中
    try:
        subprocess.run(
            ["kitty", "+kitten", "icat", "--transfer-mode=stream",
             "--place", f"{IMG_W}x{min(height, IMG_H)}@{left}x1", str(path)],
            check=False)
    except FileNotFoundError:
        return 0
    return min(height, IMG_H)


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _vis(t: str) -> str:
    return _ANSI_RE.sub("", t)


def _pad(t: str, w: int) -> str:
    d = w - len(_vis(t))
    return t + " " * max(0, d)


# ---------- 边框/行（只用横线分隔，无竖线） ----------

def _sep(width: int, ch: str = "─") -> str:
    """一条横线分隔线。"""
    return f"{_C}36m{ch * width}{_RST}"


def _top_border(width: int) -> str:
    return _sep(width)


def _mid_line(text: str, width: int) -> str:
    # 无竖线，纯文本（按可见宽补右空格）
    return _pad(text, width)


def _bottom_border(width: int) -> str:
    return _sep(width)


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
    """读取一个按键。
    返回: up/down/left/right/enter/ctrl+enter/esc/q 或字符。
    支持 CSI u (kitty键盘协议) 用于 Ctrl+Enter。
    """
    ch = sys.stdin.read(1)
    if ch == "\x1b":
        nxt = sys.stdin.read(1)
        if nxt == "[":
            # CSI 序列：读参数直到结束字母
            seq = "["
            while True:
                c = sys.stdin.read(1)
                if not c:
                    break
                seq += c
                if c == "~" or c.isalpha():
                    break
            if seq in ("[A", "[B", "[C", "[D"):
                return {"[A": "up", "[B": "down", "[C": "right", "[D": "left"}[seq]
            if seq == "[13;5u":        # Ctrl+Enter (kitty CSI u)
                return "ctrl+enter"
            return "esc"
        elif nxt == "O":               # SS3 应用模式箭头
            c = sys.stdin.read(1)
            return {"A": "up", "B": "down", "C": "right", "D": "left"}.get(c, "esc")
        return "esc"
    return ch   # '\r'/'\n'=enter, 'q', 其他字符


# ---------- 主逻辑 ----------

def run_question(q, exam: bool = False, learn: bool = False) -> dict:
    """运行一题。
    练习(exam=False,learn=False): 箭头选择+错题重答。
    学习(learn=True): 正确项绿色背景高亮, Enter下一题, Ctrl+Enter上一题。
    返回 {correct, first_wrong, quit, choice, nav} (nav: next/prev, learn模式)。
    """
    result = {"correct": False, "first_wrong": False, "quit": False,
              "choice": "", "nav": None}
    img, _ = _split_img(q["stem"])
    choices = _choices_dict(q)
    letters = list(choices.keys())
    if not letters:
        return result

    tw = _term_width()
    th = _term_height()
    ROW_GAP = 1                     # 选项项之间的空行数（行距）
    box_w = tw                      # 横线占满整行
    txt_w = tw - 2                  # 文本区宽度（略留边）
    correct = q["answer"] or ""
    _, stem = _split_img(q["stem"])

    # 动态图片高度：确保整页(图片+题目区+选项区+底部空行+反馈/帮助)不超过终端高度
    #  题目区 4 行 | 选项区(选项+项间空行+底部空1行+横线) | 反馈1 + 帮助1
    opt_block = (len(letters) - 1) * (1 + ROW_GAP) + 2   # 选项本身 + 底部空1行 + 最后横线
    fixed_rows = 4 + 1 + opt_block + 2                    # 题目区4 + 图片后1空行 + 选项块 + 反馈/帮助
    eff_img_h = max(4, min(IMG_H, th - fixed_rows - 1))
    # 布局位置记录（整体紧贴图片下方）
    TITLE_TOP = eff_img_h + 1

    def draw_frames():
        """画题目横线+选项横线（横线满宽）。返回每个选项的行号。"""
        # 题目区：横线 | 标题 | 题干 | 空行 (行距)
        _erase_from(TITLE_TOP)
        opt_top = TITLE_TOP + 4              # 题目区之后（标题2行+空行）
        _draw_at(TITLE_TOP,     _sep(tw))
        _draw_at(TITLE_TOP+1,   _mid_line(f"{_TTL}{q['subject']} · {q['source_id']}{_RST}", txt_w))
        _draw_at(TITLE_TOP+2,   _mid_line(stem, txt_w))
        _draw_at(TITLE_TOP+3,   _sep(tw))

        # 选项区：每个选项(含空行)
        rowa = {}
        for idx, ch in enumerate(letters):
            rr = opt_top + idx * (1 + ROW_GAP)   # 每项隔 ROW_GAP 行
            rowa[ch] = rr
        for idx, ch in enumerate(letters):
            _draw_at(rowa[ch], _opt_line(idx, None))
        # 最后一个选项后空 1 行，再画横线（缓冲，避免横线被裁剪/贴太近）
        opt_bottom = opt_top + (len(letters) - 1) * (1 + ROW_GAP) + 2
        _draw_at(opt_bottom, _sep(tw))
        return rowa, opt_bottom + 1

    def _opt_line(idx: int, tone) -> str:
        """生成一个选项行：纯文本，选中/对错加底纹，无竖线。tone: sel/ok/okbg/err/gray/None。"""
        ch = letters[idx]
        txt = choices[ch]
        cell = None
        if tone == "sel":
            cell = _SEL
        elif tone == "ok":
            cell = _OKT
        elif tone == "okbg":
            cell = _OKBG
        elif tone == "err":
            cell = _ERRBG
        elif tone == "gray":
            cell = _GRAY
        # 补足宽度（可见宽），覆盖选中底纹残留
        return _pad(f"{cell if cell else ''}{ch}. {txt}{_RST}", txt_w)

    # ---- 状态 ----
    sel = 0
    answered = False
    final_correct = False
    first_wrong = False

    _clear_scr()
    if img and _in_kitty():
        _render_img_centered(img, eff_img_h)

    rowa, after_opt = draw_frames()
    # 反馈/帮助行（选项区之后）
    FEEDBACK_ROW = after_opt + 1
    HELP_ROW = FEEDBACK_ROW + 1 + 0   # 帮助紧接反馈

    # 初始高亮
    if learn:
        # 学习模式：直接高亮正确项（绿底白字）
        for idx, ch in enumerate(letters):
            _draw_at(rowa[ch], _opt_line(idx, "okbg" if ch == correct else None))
    else:
        _draw_at(rowa[letters[sel]], _opt_line(sel, "sel"))

    def fmt_feedback() -> str:
        if learn:
            return f"{_OKBG}正确答案已高亮 ✓{_RST}"
        if not exam and answered:
            return f"{_OKT}✓ 正确{_RST}" if final_correct else f"{_ERRBG}✗ 答错（请重答）{_RST}"
        if exam and answered:
            return f"{_TTL}已作答{_RST}"
        return ""

    def fmt_help() -> str:
        if learn:
            return "Enter 下一题 · Ctrl+Enter 上一题 · q 退出"
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
    if learn:
        # 学习模式：无箭头，Enter 下一题 / Ctrl+Enter 上一题 / q 退出
        try:
            _enter_raw()
            while True:
                key = _read_key()
                if key in ("\r", "\n"):
                    result["nav"] = "next"
                    break
                elif key == "ctrl+enter":
                    result["nav"] = "prev"
                    break
                elif key == "q":
                    result["quit"] = True
                    break
        except (KeyboardInterrupt, EOFError):
            result["quit"] = True
        finally:
            _exit_raw()
            sys.stdout.write("\n")
            sys.stdout.flush()
        return result

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
