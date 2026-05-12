"""نقطة الدخول لـ FastAPI.

تشغيل:
    uvicorn src.api.main:app --reload --port 8000

أو في الإنتاج:
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

التطبيق:
- يخدم REST API على /api/v1/...
- ملفات ثابتة من demo/ (إن وُجدت) على /
- CORS مفتوح للتطوير (يجب تقييده في الإنتاج)
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.orchestrator import Orchestrator
from src.api.routes import router, set_dependencies
from src.api.store import DataStore
from src.utils.config import PROJECT_ROOT
from src.utils.logging import get_logger

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """دورة حياة التطبيق: تهيئة عند البدء، تنظيف عند الإغلاق."""
    # ──────────────────────────────────────────────
    # تهيئة
    # ──────────────────────────────────────────────
    data_root = Path(os.environ.get("CIE_DATA_ROOT", PROJECT_ROOT / "data"))
    log.info(f"🚀 تشغيل Call Intelligence Engine API")
    log.info(f"   data_root: {data_root}")

    store = DataStore(data_root)

    watchlist_path = data_root / "watchlist.json"
    whisper_backend = os.environ.get("CIE_WHISPER_BACKEND", "mock")
    whisper_model = os.environ.get("CIE_WHISPER_MODEL", "tiny")

    orchestrator = Orchestrator(
        store=store,
        watchlist_path=watchlist_path if watchlist_path.exists() else None,
        whisper_backend=whisper_backend,
        whisper_model=whisper_model,
    )

    set_dependencies(store, orchestrator)

    log.info(f"   مكالمات معروفة: {len(store.list_call_ids())}")
    log.info(f"   متحدثون: {len(store.get_registry_summary())}")
    log.info(f"   Whisper backend: {whisper_backend}")

    yield  # هنا التطبيق يخدم الطلبات

    # ──────────────────────────────────────────────
    # تنظيف
    # ──────────────────────────────────────────────
    log.info("⏹️  إغلاق Call Intelligence Engine API")


app = FastAPI(
    title="Call Intelligence Engine API",
    description="محرك فهم العلاقات الصوتية-اللغوية-الزمنية - REST API",
    version="0.7.0",
    lifespan=lifespan,
)

# CORS: للتطوير. في الإنتاج حدّد origins صريحة.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CIE_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# نُسجّل كل المسارات تحت /api/v1
app.include_router(router, prefix="/api/v1")


# ──────────────────────────────────────────────────────────────
# Static files (لخدمة ملفات الديمو)
# ──────────────────────────────────────────────────────────────

DEMO_DIR = Path(os.environ.get("CIE_DEMO_DIR", PROJECT_ROOT / "demo"))
if DEMO_DIR.exists():
    app.mount("/", StaticFiles(directory=DEMO_DIR, html=True), name="demo")
    log.info(f"   ديمو ثابت من: {DEMO_DIR}")
else:
    @app.get("/")
    def root() -> dict:
        """رد افتراضي عندما لا يكون ديمو متاحاً."""
        return {
            "service": "Call Intelligence Engine",
            "version": "0.7.0",
            "docs": "/docs",
            "api": "/api/v1",
            "note": "ديمو HTML غير موجود. ضع ملفاتك في demo/ أو حدّد CIE_DEMO_DIR.",
        }


# ──────────────────────────────────────────────────────────────
# معالجة الأخطاء الموحَّدة
# ──────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    log.error(f"خطأ غير متوقع: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "detail": str(exc),
            "code": 500,
        },
    )
