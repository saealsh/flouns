"""تشغيل API الخادم.

أمثلة:
    # تشغيل بسيط
    python scripts/run_api.py

    # على منفذ مخصص
    python scripts/run_api.py --port 8080

    # مع reload للتطوير
    python scripts/run_api.py --reload

    # مع backend حقيقي لـ Whisper
    CIE_WHISPER_BACKEND=faster-whisper python scripts/run_api.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    parser = argparse.ArgumentParser(description="Call Intelligence Engine API")
    parser.add_argument("--host", default="0.0.0.0", help="عنوان الاستماع")
    parser.add_argument("--port", type=int, default=8000, help="المنفذ")
    parser.add_argument("--reload", action="store_true", help="إعادة التحميل عند تغيير الكود")
    parser.add_argument("--workers", type=int, default=1, help="عدد العمّال")
    parser.add_argument("--log-level", default="info", help="مستوى التسجيل")
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError:
        print("❌ uvicorn غير مثبَّت. ثبّت: pip install fastapi uvicorn")
        return 1

    print(f"🚀 تشغيل CIE API على http://{args.host}:{args.port}")
    print(f"   docs: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "src.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
