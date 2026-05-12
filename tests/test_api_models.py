"""اختبارات لـ src.api.models."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.api.models import (
    CallSegment,
    CallSummary,
    EntityResponse,
    EventResponse,
    GraphData,
    GraphLink,
    GraphNode,
    ProcessingStatus,
    ReportSummary,
    ReviewRequest,
    ReviewStatus,
    SpeakerSummary,
    UploadResponse,
)


class TestEntityResponse:
    def test_minimal_entity(self):
        e = EntityResponse(
            id="C1:PERSON:0:4",
            type="PERSON",
            text="أحمد",
            start=0, end=4,
            confidence=0.9,
        )
        assert e.review_status == ReviewStatus.PENDING

    def test_full_entity_with_review(self):
        e = EntityResponse(
            id="C1:PERSON:0:4",
            type="PERSON",
            text="أحمد",
            start=0, end=4,
            confidence=0.9,
            review_status=ReviewStatus.CONFIRMED,
            reviewed_by="user@example.com",
            review_note="مؤكَّد",
        )
        assert e.review_status == ReviewStatus.CONFIRMED
        assert e.reviewed_by == "user@example.com"


class TestCallSegment:
    def test_valid_segment(self):
        s = CallSegment(
            speaker_name="أحمد",
            speaker_id="SPK_01",
            start=0.5,
            end=5.0,
            text="السلام عليكم",
        )
        assert s.confidence == 0.8  # default

    def test_segment_serializable(self):
        s = CallSegment(
            speaker_name="أحمد",
            speaker_id="SPK_01",
            start=0.5, end=5.0,
            text="مرحباً",
        )
        d = s.model_dump()
        assert d["speaker_name"] == "أحمد"


class TestGraphData:
    def test_empty_graph(self):
        g = GraphData(nodes=[], links=[])
        assert len(g.nodes) == 0
        assert len(g.links) == 0

    def test_populated_graph(self):
        nodes = [
            GraphNode(id="n1", label="أ", type="Person", color="#10b981"),
            GraphNode(id="n2", label="ب", type="Location", color="#f59e0b"),
        ]
        links = [
            GraphLink(source="n1", target="n2", type="MET_AT", label="اجتمع في"),
        ]
        g = GraphData(nodes=nodes, links=links)
        assert g.nodes[0].label == "أ"
        assert g.links[0].label == "اجتمع في"


class TestReviewRequest:
    def test_simple_confirmation(self):
        r = ReviewRequest(
            review_status=ReviewStatus.CONFIRMED,
            reviewed_by="reviewer1",
        )
        assert r.note is None

    def test_with_note(self):
        r = ReviewRequest(
            review_status=ReviewStatus.REJECTED,
            reviewed_by="reviewer1",
            note="ليس اسم شخص",
        )
        assert r.note == "ليس اسم شخص"

    def test_with_edits(self):
        r = ReviewRequest(
            review_status=ReviewStatus.EDITED,
            reviewed_by="reviewer1",
            edits={"text": "أحمد محمد", "type": "PERSON"},
        )
        assert r.edits["text"] == "أحمد محمد"


class TestProcessingStatus:
    def test_all_values_strings(self):
        # ProcessingStatus values هي strings (للـ JSON)
        for status in ProcessingStatus:
            assert isinstance(status.value, str)

    def test_pending_processing_completed(self):
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"


class TestUploadResponse:
    def test_basic(self):
        r = UploadResponse(
            call_id="C-abc123",
            filename="test.wav",
            size_bytes=12345,
            status=ProcessingStatus.PROCESSING,
        )
        assert r.call_id == "C-abc123"
        assert r.status == ProcessingStatus.PROCESSING


class TestReportSummary:
    def test_minimal_report(self):
        r = ReportSummary(
            total_calls=5,
            total_speakers=10,
            total_entities=50,
            total_events=20,
            total_kg_nodes=80,
            total_kg_edges=120,
            nodes_by_type={"Person": 10, "Location": 5},
            edges_by_type={"MET_AT": 15},
            top_persons=[],
            top_locations=[],
            top_keywords=[],
            watchlist_alerts=3,
        )
        assert r.total_calls == 5
        assert r.nodes_by_type["Person"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
