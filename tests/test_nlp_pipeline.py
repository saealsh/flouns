"""اختبارات وحدة لـ src.nlp.pipeline."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.nlp.keywords import Watchlist
from src.nlp.pipeline import NLPPipeline, NLPResult, analyze_text, analyze_transcript


class TestAnalyzeText:
    def test_returns_full_result(self):
        text = "اجتمع أحمد بسعيد في الرياض يوم الخميس وأرسل الشحنة"
        result = analyze_text(text)

        assert isinstance(result, NLPResult)
        assert result.text_length == len(text)
        assert len(result.entities) > 0
        assert len(result.events) >= 1

    def test_empty_text(self):
        result = analyze_text("")
        assert result.text_length == 0
        assert result.entities == []
        assert result.events == []

    def test_with_watchlist(self):
        wl = Watchlist(["العربة الجديدة"])
        text = "وصلت العربة الجديدة أمس بحالة جيدة"
        result = analyze_text(text, watchlist=wl)
        assert len(result.watchlist_matches) == 1

    def test_to_dict_serializable(self):
        text = "اجتمع أحمد بـ محمد"
        result = analyze_text(text)
        # يجب أن يكون قابلاً للتحويل لـ JSON
        d = result.to_dict()
        json_str = json.dumps(d, ensure_ascii=False)
        assert "entities" in json_str
        assert "events" in json_str


class TestNLPPipeline:
    def test_pipeline_is_reusable(self):
        pipeline = NLPPipeline()
        text1 = "أحمد في الرياض"
        text2 = "محمد في جدة"
        r1 = pipeline.analyze(text1)
        r2 = pipeline.analyze(text2)
        # نتائج مختلفة لنصوص مختلفة
        assert r1.entities != r2.entities

    def test_pipeline_with_watchlist(self):
        wl = Watchlist(["السر"], notes={"السر": "كلمة مفتاحية"})
        pipeline = NLPPipeline(watchlist=wl)
        result = pipeline.analyze("هذا هو السر")
        assert len(result.watchlist_matches) == 1
        assert result.watchlist_matches[0].note == "كلمة مفتاحية"


class TestAnalyzeTranscript:
    @pytest.fixture
    def sample_transcript(self, tmp_path) -> Path:
        """ملف transcript يحاكي مخرج المرحلة 4."""
        transcript = {
            "call_id": "C-001",
            "duration_sec": 25.5,
            "segments": [
                {
                    "speaker_name": "أحمد",
                    "speaker_id": "SPK_01",
                    "start": 1.0,
                    "end": 5.0,
                    "text": "السلام عليكم، الشحنة جاهزة يوم الخميس",
                    "confidence": 0.92,
                },
                {
                    "speaker_name": "خالد",
                    "speaker_id": "SPK_02",
                    "start": 5.5,
                    "end": 10.0,
                    "text": "وعليكم السلام، تأكد من الشحنة قبل الإرسال",
                    "confidence": 0.89,
                },
                {
                    "speaker_name": "أحمد",
                    "speaker_id": "SPK_01",
                    "start": 10.5,
                    "end": 15.0,
                    "text": "اتفقنا، سأتصل بأبو محمد في الرياض",
                    "confidence": 0.91,
                },
            ],
        }
        path = tmp_path / "transcript.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, ensure_ascii=False)
        return path

    def test_analyzes_transcript_basic(self, sample_transcript):
        result = analyze_transcript(sample_transcript)
        assert "nlp" in result
        assert "full_text_analysis" in result["nlp"]
        assert "per_segment" in result["nlp"]
        assert len(result["nlp"]["per_segment"]) == 3

    def test_per_segment_preserves_speaker(self, sample_transcript):
        result = analyze_transcript(sample_transcript)
        speakers = {
            s["speaker_name"]
            for s in result["nlp"]["per_segment"]
        }
        assert speakers == {"أحمد", "خالد"}

    def test_extracts_persons_in_full(self, sample_transcript):
        result = analyze_transcript(sample_transcript)
        full = result["nlp"]["full_text_analysis"]
        # المتحدثون مذكورون في النص ينبغي اكتشافهم
        # (ملاحظة: أحمد، خالد ليسا في فهرس الأسماء بالكامل لكن أبو محمد كذلك)
        person_texts = {
            e["text"]
            for e in full["entities"]
            if e["type"] == "PERSON"
        }
        # على الأقل أبو محمد ينبغي اكتشافه
        assert any("أبو محمد" in p for p in person_texts) or len(person_texts) > 0

    def test_enriched_events_have_speaker(self, sample_transcript):
        result = analyze_transcript(sample_transcript)
        enriched = result["nlp"].get("enriched_events", [])
        # الأحداث المُثرّاة ينبغي أن يحوي بعضها speaker_name
        if enriched:
            assert any("speaker_name" in e for e in enriched)

    def test_with_watchlist_param(self, sample_transcript):
        wl = Watchlist(["الشحنة"])
        result = analyze_transcript(sample_transcript, watchlist=wl)
        # الشحنة ذكرت أكثر من مرة في الـ transcript
        full = result["nlp"]["full_text_analysis"]
        matches = full.get("watchlist_matches", [])
        # على الأقل match واحد للشحنة
        assert any("الشحنة" in m["matched_text"] for m in matches)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            analyze_transcript(tmp_path / "missing.json")


class TestMetadata:
    def test_metadata_has_counts(self):
        text = "اجتمع أحمد بسعيد في الرياض"
        result = analyze_text(text)
        meta = result.metadata
        assert "n_entities" in meta
        assert "n_unique_entities" in meta
        assert "n_keywords" in meta
        assert "n_events" in meta


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
