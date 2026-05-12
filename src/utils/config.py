"""قراءة ملفات الإعدادات وإدارة مسارات المشروع.

يستخدم:
    from src.utils.config import load_config, PROJECT_ROOT
    cfg = load_config()
    raw_dir = PROJECT_ROOT / cfg["data"]["raw_dir"]
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# جذر المشروع = جدّ هذا الملف الثالث (src/utils/config.py → src/utils → src → root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "config.yaml"


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """قراءة ملف الإعدادات YAML.

    Args:
        path: مسار اختياري لملف الإعدادات. إذا None يُستخدم configs/config.yaml.

    Returns:
        قاموس بكل الإعدادات.

    Raises:
        FileNotFoundError: إذا لم يوجد الملف.
        yaml.YAMLError: إذا كان YAML معطوباً.
    """
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH

    if not cfg_path.exists():
        raise FileNotFoundError(
            f"ملف الإعدادات غير موجود: {cfg_path}\n"
            f"تأكد من تشغيل السكربت من جذر المشروع."
        )

    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_data_paths(cfg: dict[str, Any] | None = None) -> dict[str, Path]:
    """إرجاع مسارات البيانات المطلقة كقاموس.

    Args:
        cfg: قاموس الإعدادات (اختياري، يُحمَّل تلقائياً إذا None).

    Returns:
        قاموس بمسارات Path مطلقة لكل مجلدات البيانات.
    """
    if cfg is None:
        cfg = load_config()

    return {
        key: PROJECT_ROOT / cfg["data"][f"{key}_dir"]
        for key in ["raw", "processed", "interim", "train", "val", "test"]
    }


def ensure_dirs(*paths: Path) -> None:
    """إنشاء المجلدات إذا لم تكن موجودة (بدون خطأ إن وُجدت)."""
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)
