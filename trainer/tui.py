"""TUI 刷题界面：左右分栏(题目|图片) + 上下箭头选择 + 错题重答。

单题一页全屏渲染：
  ┌─────────────────────────────────────────────────────┐
  │ 第一冊 · book1_q1                        ▗▅▏        │
  │ 圖一標誌表示:                                        │
  │  → A. 向右轉彎   (chafa 半块画在右侧)                │
  │    B. 向左轉彎                                       │
  │    C. 應遵方向                                       │
  │    D. 路線忠告                                       │
  ├─────────────────────────────────────────────────────┤
  │ ✓ 正确                                              │
  │  ↑↓ 选择 · Enter 确认 · q 退出                       │
  └─────────────────────────────────────────────────────┘
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from typing import Optional

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.styles import Style

from config import ROOT

IMG_W = 20   # 右侧图片字符宽
IMG_H = 12   # 右侧图片字符高


# ---------- chafa 图片 → 字符行 ----------

def chafa_lines(path: str, width: int = IMG_W, height: int = IMG_H) -> list[str]:
    try:
        out = subprocess.run(
            ["chafa", "--size", f"{width}x{height}", "--format", "symbols",
             "--colors", "full", str(path)],
            capture_output=True, text=True, timeout=15)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if out.returncode != 0:
        return []
    return out.stdout.splitlines()[:height]


# ---------- 工具 ----------

def _split_img(text: str) -> tuple[Optional[str], str]:
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


@dataclass
class QState:
    q: dict
    left: list = field(default_factory=list)     # 题干+选项 文本行
    right: list = field(default_factory=list)    # chafa 图片行
    merged: list = field(default_factory=list)   # 并排后的行块
    opt_start: int = 0                            # left 中第一个选项的行号
    choices_letters: list = field(default_factory=list)  # [A,B,C,D]
    sel: int = 0
    answered: bool = False        # 本题已确认（进入反馈态）
    final_correct: bool = False
    first_wrong: bool = False     # 第一次是否答错（重答标记）
    quit: bool = False
    show_feedback: bool = False   # 是否显示对错反馈


def build_state(q) -> QState:
    img, stem = _split_img(q["stem"])
    choices = _choices_dict(q)
    left = [stem, ""]
    opt_start = 2
    letters = []
    for ch, txt in choices.items():
        left.append(f"  {ch}. {txt}")
        letters.append(ch)
    right = chafa_lines(img) if img else []

    lw = max(len(l) for l in left) + 2 if left else 8
    n = max(len(left), len(right))
    merged = []
    for i in range(n):
        l = left[i] if i < len(left) else ""
        r = right[i] if i < len(right) else ""
        # 左块按可见宽度右对齐补空格；右块(chafa ANSI)原样(不按含码长度ljust)
        merged.append(l.ljust(lw) + r.rstrip())
    return QState(q=q, left=left, right=right, merged=merged,
                  opt_start=opt_start, choices_letters=letters)


# ---------- 动态 ANSI 生成（prompt_toolkit ANSI 解析） ----------

# ANSI 色码
_C = "\x1b["         # ESC[
_RST = f"{_C}0m"
_TITLE = f"{_C}1;36m"        # 粗亮青
_SEL = f"{_C}48;2;68;68;170;38;2;255;255;255m"  # 蓝底白字(选中)
_OKTXT = f"{_C}32m"          # 绿
_ERRBG = f"{_C}48;2;136;34;34;38;2;255;255;255m"  # 红底白字(重答选中错)
_GRAY = f"{_C}90m"           # 灰(曾选错项)


def _norm_line(s: str) -> str:
    """chafa 行已含 ANSI,保留; 纯文本行返回原样。"""
    return s


def _body_html(st: QState, hide_answer: bool = False) -> str:
    """题目页主体 ANSI 字符串（题目/选项上色 + chafa 图片原样嵌入）。"""
    lines = [f"{_TITLE}{st.q['subject']} · {st.q['source_id']}{_RST}", ""]
    correct = (st.q["answer"] or "")
    for i, text in enumerate(st.merged):
        # 判定是否为选项行
        if i < len(st.left) and i >= st.opt_start and st.left[i].strip():
            letter = st.left[i].strip()[0]
            is_sel = st.sel == (i - st.opt_start)
            cell = _RST                        # 默认无色
            if not st.final_correct:
                if is_sel:
                    cell = _SEL
                # 答错重答：正确项绿色
                if st.answered and not hide_answer and letter == correct:
                    cell = _OKTXT
                # 重答中选中错误项→红底
                if st.answered and st.first_wrong and is_sel and letter != correct:
                    cell = _ERRBG
            else:
                if letter == correct:
                    cell = _OKTXT
                elif is_sel:
                    cell = _GRAY
            # 选项部分上色；图片部分(chafa ANSI)原样保留
            # 切分：左侧选项文本 + 右侧图片
            # 用固定位置切分不可靠，这里整行上色（选项行图片区也被覆盖色，但 chafa 自带色会优先级更高）
            lines.append(f"{cell}{text}{_RST}")
        else:
            # 题干/图片行：原样输出（保留 chafa ANSI）
            lines.append(text)
    return "\n".join(lines)


def _feedback_html(st: QState) -> str:
    if not st.answered:
        return ""
    if st.final_correct:
        return f"{_C}1;32m✓ 正确{_RST}"
    return (f"{_C}1;31m✗ 答错"
            + ("（请重答，正确答案已高亮）" if not st.final_correct else "")
            + f"{_RST}")


def _helpbar_html(st: QState) -> str:
    if st.answered and not st.final_correct:
        return " ↑↓ 选择要重答的选项 · Enter 确认 · q 退出（显示正确答案）"
    return " ↑↓ 选择 · Enter 确认 · q 退出"


# ---------- Application ----------

def run_question(q, exam: bool = False) -> dict:
    """运行一题箭头选择。返回 {correct, first_wrong, quit, choice}。

    exam=True：模拟考模式，作答后不显示答案、不重答，记录 choice 直接进入下一题。
    """
    st = build_state(q)
    result = {"correct": False, "first_wrong": False, "quit": False, "choice": ""}

    # 动态渲染函数（exam 模式下不显示答案）
    hide = bool(exam)
    _body_fn = lambda: _body_html(st, hide_answer=hide)
    if exam:
        _fb_fn = lambda: f"{_C}1;36m已作答{_RST}" if st.answered else ""
        _help_fn = lambda: (" ↑↓ 选择 · Enter 确认 · q 交卷"
                            if not st.answered else " ← 继续")
    else:
        _fb_fn = lambda: _feedback_html(st)
        _help_fn = lambda: _helpbar_html(st)

    kb = KeyBindings()

    @kb.add("up")
    def _up(_event):
        if not st.final_correct and st.choices_letters:
            st.sel = (st.sel - 1) % len(st.choices_letters)
        _event.app.invalidate()

    @kb.add("down")
    def _down(_event):
        if not st.final_correct and st.choices_letters:
            st.sel = (st.sel + 1) % len(st.choices_letters)
        _event.app.invalidate()

    @kb.add("q")
    @kb.add("c-c")
    def _quit(_event):
        result["quit"] = True
        _event.app.exit()

    @kb.add("enter")
    def _enter(_event):
        if not st.choices_letters:
            _event.app.exit()
            return
        if not st.answered:
            # 第一次作答
            letter = st.choices_letters[st.sel]
            if exam:
                # 模拟考：记录选择，立即下一题（不显示答案/不重答）
                result["choice"] = letter
                result["correct"] = (letter == st.q["answer"])
                _event.app.exit()
                return
            if letter == st.q["answer"]:
                st.final_correct = True
                st.answered = True
                result["correct"] = True
                _event.app.exit()          # 答对直接下一题
            else:
                st.first_wrong = True
                st.answered = True         # 显示答错，进入重答
                result["first_wrong"] = True
                _event.app.invalidate()
        else:
            # 重答（已 answered 且是错的）
            letter = st.choices_letters[st.sel]
            if letter == st.q["answer"]:
                result["correct"] = False   # 第一次错过，本题计错
                result["first_wrong"] = True
            _event.app.exit()               # 重答后无论对错都下一题
        _event.app.invalidate()

    body_control = FormattedTextControl(lambda: ANSI(_body_fn()))
    fb_control = FormattedTextControl(lambda: ANSI(_fb_fn()))
    help_control = FormattedTextControl(lambda: ANSI(_help_fn()))

    layout = Layout(
        HSplit([
            Window(body_control, wrap_lines=True),
            Window(height=1),
            Window(fb_control, height=1),
            Window(help_control, height=1, style="reverse"),
        ])
    )

    style = Style([("reverse", "bg:#333333")])

    app = Application(layout=layout, key_bindings=kb, full_screen=True, style=style)
    app.run()
    return result
