"""استخلاص الأحداث من النصوص العربية.

الحدث هو ربط بين:
- فعل/إجراء (sent shipment, met, called)
- مشاركون (من فعل، ومع من)
- زمن (متى)
- مكان (أين، إن ذُكر)

في غياب نموذج رابطي عميق (مثل AllenNLP)، نستخدم تقاطعاً ذكياً:
- في كل جملة، إذا وُجد فعل من قائمة الأفعال المهمة + كيانان (شخص/مكان/زمن)
  → نُولّد حدثاً.

استخدام:
    from src.nlp.events import EventExtractor

    extractor = EventExtractor()
    events = extractor.extract(text, entities=extracted_entities)
    # [{action: "أرسل", actors: [...], time: "...", location: "..."}]
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from src.nlp.ner import Entity
from src.utils.arabic_text import remove_diacritics
from src.utils.logging import get_logger

log = get_logger(__name__)


# أفعال مهمة (تشير إلى أحداث قابلة للتعقّب)
# نأخذ الجذع، الـ regex يطابق التصاريف
ACTION_VERBS = {
    "send": ["أرسل", "بعث", "ابعث", "ارسل", "يرسل", "ترسل", "أبعث", "أرسلت", "بعثت"],
    "receive": ["استلم", "استلمت", "تسلم", "تسلّم", "استلام", "وصل", "وصلت", "وصلني"],
    "meet": ["اجتمع", "التقى", "قابل", "قابلت", "لقي", "لقاء", "اجتماع", "تقابل"],
    "call": ["اتصل", "كلّم", "حدّث", "تكلم", "اتصلت", "مكالمة", "نادى"],
    "go": ["ذهب", "ذهبت", "راح", "رحت", "توجه", "توجّه", "سافر", "وصل"],
    "arrive": ["وصل", "وصلت", "حضر", "حضرت", "بلغ", "بلغت", "قدم"],
    "deliver": ["سلّم", "سلم", "أوصل", "أوصلت", "ناول", "أعطى", "أعطيت"],
    "agree": ["اتفق", "اتفقت", "وافق", "وافقت", "موافق", "اتفاق"],
    "confirm": ["أكّد", "أكد", "أكدت", "تأكيد", "أثبت", "أثبتت"],
    "cancel": ["ألغى", "ألغت", "ألغيت", "إلغاء", "أوقف", "أوقفت"],
    "postpone": ["أجّل", "أجل", "أجلت", "تأجيل", "أخّر", "أخر"],
    "buy": ["اشترى", "اشتريت", "ابتاع", "شراء", "بضاعة"],
    "sell": ["باع", "بعت", "بيع", "بيعت"],
    "pay": ["دفع", "دفعت", "سدّد", "سدد", "تسديد", "حوّل", "حول"],
    "request": ["طلب", "طلبت", "أراد", "أردت", "يطلب", "تطلب"],
    "promise": ["وعد", "وعدت", "تعهّد", "تعهد", "التزم"],
    "warn": ["حذّر", "حذر", "حذرت", "نبّه", "أنذر"],
    "decide": ["قرّر", "قرر", "قررت", "اتخذ قراراً", "قرار"],
}

# تجميع كل الأفعال في مجموعة واحدة مع الإشارة للنوع
VERB_TO_ACTION: dict[str, str] = {}
for action, verbs in ACTION_VERBS.items():
    for v in verbs:
        VERB_TO_ACTION[v] = action

ALL_VERBS = set(VERB_TO_ACTION.keys())


@dataclass
class Event:
    """حدث مستخرج من نص."""

    action: str               # نوع الفعل (send, meet, ...)
    verb_text: str            # الفعل كما ظهر في النص
    sentence: str             # الجملة الكاملة
    sentence_start: int       # موقع الجملة في النص
    actors: list[dict] = field(default_factory=list)        # الأشخاص المشاركون
    locations: list[dict] = field(default_factory=list)     # الأماكن المذكورة
    times: list[dict] = field(default_factory=list)         # الأزمنة المذكورة
    objects: list[str] = field(default_factory=list)        # الأشياء المذكورة (إن أمكن)
    confidence: float = 0.7

    def to_dict(self) -> dict:
        return asdict(self)


def split_sentences(text: str) -> list[tuple[str, int]]:
    """تقسيم النص لجمل مع الاحتفاظ بمواقعها.

    Returns:
        قائمة (sentence, start_index).
    """
    if not text:
        return []

    # علامات نهاية الجملة العربية والإنجليزية
    # نتعامل مع المتعدد بدون كسر الجملة المهمة (e.g., 9:30 ليس .)
    sentences = []
    pattern = re.compile(r"[.!?؟।]+\s+|\n+")
    last_end = 0
    for m in pattern.finditer(text):
        sent = text[last_end:m.start()].strip()
        if sent:
            sentences.append((sent, last_end))
        last_end = m.end()
    # الجزء الأخير
    if last_end < len(text):
        rest = text[last_end:].strip()
        if rest:
            sentences.append((rest, last_end))

    return sentences


class EventExtractor:
    """مستخرج الأحداث."""

    def __init__(self, *, min_actors: int = 0):
        """
        Args:
            min_actors: أدنى عدد actors لقبول الحدث (0 = نقبل الأحداث بدون اسم متحدث).
        """
        self.min_actors = min_actors

    def extract(
        self,
        text: str,
        entities: list[Entity] | None = None,
    ) -> list[Event]:
        """استخلاص الأحداث.

        Args:
            text: النص.
            entities: كيانات مستخرجة سابقاً (إن None، يعمل بدونها).

        Returns:
            قائمة Event.
        """
        if not text:
            return []

        sentences = split_sentences(text)
        events: list[Event] = []

        for sent, sent_start in sentences:
            # ابحث عن فعل في الجملة
            verb_matches = self._find_verbs(sent)
            if not verb_matches:
                continue

            # كل فعل ينتج حدثاً مستقلاً (الجملة قد تحوي عدة أفعال)
            for verb_text, verb_pos in verb_matches:
                action = VERB_TO_ACTION[verb_text]

                # نُقسّم الكيانات بناءً على موقع الجملة
                sent_end = sent_start + len(sent)
                sent_entities = []
                if entities:
                    sent_entities = [
                        e for e in entities
                        if sent_start <= e.start < sent_end
                    ]

                actors = [
                    {"text": e.text, "normalized": e.normalized, "source": "ner"}
                    for e in sent_entities
                    if e.type == "PERSON"
                ]
                locations = [
                    {"text": e.text, "normalized": e.normalized}
                    for e in sent_entities
                    if e.type == "LOCATION"
                ]
                times = [
                    {"text": e.text, "normalized": e.normalized, "type": e.type}
                    for e in sent_entities
                    if e.type in ("DATE", "TIME")
                ]

                if len(actors) < self.min_actors:
                    continue

                # ثقة الحدث: تزداد كلما زاد عدد الكيانات
                ctx_count = len(actors) + len(locations) + len(times)
                confidence = 0.5 + min(ctx_count * 0.12, 0.45)

                events.append(
                    Event(
                        action=action,
                        verb_text=verb_text,
                        sentence=sent,
                        sentence_start=sent_start,
                        actors=actors,
                        locations=locations,
                        times=times,
                        objects=self._extract_objects(sent, verb_pos),
                        confidence=round(confidence, 3),
                    )
                )

        return events

    def _find_verbs(self, sentence: str) -> list[tuple[str, int]]:
        """البحث عن أفعال مهمة في الجملة.

        ندعم بادئات شائعة:
        - "س" + فعل = مستقبل (سأرسل، سيذهب)
        - "لا/ما/لم/لن" + فعل = نفي
        - "و/ف" + فعل = ربط
        """
        results = []

        # بادئات شائعة قد تسبق الفعل
        prefixes = ["", "س", "و", "ف", "وس", "فس", "ل", "ولا", "فلا"]

        for verb in ALL_VERBS:
            # المطابقة المباشرة (الفعل كما هو)
            for m in re.finditer(
                r"(?<![\u0600-\u06FF])" + re.escape(verb) + r"(?![\u0600-\u06FF])",
                sentence,
            ):
                results.append((verb, m.start()))

            # المطابقة مع البادئات (سأرسل، فأرسل، إلخ)
            for prefix in prefixes[1:]:  # نتخطى "" لأنه فعل المطابقة المباشرة
                prefixed = prefix + verb
                for m in re.finditer(
                    r"(?<![\u0600-\u06FF])" + re.escape(prefixed) + r"(?![\u0600-\u06FF])",
                    sentence,
                ):
                    # نسجّل الفعل الأصلي (verb) لكن بموقع المطابقة الفعلية
                    results.append((verb, m.start()))

        # ترتيب حسب الموقع، وإزالة التداخل (الأطول يفوز)
        results.sort(key=lambda r: (r[1], -len(r[0])))
        kept = []
        for verb, pos in results:
            overlaps = any(
                pos < kp + len(kv) and pos + len(verb) > kp
                for kv, kp in kept
            )
            if not overlaps:
                kept.append((verb, pos))
        return kept

    def _extract_objects(self, sentence: str, verb_pos: int) -> list[str]:
        """محاولة استخراج المفعول/الأشياء بعد الفعل (heuristic).

        نأخذ الكلمات التالية للفعل (حتى علامة ترقيم أو حرف جر) كأشياء محتملة.
        """
        # ما بعد الفعل
        after = sentence[verb_pos:]
        # نقسم على حروف الجر وعلامات الترقيم
        parts = re.split(r"\s+(?:في|إلى|من|على|عند|مع|قبل|بعد|عبر|نحو)\s+|[،,.;:]", after, maxsplit=1)
        if not parts:
            return []

        head = parts[0].strip()
        # احذف الفعل نفسه
        words = head.split()[1:]
        # خذ ما بعد الفعل كأشياء محتملة (حتى 4 كلمات)
        candidates = []
        for w in words[:4]:
            w = w.strip(".,؛،\"'")
            if len(w) >= 3 and re.match(r"^[\u0600-\u06FF]+$", w):
                candidates.append(w)
            else:
                break
        return candidates


def group_events_by_actor(events: list[Event]) -> dict[str, list[dict]]:
    """تجميع الأحداث حسب الشخص المشارك (لبناء ملف شخص في الرسم البياني).

    Returns:
        قاموس {normalized_actor: [event_dict, ...]}
    """
    grouped: dict[str, list[dict]] = {}
    for event in events:
        for actor in event.actors:
            key = actor.get("normalized") or actor["text"]
            grouped.setdefault(key, []).append(event.to_dict())
    return grouped


def events_to_kg_triples(events: list[Event]) -> list[dict]:
    """تحويل الأحداث إلى triples لرسم المعرفة.

    Triples بصيغة (subject, relation, object) — يستخدمها مرحلة 6 (Neo4j).

    Returns:
        قائمة [{subject, relation, object, attributes}]
    """
    triples = []
    for event in events:
        # علاقات actor → action
        for actor in event.actors:
            for location in event.locations:
                triples.append({
                    "subject": actor.get("normalized") or actor["text"],
                    "relation": f"{event.action}_at",
                    "object": location.get("normalized") or location["text"],
                    "attributes": {
                        "verb": event.verb_text,
                        "confidence": event.confidence,
                    },
                })
            for time in event.times:
                triples.append({
                    "subject": actor.get("normalized") or actor["text"],
                    "relation": f"{event.action}_on",
                    "object": time.get("normalized") or time["text"],
                    "attributes": {
                        "verb": event.verb_text,
                        "confidence": event.confidence,
                    },
                })

        # علاقات actor → actor (اثنان في نفس الحدث)
        if len(event.actors) >= 2:
            for i, a1 in enumerate(event.actors):
                for a2 in event.actors[i + 1:]:
                    triples.append({
                        "subject": a1.get("normalized") or a1["text"],
                        "relation": f"{event.action}_with",
                        "object": a2.get("normalized") or a2["text"],
                        "attributes": {
                            "verb": event.verb_text,
                            "confidence": event.confidence,
                        },
                    })
    return triples
