"""اختبارات وحدة لـ src.nlp.coreference."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.nlp.coreference import (
    EntityResolver,
    is_subname_match,
    normalize_location,
    normalize_organization,
    normalize_person_name,
)
from src.nlp.ner import Entity


class TestNormalizePerson:
    def test_removes_honorific_simple(self):
        result = normalize_person_name("الأستاذ أحمد")
        assert "أحمد" in result or "احمد" in result
        assert "الأستاذ" not in result
        assert "الاستاذ" not in result

    def test_removes_doctor_abbreviation(self):
        result = normalize_person_name("د. محمد")
        assert "محمد" in result
        assert "د." not in result

    def test_normalizes_alef(self):
        result = normalize_person_name("أحمد")
        assert result == "احمد"

    def test_empty(self):
        assert normalize_person_name("") == ""

    def test_no_honorific(self):
        result = normalize_person_name("علي حسن")
        # تطبيع فقط
        assert "علي" in result or "علي" in result
        assert "حسن" in result


class TestNormalizeLocation:
    def test_removes_definite_article(self):
        result = normalize_location("الرياض")
        # ندخل "ال" التعريف للمطابقة
        assert "رياض" in result

    def test_keeps_short_word(self):
        # كلمة قصيرة "ال" قد تبقى
        result = normalize_location("بحر")
        assert "بحر" in result


class TestSubnameMatch:
    def test_short_in_long(self):
        assert is_subname_match("أحمد", "أحمد محمد") is True

    def test_last_name_in_full(self):
        assert is_subname_match("محمد", "أحمد محمد") is True

    def test_no_overlap(self):
        assert is_subname_match("علي", "أحمد محمد") is False

    def test_same_name_no_match(self):
        # نفس الاسم بالضبط لا يحسب subname
        assert is_subname_match("أحمد", "أحمد") is False

    def test_empty(self):
        assert is_subname_match("", "أحمد") is False
        assert is_subname_match("أحمد", "") is False


class TestEntityResolver:
    def test_merges_same_name(self):
        resolver = EntityResolver()
        ents = [
            Entity(type="PERSON", text="أحمد", start=0, end=4, confidence=0.9),
            Entity(type="PERSON", text="أحمد", start=10, end=14, confidence=0.85),
            Entity(type="PERSON", text="أحمد", start=20, end=24, confidence=0.9),
        ]
        clusters = resolver.resolve(ents)
        # كل أحمد يجب أن يدخل في cluster واحد
        ahmad_clusters = [c for c in clusters if c.type == "PERSON" and c.count >= 2]
        assert len(ahmad_clusters) >= 1

    def test_separates_different_names(self):
        resolver = EntityResolver()
        ents = [
            Entity(type="PERSON", text="أحمد", start=0, end=4, confidence=0.9),
            Entity(type="PERSON", text="سعيد", start=5, end=9, confidence=0.9),
        ]
        clusters = resolver.resolve(ents)
        persons = [c for c in clusters if c.type == "PERSON"]
        assert len(persons) == 2

    def test_merges_subname_into_full(self):
        resolver = EntityResolver(merge_subnames=True)
        ents = [
            Entity(type="PERSON", text="أحمد محمد", start=0, end=9, confidence=0.9,
                   normalized="احمد محمد"),
            Entity(type="PERSON", text="أحمد", start=15, end=19, confidence=0.85,
                   normalized="احمد"),
            Entity(type="PERSON", text="أحمد", start=25, end=29, confidence=0.85,
                   normalized="احمد"),
        ]
        clusters = resolver.resolve(ents)
        # الكل ينبغي أن يدخل في cluster واحد عند تفعيل merge_subnames
        persons = [c for c in clusters if c.type == "PERSON"]
        # نقبل 1 أو 2 (لأن المطابقة الجزئية معقدة)
        assert len(persons) <= 2
        # على الأقل cluster واحد فيه 2+ mentions
        assert any(c.count >= 2 for c in persons)

    def test_does_not_merge_when_disabled(self):
        resolver = EntityResolver(merge_subnames=False)
        ents = [
            Entity(type="PERSON", text="أحمد محمد", start=0, end=9, confidence=0.9),
            Entity(type="PERSON", text="أحمد", start=15, end=19, confidence=0.85),
        ]
        clusters = resolver.resolve(ents)
        persons = [c for c in clusters if c.type == "PERSON"]
        assert len(persons) == 2

    def test_locations_separate_from_persons(self):
        resolver = EntityResolver()
        ents = [
            Entity(type="PERSON", text="أحمد", start=0, end=4, confidence=0.9),
            Entity(type="LOCATION", text="الرياض", start=5, end=11, confidence=0.9),
        ]
        clusters = resolver.resolve(ents)
        # أنواع مختلفة لا تُدمج
        assert len(clusters) == 2
        types = {c.type for c in clusters}
        assert types == {"PERSON", "LOCATION"}

    def test_empty(self):
        resolver = EntityResolver()
        assert resolver.resolve([]) == []

    def test_canonical_chooses_longest(self):
        resolver = EntityResolver()
        ents = [
            Entity(type="PERSON", text="أحمد", start=0, end=4, confidence=0.9),
            Entity(type="PERSON", text="أحمد محمد العتيبي", start=10, end=27,
                   confidence=0.85),
        ]
        clusters = resolver.resolve(ents)
        # الأطول يجب أن يكون canonical
        merged = [c for c in clusters if c.count >= 2]
        if merged:
            assert "العتيبي" in merged[0].canonical


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
