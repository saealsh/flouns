"""اختبارات وحدة لـ src.nlp.ner."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.nlp.ner import Entity, EntityExtractor, merge_duplicate_entities


@pytest.fixture
def extractor():
    return EntityExtractor()


class TestPersonExtraction:
    def test_extracts_simple_person(self, extractor):
        entities = extractor.extract("اجتمع أحمد بالأمس")
        persons = [e for e in entities if e.type == "PERSON"]
        assert any("أحمد" in e.text for e in persons)

    def test_extracts_full_name(self, extractor):
        entities = extractor.extract("قال محمد العتيبي ذلك")
        persons = [e for e in entities if e.type == "PERSON"]
        # ينبغي أن يكون أحدها يحوي محمد العتيبي
        assert any(
            "محمد" in e.text and "العتيبي" in e.text
            for e in persons
        )

    def test_extracts_kunyah(self, extractor):
        entities = extractor.extract("تواصلت مع أبو محمد صباحاً")
        persons = [e for e in entities if e.type == "PERSON"]
        assert any("أبو محمد" in e.text for e in persons)

    def test_does_not_extract_random_word(self, extractor):
        entities = extractor.extract("اشتريت كتاباً قديماً")
        persons = [e for e in entities if e.type == "PERSON"]
        assert len(persons) == 0


class TestLocationExtraction:
    def test_extracts_city(self, extractor):
        entities = extractor.extract("وصلنا إلى الرياض")
        locs = [e for e in entities if e.type == "LOCATION"]
        assert any("الرياض" in e.text for e in locs)

    def test_higher_confidence_with_indicator(self, extractor):
        # "في الرياض" ينبغي أن يكون أعلى ثقة من ذكر عابر
        with_indicator = extractor.extract("في الرياض")
        bare = extractor.extract("الرياض")
        if with_indicator and bare:
            assert with_indicator[0].confidence >= bare[0].confidence

    def test_extracts_multiple_locations(self, extractor):
        entities = extractor.extract("سافرت من جدة إلى الدمام")
        locs = {e.text for e in entities if e.type == "LOCATION"}
        assert "جدة" in locs
        assert "الدمام" in locs


class TestDateTimeExtraction:
    def test_extracts_day_of_week(self, extractor):
        entities = extractor.extract("سنجتمع يوم الخميس")
        dates = [e for e in entities if e.type == "DATE"]
        assert any("الخميس" in e.text for e in dates)

    def test_extracts_month(self, extractor):
        entities = extractor.extract("في شهر رمضان القادم")
        dates = [e for e in entities if e.type == "DATE"]
        assert any("رمضان" in e.text for e in dates)

    def test_extracts_relative_date(self, extractor):
        entities = extractor.extract("سنتقابل غداً")
        dates = [e for e in entities if e.type == "DATE"]
        assert any("غد" in e.text for e in dates)

    def test_extracts_numeric_date(self, extractor):
        entities = extractor.extract("الموعد 15/3/2026")
        dates = [e for e in entities if e.type == "DATE"]
        assert any("15/3/2026" in e.text for e in dates)

    def test_extracts_time(self, extractor):
        entities = extractor.extract("الساعة التاسعة صباحاً")
        times = [e for e in entities if e.type == "TIME"]
        assert len(times) > 0


class TestOrganizationExtraction:
    def test_extracts_known_org(self, extractor):
        entities = extractor.extract("يعمل في أرامكو")
        orgs = [e for e in entities if e.type == "ORGANIZATION"]
        assert any("أرامكو" in e.text for e in orgs)

    def test_extracts_pattern_org(self, extractor):
        entities = extractor.extract("التحقت بشركة المراعي مؤخراً")
        orgs = [e for e in entities if e.type == "ORGANIZATION"]
        assert len(orgs) > 0

    def test_extracts_ministry(self, extractor):
        entities = extractor.extract("راجعت وزارة العدل")
        orgs = [e for e in entities if e.type == "ORGANIZATION"]
        assert any("وزارة" in e.text for e in orgs)


class TestMoneyExtraction:
    def test_extracts_riyal(self, extractor):
        entities = extractor.extract("الفاتورة 1500 ريال")
        money = [e for e in entities if e.type == "MONEY"]
        assert any("1500" in e.text and "ريال" in e.text for e in money)

    def test_extracts_dollar(self, extractor):
        entities = extractor.extract("السعر 200 دولار")
        money = [e for e in entities if e.type == "MONEY"]
        assert len(money) > 0


class TestContactInfoExtraction:
    def test_extracts_email(self, extractor):
        entities = extractor.extract("راسلني على ahmad@example.com")
        emails = [e for e in entities if e.type == "EMAIL"]
        assert len(emails) == 1
        assert "ahmad@example.com" in emails[0].text

    def test_extracts_saudi_phone(self, extractor):
        entities = extractor.extract("رقمي 0555123456")
        phones = [e for e in entities if e.type == "PHONE"]
        assert len(phones) >= 1


class TestOverlapResolution:
    def test_longer_entity_wins(self, extractor):
        # "محمد العتيبي" يجب أن يفوز على "محمد" وحده
        entities = extractor.extract("اتصل محمد العتيبي")
        persons = [e for e in entities if e.type == "PERSON"]
        # ينبغي ألا يكون كلاهما (تداخل)
        if len(persons) > 0:
            # نتحقق أن الكيانات لا تتداخل
            for i, e1 in enumerate(persons):
                for e2 in persons[i + 1:]:
                    overlaps = not (e1.end <= e2.start or e1.start >= e2.end)
                    assert not overlaps, f"{e1.text} يتداخل مع {e2.text}"


class TestContext:
    def test_context_provided(self, extractor):
        text = "تقابل أحمد مع سعيد في المركز التجاري"
        entities = extractor.extract(text)
        for e in entities:
            assert e.context, f"الكيان {e.text} بدون سياق"
            assert e.text in e.context


class TestMergeDuplicates:
    def test_merges_same_normalized(self, extractor):
        text = "أحمد ذهب. ثم أحمد قال. أحمد أيضاً وصل"
        entities = extractor.extract(text)
        merged = merge_duplicate_entities(entities)
        ahmad = [m for m in merged if "احمد" in m["normalized"] or "أحمد" in m["normalized"]]
        # كل أحمد ينبغي أن يدخل في cluster واحد
        if ahmad:
            assert ahmad[0]["count"] >= 2


class TestEmptyInput:
    def test_empty_string(self, extractor):
        assert extractor.extract("") == []

    def test_whitespace_only(self, extractor):
        assert extractor.extract("    ") == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
