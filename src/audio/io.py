"""قراءة الصوت من أي صيغة وتطبيعه إلى WAV mono 16kHz 16-bit.

لماذا الصيغة الموحدة؟
- Whisper وpyannote يتوقعان 16kHz mono.
- ffmpeg يعالج كل صيغة معروفة، ثم نقرأ بـ soundfile (الأسرع).
- 16-bit PCM يكفي للكلام، لا حاجة لـ 24-bit أو float.

استخدام:
    from src.audio.io import load_and_normalize, save_audio

    audio, sr = load_and_normalize("call.mp3")
    save_audio(audio, sr, "call_normalized.wav")
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from src.utils.logging import get_logger

log = get_logger(__name__)

# الإعدادات الموحّدة (يجب أن تطابق configs/config.yaml)
TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1
TARGET_BIT_DEPTH = 16

# الصيغ التي يمكن لـ soundfile قراءتها مباشرة دون ffmpeg
NATIVE_FORMATS = {".wav", ".flac", ".ogg", ".aiff"}
# باقي الصيغ تحتاج ffmpeg أولاً
FFMPEG_FORMATS = {".mp3", ".m4a", ".aac", ".wma", ".opus", ".webm", ".amr", ".3gp"}


class AudioLoadError(Exception):
    """خطأ في تحميل الملف الصوتي."""


def _check_ffmpeg() -> None:
    """التأكد من توفّر ffmpeg في PATH."""
    if shutil.which("ffmpeg") is None:
        raise AudioLoadError(
            "ffmpeg غير مثبّت. ثبّته:\n"
            "  Ubuntu: sudo apt install ffmpeg\n"
            "  macOS:  brew install ffmpeg\n"
            "  Windows: https://ffmpeg.org/download.html"
        )


def _convert_with_ffmpeg(src: Path, dst: Path) -> None:
    """تحويل ملف لـ WAV mono 16kHz 16-bit عبر ffmpeg.

    Raises:
        AudioLoadError: عند فشل التحويل.
    """
    _check_ffmpeg()

    cmd = [
        "ffmpeg",
        "-y",                      # استبدال الإخراج إن وُجد
        "-i", str(src),            # المدخل
        "-ar", str(TARGET_SAMPLE_RATE),  # تردد العينة
        "-ac", str(TARGET_CHANNELS),     # القنوات
        "-sample_fmt", "s16",      # 16-bit PCM
        "-loglevel", "error",      # تقليل الضجيج في المخرج
        str(dst),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired as e:
        raise AudioLoadError(f"تجاوز ffmpeg المهلة (5 دقائق): {src}") from e

    if result.returncode != 0:
        raise AudioLoadError(
            f"فشل ffmpeg لـ {src}:\n{result.stderr.strip()}"
        )


def load_and_normalize(
    path: Path | str,
    target_sr: int = TARGET_SAMPLE_RATE,
) -> tuple[np.ndarray, int]:
    """تحميل ملف صوتي بأي صيغة وإرجاعه كـ mono float32 بالتردد المستهدف.

    Args:
        path: مسار الملف.
        target_sr: تردد العينة المستهدف (افتراضياً 16000).

    Returns:
        (audio, sample_rate) — audio بصيغة float32 في النطاق [-1, 1].

    Raises:
        FileNotFoundError: الملف غير موجود.
        AudioLoadError: فشل في القراءة أو التحويل.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"الملف غير موجود: {path}")

    ext = path.suffix.lower()
    if not ext:
        raise AudioLoadError(f"الملف بدون امتداد: {path}")

    # المسار السريع: الصيغ الأصلية
    if ext in NATIVE_FORMATS:
        try:
            audio, sr = sf.read(str(path), dtype="float32", always_2d=False)
        except Exception as e:
            raise AudioLoadError(f"تعذّر قراءة {path}: {e}") from e
    elif ext in FFMPEG_FORMATS or True:  # نحاول ffmpeg لأي صيغة غير معروفة
        # تحويل عبر ffmpeg إلى ملف مؤقت
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            _convert_with_ffmpeg(path, tmp_path)
            audio, sr = sf.read(str(tmp_path), dtype="float32", always_2d=False)
        finally:
            tmp_path.unlink(missing_ok=True)

    # دمج القنوات إن كانت ستيريو
    if audio.ndim > 1:
        audio = audio.mean(axis=1).astype(np.float32)

    # إعادة عيّنة إن لزم (نادر بعد ffmpeg، لكن للملفات الأصلية الـ wav)
    if sr != target_sr:
        try:
            import librosa  # استيراد كسول
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
        except ImportError:
            log.warning(
                f"librosa غير متاحة، يبقى التردد {sr} بدلاً من {target_sr}. "
                "قد تكون النتائج غير متوقعة."
            )

    return audio, sr


def save_audio(
    audio: np.ndarray,
    sr: int,
    path: Path | str,
    bit_depth: int = TARGET_BIT_DEPTH,
) -> None:
    """حفظ مصفوفة صوت كـ WAV.

    Args:
        audio: المصفوفة (1D، float).
        sr: تردد العينة.
        path: مسار الإخراج.
        bit_depth: 16 أو 24 أو 32.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    subtype = {16: "PCM_16", 24: "PCM_24", 32: "FLOAT"}[bit_depth]

    # قصّ الأمواج خارج النطاق لتجنّب التشبع المفاجئ
    audio = np.clip(audio, -1.0, 1.0).astype(np.float32)

    sf.write(str(path), audio, sr, subtype=subtype)
    log.debug(f"حُفظ الصوت: {path} ({len(audio) / sr:.2f}ث، {sr}Hz, {bit_depth}-bit)")


def get_audio_info(path: Path | str) -> dict:
    """قراءة الميتاداتا فقط (بدون تحميل العينات) — سريع جداً.

    Returns:
        قاموس فيه: duration_sec, sample_rate, channels, format, frames, subtype.
    """
    path = Path(path)
    try:
        info = sf.info(str(path))
        return {
            "path": str(path),
            "duration_sec": round(info.duration, 3),
            "sample_rate": info.samplerate,
            "channels": info.channels,
            "format": info.format,
            "subtype": info.subtype,
            "frames": info.frames,
        }
    except Exception as e:
        # ربما صيغة لا يدعمها soundfile، نستخدم ffprobe احتياطياً
        return _get_info_via_ffprobe(path)


def _get_info_via_ffprobe(path: Path) -> dict:
    """قراءة معلومات الملف عبر ffprobe (ل mp3/m4a/...)."""
    import json

    if shutil.which("ffprobe") is None:
        raise AudioLoadError("ffprobe غير متوفر (يأتي مع ffmpeg)")

    cmd = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_streams",
        "-select_streams", "a:0",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise AudioLoadError(f"ffprobe فشل لـ {path}: {result.stderr}")

    data = json.loads(result.stdout)
    if not data.get("streams"):
        raise AudioLoadError(f"لا قناة صوتية في {path}")

    stream = data["streams"][0]
    return {
        "path": str(path),
        "duration_sec": round(float(stream.get("duration", 0)), 3),
        "sample_rate": int(stream.get("sample_rate", 0)),
        "channels": int(stream.get("channels", 0)),
        "format": stream.get("codec_name", "unknown"),
        "subtype": stream.get("sample_fmt", "unknown"),
        "frames": int(stream.get("duration_ts", 0)),
    }
