"""توليد بيانات اصطناعية بصيغ متعددة لاختبار الـ pipeline قبل وصول البيانات الحقيقية.

ينتج ملفات بنفس البنى المعروضة في الديمو (txt, srt, vtt, json, csv) في:
    data/raw/synthetic/

التشغيل:
    python scripts/generate_synthetic_transcripts.py
    python scripts/generate_synthetic_transcripts.py --count 20
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.config import PROJECT_ROOT
from src.utils.logging import get_logger

log = get_logger(__name__)


# قوالب محادثات نموذجية لكل سيناريو
TEMPLATES = {
    "logistics": [
        ("أحمد", "السلام عليكم، الشحنة جاهزة للإرسال يوم الخميس."),
        ("خالد", "وعليكم السلام. الموعد مناسب، تأكد من العربة الجديدة قبل الإرسال."),
        ("أحمد", "طيب، سأبلّغ الفريق. هل نثبت الاجتماع قبل التسليم؟"),
        ("خالد", "نعم، الساعة التاسعة صباح الاثنين عند النقطة المعتادة."),
        ("أحمد", "متفقون. سأرسل التأكيد عبر القناة نفسها."),
        ("خالد", "ممتاز. لا تنسَ التنسيق مع أبو محمد قبل البدء."),
    ],
    "meeting": [
        ("سعود", "السلام عليكم جميعاً، نبدأ الاجتماع الآن."),
        ("ريم", "وعليكم السلام، جاهزة."),
        ("فهد", "لدي ملاحظات على البنود السابقة."),
        ("سعود", "تفضل، اذكرها بالترتيب."),
        ("فهد", "البند الثالث يحتاج مراجعة من الفريق القانوني."),
        ("ريم", "أوافق، خصوصاً ما يتعلق بشروط التسليم."),
    ],
    "urgent": [
        ("أحمد", "خالد، مكالمة عاجلة. نحتاج تغيير الموعد فوراً."),
        ("خالد", "ما الذي حدث؟"),
        ("أحمد", "ظهرت مشكلة في القناة الأخرى، نحتاج بديلاً."),
        ("خالد", "حسناً، سأتواصل مع أبو محمد خلال ساعة."),
        ("أحمد", "أبلغني فور الجاهزية، الأمر طارئ."),
    ],
    "confirmation": [
        ("نورة", "تم استلام الشحنة بنجاح."),
        ("سعود", "ممتاز، هل التوقيع جاهز؟"),
        ("نورة", "نعم، أرسلته على البريد قبل قليل."),
        ("سعود", "شكراً، سأبلّغ الإدارة."),
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="توليد بيانات اصطناعية للاختبار")
    parser.add_argument("--count", type=int, default=12, help="عدد المكالمات")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="مجلد الإخراج (افتراضياً data/raw/synthetic)",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def format_timestamp_srt(seconds: float) -> str:
    """تنسيق SRT: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """تنسيق VTT: HH:MM:SS.mmm"""
    return format_timestamp_srt(seconds).replace(",", ".")


def format_timestamp_short(seconds: float) -> str:
    """تنسيق MM:SS"""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def generate_call(call_id: str, template_key: str, rng: random.Random) -> dict:
    """توليد مكالمة كاملة بكل صيغها."""
    template = TEMPLATES[template_key]
    cursor = 3.0  # ثوانٍ من بداية المكالمة
    lines = []
    for speaker, text in template:
        duration = 4.0 + rng.random() * 4.0  # 4-8 ثوانٍ لكل سطر
        line = {
            "speaker": speaker,
            "start_sec": cursor,
            "end_sec": cursor + duration,
            "text": text,
            "confidence": round(0.82 + rng.random() * 0.16, 2),
        }
        lines.append(line)
        cursor += duration + rng.random() * 1.5  # توقّف صغير

    return {
        "call_id": call_id,
        "topic": template_key,
        "duration_sec": cursor,
        "lines": lines,
    }


def write_txt(call: dict, path: Path) -> None:
    """صيغة TXT بسيطة: 'متحدث: نص'."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Call ID: {call['call_id']}  |  Topic: {call['topic']}\n\n")
        for line in call["lines"]:
            ts = format_timestamp_short(line["start_sec"])
            f.write(f"[{ts}] {line['speaker']}: {line['text']}\n")


def write_srt(call: dict, path: Path) -> None:
    """صيغة SRT (ترجمة الفيديو)."""
    with open(path, "w", encoding="utf-8") as f:
        for i, line in enumerate(call["lines"], 1):
            f.write(f"{i}\n")
            f.write(
                f"{format_timestamp_srt(line['start_sec'])} --> "
                f"{format_timestamp_srt(line['end_sec'])}\n"
            )
            f.write(f"{line['speaker']}: {line['text']}\n\n")


def write_vtt(call: dict, path: Path) -> None:
    """صيغة WebVTT."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for line in call["lines"]:
            f.write(
                f"{format_timestamp_vtt(line['start_sec'])} --> "
                f"{format_timestamp_vtt(line['end_sec'])}\n"
            )
            f.write(f"<v {line['speaker']}>{line['text']}\n\n")


def write_json(call: dict, path: Path) -> None:
    """صيغة JSON بنفس بنية الديمو."""
    segments = [
        {
            "start": line["start_sec"],
            "end": line["end_sec"],
            "speaker": line["speaker"],
            "text": line["text"],
            "confidence": line["confidence"],
        }
        for line in call["lines"]
    ]
    payload = {
        "call_id": call["call_id"],
        "topic": call["topic"],
        "duration_sec": round(call["duration_sec"], 2),
        "language": "ar",
        "segments": segments,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def write_csv(call: dict, path: Path) -> None:
    """صيغة CSV لمن يعالج البيانات في Excel/Pandas."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end", "speaker", "text", "confidence"])
        for line in call["lines"]:
            writer.writerow(
                [
                    f"{line['start_sec']:.2f}",
                    f"{line['end_sec']:.2f}",
                    line["speaker"],
                    line["text"],
                    line["confidence"],
                ]
            )


def main() -> int:
    args = parse_args()
    rng = random.Random(args.seed)

    output_dir = args.output_dir or (PROJECT_ROOT / "data" / "raw" / "synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    template_keys = list(TEMPLATES.keys())

    log.info(f"توليد {args.count} مكالمة اصطناعية في {output_dir}")
    summary = []

    for i in range(1, args.count + 1):
        call_id = f"SYN-{i:03d}"
        topic = rng.choice(template_keys)
        call = generate_call(call_id, topic, rng)

        # كتابة الصيغ الخمس لكل مكالمة
        formats = {
            "txt": write_txt,
            "srt": write_srt,
            "vtt": write_vtt,
            "json": write_json,
            "csv": write_csv,
        }
        for ext, writer_fn in formats.items():
            sub_dir = output_dir / ext
            sub_dir.mkdir(exist_ok=True)
            writer_fn(call, sub_dir / f"{call_id}.{ext}")

        summary.append(
            {
                "call_id": call_id,
                "topic": topic,
                "duration_sec": round(call["duration_sec"], 2),
                "lines_count": len(call["lines"]),
                "speakers": sorted({l["speaker"] for l in call["lines"]}),
            }
        )

    # سجل ملخص
    with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_count": len(summary),
                "formats": ["txt", "srt", "vtt", "json", "csv"],
                "calls": summary,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    log.info(f"✅ تم توليد {len(summary)} مكالمة في 5 صيغ")
    log.info(f"📁 الملخص: {output_dir / 'summary.json'}")
    log.info(f"💡 جرّب رفع أحد ملفات .txt على واجهة الديمو لاختبارها")
    return 0


if __name__ == "__main__":
    sys.exit(main())
