"""全局配置：数据路径。

路径均相对项目根，随项目可移植。
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
IMAGE_DIR = DATA_DIR / "images"            # 题目图片
IMAGE_CACHE_DIR = DATA_DIR / "images_cache"  # 放大后图片缓存
LOGS_DIR = DATA_DIR / "logs"              # 运行日志
DB_PATH = DATA_DIR / "questions.db"        # 题库数据库
LOG_FILE = LOGS_DIR / "drive_practice.log" # 应用运行日志
EXAM_DATE_FILE = DATA_DIR / "exam_date"    # 考试日期(edata 设置,启动显示倒计时)


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    IMAGE_DIR.mkdir(exist_ok=True)
    IMAGE_CACHE_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
