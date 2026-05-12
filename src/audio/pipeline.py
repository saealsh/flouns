"""خط معالجة الصوت الموحَّد للمرحلة 2.

ينفّذ ثلاث خطوات على كل ملف:
1. تطبيع: WAV mono 16kHz 16-bit.
2. تقرير جودة: SNR، RMS، نسبة الصمت، التشبع.
3. VAD: استخلاص قطع الكلام مع طوابعها الزمنية.

الناتج لكل ملف:
    {
      "input_path": ...,
      "output_path": ...,        # الملف المُطبَّع
      "duration_sec": ...,
      "quality": {...},          # QualityMetrics
      "vad": {
        "method": "energy",
        "speech_segments": [(start, end), ...],
        "total_speech_sec": ...,
        "speech_ratio": ...,     # نسبة الكلام للمدة الكلية
      },
      "status": "ok" | "warning" | "failed",
      "warnings": [...]
    }

استخدام:
    from src.audio.pipeline import process_audio_file

    report = process_audio_file("call.mp3", output_dir="data/processed")
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.audio.io import AudioLoadError, load_and_normalize, save_audio
from src.audio.quality import QualityMetrics, compute_quality_metrics
from src.audio.vad import VADMethod, detect_speech_segments, total_speech_duration
from src.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class ProcessingReport:
    """تقرير معالجة ملف واحد."""

    input_path: str
    output_path: str | None
    duration_sec: float
    quality: dict[str, Any]
    vad: dict[str, Any]
    status: str  # "ok" | "warning" | "failed"
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_path": self.input_path,
            "output_path": self.output_path,
            "duration_sec": self.duration_sec,
            "quality": self.quality,
            "vad": self.vad,
            "status": self.status,
            "warnings": self.warnings,
            "error": self.error,
        }


def process_audio_file(
    input_path: Path | str,
    output_dir: Path | str | None = None,
    *,
    vad_method: VADMethod = "energy",
    quality_thresholds: dict[str, float] | None = None,
    save_normalized: bool = True,
) -> ProcessingReport:
    """معالجة ملف صوتي واحد عبر الخط الكامل.

    Args:
        input_path: مسار الملف الأصلي.
        output_dir: مجلد لحفظ الملف المطبَّع. إذا None لا يُحفظ.
        vad_method: "energy" أو "silero".
        quality_thresholds: كلمات مفتاحية لـ compute_quality_metrics.
        save_normalized: حفظ الملف المطبَّع على القرص.

    Returns:
        ProcessingReport.
    """
    input_path = Path(input_path)
    thresholds = quality_thresholds or {}

    # 1. تطبيع
    try:
        audio, sr = load_and_normalize(input_path)
    except (FileNotFoundError, AudioLoadError) as e:
        return ProcessingReport(
            input_path=str(input_path),
            output_path=None,
            duration_sec=0.0,
            quality={},
            vad={},
            status="failed",
            error=str(e),
        )

    duration = audio.size / sr

    # 2. حفظ الملف المطبَّع
    output_path: Path | None = None
    if save_normalized and output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{input_path.stem}.wav"
        save_audio(audio, sr, output_path)

    # 3. الجودة
    quality: QualityMetrics = compute_quality_metrics(audio, sr, **thresholds)

    # 4. VAD
    try:
        segments = detect_speech_segments(audio, sr, method=vad_method)
        total_speech = total_speech_duration(segments)
        vad_info = {
            "method": vad_method,
            "speech_segments": [s.to_tuple() for s in segments],
            "n_segments": len(segments),
            "total_speech_sec": round(total_speech, 3),
            "speech_ratio": round(total_speech / duration, 4) if duration > 0 else 0.0,
        }
    except ImportError as e:
        log.warning(f"VAD '{vad_method}' غير متاح، استخدام energy: {e}")
        segments = detect_speech_segments(audio, sr, method="energy")
        total_speech = total_speech_duration(segments)
        vad_info = {
            "method": "energy",
            "speech_segments": [s.to_tuple() for s in segments],
            "n_segments": len(segments),
            "total_speech_sec": round(total_speech, 3),
            "speech_ratio": round(total_speech / duration, 4) if duration > 0 else 0.0,
            "fallback_reason": str(e),
        }

    # 5. تجميع الحالة والتحذيرات
    warnings: list[str] = list(quality.issues)

    if vad_info["n_segments"] == 0:
        warnings.append("VAD لم يكشف أي كلام")
    elif vad_info["speech_ratio"] < 0.1:
        warnings.append(
            f"نسبة الكلام {vad_info['speech_ratio']:.0%} منخفضة جداً"
        )

    if not quality.passes:
        status = "warning"
    elif warnings:
        status = "warning"
    else:
        status = "ok"

    return ProcessingReport(
        input_path=str(input_path),
        output_path=str(output_path) if output_path else None,
        duration_sec=round(duration, 3),
        quality=quality.to_dict(),
        vad=vad_info,
        status=status,
        warnings=warnings,
    )


def process_directory(
    input_dir: Path | str,
    output_dir: Path | str,
    *,
    extensions: tuple[str, ...] = (".wav", ".mp3", ".m4a", ".flac", ".ogg"),
    vad_method: VADMethod = "energy",
    quality_thresholds: dict[str, float] | None = None,
) -> list[ProcessingReport]:
    """معالجة كل ملفات الصوت في مجلد.

    Args:
        input_dir: مجلد المدخلات.
        output_dir: مجلد المخرجات.
        extensions: امتدادات قابلة للمعالجة.
        vad_method: طريقة VAD.
        quality_thresholds: عتبات الجودة المخصّصة.

    Returns:
        قائمة تقارير لكل ملف.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    files: list[Path] = []
    for ext in extensions:
        files.extend(input_dir.rglob(f"*{ext}"))

    if not files:
        log.warning(f"لا ملفات صوتية في {input_dir}")
        return []

    log.info(f"معالجة {len(files)} ملف من {input_dir}")
    reports = []
    for f in files:
        report = process_audio_file(
            f,
            output_dir,
            vad_method=vad_method,
            quality_thresholds=quality_thresholds,
        )
        reports.append(report)
        status_emoji = {"ok": "✅", "warning": "⚠️", "failed": "❌"}[report.status]
        log.info(f"  {status_emoji} {f.name} ({report.duration_sec:.1f}ث)")

    return reports
