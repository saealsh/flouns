"""اختبارات تكامل لـ API endpoints.

نستخدم TestClient من FastAPI لاختبار المسارات بدون تشغيل خادم.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient مع مخزن نظيف."""
    # نُعيّن data_root في env قبل استيراد الـ app
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setenv("CIE_DATA_ROOT", str(data_dir))
    monkeypatch.setenv("CIE_WHISPER_BACKEND", "mock")

    # نُعيد استيراد الـ app
    import importlib
    from fastapi.testclient import TestClient
    import src.api.main
    importlib.reload(src.api.main)

    with TestClient(src.api.main.app) as c:
        yield c


@pytest.fixture
def store_with_data(tmp_path):
    """مخزن مُعبّأ ببيانات للاختبار."""
    from src.api.store import DataStore

    data_dir = tmp_path / "data"
    store = DataStore(data_dir)

    transcript = {
        "call_id": "C-TEST",
        "duration_sec": 30.0,
        "language": "ar",
        "segments": [
            {"speaker_name": "أحمد", "speaker_id": "SPK_01",
             "start": 0.5, "end": 5.0, "text": "اجتمعنا في الرياض", "confidence": 0.9},
            {"speaker_name": "خالد", "speaker_id": "SPK_02",
             "start": 5.5, "end": 10.0, "text": "نعم يوم الخميس", "confidence": 0.92},
        ],
    }
    store.save_transcript("C-TEST", transcript)

    nlp = {
        **transcript,
        "nlp": {
            "full_text_analysis": {
                "entities": [
                    {"type": "LOCATION", "text": "الرياض", "start": 10, "end": 16,
                     "confidence": 0.9, "normalized": "رياض", "source": "dictionary",
                     "context": "في الرياض نعم"},
                    {"type": "DATE", "text": "الخميس", "start": 25, "end": 31,
                     "confidence": 0.85, "normalized": "الخميس", "source": "rule",
                     "context": "يوم الخميس"},
                ],
                "events": [],
                "kg_triples": [],
                "watchlist_matches": [],
                "metadata": {"n_entities": 2, "n_events": 0},
            },
            "per_segment": [],
            "enriched_events": [],
        },
    }
    store.save_nlp("C-TEST", nlp)

    # KG بسيط
    kg_data = {
        "nodes": [
            {"id": "Call:C-TEST", "label": "C-TEST", "type": "Call",
             "color": "#3b82f6", "size": 12, "properties": {}},
            {"id": "Person:ahmad", "label": "أحمد", "type": "Person",
             "color": "#10b981", "size": 14, "properties": {"mention_count": 2}},
            {"id": "Location:riyadh", "label": "الرياض", "type": "Location",
             "color": "#f59e0b", "size": 12, "properties": {"mention_count": 1}},
        ],
        "links": [
            {"source": "Person:ahmad", "target": "Call:C-TEST",
             "type": "PARTICIPATED_IN", "label": "شارك في", "weight": 1, "properties": {}},
        ],
        "metadata": {"node_count": 3, "link_count": 1},
    }
    store.save_kg_data(kg_data)

    return store, data_dir


@pytest.fixture
def client_with_data(store_with_data, monkeypatch):
    """TestClient مع بيانات مُعبَّأة."""
    _, data_dir = store_with_data
    monkeypatch.setenv("CIE_DATA_ROOT", str(data_dir))
    monkeypatch.setenv("CIE_WHISPER_BACKEND", "mock")

    import importlib
    from fastapi.testclient import TestClient
    import src.api.main
    importlib.reload(src.api.main)

    with TestClient(src.api.main.app) as c:
        yield c


class TestHealth:
    def test_health_endpoint(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_info_endpoint(self, client):
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert "calls" in data


class TestCallsEndpoints:
    def test_list_calls_empty(self, client):
        response = client.get("/api/v1/calls")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_calls_populated(self, client_with_data):
        response = client_with_data.get("/api/v1/calls")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["call_id"] == "C-TEST"

    def test_get_call_details(self, client_with_data):
        response = client_with_data.get("/api/v1/calls/C-TEST")
        assert response.status_code == 200
        data = response.json()
        assert data["call_id"] == "C-TEST"
        assert len(data["segments"]) == 2
        assert data["segments"][0]["speaker_name"] == "أحمد"

    def test_get_missing_call(self, client):
        response = client.get("/api/v1/calls/MISSING")
        assert response.status_code == 404

    def test_get_call_entities(self, client_with_data):
        response = client_with_data.get("/api/v1/calls/C-TEST/entities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        types = {e["type"] for e in data}
        assert "LOCATION" in types
        assert "DATE" in types
        # كل كيان له id ومرحلة مراجعة
        for ent in data:
            assert "id" in ent
            assert ent["review_status"] == "pending"

    def test_get_call_events_empty(self, client_with_data):
        response = client_with_data.get("/api/v1/calls/C-TEST/events")
        assert response.status_code == 200
        assert response.json() == []


class TestGraphEndpoints:
    def test_empty_graph(self, client):
        response = client.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()
        assert data["nodes"] == []

    def test_populated_graph(self, client_with_data):
        response = client_with_data.get("/api/v1/graph")
        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) == 3
        assert len(data["links"]) == 1

    def test_graph_summary(self, client_with_data):
        response = client_with_data.get("/api/v1/graph/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_nodes"] == 3
        assert "nodes_by_type" in data
        assert data["nodes_by_type"]["Person"] == 1


class TestReviewEndpoints:
    def test_submit_review_for_entity(self, client_with_data):
        # نحتاج أولاً entity_id حقيقي
        entities_response = client_with_data.get("/api/v1/calls/C-TEST/entities")
        entity = entities_response.json()[0]
        entity_id = entity["id"]

        # نُقدّم مراجعة
        response = client_with_data.post(
            f"/api/v1/calls/C-TEST/reviews/{entity_id}",
            json={
                "review_status": "confirmed",
                "reviewed_by": "tester",
                "note": "صحيح",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["review_status"] == "confirmed"
        assert data["applied"] is True

    def test_review_persists_in_entity_get(self, client_with_data):
        entities = client_with_data.get("/api/v1/calls/C-TEST/entities").json()
        entity_id = entities[0]["id"]

        client_with_data.post(
            f"/api/v1/calls/C-TEST/reviews/{entity_id}",
            json={"review_status": "rejected", "reviewed_by": "tester"},
        )

        # نقرأ الكيانات مجدداً
        updated = client_with_data.get("/api/v1/calls/C-TEST/entities").json()
        confirmed_entity = next(e for e in updated if e["id"] == entity_id)
        assert confirmed_entity["review_status"] == "rejected"
        assert confirmed_entity["reviewed_by"] == "tester"

    def test_list_pending_reviews(self, client_with_data):
        response = client_with_data.get("/api/v1/reviews/pending")
        assert response.status_code == 200
        data = response.json()
        # كل الكيانات في البداية pending
        assert data["total_pending"] >= 2

    def test_list_pending_excludes_reviewed(self, client_with_data):
        entities = client_with_data.get("/api/v1/calls/C-TEST/entities").json()
        entity_id = entities[0]["id"]

        # نُقدّم مراجعة لواحد
        client_with_data.post(
            f"/api/v1/calls/C-TEST/reviews/{entity_id}",
            json={"review_status": "confirmed", "reviewed_by": "tester"},
        )

        # القائمة المعلَّقة يجب أن تُنقص بواحد
        response = client_with_data.get("/api/v1/reviews/pending")
        pending = response.json()["items"]
        ids = {p["entity_id"] for p in pending}
        assert entity_id not in ids


class TestReports:
    def test_report_summary(self, client_with_data):
        response = client_with_data.get("/api/v1/reports/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_calls"] == 1
        assert data["total_entities"] == 2
        assert data["total_kg_nodes"] == 3


class TestUpload:
    def test_upload_valid_wav(self, client):
        # صوت ضوضاء بسيطة (لن يُعالج فعلاً لأن backend mock)
        wav_bytes = b"RIFF" + b"\x00" * 100  # ليس WAV حقيقي لكن المهم بايتات

        response = client.post(
            "/api/v1/uploads",
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
        )
        # قد يفشل الـ pipeline لأن البايتات ليست WAV صالحاً، لكن الـ upload نفسه ينجح
        assert response.status_code in (200, 201)
        data = response.json()
        assert "call_id" in data
        assert data["filename"] == "test.wav"

    def test_upload_rejects_unsupported_extension(self, client):
        response = client.post(
            "/api/v1/uploads",
            files={"file": ("test.exe", b"data", "application/octet-stream")},
        )
        assert response.status_code == 415

    def test_upload_empty_file(self, client):
        response = client.post(
            "/api/v1/uploads",
            files={"file": ("test.wav", b"", "audio/wav")},
        )
        assert response.status_code == 400


class TestSpeakers:
    def test_list_speakers_empty(self, client):
        response = client.get("/api/v1/speakers")
        assert response.status_code == 200
        assert response.json() == []

    def test_missing_speaker(self, client):
        response = client.get("/api/v1/speakers/SPK_999")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
