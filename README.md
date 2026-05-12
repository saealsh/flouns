# Call Intelligence Engine — محرك فهم العلاقات الصوتية–اللغوية–الزمنية

> مشروع تخرج لتحويل المكالمات الهاتفية إلى شبكة معرفة ذكية تربط الأشخاص والكلمات والأحداث والأزمنة.

---

## 🎯 ما هذا المشروع؟

نظام متكامل يستقبل ملفات صوتية (محادثات/مكالمات/مقابلات بالعربية) ويُخرج:
- تفريغاً نصياً مع تمييز المتحدثين، طوابع زمنية، ونسب ثقة.
- استخلاص الكيانات (أشخاص، أحداث، أزمنة، كلمات مفتاحية).
- شبكة معرفة (Neo4j) تربط كل ذلك بصرياً.
- شجرة مكالمات تظهر التسلسل الزمني للأحداث.
- حلقة تدقيق بشري لضمان الجودة.

التفاصيل الكاملة في `docs/خطة-مشروع-التخرج-Call-Intelligence-Engine.docx`.

---

## 📂 هيكل المشروع

```
cie/
├── configs/              # ملفات الإعدادات YAML
│   └── config.yaml
├── data/                 # البيانات (الملفات الصوتية لا تُرفع لـ git)
│   ├── raw/              # البيانات الخام (Common Voice، التسجيلات الخاصة)
│   ├── processed/        # البيانات بعد المعالجة الأولية
│   ├── train/            # تقسيم التدريب (70%)
│   ├── val/              # تقسيم التحقق (15%)
│   ├── test/             # تقسيم الاختبار النهائي (15%)
│   ├── interim/          # ملفات وسيطة قابلة للحذف
│   └── Datasheet.md      # توثيق المجموعة
├── docs/                 # توثيق المشروع
├── notebooks/            # دفاتر Jupyter للتجارب
├── scripts/              # سكربتات قابلة للتشغيل من سطر الأوامر
│   ├── download_common_voice.py
│   ├── prepare_dataset.py
│   ├── validate_dataset.py
│   └── generate_synthetic_transcripts.py
├── src/                  # كود المشروع
│   ├── ingestion/        # استيعاب البيانات (manifests)
│   ├── audio/            # معالجة الصوت (مرحلة 2)
│   ├── asr/              # التفريغ التلقائي (مرحلة 4)
│   ├── nlp/              # معالجة اللغة (مرحلة 5)
│   ├── kg/               # شبكة المعرفة (مرحلة 6)
│   ├── api/              # واجهة REST (مرحلة 7)
│   └── utils/            # أدوات عامة
└── tests/                # اختبارات الوحدة
```

---

## 🚀 البدء السريع

### 1. التثبيت

```bash
git clone <repo-url>
cd cie

# بيئة افتراضية (موصى به)
python -m venv .venv
source .venv/bin/activate   # على Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. تثبيت ffmpeg (متطلب نظام)

- **Ubuntu/Debian:** `sudo apt install ffmpeg`
- **macOS:** `brew install ffmpeg`
- **Windows:** [ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### 3. اختبار البنية بدون تحميل بيانات

```bash
# توليد بيانات نصية اصطناعية للاختبار
python scripts/generate_synthetic_transcripts.py --count 12

# توليد ملفات صوتية اختبارية متنوعة
python scripts/generate_audio_test_samples.py

# تشغيل خط معالجة الصوت على ملفات الاختبار
python scripts/process_audio.py \
  --input data/raw/test_samples \
  --output data/processed/test_samples

# تشغيل كل الاختبارات (82+ اختبار)
pytest

# فحص الكود
ruff check src/ scripts/
```

### 4. تحميل بيانات Common Voice

```bash
# قبول شروط Common Voice (مرة واحدة):
# https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0

huggingface-cli login
python scripts/download_common_voice.py --max-clips 100
```

### 5. تقسيم البيانات

```bash
python scripts/prepare_dataset.py --strategy speaker
python scripts/validate_dataset.py
```

### 6. معالجة الصوت (المرحلة 2)

```bash
# تطبيع + فحص جودة + VAD على كل ملف
python scripts/process_audio.py

# أو على مجلد محدد
python scripts/process_audio.py \
  --input data/train/audio \
  --output data/processed/train

# باستخدام Silero VAD (يحتاج torch)
python scripts/process_audio.py --vad silero
```

التقرير الناتج (`processing_report.json`) لكل ملف يحوي:
- `quality`: SNR، RMS، نسبة الصمت، التشبع، النطاق الديناميكي
- `vad`: قائمة قطع الكلام مع طوابعها الزمنية
- `status`: `ok` / `warning` / `failed`
- `warnings`: قائمة المشاكل المكتشفة

### 7. فصل المتحدثين (المرحلة 3)

```bash
# diarization لملف واحد
python scripts/diarize.py --input call.wav

# مع تحديد عدد المتحدثين المعروف
python scripts/diarize.py --input call.wav --n-speakers 3

# مجلد كامل مع بناء قاعدة بصمات تراكمية
python scripts/diarize.py \
  --input-dir data/processed/train \
  --output data/diarized

# تحميل قاعدة بصمات موجودة وتحديثها
python scripts/diarize.py \
  --input new_call.wav \
  --registry data/diarized/registry.json
```

النتيجة لكل ملف (`<name>.diarization.json`):
- `segments`: قائمة [start, end, speaker_id, speaker_name, cluster_id, similarity, status]
- `speakers_summary`: إحصاءات لكل متحدث في الملف
- `metadata`: تفاصيل الـ pipeline (الطريقة، عدد القطع، إلخ)

قاعدة البصمات (`registry.json` + `registry.npz`) تنمو تراكمياً عبر الملفات.

**التقنيات المستخدمة:**
- **MFCC backend** (افتراضي، بدون torch): 78-d ميزات MFCC + delta + delta-delta
- **SpeechBrain ECAPA-TDNN** (اختياري، يحتاج torch): 192-d، أدق بكثير

**ملاحظة عن دقة MFCC:** ميزات MFCC الكلاسيكية تنتج تشابهاً عالياً بين متحدثين مختلفين أحياناً. للإنتاج، شغّل `--embedding speechbrain` (يحتاج `pip install speechbrain torch`).

### 8. التفريغ التلقائي (المرحلة 4)

```bash
# اختبار سريع بـ mock (بدون نموذج)
python scripts/transcribe.py \
  --input call.wav \
  --output data/transcripts \
  --backend mock

# تفريغ حقيقي بـ faster-whisper (يحتاج نموذجاً ~3GB)
pip install faster-whisper
python scripts/transcribe.py \
  --input call.wav \
  --output data/transcripts \
  --backend faster-whisper \
  --model large-v3 \
  --device auto \
  --n-speakers 2

# مع prompt لتوجيه النموذج للمصطلحات الخاصة
python scripts/transcribe.py \
  --input call.wav \
  --output data/transcripts \
  --initial-prompt "أحمد، خالد، الشحنة، المستودع"

# مجلد كامل مع قاعدة بصمات تراكمية
python scripts/transcribe.py \
  --input-dir data/processed \
  --output data/transcripts \
  --registry data/diarized/registry.json
```

**صيغ التصدير المدعومة:**
- `json`: البنية الكاملة (للبرمجة)
- `txt`: قراءة بشرية مع طوابع
- `srt` / `vtt`: ترجمات الفيديو القياسية
- `csv`: لـ Excel/Pandas
- `demo`: نفس بنية SEED_TRANSCRIPTS في الديمو (للرفع المباشر)

**تقييم WER/CER:**

```python
from src.asr.metrics import evaluate_transcript

result = evaluate_transcript(
    reference_text="السلام عليكم ورحمة الله",
    hypothesis_text="السلام عليكم ورحمته الله",
    reference_segments=ref_segments,
    hypothesis_segments=hyp_segments,
)
print(f"WER: {result['summary']['wer_percent']}%")
print(f"CER: {result['summary']['cer_percent']}%")
print(f"Speaker Accuracy: {result['summary']['saa_percent']}%")
```

**معايير القبول للمرحلة 4** (من خطة المشروع):
- WER ≤ 15% للفصحى، ≤ 25% للهجات
- Speaker attribution accuracy ≥ 92%
- Confidence calibration معقولة (لا تضخيم للثقة الزائف)

### 9. معالجة اللغة الطبيعية (المرحلة 5)

```bash
# تحليل نص خام
python scripts/extract_entities.py \
  --text "اجتمع أحمد بسعيد في الرياض الخميس"

# تحليل ملف transcript من المرحلة 4
python scripts/extract_entities.py \
  --input data/transcripts/call_001.json \
  --output data/nlp/

# مجلد كامل
python scripts/extract_entities.py \
  --input-dir data/transcripts/ \
  --output data/nlp/

# مع watchlist (قائمة مصطلحات يتعقّبها المحلّل)
python scripts/extract_entities.py \
  --input call.json \
  --watchlist data/watchlist.json
```

**ما يستخرجه النظام:**
- **كيانات مسمّاة** (NER): أشخاص، أماكن، منظمات، تواريخ، أوقات، مبالغ، هواتف
- **كلمات مفتاحية**: مع تصفية stopwords وتجذيع خفيف
- **مصطلحات مُتعقَّبة**: مطابقة مرنة (تجاهل الحركات، توحيد الألف)
- **أحداث**: فعل + مشاركون + زمن + مكان (مع دعم بادئات: سـ، فـ، ولا...)
- **Coreference**: تجميع "أحمد" و"أحمد محمد" و"الأستاذ أحمد"
- **KG Triples**: جاهزة للمرحلة 6 (subject → relation → object)

**صيغة ملف watchlist (JSON):**

```json
{
  "version": "1.0",
  "terms": [
    {"term": "العربة الجديدة", "note": "كلمة مفتاحية"},
    {"term": "أبو محمد", "note": "اسم متكرر"}
  ]
}
```

**معايير القبول للمرحلة 5** (من خطة المشروع):
- F1 ≥ 70% على PERSON و LOCATION (يحتاج تقييماً مرجعياً)
- استخلاص ≥ 80% من المصطلحات في watchlist
- تجميع coreference يقلل التكرار ≥ 50%

### 10. شبكة المعرفة (المرحلة 6)

```bash
# بناء KG من ملفات NLP + تشغيل استعلامات + تصدير للديمو
python scripts/build_kg.py \
  --input-dir data/nlp/ \
  --output data/kg/ \
  --export-demo \
  --query

# تصدير بصيغ متعددة
python scripts/build_kg.py \
  --input-dir data/nlp/ \
  --output data/kg/ \
  --export-demo \
  --export-cytoscape \
  --export-dot
```

**أنواع العقد في الرسم:**
- `Call` — مكالمة
- `Speaker` — متحدث (من registry)
- `Person`, `Location`, `Organization`
- `Date`, `Time`, `Money`, `Phone`, `Email`
- `Keyword` — كلمة من watchlist
- `Event` — حدث مستخرج (فعل + مشاركون + زمن + مكان)

**أنواع العلاقات الرئيسية:**
- `PARTICIPATED_IN` — Speaker → Call
- `MENTIONED_IN` — Entity → Call
- `MENTIONED` — Speaker → Entity
- `HAS_ACTOR` — Event → Person
- `OCCURRED_AT`, `OCCURRED_ON` — Event → Location/Date
- `MET_WITH`, `AGREED_WITH`, `SENT_TO`, `CALLED`
- `MATCHES_WATCHLIST` — Call → Keyword

**استعلامات معرفية متوفرة في `KGQueries`:**

```python
from src.kg.backends import NetworkXBackend
from src.kg.queries import KGQueries
from src.kg.schema import NodeType

backend = NetworkXBackend.load("data/kg/graph.json")
q = KGQueries(backend)

# إحصاءات شاملة
q.summary()

# الأكثر ذِكراً
q.top_persons(limit=10)
q.top_locations(limit=10)
q.top_keywords(limit=10)

# علاقات
q.who_met_whom()
q.persons_at_location("الرياض")
q.person_timeline("أحمد")
q.path_between("أحمد", "خالد")

# تحليل شبكي
q.central_persons(limit=5)  # betweenness centrality
q.communities()             # مكونات متصلة

# watchlist
q.calls_matching_watchlist()
q.speakers_using_watchlist_term("الشحنة")
```

**Neo4j Backend (اختياري للإنتاج):**

```bash
# تشغيل Neo4j
docker run -d -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password neo4j:5

# تركيب التبعية
pip install neo4j
```

```python
from src.kg.backends import Neo4jBackend
from src.kg.builder import KGBuilder

backend = Neo4jBackend(uri="bolt://localhost:7687", password="password")
builder = KGBuilder(backend)
builder.ingest_directory("data/nlp/")

# استعلامات Cypher
backend.cypher("""
    MATCH (p:Person)-[:HAS_ACTOR]-(e:Event)-[:OCCURRED_AT]->(l:Location)
    RETURN p.label, e.action, l.label
""")
```

**معايير القبول للمرحلة 6** (من خطة المشروع):
- عقد فريدة عبر المكالمات (لا تكرار لنفس الشخص)
- أزمنة الاستعلام < 1s على رسم 100K عقدة (Neo4j)
- تصدير صحيح بصيغة الديمو (graph.html)

### 11. الواجهة البرمجية + التدقيق البشري (المرحلة 7)

```bash
# تشغيل API محلياً
python scripts/run_api.py --reload

# أو بـ uvicorn مباشرة
uvicorn src.api.main:app --reload --port 8000

# تشغيل عبر Docker
docker-compose up -d

# مع Neo4j أيضاً
docker-compose --profile neo4j up -d
```

**أهم نقاط النهاية (Endpoints):**

| المسار | الوصف | الديمو |
|--------|-------|--------|
| `GET /api/v1/health` | فحص صحة | — |
| `GET /api/v1/calls` | قائمة المكالمات | `calls.html` |
| `GET /api/v1/calls/{id}` | تفاصيل مكالمة | `calls.html` |
| `GET /api/v1/calls/{id}/entities` | كيانات مع حالة التدقيق | — |
| `GET /api/v1/calls/{id}/events` | أحداث | — |
| `GET /api/v1/calls/{id}/watchlist` | تطابقات watchlist | — |
| `GET /api/v1/speakers` | قائمة المتحدثين | `speakers.html` |
| `GET /api/v1/speakers/{id}` | تفاصيل متحدث | `speakers.html` |
| `GET /api/v1/graph` | رسم المعرفة | `graph.html` |
| `GET /api/v1/graph/summary` | ملخص الرسم | — |
| `POST /api/v1/uploads` | رفع ملف صوتي | `uploads.html` |
| `GET /api/v1/jobs` | وظائف المعالجة | — |
| `GET /api/v1/jobs/{id}` | حالة وظيفة | — |
| `GET /api/v1/reports/summary` | تقرير شامل | `reports.html` |
| `POST /api/v1/calls/{id}/reviews/{entity_id}` | تقديم مراجعة بشرية | جديد |
| `GET /api/v1/calls/{id}/reviews` | كل المراجعات | جديد |
| `GET /api/v1/reviews/pending` | كيانات تحتاج مراجعة | جديد |

**توثيق Swagger تفاعلي تلقائي على `/docs`**

**التدقيق البشري (HITL):**

النظام يدعم مراجعة الكيانات والأحداث المستخرجة. ثلاث حالات:

```bash
# تأكيد كيان
curl -X POST http://localhost:8000/api/v1/calls/C-001/reviews/C-001:PERSON:0:4 \
  -H "Content-Type: application/json" \
  -d '{"review_status": "confirmed", "reviewed_by": "user1"}'

# رفض كيان
curl -X POST http://localhost:8000/api/v1/calls/C-001/reviews/C-001:PERSON:0:4 \
  -H "Content-Type: application/json" \
  -d '{"review_status": "rejected", "reviewed_by": "user1", "note": "ليس اسم شخص"}'

# تعديل كيان
curl -X POST http://localhost:8000/api/v1/calls/C-001/reviews/C-001:PERSON:0:4 \
  -H "Content-Type: application/json" \
  -d '{"review_status": "edited", "reviewed_by": "user1",
       "edits": {"text": "أحمد محمد", "type": "PERSON"}}'
```

**متغيرات البيئة:**

```bash
CIE_DATA_ROOT=/data                  # مجلد البيانات (افتراضي: data/)
CIE_DEMO_DIR=/app/demo               # مجلد ملفات HTML الديمو
CIE_WHISPER_BACKEND=faster-whisper   # mock | faster-whisper
CIE_WHISPER_MODEL=large-v3           # tiny | base | small | medium | large-v3
CIE_CORS_ORIGINS=https://yoursite.com  # CORS allowed origins
```

**نشر بـ Docker:**

```bash
# بناء الصورة
docker build -t cie-api .

# تشغيل
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  -e CIE_WHISPER_BACKEND=mock \
  --name cie cie-api

# مع docker-compose (يشمل volume للبيانات)
docker-compose up -d

# إضافة Neo4j
docker-compose --profile neo4j up -d
```

**معايير القبول للمرحلة 7** (من خطة المشروع):
- زمن استجابة API < 200ms لمعظم الاستعلامات
- معالجة الرفع تعمل end-to-end (audio → KG)
- HITL يحفظ ويُسترجع بشكل صحيح
- توافق صيغة المخرجات مع HTML الديمو

---

## ✅ معايير قبول المرحلة 1

ينبغي أن يمرّ `validate_dataset.py` بدون أخطاء قبل الانتقال للمرحلة 2:

- [ ] المدة الإجمالية ≥ 10 ساعات
- [ ] عدد المتحدثين الفريدين ≥ 4
- [ ] لهجتان على الأقل
- [ ] لا تسرّب متحدثين بين train/val/test
- [ ] كل الملفات الصوتية موجودة وقابلة للقراءة
- [ ] لا مقاطع بدون تفريغ مرجعي
- [ ] توزيع جنس مقبول (≥ 20% لكل من ذكر وأنثى)

---

## 🗺️ خارطة الطريق

| المرحلة | الموضوع | الحالة |
|---|---|---|
| 1 | جمع البيانات وتجهيزها | ✅ مكتملة |
| 2 | معالجة الصوت وVAD | ✅ مكتملة |
| 3 | فصل المتحدثين (Diarization) | ✅ مكتملة |
| 4 | التفريغ التلقائي (Whisper) | ✅ مكتملة |
| 5 | معالجة اللغة الطبيعية | ✅ مكتملة |
| 6 | شبكة المعرفة (Neo4j) | ✅ مكتملة |
| 7 | الواجهة + التدقيق البشري | ✅ مكتملة |

---

## ⚖️ الترخيص والأخلاقيات

هذا مشروع بحثي/أكاديمي. راجع `data/Datasheet.md` للقيود والتوصيات.

**ممنوع** استخدام النظام في:
- اتخاذ قرارات أوتوماتيكية تؤثر على حياة الناس.
- التعرّف الصوتي البيومتري لأغراض إنفاذ القانون.
- النشر التجاري دون مراجعة قانونية.

---

## 🛠️ تطوير

```bash
# تنسيق الكود
black src/ scripts/ tests/

# فحص جودة الكود
ruff check src/ scripts/ tests/

# تشغيل الاختبارات مع تغطية
pytest --cov=src --cov-report=html
```
