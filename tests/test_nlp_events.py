"""اختبارات وحدة لـ src.nlp.events."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.nlp.events import (
    EventExtractor,
    events_to_kg_triples,
    group_events_by_actor,
    split_sentences,
)
from src.nlp.ner import EntityExtractor


@pytest.fixture
def extractor():
    return EventExtractor()


@pytest.fixture
def ner():
    return EntityExtractor()


class TestSentenceSplit:
    def test_splits_on_period(self):
        sents = split_sentences("جملة أولى. جملة ثانية. ثالثة.")
        assert len(sents) == 3

    def test_preserves_positions(self):
        text = "أولى. ثانية. ثالثة."
        sents = split_sentences(text)
        for s, pos in sents:
            assert text[pos:pos + len(s)] == s

    def test_handles_question_marks(self):
        sents = split_sentences("هل أنت بخير؟ نعم.")
        assert len(sents) == 2

    def test_single_sentence(self):
        sents = split_sentences("جملة واحدة بدون نقطة")
        assert len(sents) == 1

    def test_empty(self):
        assert split_sentences("") == []


class TestEventExtraction:
    def test_extracts_meeting_event(self, extractor, ner):
        text = "اجتمع أحمد بسعيد في الرياض"
        entities = ner.extract(text)
        events = extractor.extract(text, entities=entities)
        # ينبغي أن يكون هناك حدث meet
        meet_events = [e for e in events if e.action == "meet"]
        assert len(meet_events) >= 1

    def test_extracts_send_event(self, extractor, ner):
        text = "أرسل خالد الشحنة يوم الخميس"
        entities = ner.extract(text)
        events = extractor.extract(text, entities=entities)
        send_events = [e for e in events if e.action == "send"]
        assert len(send_events) >= 1

    def test_event_includes_actors(self, extractor, ner):
        text = "اتصل محمد بأحمد"
        entities = ner.extract(text)
        events = extractor.extract(text, entities=entities)
        if events:
            # يجب أن يكون فيه actor واحد على الأقل
            assert any(len(e.actors) >= 1 for e in events)

    def test_event_includes_time(self, extractor, ner):
        text = "وصلت الشحنة يوم الجمعة"
        entities = ner.extract(text)
        events = extractor.extract(text, entities=entities)
        if events:
            # ينبغي أن أحدها فيه time أو date
            has_time = any(
                len(e.times) >= 1 for e in events
            )
            assert has_time

    def test_event_includes_location(self, extractor, ner):
        text = "اجتمعنا في الرياض"
        entities = ner.extract(text)
        events = extractor.extract(text, entities=entities)
        if events:
            has_location = any(
                len(e.locations) >= 1 for e in events
            )
            assert has_location

    def test_no_event_without_verb(self, extractor):
        text = "السماء زرقاء جداً اليوم"
        events = extractor.extract(text)
        # لا أفعال حدث → لا events
        assert events == []

    def test_multiple_events_in_paragraph(self, extractor, ner):
        text = "اجتمع أحمد بسعيد. ثم أرسل الشحنة. ووصل إلى الرياض."
        entities = ner.extract(text)
        events = extractor.extract(text, entities=entities)
        # على الأقل ٢ حدثين
        assert len(events) >= 2

    def test_confidence_increases_with_context(self, extractor, ner):
        # حدث بسياق ثري vs حدث بدون سياق
        rich = "اجتمع أحمد بسعيد في الرياض يوم الخميس"
        poor = "اجتمع"

        rich_ent = ner.extract(rich)
        poor_ent = ner.extract(poor)

        rich_events = extractor.extract(rich, entities=rich_ent)
        poor_events = extractor.extract(poor, entities=poor_ent)

        if rich_events and poor_events:
            assert rich_events[0].confidence > poor_events[0].confidence


class TestGroupByActor:
    def test_groups_correctly(self, extractor, ner):
        text = "أرسل أحمد الشحنة. ثم اتصل أحمد"
        entities = ner.extract(text)
        events = extractor.extract(text, entities=entities)
        grouped = group_events_by_actor(events)
        # يجب أن يكون "أحمد" مفتاحاً
        ahmad_keys = [k for k in grouped if "احمد" in k.lower() or "أحمد" in k]
        assert len(ahmad_keys) >= 1


class TestKGTriples:
    def test_actor_at_location(self, extractor, ner):
        text = "اجتمع أحمد في الرياض"
        entities = ner.extract(text)
        events = extractor.extract(text, entities=entities)
        triples = events_to_kg_triples(events)
        # يجب أن يكون فيه triple بعلاقة meet_at
        at_triples = [t for t in triples if "_at" in t["relation"]]
        assert len(at_triples) >= 1

    def test_actor_with_actor(self, extractor, ner):
        text = "اجتمع أحمد مع سعيد"
        entities = ner.extract(text)
        events = extractor.extract(text, entities=entities)
        triples = events_to_kg_triples(events)
        with_triples = [t for t in triples if "_with" in t["relation"]]
        assert len(with_triples) >= 1

    def test_triple_structure(self, extractor, ner):
        text = "أرسل أحمد الشحنة إلى الرياض"
        entities = ner.extract(text)
        events = extractor.extract(text, entities=entities)
        triples = events_to_kg_triples(events)
        for t in triples:
            assert "subject" in t
            assert "relation" in t
            assert "object" in t
            assert "attributes" in t


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
