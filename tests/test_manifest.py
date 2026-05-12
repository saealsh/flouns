"""اختبارات وحدة لـ src.ingestion.manifest."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.ingestion.manifest import (
    load_manifest,
    make_clip_record,
    merge_manifests,
    save_manifest,
    utcnow_iso,
)


def test_utcnow_iso_format():
    ts = utcnow_iso()
    # الصيغة: 2026-05-10T12:00:00Z
    assert len(ts) == 20
    assert ts.endswith("Z")
    assert ts[10] == "T"


def test_make_clip_record_minimal():
    rec = make_clip_record(
        clip_id="test_001",
        source="test",
        audio_path="data/raw/test.wav",
        transcript="مرحباً",
        duration_sec=3.5,
    )
    assert rec["clip_id"] == "test_001"
    assert rec["transcript"] == "مرحباً"
    assert rec["duration_sec"] == 3.5
    assert rec["language"] == "ar"
    assert rec["split"] == "unassigned"
    assert "ingested_at" in rec


def test_make_clip_record_with_extras():
    rec = make_clip_record(
        clip_id="test_002",
        source="cv",
        audio_path="x.wav",
        transcript="نص",
        duration_sec=1.0,
        speaker_id="spk_abc",
        gender="female",
        dialect="gulf",
        extra={"age": "twenties"},
    )
    assert rec["speaker_id"] == "spk_abc"
    assert rec["gender"] == "female"
    assert rec["dialect"] == "gulf"
    assert rec["extra"]["age"] == "twenties"


def test_save_and_load_manifest(tmp_path):
    records = [
        make_clip_record("c1", "src", "a.wav", "نص أول", 2.0),
        make_clip_record("c2", "src", "b.wav", "نص ثانٍ", 3.5),
    ]
    path = tmp_path / "manifest.json"
    save_manifest(records, path)

    assert path.exists()
    loaded = load_manifest(path)
    assert loaded["total_clips"] == 2
    assert loaded["total_duration_sec"] == 5.5
    assert len(loaded["clips"]) == 2
    assert loaded["clips"][0]["transcript"] == "نص أول"


def test_load_manifest_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_manifest(tmp_path / "missing.json")


def test_arabic_preserved_in_manifest(tmp_path):
    """تأكد من أن العربية لا تُهرَّب لـ \\uXXXX."""
    rec = make_clip_record("c", "s", "a.wav", "السلام عليكم", 1.0)
    path = tmp_path / "m.json"
    save_manifest([rec], path)
    raw = path.read_text(encoding="utf-8")
    assert "السلام عليكم" in raw
    assert "\\u0627" not in raw  # ليس مهرّباً


def test_merge_manifests_deduplicates(tmp_path):
    m1 = {"clips": [make_clip_record("a", "s", "x.wav", "نص", 1.0)]}
    m2 = {"clips": [
        make_clip_record("a", "s", "x.wav", "نص مكرر", 1.0),  # نفس clip_id
        make_clip_record("b", "s", "y.wav", "نص ثانٍ", 2.0),
    ]}
    merged = merge_manifests([m1, m2])
    assert len(merged) == 2
    ids = {r["clip_id"] for r in merged}
    assert ids == {"a", "b"}
    # الأول يُبقى (نص الأصلي)
    a_record = next(r for r in merged if r["clip_id"] == "a")
    assert a_record["transcript"] == "نص"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
