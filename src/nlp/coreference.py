"""تطبيع الكيانات وتجميع المراجع المتشابهة (light coreference resolution).

المشكلة:
في مكالمة واحدة قد يُذكر «أحمد»، «أحمد محمد»، «أ. محمد»، «الأخ أحمد» —
نريد توحيد هذه إلى كيان واحد.

نوفّر طبقتين:
1. **تطبيع نصي** (مدمج): إزالة الألقاب، توحيد الإملاء، مطابقة الجذع.
2. **تجميع جغرافي** عبر similarity مع threshold.

استخدام:
    from src.nlp.coreference import EntityResolver

    resolver = EntityResolver()
    canonical = resolver.resolve(entities)
    # canonical[i] = نسخة مُوحَّدة من entities[i]
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from src.nlp.ner import Entity
from src.utils.arabic_text import normalize_alef, normalize_yaa, remove_diacritics
from src.utils.logging import get_logger

log = get_logger(__name__)


# ألقاب وكلمات قبل الاسم تُحذف للحصول على الجذع
ARABIC_HONORIFICS = {
    "السيد", "الأستاذ", "الدكتور", "الشيخ", "المهندس", "الأخ", "الأخت",
    "الأمير", "الأميرة", "الملك", "الملكة", "الوزير", "النائب",
    "الرئيس", "المدير", "العم", "الخال", "الجد", "الجدة",
    "د.", "أ.", "م.", "أ.د.", "السيدة", "الآنسة",
}

# علامات تدلّ على أن الكيانين بالتأكيد نفس الشخص رغم اختلاف النص
SAME_ENTITY_INDICATORS = {
    "أبو", "أم", "ابن", "بن", "بنت",
}


@dataclass
class EntityCluster:
    """مجموعة كيانات تشير لنفس الشيء."""

    canonical: str                        # الاسم القياسي
    type: str
    mentions: list[Entity] = field(default_factory=list)
    confidence: float = 1.0

    @property
    def count(self) -> int:
        return len(self.mentions)

    def to_dict(self) -> dict:
        return {
            "canonical": self.canonical,
            "type": self.type,
            "count": self.count,
            "confidence": round(self.confidence, 3),
            "mentions": [
                {
                    "text": m.text,
                    "start": m.start,
                    "end": m.end,
                    "confidence": m.confidence,
                }
                for m in self.mentions
            ],
        }


def normalize_person_name(name: str) -> str:
    """تطبيع اسم شخص: حذف الحركات + الألقاب + توحيد الألف.

    Examples:
        "الأستاذ أحمد محمد" → "احمد محمد"
        "أ. أحمد" → "احمد"
        "السيدة فاطمة" → "فاطمه" (التاء المربوطة قد تتغير)
    """
    if not name:
        return ""

    # إزالة الحركات وتوحيد الألف والياء أولاً
    name = remove_diacritics(name)
    name = normalize_alef(name)
    name = normalize_yaa(name)

    # نطبّع الألقاب أيضاً للمقارنة (لأنها قد تكون مع الهمزة في القاموس)
    normalized_honorifics = {
        normalize_yaa(normalize_alef(remove_diacritics(h)))
        for h in ARABIC_HONORIFICS
    }

    # حذف الألقاب من البداية
    words = name.split()
    while words:
        first = words[0].rstrip(".:")
        first_with_dot = first + "."
        if first in normalized_honorifics or first_with_dot in normalized_honorifics:
            words.pop(0)
        else:
            break

    return " ".join(w for w in words if w.strip())


def normalize_location(name: str) -> str:
    """تطبيع اسم مكان."""
    if not name:
        return ""
    name = remove_diacritics(name)
    name = normalize_alef(name)
    name = normalize_yaa(name)
    # إزالة "ال" التعريف للمطابقة
    if name.startswith("ال") and len(name) > 3:
        name = name[2:]
    return name.strip()


def normalize_organization(name: str) -> str:
    """تطبيع اسم منظمة."""
    if not name:
        return ""
    name = remove_diacritics(name)
    name = normalize_alef(name)
    # نُبقي على كلمات مثل "شركة" / "مؤسسة" — تساعد في التمييز
    return " ".join(name.split())


# قاموس مطبّعات لكل نوع
NORMALIZERS = {
    "PERSON": normalize_person_name,
    "LOCATION": normalize_location,
    "ORGANIZATION": normalize_organization,
}


def is_subname_match(short: str, long: str) -> bool:
    """هل short جزء من long؟ (مفيد لمطابقة "أحمد" ضمن "أحمد محمد").

    مثال: "أحمد" ضمن "أحمد محمد" → True
          "محمد" ضمن "أحمد محمد" → True (الكلمة الأخيرة)
          "علي" ضمن "أحمد محمد" → False
    """
    if not short or not long or short == long:
        return False

    short_words = short.split()
    long_words = long.split()

    if len(short_words) >= len(long_words):
        return False

    # short مجموعة من الكلمات (متتالية أو لا) في long
    short_set = set(short_words)
    long_set = set(long_words)
    return short_set.issubset(long_set)


class EntityResolver:
    """تجميع الكيانات المتشابهة في clusters قياسية."""

    def __init__(
        self,
        *,
        merge_subnames: bool = True,
        case_insensitive: bool = True,
    ):
        """
        Args:
            merge_subnames: دمج "أحمد" مع "أحمد محمد" تلقائياً.
            case_insensitive: تجاهل حالة الأحرف (لا يهم للعربية، يهم لـ EMAIL).
        """
        self.merge_subnames = merge_subnames
        self.case_insensitive = case_insensitive

    def resolve(self, entities: list[Entity]) -> list[EntityCluster]:
        """تجميع الكيانات في clusters قياسية.

        Args:
            entities: كل الكيانات المستخرجة من نص ما.

        Returns:
            قائمة EntityCluster، كل واحد يجمع mentions الكيان نفسه.
        """
        if not entities:
            return []

        # 1. تجميع حسب النوع + الشكل القياسي
        type_groups: dict[str, list[Entity]] = {}
        for e in entities:
            type_groups.setdefault(e.type, []).append(e)

        all_clusters: list[EntityCluster] = []
        for etype, ents in type_groups.items():
            clusters = self._cluster_within_type(etype, ents)
            all_clusters.extend(clusters)

        # 2. ترتيب حسب التكرار (الأكثر ذكراً أولاً)
        all_clusters.sort(key=lambda c: -c.count)
        return all_clusters

    def _cluster_within_type(
        self,
        etype: str,
        entities: list[Entity],
    ) -> list[EntityCluster]:
        """تجميع كيانات من نفس النوع."""
        if not entities:
            return []

        normalizer = NORMALIZERS.get(etype, lambda x: x.lower() if self.case_insensitive else x)

        # 1. خرائط بصيغة قياسية
        norm_to_mentions: dict[str, list[Entity]] = {}
        for e in entities:
            norm = normalizer(e.text)
            if not norm:
                norm = e.normalized or e.text
            norm_to_mentions.setdefault(norm, []).append(e)

        # 2. (اختياري) دمج الأسماء الجزئية مع الكاملة
        if self.merge_subnames and etype == "PERSON":
            self._merge_subnames(norm_to_mentions)

        # 3. بناء clusters
        clusters = []
        for norm, mentions in norm_to_mentions.items():
            # متوسط الثقة كثقة للـ cluster
            avg_conf = sum(m.confidence for m in mentions) / len(mentions)
            clusters.append(
                EntityCluster(
                    canonical=self._pick_canonical(mentions),
                    type=etype,
                    mentions=mentions,
                    confidence=avg_conf,
                )
            )
        return clusters

    def _merge_subnames(self, mapping: dict[str, list[Entity]]) -> None:
        """دمج "أحمد" مع "أحمد محمد" — يعدّل mapping في المكان."""
        keys = sorted(mapping.keys(), key=lambda k: len(k.split()))
        merged = set()

        for short_key in keys:
            if short_key in merged or not short_key:
                continue
            for long_key in keys:
                if long_key == short_key or long_key in merged:
                    continue
                if is_subname_match(short_key, long_key):
                    # ادمج short في long (الطويل أكثر تحديداً)
                    mapping[long_key].extend(mapping[short_key])
                    merged.add(short_key)
                    break

        for k in merged:
            mapping.pop(k, None)

    def _pick_canonical(self, mentions: list[Entity]) -> str:
        """اختيار الشكل القياسي من قائمة mentions.

        نختار الأطول (يحوي أكبر قدر من المعلومات).
        """
        return max(mentions, key=lambda m: (len(m.text), m.confidence)).text


def build_global_resolver(
    all_entities: list[list[Entity]],
) -> dict[str, EntityCluster]:
    """بناء resolver على مستوى كل المكالمات (عبر ملفات متعددة).

    Args:
        all_entities: قائمة من قوائم الكيانات (مكالمة لكل قائمة).

    Returns:
        قاموس normalized → EntityCluster.
    """
    resolver = EntityResolver()
    flat = [e for ents in all_entities for e in ents]
    clusters = resolver.resolve(flat)
    return {c.canonical: c for c in clusters}
