"""تطبيع وتنظيف النصوص العربية للتفريغ المرجعي.

تتعامل مع:
- توحيد الهمزات (إ، أ، آ → ا) أو الإبقاء عليها حسب الحاجة
- إزالة التشكيل (الحركات)
- توحيد التاء المربوطة وألف المقصورة
- إزالة الأرقام الإنجليزية وتحويلها لعربية (اختياري)
- تنظيف المسافات والرموز

استخدام:
    from src.utils.arabic_text import normalize_for_asr, clean_text
    text = normalize_for_asr("الْعَرَبِيَّة جَمِيلَةٌ!")
"""
from __future__ import annotations

import re
import unicodedata

# الحركات العربية
DIACRITICS = re.compile(r"[\u064B-\u0652\u0670\u0640]")  # ـ تطويل أيضاً

# علامات الترقيم العربية + اللاتينية
PUNCTUATION_PATTERN = re.compile(r"[!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~،؛؟«»…]")

# الأرقام
ARABIC_INDIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ASCII_DIGITS = "0123456789"


def remove_diacritics(text: str) -> str:
    """إزالة كل الحركات والشدّة والتطويل."""
    return DIACRITICS.sub("", text)


def normalize_alef(text: str, keep_hamza: bool = False) -> str:
    """توحيد أشكال الألف.

    Args:
        text: النص المدخل.
        keep_hamza: إذا True يُبقي الهمزة على الألف. إذا False يحوّل الكل لـ ا.
    """
    if keep_hamza:
        return text
    return re.sub(r"[إأآٱ]", "ا", text)


def normalize_yaa(text: str) -> str:
    """توحيد الياء وألف المقصورة → ي."""
    return text.replace("ى", "ي").replace("ئ", "ي")


def normalize_taa(text: str) -> str:
    """توحيد التاء المربوطة → ه (شائع في التطبيع للبحث، لكن ليس للتفريغ المرجعي)."""
    return text.replace("ة", "ه")


def arabic_to_ascii_digits(text: str) -> str:
    """تحويل الأرقام الهندية العربية → أرقام لاتينية."""
    table = str.maketrans(ARABIC_INDIC_DIGITS, ASCII_DIGITS)
    return text.translate(table)


def ascii_to_arabic_digits(text: str) -> str:
    """تحويل الأرقام اللاتينية → أرقام هندية عربية."""
    table = str.maketrans(ASCII_DIGITS, ARABIC_INDIC_DIGITS)
    return text.translate(table)


def remove_punctuation(text: str) -> str:
    """إزالة كل علامات الترقيم."""
    return PUNCTUATION_PATTERN.sub(" ", text)


def collapse_whitespace(text: str) -> str:
    """دمج المسافات المتعددة في مسافة واحدة."""
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str) -> str:
    """تنظيف خفيف: إزالة الحركات + توحيد المسافات.

    يُحافظ على الترقيم والأشكال المختلفة للحروف (للتفريغ المرجعي).
    """
    text = unicodedata.normalize("NFC", text)
    text = remove_diacritics(text)
    return collapse_whitespace(text)


def normalize_for_asr(text: str) -> str:
    """تطبيع كامل للمقارنة مع مخرج ASR (لحساب WER لاحقاً).

    - إزالة الحركات
    - توحيد الألف والياء
    - إزالة الترقيم
    - توحيد المسافات

    لا يُستخدم للتفريغ المرجعي نفسه — فقط لمرحلة التقييم.
    """
    text = unicodedata.normalize("NFC", text)
    text = remove_diacritics(text)
    text = normalize_alef(text)
    text = normalize_yaa(text)
    text = remove_punctuation(text)
    return collapse_whitespace(text)


def is_arabic(text: str, threshold: float = 0.5) -> bool:
    """التحقق إن كان النص عربياً (نسبة الحروف العربية ≥ threshold)."""
    if not text:
        return False
    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    total_letters = sum(1 for c in text if c.isalpha())
    if total_letters == 0:
        return False
    return arabic_chars / total_letters >= threshold


def word_count(text: str) -> int:
    """عدّ الكلمات بعد التنظيف الخفيف."""
    return len(clean_text(text).split())
