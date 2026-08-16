"""应用日志系统：运行时信息/错误写入 data/logs/，便于排查问题。

用法：
    from trainer.logger import get_logger
    log = get_logger(__name__)
    log.info("..."); log.warning("..."); log.error("...", exc_info=True)

日志同时输出到：
  · data/logs/drive_practice.log （文件，方便回溯）
  · stderr （控制台，仅 WARNING 及以上，避免干扰 UI）
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

from config import LOG_FILE, LOGS_DIR

_FMT_FILE = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_FMT_CONSOLE = "%(levelname)s: %(message)s"


def _rotating_path() -> Path:
    """日志文件。超过阈值时用带时间戳的旧档轮转（简单滚动）。"""
    MAX_BYTES = 5 * 1024 * 1024   # 5MB
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_BYTES:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            LOG_FILE.rename(LOGS_DIR / f"drive_practice.{stamp}.log")
        except OSError:
            pass
    return LOG_FILE


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """初始化根日志配置，返回名称为 'drive' 的根 logger。"""
    root = logging.getLogger("drive")
    if root.handlers:               # 已初始化，避免重复 add
        return root
    root.setLevel(level)

    # 文件 handler（记录全部级别，含 debug 便于排查）
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(str(_rotating_path()), encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(_FMT_FILE))
        root.addHandler(fh)
    except OSError:
        pass

    # 控制台 handler（仅 WARNING+，避免污染交互界面）
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter(_FMT_CONSOLE))
    root.addHandler(ch)

    return root


def get_logger(name: str | None = None) -> logging.Logger:
    """获取带 'drive' 前缀的 logger（共享一份配置）。"""
    setup_logging()
    return logging.getLogger("drive" + (f".{name}" if name else ""))
