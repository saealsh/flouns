"""اختبارات لـ src.api.store."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.api.models import ProcessingStatus
from src.api.store import DataStore, make_entity_id, make_event_id


@pytest.fixture
def store(tmp_path):
    return DataStore(tmp_path / "data")


@pytest.fixture
def sample_transcript() -> dict:
    return {
        "call_id": "C-001",
        "duration_sec": 30.0,
        "language": "ar",
        "segments": [
            {
                "speaker_name": "أحمد", "speaker_id": "SPK_01",
                "start": 0.5, "end": 5.0,
                "text": "السلام عليكم",
                "confidence": 0.9,
            },
            {
                "speaker_name": "خالد", "speaker_id": "SPK_02",
                "start": 5.5, "end": 10.0,
                "text": "وعليكم السلام",
                "confidence": 0.92,
            },
        ],
    }


@pytest.fixture
def sample_nlp() -> dict:
    return {
        "call_id": "C-001",
        "segments": [],
        "nlp": {
            "full_text_analysis": {
                "entities": [
                    {"type": "PERSON", "text": "أحمد", "start": 5, "end": 9,
                     "confidence": 0.9, "normalized": "احمد", "source": "ner",
                     "context": "السلام أحمد عليكم"},
                ],
                "events": [],
                "watchlist_matches": [
                    {"term": "السلام", "matched_text": "السلام",
                     "start": 0, "end": 6, "note": ""},
                ],
                "metadata": {},
            },
            "per_segment": [],
            "enriched_events": [],
        },
    }


class TestDataStoreInit:
    def test_creates_directories(self, tmp_path):
        store = DataStore(tmp_path / "data")
        assert store.transcripts_dir.exists()
        assert store.nlp_dir.exists()
        assert store.kg_dir.exists()
        assert store.reviews_dir.exists()


class TestCalls:
    def test_empty_store_has_no_calls(self, store):
        assert store.list_call_ids() == []

    def test_save_and_retrieve_transcript(self, store, sample_transcript):
        store.save_transcript("C-001", sample_transcript)
        retrieved = store.get_call_transcript("C-001")
        assert retrieved is not None
        assert retrieved["call_id"] == "C-001"

    def test_list_includes_saved(self, store, sample_transcript):
        store.save_transcript("C-001", sample_transcript)
        store.save_transcript("C-002", sample_transcript)
        ids = store.list_call_ids()
        assert "C-001" in ids
        assert "C-002" in ids

    def test_get_missing_returns_none(self, store):
        assert store.get_call_transcript("MISSING") is None

    def test_call_summary_basic(self, store, sample_transcript):
        store.save_transcript("C-001", sample_transcript)
        summary = store.get_call_summary("C-001")
        assert summary["call_id"] == "C-001"
        assert summary["n_segments"] == 2
        assert summary["n_speakers"] == 2

    def test_call_summary_with_nlp(self, store, sample_transcript, sample_nlp):
        store.save_transcript("C-001", sample_transcript)
        store.save_nlp("C-001", sample_nlp)
        summary = store.get_call_summary("C-001")
        assert summary["has_nlp"] is True
        assert summary["watchlist_hits"] == 1


class TestUploads:
    def test_save_upload(self, store):
        content = b"fake audio bytes"
        call_id, path = store.save_upload("test.wav", content)
        assert call_id.startswith("C-")
        assert path.exists()
        assert path.read_bytes() == content

    def test_get_upload_path(self, store):
        content = b"test"
        call_id, _ = store.save_upload("file.wav", content)
        path = store.get_upload_path(call_id)
        assert path is not None
        assert path.exists()

    def test_same_content_same_id(self, store):
        content = b"same content"
        c1, _ = store.save_upload("a.wav", content)
        c2, _ = store.save_upload("b.wav", content)
        # نفس المحتوى → نفس الـ ID
        assert c1 == c2


class TestReviews:
    def test_no_reviews_initially(self, store):
        assert store.get_reviews("C-001") == {}

    def test_save_review(self, store):
        review = {
            "review_status": "confirmed",
            "reviewed_by": "user1",
            "note": "صحيح",
        }
        store.save_review("C-001", "entity_1", review)
        retrieved = store.get_review_for("C-001", "entity_1")
        assert retrieved is not None
        assert retrieved["review_status"] == "confirmed"
        assert "reviewed_at" in retrieved

    def test_multiple_reviews_same_call(self, store):
        store.save_review("C-001", "e1", {"review_status": "confirmed", "reviewed_by": "u"})
        store.save_review("C-001", "e2", {"review_status": "rejected", "reviewed_by": "u"})
        all_reviews = store.get_reviews("C-001")
        assert len(all_reviews) == 2

    def test_update_existing_review(self, store):
        store.save_review("C-001", "e1", {"review_status": "pending", "reviewed_by": "u"})
        store.save_review("C-001", "e1", {"review_status": "confirmed", "reviewed_by": "u"})
        r = store.get_review_for("C-001", "e1")
        assert r["review_status"] == "confirmed"


class TestJobs:
    def test_create_job(self, store):
        job_id = store.create_job("C-001")
        assert job_id.startswith("job_")
        job = store.get_job(job_id)
        assert job is not None
        assert job["call_id"] == "C-001"
        assert job["status"] == "pending"

    def test_update_job(self, store):
        job_id = store.create_job("C-001")
        store.update_job(job_id, status="completed", progress=1.0)
        job = store.get_job(job_id)
        assert job["status"] == "completed"
        assert job["progress"] == 1.0

    def test_get_missing_job(self, store):
        assert store.get_job("missing") is None

    def test_list_recent_jobs(self, store):
        ids = [store.create_job(f"C-{i:03d}") for i in range(5)]
        recent = store.list_recent_jobs(limit=3)
        assert len(recent) == 3


class TestEntityIds:
    def test_consistent_entity_id(self):
        ent = {"type": "PERSON", "start": 0, "end": 4}
        id1 = make_entity_id("C-001", ent)
        id2 = make_entity_id("C-001", ent)
        assert id1 == id2

    def test_different_calls_different_ids(self):
        ent = {"type": "PERSON", "start": 0, "end": 4}
        assert make_entity_id("C-001", ent) != make_entity_id("C-002", ent)

    def test_event_id(self):
        ev = {"action": "send", "sentence_start": 10}
        assert make_event_id("C-001", ev) == "C-001:event:10:send"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
