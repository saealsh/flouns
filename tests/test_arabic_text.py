"""اختبارات وحدة لـ src.utils.arabic_text."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.utils.arabic_text import (
    arabic_to_ascii_digits,
    ascii_to_arabic_digits,
    clean_text,
    is_arabic,
    normalize_alef,
    normalize_for_asr,
    normalize_yaa,
    remove_diacritics,
    remove_punctuation,
    word_count,
)


class TestRemoveDiacritics:
    def test_removes_fatha(self):
        assert remove_diacritics("بَاب") == "باب"

    def test_removes_all_diacritics(self):
        assert remove_diacritics("الْعَرَبِيَّةُ") == "العربية"

    def test_no_change_when_no_diacritics(self):
        assert remove_diacritics("السلام") == "السلام"

    def test_removes_tatweel(self):
        assert remove_diacritics("الـعـربـية") == "العربية"


class TestNormalizeAlef:
    def test_alef_with_hamza_above(self):
        assert normalize_alef("أحمد") == "احمد"

    def test_alef_with_hamza_below(self):
        assert normalize_alef("إيمان") == "ايمان"

    def test_alef_with_madda(self):
        assert normalize_alef("آمال") == "امال"

    def test_keep_hamza_when_requested(self):
        assert normalize_alef("أحمد", keep_hamza=True) == "أحمد"


class TestNormalizeYaa:
    def test_alef_maksura(self):
        assert normalize_yaa("على") == "علي"

    def test_yaa_with_hamza(self):
        assert normalize_yaa("سئل") == "سيل"


class TestDigits:
    def test_arabic_to_ascii(self):
        assert arabic_to_ascii_digits("الساعة ٩:٣٠") == "الساعة 9:30"

    def test_ascii_to_arabic(self):
        assert ascii_to_arabic_digits("12 يناير 2026") == "١٢ يناير ٢٠٢٦"


class TestPunctuation:
    def test_removes_arabic_punct(self):
        result = remove_punctuation("مرحباً، كيف حالك؟")
        # المسافات قد تتغيّر، فقط نتأكد لا فاصلة ولا علامة استفهام
        assert "،" not in result
        assert "؟" not in result

    def test_removes_ellipsis(self):
        assert "…" not in remove_punctuation("نعم… أكيد")


class TestCleanText:
    def test_removes_diacritics_and_normalizes_spaces(self):
        result = clean_text("الْعَرَبِيَّةُ  جَمِيلَةٌ")
        assert result == "العربية جميلة"


class TestNormalizeForAsr:
    def test_full_normalization(self):
        # هذا التطبيع يستخدم لمقارنة WER
        original = "أَهْلاً، يا أَحْمَد!"
        normalized = normalize_for_asr(original)
        assert "،" not in normalized
        assert "!" not in normalized
        assert "أ" not in normalized  # توحدت
        # الكلمات الجوهرية موجودة
        assert "اهلا" in normalized or "اهلاً" in normalized


class TestIsArabic:
    def test_pure_arabic(self):
        assert is_arabic("السلام عليكم") is True

    def test_pure_english(self):
        assert is_arabic("Hello world") is False

    def test_empty(self):
        assert is_arabic("") is False

    def test_mostly_arabic(self):
        assert is_arabic("هذا نص عربي مع word واحدة") is True

    def test_mostly_english(self):
        assert is_arabic("This is English with كلمة") is False


class TestWordCount:
    def test_simple(self):
        assert word_count("السلام عليكم ورحمة الله") == 4

    def test_with_diacritics(self):
        assert word_count("الْسَّلَام عَلَيْكُم") == 2

    def test_extra_spaces(self):
        assert word_count("كلمة    أخرى") == 2

    def test_empty(self):
        assert word_count("") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
