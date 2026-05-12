"""توليد ملفات صوتية متنوعة لاختبار خط معالجة المرحلة 2.

ينتج 6 ملفات تمثل سيناريوهات حقيقية مختلفة:
1. clean_speech: كلام نظيف بنوبات صمت — الحالة المثالية.
2. noisy_speech: كلام مع ضوضاء خلفية ثابتة — يحتاج معالجة.
3. continuous_speech: كلام متواصل بدون صمت — لقياس SNR بدون مرجع.
4. silent: ملف صامت تماماً — يجب رفضه.
5. clipped: مشبَّع — تشويه واضح.
6. mixed_dialogue: محادثة بصوتين مختلفين (250Hz و500Hz) — يشبه حواراً.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import soundfile as sf

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "test_samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SR = 16000


def make_speech_like(duration: float, freq: float = 200, amp: float = 0.4) -> np.ndarray:
    """موجة تشبه الكلام: تركيب جيبيات + ظرف amplitude متغيّر."""
    t = np.linspace(0, duration, int(SR * duration), endpoint=False)
    # تركيب 3 ترددات لمحاكاة طيف الكلام
    signal = (
        amp * np.sin(2 * np.pi * freq * t)
        + 0.5 * amp * np.sin(2 * np.pi * freq * 2 * t)
        + 0.3 * amp * np.sin(2 * np.pi * freq * 3 * t)
    )
    # ظرف يتذبذب لمحاكاة المقاطع
    envelope = 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 4 * t))
    return (signal * envelope).astype(np.float32)


def make_silence(duration: float) -> np.ndarray:
    return np.zeros(int(SR * duration), dtype=np.float32)


def make_noise(duration: float, amp: float = 0.005) -> np.ndarray:
    rng = np.random.default_rng(42)
    return (amp * rng.standard_normal(int(SR * duration))).astype(np.float32)


def main() -> None:
    # 1. كلام نظيف: صمت → كلام → صمت → كلام → صمت
    clean = np.concatenate([
        make_silence(0.5),
        make_speech_like(1.5),
        make_silence(0.7),
        make_speech_like(1.2, freq=180),
        make_silence(0.5),
    ])
    sf.write(str(OUT_DIR / "clean_speech.wav"), clean, SR)

    # 2. كلام صاخب: نفس الأعلاه + ضوضاء خفيفة
    noisy = clean + make_noise(len(clean) / SR, amp=0.02)
    noisy = np.clip(noisy, -1.0, 1.0).astype(np.float32)
    sf.write(str(OUT_DIR / "noisy_speech.wav"), noisy, SR)

    # 3. كلام متواصل: لا صمت
    continuous = make_speech_like(3.0)
    sf.write(str(OUT_DIR / "continuous_speech.wav"), continuous, SR)

    # 4. صامت تماماً
    silent = make_silence(2.0)
    sf.write(str(OUT_DIR / "silent.wav"), silent, SR)

    # 5. مشبَّع: نضرب الإشارة بـ 5 ثم نقصّها
    raw = make_speech_like(2.0, amp=0.6)
    clipped = np.clip(raw * 5.0, -1.0, 1.0).astype(np.float32)
    sf.write(str(OUT_DIR / "clipped.wav"), clipped, SR)

    # 6. حوار: متحدث 1 (تردد منخفض) ثم متحدث 2 (تردد عالٍ)
    speaker1 = make_speech_like(1.5, freq=150, amp=0.4)
    speaker2 = make_speech_like(1.5, freq=350, amp=0.45)
    pause = make_silence(0.4)
    dialogue = np.concatenate([
        make_silence(0.3),
        speaker1,
        pause,
        speaker2,
        pause,
        speaker1,
        make_silence(0.3),
    ])
    sf.write(str(OUT_DIR / "mixed_dialogue.wav"), dialogue, SR)

    print(f"✅ تم توليد 6 ملفات في: {OUT_DIR}")
    for f in sorted(OUT_DIR.glob("*.wav")):
        info = sf.info(str(f))
        print(f"  • {f.name}: {info.duration:.2f}ث، {info.samplerate}Hz")


if __name__ == "__main__":
    main()
