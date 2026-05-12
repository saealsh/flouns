"""اختبارات لـ src.kg.builder."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.kg.backends import NetworkXBackend
from src.kg.builder import KGBuilder
from src.kg.schema import EdgeType, NodeType


@pytest.fixture
def builder():
    return KGBuilder(NetworkXBackend())


@pytest.fixture
def sample_nlp_data() -> dict:
    """بيانات تحاكي مخرج analyze_transcript من المرحلة 5."""
    return {
        "call_id": "C-TEST-001",
        "duration_sec": 25.5,
        "language": "ar",
        "segments": [
            {
                "speaker_name": "أحمد",
                "speaker_id": "SPK_01",
                "start": 1.0,
                "end": 5.0,
                "text": "السلام عليكم، الشحنة جاهزة يوم الخميس",
            },
            {
                "speaker_name": "خالد",
                "speaker_id": "SPK_02",
                "start": 5.5,
                "end": 10.0,
                "text": "وعليكم السلام، تأكد قبل الإرسال",
            },
        ],
        "nlp": {
            "full_text_analysis": {
                "entities": [
                    {
                        "type": "PERSON", "text": "أحمد",
                        "start": 0, "end": 4,
                        "confidence": 0.9, "normalized": "احمد", "source": "ner",
                    },
                    {
                        "type": "PERSON", "text": "خالد",
                        "start": 50, "end": 54,
                        "confidence": 0.9, "normalized": "خالد", "source": "ner",
                    },
                    {
                        "type": "LOCATION", "text": "الرياض",
                        "start": 100, "end": 106,
                        "confidence": 0.85, "normalized": "رياض", "source": "dictionary",
                    },
                    {
                        "type": "DATE", "text": "الخميس",
                        "start": 30, "end": 36,
                        "confidence": 0.85, "normalized": "الخميس", "source": "rule",
                    },
                ],
                "events": [],
                "kg_triples": [],
                "watchlist_matches": [
                    {
                        "term": "الشحنة",
                        "matched_text": "الشحنة",
                        "start": 20, "end": 26,
                        "note": "مادة متعقَّبة",
                    },
                ],
                "metadata": {"n_entities": 4, "n_events": 0, "n_keywords": 5},
            },
            "per_segment": [
                {
                    "speaker_name": "أحمد",
                    "speaker_id": "SPK_01",
                    "start": 1.0, "end": 5.0,
                    "text": "السلام عليكم، الشحنة جاهزة",
                    "entities": [],
                    "events": [],
                    "watchlist_matches": [],
                },
            ],
            "enriched_events": [
                {
                    "action": "send",
                    "verb_text": "أرسل",
                    "sentence": "سأرسل الشحنة إلى الرياض",
                    "sentence_start": 90,
                    "actors": [{"text": "أحمد", "normalized": "احمد"}],
                    "locations": [{"text": "الرياض", "normalized": "رياض"}],
                    "times": [],
                    "objects": [],
                    "confidence": 0.7,
                    "speaker_name": "أحمد",
                    "speaker_id": "SPK_01",
                    "segment_start": 1.0,
                    "segment_end": 5.0,
                },
            ],
        },
    }


class TestIngestCall:
    def test_creates_call_node(self, builder, sample_nlp_data):
        builder.ingest_call(sample_nlp_data)
        call_nodes = builder.backend.nodes_by_type(NodeType.CALL)
        assert len(call_nodes) == 1
        assert call_nodes[0].label == "C-TEST-001"

    def test_creates_speaker_nodes(self, builder, sample_nlp_data):
        builder.ingest_call(sample_nlp_data)
        speakers = builder.backend.nodes_by_type(NodeType.SPEAKER)
        assert len(speakers) == 2

    def test_speakers_linked_to_call(self, builder, sample_nlp_data):
        builder.ingest_call(sample_nlp_data)
        # كل متحدث يجب أن يكون له PARTICIPATED_IN → Call
        for spk in builder.backend.nodes_by_type(NodeType.SPEAKER):
            edges = builder.backend.get_edges(
                source=spk.id, edge_type=EdgeType.PARTICIPATED_IN,
            )
            assert len(edges) >= 1

    def test_entities_added(self, builder, sample_nlp_data):
        builder.ingest_call(sample_nlp_data)
        persons = builder.backend.nodes_by_type(NodeType.PERSON)
        locations = builder.backend.nodes_by_type(NodeType.LOCATION)
        dates = builder.backend.nodes_by_type(NodeType.DATE)
        assert len(persons) >= 2
        assert len(locations) >= 1
        assert len(dates) >= 1

    def test_entities_linked_to_call(self, builder, sample_nlp_data):
        builder.ingest_call(sample_nlp_data)
        # كل entity يجب أن يكون له MENTIONED_IN → Call
        for ent in builder.backend.nodes_by_type(NodeType.LOCATION):
            edges = builder.backend.get_edges(
                source=ent.id, edge_type=EdgeType.MENTIONED_IN,
            )
            assert len(edges) >= 1

    def test_watchlist_creates_keyword_node(self, builder, sample_nlp_data):
        builder.ingest_call(sample_nlp_data)
        keywords = builder.backend.nodes_by_type(NodeType.KEYWORD)
        assert len(keywords) == 1
        assert keywords[0].label == "الشحنة"

    def test_call_matches_watchlist_edge(self, builder, sample_nlp_data):
        builder.ingest_call(sample_nlp_data)
        match_edges = builder.backend.get_edges(edge_type=EdgeType.MATCHES_WATCHLIST)
        assert len(match_edges) >= 1

    def test_event_node_created(self, builder, sample_nlp_data):
        builder.ingest_call(sample_nlp_data)
        events = builder.backend.nodes_by_type(NodeType.EVENT)
        assert len(events) == 1
        assert events[0].properties["action"] == "send"

    def test_event_linked_to_actor(self, builder, sample_nlp_data):
        builder.ingest_call(sample_nlp_data)
        events = builder.backend.nodes_by_type(NodeType.EVENT)
        actor_edges = builder.backend.get_edges(
            source=events[0].id, edge_type=EdgeType.HAS_ACTOR,
        )
        assert len(actor_edges) == 1

    def test_event_linked_to_location(self, builder, sample_nlp_data):
        builder.ingest_call(sample_nlp_data)
        events = builder.backend.nodes_by_type(NodeType.EVENT)
        loc_edges = builder.backend.get_edges(
            source=events[0].id, edge_type=EdgeType.OCCURRED_AT,
        )
        assert len(loc_edges) == 1


class TestIngestFromFile:
    def test_ingest_from_file(self, builder, sample_nlp_data, tmp_path):
        path = tmp_path / "call.nlp.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sample_nlp_data, f, ensure_ascii=False)
        result = builder.ingest_call_from_file(path)
        assert result["call_id"] == "C-TEST-001"
        assert result["nodes_added"] > 0

    def test_missing_file_raises(self, builder, tmp_path):
        with pytest.raises(FileNotFoundError):
            builder.ingest_call_from_file(tmp_path / "missing.json")


class TestIngestDirectory:
    def test_ingest_multiple_calls(self, builder, sample_nlp_data, tmp_path):
        # نُنشئ 3 ملفات بنفس البنية لكن call_id مختلف
        for i in range(3):
            data = {**sample_nlp_data, "call_id": f"C-MULTI-{i:03d}"}
            with open(tmp_path / f"call_{i}.nlp.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

        result = builder.ingest_directory(tmp_path)
        assert result["n_files"] == 3
        # ثلاث Call عقد، نفس الـ Speakers والـ Persons (يتم دمجها)
        assert len(builder.backend.nodes_by_type(NodeType.CALL)) == 3


class TestPersonsLinkedAcrossCalls:
    def test_same_person_in_multiple_calls(self, builder, sample_nlp_data, tmp_path):
        """نفس الشخص في مكالمتين يدمج في عقدة واحدة مع mention_count مرتفع."""
        # مكالمتان مع نفس الأشخاص
        for i in range(2):
            data = {**sample_nlp_data, "call_id": f"C-{i:03d}"}
            builder.ingest_call(data)

        persons = builder.backend.nodes_by_type(NodeType.PERSON)
        # عدد الأشخاص الفريد لم يزد
        assert len(persons) == 2
        # mention_count زاد
        for p in persons:
            assert p.properties.get("mention_count", 0) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
