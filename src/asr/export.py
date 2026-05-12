"""تصدير التفريغ المحاذى لصيغ متعددة.

الصيغ المدعومة:
- **JSON**: البنية الكاملة (مع كلمات وثقة).
- **TXT**: قراءة بشرية: [HH:MM:SS] متحدث: نص.
- **SRT**: ترجمات فيديو معيارية.
- **VTT**: WebVTT (الويب).
- **Demo JSON**: نفس بنية SEED_TRANSCRIPTS في الديمو (لرفعها مباشرة).

استخدام:
    from src.asr.export import export_aligned_transcript

    export_aligned_transcript(aligned, "output/C-001", formats=["json", "srt", "txt"])
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from src.asr.alignment import AlignedTranscript
from src.utils.logging import get_logger

log = get_logger(__name__)


def _fmt_timestamp_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _fmt_timestamp_vtt(seconds: float) -> str:
    return _fmt_timestamp_srt(seconds).replace(",", ".")


def _fmt_timestamp_short(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def export_json(transcript: AlignedTranscript, path: Path) -> None:
    """تصدير JSON كامل (بكل التفاصيل)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(transcript.to_dict(), f, ensure_ascii=False, indent=2)


def export_txt(transcript: AlignedTranscript, path: Path) -> None:
    """تصدير TXT للقراءة البشرية."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Call ID: {transcript.call_id}\n")
        f.write(f"# Duration: {transcript.duration_sec:.2f}s\n")
        f.write(f"# Language: {transcript.language}\n")
        f.write(f"# Avg Confidence: {transcript.avg_confidence:.2%}\n")
        f.write(f"# Speakers: {', '.join(s['speaker_name'] for s in transcript.speakers)}\n\n")

        for seg in transcript.segments:
            ts = _fmt_timestamp_short(seg.start)
            conf_marker = "" if seg.confidence > 0.85 else f" (⚠️ {seg.confidence:.0%})"
            f.write(f"[{ts}] {seg.speaker_name}: {seg.text}{conf_marker}\n")


def export_srt(transcript: AlignedTranscript, path: Path) -> None:
    """تصدير ترجمة SRT (تنسيق الفيديو القياسي)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(transcript.segments, 1):
            f.write(f"{i}\n")
            f.write(f"{_fmt_timestamp_srt(seg.start)} --> {_fmt_timestamp_srt(seg.end)}\n")
            f.write(f"{seg.speaker_name}: {seg.text}\n\n")


def export_vtt(transcript: AlignedTranscript, path: Path) -> None:
    """تصدير WebVTT."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        f.write(f"NOTE Call ID: {transcript.call_id}\n\n")
        for seg in transcript.segments:
            f.write(f"{_fmt_timestamp_vtt(seg.start)} --> {_fmt_timestamp_vtt(seg.end)}\n")
            f.write(f"<v {seg.speaker_name}>{seg.text}\n\n")


def export_csv(transcript: AlignedTranscript, path: Path) -> None:
    """تصدير CSV (لـ Excel/Pandas)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end", "duration", "speaker_id", "speaker_name", "text", "confidence"])
        for seg in transcript.segments:
            writer.writerow([
                f"{seg.start:.2f}",
                f"{seg.end:.2f}",
                f"{seg.duration:.2f}",
                seg.speaker_id or "",
                seg.speaker_name,
                seg.text,
                f"{seg.confidence:.4f}",
            ])


def export_demo_format(transcript: AlignedTranscript, path: Path) -> None:
    """تصدير بصيغة SEED_TRANSCRIPTS من الديمو (للرفع المباشر).

    البنية:
        [
          {
            "call_id": "C-001",
            "speaker_name": "أحمد",
            "speaker_slot": 1,
            "time_stamp": "00:03",
            "text": "...",
            "confidence": 0.91
          },
          ...
        ]
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # ترتيب المتحدثين بالظهور الأول → speaker_slot 1, 2, 3...
    speaker_slots: dict[str, int] = {}
    for seg in transcript.segments:
        key = seg.speaker_id or seg.speaker_name
        if key not in speaker_slots:
            speaker_slots[key] = len(speaker_slots) + 1

    rows = []
    for seg in transcript.segments:
        key = seg.speaker_id or seg.speaker_name
        rows.append({
            "call_id": transcript.call_id,
            "speaker_name": seg.speaker_name,
            "speaker_slot": speaker_slots[key],
            "time_stamp": _fmt_timestamp_short(seg.start),
            "text": seg.text,
            "confidence": round(seg.confidence, 2),
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


_EXPORTERS = {
    "json": (export_json, ".json"),
    "txt": (export_txt, ".txt"),
    "srt": (export_srt, ".srt"),
    "vtt": (export_vtt, ".vtt"),
    "csv": (export_csv, ".csv"),
    "demo": (export_demo_format, ".demo.json"),
}


def export_aligned_transcript(
    transcript: AlignedTranscript,
    output_path: Path | str,
    formats: list[str] | None = None,
) -> dict[str, Path]:
    """تصدير لعدة صيغ دفعة واحدة.

    Args:
        transcript: التفريغ المحاذى.
        output_path: المسار الأساسي (بدون امتداد).
        formats: قائمة الصيغ. إن None، تُصدَّر كلها.

    Returns:
        قاموس {format: path} للملفات المُصدَّرة.
    """
    if formats is None:
        formats = list(_EXPORTERS.keys())

    base = Path(output_path)
    base.parent.mkdir(parents=True, exist_ok=True)

    results = {}
    for fmt in formats:
        if fmt not in _EXPORTERS:
            log.warning(f"صيغة غير معروفة: {fmt}")
            continue
        exporter, ext = _EXPORTERS[fmt]
        path = base.with_suffix(ext)
        try:
            exporter(transcript, path)
            results[fmt] = path
            log.debug(f"  • {fmt}: {path}")
        except Exception as e:
            log.error(f"فشل تصدير {fmt}: {e}")

    return results
