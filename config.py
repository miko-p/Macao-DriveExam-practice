"""全局配置：数据路径。

路径均相对项目根，随项目可移植。
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
IMAGE_DIR = DATA_DIR / "images"            # 题目图片
DB_PATH = DATA_DIR / "questions.db"        # 题库数据库


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    IMAGE_DIR.mkdir(exist_ok=True)
