"""إعداد موحّد للتسجيل (logging) عبر loguru.

استخدام:
    from src.utils.logging import get_logger
    log = get_logger(__name__)
    log.info("بدء المعالجة...")
    log.warning("تحذير من شيء ما")
    log.error("خطأ مع تتبع كامل")
"""
from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger as _logger

from src.utils.config import PROJECT_ROOT, load_config

_initialized = False


def _setup_logger() -> None:
    """تهيئة loguru مرة واحدة فقط مع المخرجات إلى الطرفية + ملف."""
    global _initialized
    if _initialized:
        return

    cfg = load_config()
    log_cfg = cfg.get("logging", {})

    _logger.remove()  # إزالة المعالج الافتراضي

    # ── الطرفية: تنسيق ملوّن وسهل القراءة ──
    _logger.add(
        sys.stderr,
        level=log_cfg.get("level", "INFO"),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}:{function}:{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # ── الملف: كل شيء مع تدوير ──
    log_file = log_cfg.get("file", "logs/cie.log")
    log_path = PROJECT_ROOT / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)

    _logger.add(
        log_path,
        level="DEBUG",
        rotation=log_cfg.get("rotation", "10 MB"),
        retention=log_cfg.get("retention", "30 days"),
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    )

    _initialized = True


def get_logger(name: str = "cie"):
    """إرجاع logger مهيّأ بالاسم المعطى.

    Args:
        name: اسم المسجّل (عادة __name__).

    Returns:
        كائن logger من loguru.
    """
    _setup_logger()
    return _logger.bind(name=name)
