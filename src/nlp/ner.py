"""استخلاص الكيانات المسماة (Named Entity Recognition) من النص العربي.

الكيانات المدعومة:
- PERSON: أشخاص (أحمد، فاطمة، محمد بن سعيد)
- LOCATION: أماكن (الرياض، شارع الملك فهد)
- ORGANIZATION: منظمات (أرامكو، الشركة السعودية)
- DATE: تواريخ مطلقة ونسبية
- TIME: أوقات
- MONEY: مبالغ مالية
- PHONE: أرقام هواتف
- EMAIL: بريد إلكتروني
- KEYWORD: كلمات مفتاحية محددة (للتفعيل لاحقاً)

طبقتان:
1. **rule-based** (مدمج): قواميس + أنماط regex + قواعد سياقية.
2. **spaCy** (اختياري): يستخدم نموذج عربي إن وُجد، fallback للقواعد.

استخدام:
    from src.nlp.ner import EntityExtractor

    extractor = EntityExtractor()
    entities = extractor.extract("اجتمع أحمد بسعيد في الرياض يوم الخميس")
    # [{type: PERSON, text: "أحمد", start: 7, end: 11, confidence: 0.9}, ...]
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Literal

from src.utils.arabic_text import normalize_alef, remove_diacritics
from src.utils.logging import get_logger

log = get_logger(__name__)

EntityType = Literal[
    "PERSON", "LOCATION", "ORGANIZATION",
    "DATE", "TIME", "MONEY", "PHONE", "EMAIL", "KEYWORD",
]


@dataclass
class Entity:
    """كيان مكتشف في النص."""

    type: EntityType
    text: str           # النص الأصلي كما ظهر
    start: int          # موقع البداية في النص
    end: int            # موقع النهاية
    confidence: float = 0.8
    normalized: str = ""  # النص بعد التطبيع (للمطابقة)
    source: str = "rule"  # rule | spacy | dictionary
    context: str = ""     # السياق المحيط (10 أحرف قبل/بعد)

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────
# قواميس الأشخاص: أسماء أولى عربية شائعة
# ─────────────────────────────────────────────────────────────────

ARABIC_FIRST_NAMES = {
    # أسماء ذكور شائعة
    "أحمد", "محمد", "علي", "حسن", "حسين", "خالد", "سعد", "سعود", "سعيد", "فهد", "بندر",
    "ناصر", "عبدالله", "عبدالرحمن", "عبدالعزيز", "إبراهيم", "يوسف", "يعقوب",
    "موسى", "عيسى", "هارون", "زيد", "عمر", "عثمان", "أبوبكر", "حمزة", "طارق",
    "وليد", "سلمان", "سامي", "ماجد", "نواف", "تركي", "مشاري", "راشد", "صالح",
    "ياسر", "وائل", "هشام", "كريم", "أمين", "محمود", "مصطفى", "أيمن", "أنس",
    "أسامة", "بسام", "جمال", "حازم", "خليل", "رامي", "رياض", "زياد", "سامر",
    "شاكر", "صبري", "ضياء", "طلال", "عادل", "عامر", "غسان", "فادي", "فارس",
    "نوح", "إسماعيل", "إسحاق", "يحيى", "بلال", "أديب", "سلمان", "سلطان",
    "فيصل", "حمد", "نايف", "مهنا", "رزان", "غازي", "سرحان", "كمال",
    # أسماء إناث شائعة
    "فاطمة", "خديجة", "عائشة", "زينب", "مريم", "سارة", "هند", "نورة", "ريم",
    "منى", "سلمى", "ليلى", "هدى", "نوال", "نجلاء", "سمر", "رنا", "دانة",
    "روان", "لمى", "غادة", "أمل", "إيمان", "آلاء", "أسماء", "بشرى", "تهاني",
    "حنان", "خولة", "دلال", "ذكرى", "رحاب", "زهراء", "سعاد", "شيماء", "صفاء",
    "نهى", "وفاء", "نجوى", "أروى", "بثينة", "جواهر", "ربى", "شذى", "عبير",
    # كنى
    "أبو", "أم", "ابن", "بنت", "بن",
}

# أسماء عائلات شائعة (قبائل وعائلات)
ARABIC_FAMILY_NAMES = {
    "السعدي", "القحطاني", "الغامدي", "الحربي", "العتيبي", "الشهري", "الزهراني",
    "العنزي", "الدوسري", "الشمري", "المطيري", "الرشيد", "الراجحي", "العثيمين",
    "الفايز", "الصباح", "الثاني", "المالكي", "العقيل", "الفهد", "المنصور",
    "الحسيني", "العمري", "البكر", "النصر", "الفيصل", "السديري", "السهيلي",
}

# ─────────────────────────────────────────────────────────────────
# قواميس الأماكن
# ─────────────────────────────────────────────────────────────────

ARABIC_LOCATIONS = {
    # دول
    "السعودية", "المملكة", "الإمارات", "الكويت", "البحرين", "قطر", "عُمان",
    "اليمن", "العراق", "الأردن", "سوريا", "لبنان", "فلسطين", "مصر", "ليبيا",
    "تونس", "الجزائر", "المغرب", "السودان", "موريتانيا", "الصومال",
    # مدن سعودية
    "الرياض", "جدة", "مكة", "المدينة", "الدمام", "الخبر", "الظهران", "الأحساء",
    "الطائف", "بريدة", "تبوك", "حائل", "أبها", "نجران", "جازان", "ينبع",
    "الجبيل", "القصيم", "حفر الباطن", "الخرج", "الجوف",
    # مدن خليجية وعربية رئيسة
    "دبي", "أبوظبي", "الشارقة", "العين", "الدوحة", "المنامة", "مسقط",
    "القاهرة", "الإسكندرية", "الجيزة", "أسوان", "الأقصر", "دمشق", "حلب",
    "بيروت", "عمّان", "بغداد", "الموصل", "البصرة", "صنعاء", "عدن",
    # مفاهيم أماكن
    "المطار", "المسجد", "المستشفى", "الجامعة", "المدرسة", "السوق", "الميناء",
    "المكتب", "الشارع", "الطريق", "الميدان", "الحي", "المركز",
}

LOCATION_INDICATORS = {
    "في", "إلى", "من", "عند", "بـ", "ب", "نحو", "صوب", "تجاه",
}

# ─────────────────────────────────────────────────────────────────
# قواميس المنظمات
# ─────────────────────────────────────────────────────────────────

ORG_PATTERNS = [
    r"شركة\s+\S+(?:\s+\S+)*",
    r"مؤسسة\s+\S+(?:\s+\S+)*",
    r"وزارة\s+\S+(?:\s+\S+)*",
    r"هيئة\s+\S+(?:\s+\S+)*",
    r"بنك\s+\S+(?:\s+\S+)*",
    r"جامعة\s+\S+(?:\s+\S+)*",
    r"كلية\s+\S+(?:\s+\S+)*",
    r"مستشفى\s+\S+",
    r"مجموعة\s+\S+(?:\s+\S+)*",
]

KNOWN_ORGS = {
    "أرامكو", "سابك", "stc", "موبايلي", "زين", "الراجحي", "الأهلي",
    "سامبا", "البنك السعودي", "نيوم", "روشن", "علم", "تكامل",
    "أكوا", "معادن", "المراعي", "بن داود", "العثيم", "الدانوب",
}

# ─────────────────────────────────────────────────────────────────
# أنماط التواريخ والأوقات
# ─────────────────────────────────────────────────────────────────

DAYS_OF_WEEK = {
    "السبت", "الأحد", "الاثنين", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة",
}

MONTHS_AR = {
    "محرم", "صفر", "ربيع الأول", "ربيع الثاني", "ربيع الآخر", "جمادى الأولى",
    "جمادى الآخرة", "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة",
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس",
    "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
    "كانون الثاني", "شباط", "آذار", "نيسان", "أيار", "حزيران", "تموز",
    "آب", "أيلول", "تشرين الأول", "تشرين الثاني", "كانون الأول",
}

RELATIVE_DATE_PATTERNS = [
    r"اليوم", r"أمس", r"غداً?", r"البارحة",
    r"الأسبوع\s+(?:الماضي|القادم|الحالي|المقبل)",
    r"الشهر\s+(?:الماضي|القادم|الحالي|المقبل)",
    r"السنة\s+(?:الماضية|القادمة|الحالية|المقبلة)",
    r"بعد\s+(?:ساعة|ساعتين|يوم|يومين|أسبوع|شهر|سنة)",
    r"قبل\s+(?:ساعة|ساعتين|يوم|يومين|أسبوع|شهر|سنة)",
    r"منذ\s+(?:ساعة|ساعتين|يوم|يومين|أسبوع|شهر|سنة)",
]

TIME_PATTERNS = [
    r"الساعة\s+(?:الواحدة|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|الحادية\s+عشرة|الثانية\s+عشرة)",
    r"الساعة\s+\d{1,2}(?::\d{2})?",
    r"\d{1,2}:\d{2}\s*(?:ص|م|صباحاً|مساءً|ظهراً)?",
    r"(?:صباحاً|مساءً|ظهراً|عصراً|ليلاً|فجراً)",
    r"منتصف\s+(?:الليل|النهار)",
]

# ─────────────────────────────────────────────────────────────────
# أنماط المال والأرقام
# ─────────────────────────────────────────────────────────────────

MONEY_PATTERNS = [
    r"\d+(?:[.,]\d+)?\s*(?:ريال|ر\.س|درهم|دينار|جنيه|دولار|يورو)",
    r"(?:ريال|ر\.س|درهم|دينار|جنيه|دولار|يورو)\s*\d+(?:[.,]\d+)?",
    r"\d+(?:[.,]\d+)?\s*(?:مليون|مليار|ألف)\s*(?:ريال|درهم|دولار)?",
]

PHONE_PATTERNS = [
    r"(?:\+|00)\d{1,4}[-\s]?\d{2,4}[-\s]?\d{3,8}",
    r"05\d{8}",
    r"\d{3}[-\s]\d{3}[-\s]\d{4}",
]

EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"


class EntityExtractor:
    """مستخرج كيانات هجين."""

    def __init__(self, *, use_spacy: bool = False, spacy_model: str | None = None):
        """
        Args:
            use_spacy: محاولة استخدام spaCy للنماذج الأدق.
            spacy_model: اسم نموذج spaCy (مثل xx_ent_wiki_sm).
        """
        self.use_spacy = use_spacy
        self.spacy_nlp = None
        if use_spacy:
            self._load_spacy(spacy_model)

    def _load_spacy(self, model_name: str | None) -> None:
        try:
            import spacy

            # نماذج مرشّحة بالترتيب
            candidates = [model_name] if model_name else [
                "xx_ent_wiki_sm",  # متعدد اللغات يدعم العربية
                "ar_core_news_lg",  # غير رسمي، قد لا يتوفر
            ]
            for m in candidates:
                if not m:
                    continue
                try:
                    self.spacy_nlp = spacy.load(m)
                    log.info(f"حُمّل نموذج spaCy: {m}")
                    return
                except OSError:
                    continue
            log.warning("لم يُحمَّل أي نموذج spaCy، نعتمد على القواعد فقط")
        except ImportError:
            log.warning("spaCy غير مثبّت، نعتمد على القواعد فقط")

    def extract(self, text: str) -> list[Entity]:
        """استخلاص كل الكيانات من نص.

        Args:
            text: النص العربي.

        Returns:
            قائمة Entity مرتّبة حسب موقع البداية.
        """
        if not text:
            return []

        entities: list[Entity] = []

        # 1. أنماط دقيقة (regex): تاريخ، وقت، مال، هاتف، بريد
        entities.extend(self._extract_emails(text))
        entities.extend(self._extract_phones(text))
        entities.extend(self._extract_money(text))
        entities.extend(self._extract_dates(text))
        entities.extend(self._extract_times(text))

        # 2. منظمات (قواعد + قاموس)
        entities.extend(self._extract_organizations(text))

        # 3. spaCy (إن متاح)
        if self.spacy_nlp:
            entities.extend(self._extract_spacy(text))

        # 4. قواميس: أشخاص وأماكن (آخراً لأن الـ regex قد تتداخل)
        entities.extend(self._extract_persons(text))
        entities.extend(self._extract_locations(text))

        # تنظيف: إزالة التداخلات (الكيان الأطول يفوز)
        entities = self._resolve_overlaps(entities)

        # إضافة السياق لكل كيان
        for e in entities:
            e.context = self._get_context(text, e.start, e.end)

        return sorted(entities, key=lambda x: x.start)

    def _extract_emails(self, text: str) -> list[Entity]:
        return [
            Entity(
                type="EMAIL",
                text=m.group(),
                start=m.start(),
                end=m.end(),
                confidence=0.99,
                normalized=m.group().lower(),
                source="rule",
            )
            for m in re.finditer(EMAIL_PATTERN, text)
        ]

    def _extract_phones(self, text: str) -> list[Entity]:
        results = []
        for pattern in PHONE_PATTERNS:
            for m in re.finditer(pattern, text):
                results.append(
                    Entity(
                        type="PHONE",
                        text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=0.95,
                        normalized=re.sub(r"[\s\-]", "", m.group()),
                        source="rule",
                    )
                )
        return results

    def _extract_money(self, text: str) -> list[Entity]:
        results = []
        for pattern in MONEY_PATTERNS:
            for m in re.finditer(pattern, text):
                results.append(
                    Entity(
                        type="MONEY",
                        text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=0.90,
                        normalized=m.group().strip(),
                        source="rule",
                    )
                )
        return results

    def _extract_dates(self, text: str) -> list[Entity]:
        results = []
        # أيام الأسبوع
        for day in DAYS_OF_WEEK:
            for m in re.finditer(r"\b" + re.escape(day) + r"\b", text):
                results.append(
                    Entity(
                        type="DATE",
                        text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=0.85,
                        normalized=remove_diacritics(m.group()),
                        source="dictionary",
                    )
                )
        # الأشهر
        for month in MONTHS_AR:
            for m in re.finditer(r"\b" + re.escape(month) + r"\b", text):
                results.append(
                    Entity(
                        type="DATE",
                        text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=0.85,
                        normalized=remove_diacritics(m.group()),
                        source="dictionary",
                    )
                )
        # تواريخ نسبية
        for pattern in RELATIVE_DATE_PATTERNS:
            for m in re.finditer(pattern, text):
                results.append(
                    Entity(
                        type="DATE",
                        text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=0.80,
                        normalized=remove_diacritics(m.group()),
                        source="rule",
                    )
                )
        # تواريخ رقمية: 12/3/2026 أو 2026-03-12
        for m in re.finditer(r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b", text):
            results.append(
                Entity(
                    type="DATE",
                    text=m.group(),
                    start=m.start(),
                    end=m.end(),
                    confidence=0.95,
                    normalized=m.group(),
                    source="rule",
                )
            )
        return results

    def _extract_times(self, text: str) -> list[Entity]:
        results = []
        for pattern in TIME_PATTERNS:
            for m in re.finditer(pattern, text):
                results.append(
                    Entity(
                        type="TIME",
                        text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=0.85,
                        normalized=remove_diacritics(m.group()),
                        source="rule",
                    )
                )
        return results

    def _extract_organizations(self, text: str) -> list[Entity]:
        results = []
        # القاموس
        for org in KNOWN_ORGS:
            for m in re.finditer(r"\b" + re.escape(org) + r"\b", text):
                results.append(
                    Entity(
                        type="ORGANIZATION",
                        text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=0.90,
                        normalized=normalize_alef(remove_diacritics(m.group())),
                        source="dictionary",
                    )
                )
        # الأنماط
        for pattern in ORG_PATTERNS:
            for m in re.finditer(pattern, text):
                # حد طول معقول (لا نأخذ "شركة قال محمد...")
                if len(m.group().split()) <= 5:
                    results.append(
                        Entity(
                            type="ORGANIZATION",
                            text=m.group(),
                            start=m.start(),
                            end=m.end(),
                            confidence=0.70,
                            normalized=normalize_alef(remove_diacritics(m.group())),
                            source="rule",
                        )
                    )
        return results

    def _extract_persons(self, text: str) -> list[Entity]:
        results = []

        # 1. كنى (أبو/أم + اسم)
        for m in re.finditer(r"(?:أبو|أم)\s+(\S+?)(?=[\s.,؛،!?؟]|$)", text):
            # نأخذ المجموعة الكاملة من البداية لنهاية الاسم (دون علامات ترقيم)
            full_match = m.group()
            start = m.start()
            # إزالة علامات ترقيم في النهاية
            stripped = full_match.rstrip(".,؛،!?؟")
            end = start + len(stripped)
            results.append(
                Entity(
                    type="PERSON",
                    text=stripped,
                    start=start,
                    end=end,
                    confidence=0.92,
                    normalized=normalize_alef(remove_diacritics(stripped)),
                    source="rule",
                )
            )

        # 2. أسماء من القاموس + امتداد لاسم العائلة المحتمل
        # نطابق الكلمات كاملة (word boundaries)
        for name in ARABIC_FIRST_NAMES:
            if name in {"أبو", "أم", "ابن", "بنت", "بن"}:
                continue  # لها معالجة منفصلة
            # \b لا يعمل جيداً مع العربية في بعض المحركات؛ نستخدم نظرة جانبية
            pattern = r"(?<![\u0600-\u06FF])" + re.escape(name) + r"(?![\u0600-\u06FF])"
            for m in re.finditer(pattern, text):
                start, end = m.start(), m.end()
                # توسيع: إن تلاه اسم عائلة من القاموس أو اسم آخر من القاموس
                # (لا نأخذ كل ما يبدأ بـ "ال" — قد يكون اسم عام)
                ext_pattern = r"\s+(\S+)"
                ext_m = re.match(ext_pattern, text[end:])
                if ext_m:
                    next_word = ext_m.group(1).strip(".,؛،")
                    # نتوسّع فقط إذا كانت الكلمة التالية:
                    # - اسم عائلة من القاموس، أو
                    # - اسم أول من القاموس (مثل "محمد العتيبي")
                    if (
                        next_word in ARABIC_FAMILY_NAMES
                        or next_word in ARABIC_FIRST_NAMES
                    ):
                        end = end + ext_m.end()

                results.append(
                    Entity(
                        type="PERSON",
                        text=text[m.start():end],
                        start=m.start(),
                        end=end,
                        confidence=0.85,
                        normalized=normalize_alef(remove_diacritics(text[m.start():end])).strip(),
                        source="dictionary",
                    )
                )

        return results

    def _extract_locations(self, text: str) -> list[Entity]:
        results = []
        for loc in ARABIC_LOCATIONS:
            pattern = r"(?<![\u0600-\u06FF])" + re.escape(loc) + r"(?![\u0600-\u06FF])"
            for m in re.finditer(pattern, text):
                # رفع الثقة إذا سبقه مؤشر مكان
                start = m.start()
                preceding = text[max(0, start - 5):start].strip()
                confidence = 0.90 if any(
                    preceding.endswith(ind) for ind in LOCATION_INDICATORS
                ) else 0.75
                results.append(
                    Entity(
                        type="LOCATION",
                        text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=confidence,
                        normalized=normalize_alef(remove_diacritics(m.group())),
                        source="dictionary",
                    )
                )
        return results

    def _extract_spacy(self, text: str) -> list[Entity]:
        """استخلاص عبر spaCy إن متاح."""
        if not self.spacy_nlp:
            return []
        results = []
        try:
            doc = self.spacy_nlp(text)
        except Exception as e:
            log.warning(f"spaCy فشل: {e}")
            return []

        # ربط تسميات spaCy بأنواعنا
        mapping = {
            "PER": "PERSON", "PERSON": "PERSON",
            "LOC": "LOCATION", "GPE": "LOCATION",
            "ORG": "ORGANIZATION",
            "DATE": "DATE", "TIME": "TIME",
            "MONEY": "MONEY",
        }
        for ent in doc.ents:
            our_type = mapping.get(ent.label_)
            if not our_type:
                continue
            results.append(
                Entity(
                    type=our_type,  # type: ignore
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.88,
                    normalized=normalize_alef(remove_diacritics(ent.text)).strip(),
                    source="spacy",
                )
            )
        return results

    def _resolve_overlaps(self, entities: list[Entity]) -> list[Entity]:
        """إزالة الكيانات المتداخلة: الأطول/الأعلى ثقة يفوز."""
        if not entities:
            return []

        # ترتيب: أطول، ثم أعلى ثقة، ثم أقدم بداية
        sorted_ents = sorted(
            entities,
            key=lambda e: (-(e.end - e.start), -e.confidence, e.start),
        )

        kept: list[Entity] = []
        for ent in sorted_ents:
            overlaps = any(
                not (ent.end <= k.start or ent.start >= k.end)
                for k in kept
            )
            if not overlaps:
                kept.append(ent)

        return kept

    def _get_context(self, text: str, start: int, end: int, window: int = 15) -> str:
        """استخراج سياق محيط لإظهار النص في التقارير."""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        return text[ctx_start:ctx_end].strip()


def merge_duplicate_entities(entities: list[Entity]) -> list[dict]:
    """تجميع تكرارات نفس الكيان (normalized) عبر النص.

    مفيد لبناء قاموس فريد من نتائج طويلة.

    Returns:
        قائمة [{type, normalized, mentions: [...], count}]
    """
    grouped: dict[tuple[str, str], list[Entity]] = {}
    for e in entities:
        key = (e.type, e.normalized)
        grouped.setdefault(key, []).append(e)

    result = []
    for (etype, norm), mentions in grouped.items():
        result.append({
            "type": etype,
            "normalized": norm,
            "count": len(mentions),
            "mentions": [
                {
                    "text": m.text,
                    "start": m.start,
                    "end": m.end,
                    "confidence": m.confidence,
                    "context": m.context,
                }
                for m in mentions
            ],
            "avg_confidence": round(
                sum(m.confidence for m in mentions) / len(mentions), 3
            ),
        })
    return sorted(result, key=lambda x: (-x["count"], x["type"]))
