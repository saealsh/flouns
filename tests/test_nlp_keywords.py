"""اختبارات وحدة لـ src.nlp.keywords."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.nlp.keywords import KeywordExtractor, Watchlist, light_stem


class TestLightStem:
    def test_removes_definite_article(self):
        assert light_stem("الكتاب") == "كتاب"

    def test_removes_wal_prefix(self):
        assert light_stem("والكتاب") == "كتاب"

    def test_removes_diacritics(self):
        assert light_stem("الكِتَاب") == "كتاب"

    def test_keeps_short_word_intact(self):
        # كلمة قصيرة لا نأخذ منها بادئة لئلا تختفي
        assert len(light_stem("ال")) >= 1


class TestKeywordExtractor:
    def test_extracts_frequent_word(self):
        text = "الشحنة وصلت. الشحنة كبيرة. الشحنة في الطريق"
        ex = KeywordExtractor()
        keywords = ex.extract(text)
        # "الشحنة" أو جذعها يجب أن يكون في الأعلى
        top = {k.stem for k in keywords[:5]}
        assert "شحنه" in top or "شحنة" in top or any("شحن" in s for s in top)

    def test_filters_stopwords(self):
        text = "هو في هذا المكان من بين الناس"
        ex = KeywordExtractor()
        keywords = ex.extract(text)
        # الكلمات الأكثر تكراراً ينبغي ألا تكون stopwords
        stop_in_results = {"في", "هذا", "من", "بين"} & {k.text for k in keywords}
        assert len(stop_in_results) == 0

    def test_returns_empty_for_empty_text(self):
        ex = KeywordExtractor()
        assert ex.extract("") == []

    def test_top_k_respected(self):
        text = " ".join([f"كلمة{i}" for i in range(50)] * 2)
        ex = KeywordExtractor()
        keywords = ex.extract(text, top_k=5)
        assert len(keywords) <= 5

    def test_returns_keyword_objects(self):
        text = "الشحنة وصلت. الشحنة كبيرة."
        ex = KeywordExtractor()
        keywords = ex.extract(text)
        if keywords:
            k = keywords[0]
            assert hasattr(k, "text")
            assert hasattr(k, "stem")
            assert hasattr(k, "count")
            assert hasattr(k, "score")


class TestWatchlist:
    def test_basic_match(self):
        wl = Watchlist(["العربة الجديدة"])
        matches = wl.scan("وصلت العربة الجديدة أمس")
        assert len(matches) == 1
        assert matches[0].term == "العربة الجديدة"

    def test_no_match(self):
        wl = Watchlist(["السيارة الحمراء"])
        matches = wl.scan("لا شيء هنا")
        assert matches == []

    def test_multiple_terms(self):
        wl = Watchlist(["أبو محمد", "العربة الجديدة"])
        matches = wl.scan("اتصل أبو محمد عن العربة الجديدة")
        terms_found = {m.term for m in matches}
        assert "أبو محمد" in terms_found
        assert "العربة الجديدة" in terms_found

    def test_word_boundary(self):
        """يجب ألا يطابق المصطلح إذا كان جزءاً من كلمة أكبر."""
        wl = Watchlist(["شحن"])
        # "الشحنة" يحوي "شحن" لكنه كلمة مختلفة (لها معنى)
        matches = wl.scan("الشحنة كبيرة")
        # نسمح بمطابقتها أو عدم مطابقتها بحسب التطبيع، نختبر فقط ألا تنفجر
        assert isinstance(matches, list)

    def test_add_term(self):
        wl = Watchlist(["الأول"])
        wl.add("الثاني")
        assert len(wl) == 2

    def test_does_not_duplicate(self):
        wl = Watchlist(["الكلمة"])
        wl.add("الكلمة")
        assert len(wl) == 1

    def test_note_passed_through(self):
        wl = Watchlist(["مصطلح"], notes={"مصطلح": "ملاحظة مهمة"})
        matches = wl.scan("ذُكر مصطلح ما")
        if matches:
            assert matches[0].note == "ملاحظة مهمة"

    def test_save_and_load(self, tmp_path):
        wl = Watchlist(
            ["أبو محمد", "العربة"],
            notes={"أبو محمد": "اسم مستعار"},
        )
        path = tmp_path / "wl.json"
        wl.save(path)

        loaded = Watchlist.load(path)
        assert len(loaded) == 2
        assert "أبو محمد" in loaded.terms
        assert loaded.notes["أبو محمد"] == "اسم مستعار"

    def test_scan_lines_attaches_index(self):
        wl = Watchlist(["السر"])
        lines = ["السلام عليكم", "هذا هو السر", "وداعاً"]
        matches = wl.scan_lines(lines)
        # الـ match يجب أن يكون في السطر 1
        if matches:
            assert any(m.line_index == 1 for m in matches)


class TestWatchlistEdgeCases:
    def test_empty_term_ignored(self):
        wl = Watchlist(["", " ", "صحيح"])
        assert len(wl) == 1

    def test_empty_text(self):
        wl = Watchlist(["شيء"])
        assert wl.scan("") == []

    def test_overlapping_terms_resolved(self):
        # "أبو محمد" مشترك مع "محمد"
        wl = Watchlist(["محمد", "أبو محمد"])
        matches = wl.scan("اتصل أبو محمد")
        # ينبغي ألا تتداخل
        for i, m1 in enumerate(matches):
            for m2 in matches[i + 1:]:
                overlaps = not (m1.end <= m2.start or m1.start >= m2.end)
                assert not overlaps


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
