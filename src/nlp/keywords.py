"""استخلاص الكلمات المفتاحية والمصطلحات من النص العربي.

يخدم استخدامين:
1. **كلمات مفتاحية عامة** (TF-IDF أو RAKE): الكلمات الأكثر دلالة في النص.
2. **مصطلحات مُشفّرة محددة** (watchlist): قائمة مصطلحات يتعقّبها المحلّل.

الفرق المهم:
- NER يكشف الكيانات «الواضحة» (أشخاص، أماكن).
- Keywords يكشف ما يصفه المتحدثون (أفعال، أشياء، مفاهيم).
- Watchlist يتعقّب مفردات اصطلاحية معروفة سلفاً.

استخدام:
    from src.nlp.keywords import KeywordExtractor, Watchlist

    # كلمات مفتاحية عامة
    extractor = KeywordExtractor()
    keywords = extractor.extract(text, top_k=10)

    # مفردات اصطلاحية يتعقّبها المحلّل
    watch = Watchlist(["العربة الجديدة", "أبو محمد", "القناة"])
    matches = watch.scan(text)
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass

from src.utils.arabic_text import (
    clean_text,
    normalize_alef,
    normalize_yaa,
    remove_diacritics,
)
from src.utils.logging import get_logger

log = get_logger(__name__)


# كلمات وقف عربية شائعة (stopwords) — تُستبعد من الكلمات المفتاحية
ARABIC_STOPWORDS = {
    # حروف جر وعطف
    "في", "على", "إلى", "من", "عن", "مع", "بين", "حتى", "إذ", "إذا", "أن",
    "أنّ", "لكن", "ثم", "أو", "أم", "إما", "بل", "غير", "سوى", "خلا", "عدا",
    "حاشا", "حيث", "كي", "لكي", "لكن", "ولكن", "و", "ف", "ل", "ب", "ك",
    # ضمائر
    "هو", "هي", "هم", "هن", "أنت", "أنتم", "أنتن", "أنا", "نحن", "أنتما",
    "هما", "هذا", "هذه", "هؤلاء", "ذلك", "تلك", "أولئك", "الذي", "التي",
    "اللذان", "اللتان", "الذين", "اللواتي", "اللائي", "اللاتي",
    # أفعال ربط شائعة
    "كان", "كانت", "يكون", "تكون", "أصبح", "أمسى", "بات", "ظل", "صار",
    "ليس", "ليست", "لست", "لسنا", "لستم", "لسن",
    # شائعة
    "قال", "قالت", "قلت", "يقول", "تقول", "أقول",
    "نعم", "لا", "بلى", "كلا", "ربما", "لعل", "قد", "قط", "أبداً", "دائماً",
    "كل", "بعض", "أكثر", "أقل", "أن", "إن", "أنه", "إنه", "أي", "أية", "أيها",
    "ما", "ماذا", "متى", "أين", "كيف", "لماذا", "كم",
    "الذي", "التي", "هذه", "ذاك",
    # أرقام كلمة
    "واحد", "اثنان", "ثلاث", "أربع", "خمس",
    # عام
    "شيء", "أشياء", "أمر", "أمور", "حال", "أحوال", "وقت", "أوقات",
    "يوم", "أيام", "شهر", "أشهر", "سنة", "سنوات", "ساعة", "ساعات",
}

# لاحقات تصريفية شائعة (للجذع البسيط)
ARABIC_SUFFIXES = ["ها", "هم", "هن", "ها", "ون", "ين", "ات", "ان", "تين", "تان"]
ARABIC_PREFIXES = ["ال", "وال", "بال", "كال", "فال", "لل", "و", "ف", "ب", "ك", "ل"]


def light_stem(word: str) -> str:
    """جذع خفيف للكلمة العربية (إزالة بادئات/لواحق شائعة).

    لا يساوي الجذر الصرفي الحقيقي (لذلك يحتاج CAMeL Tools)، لكنه يكفي
    لتجميع التكرارات الإملائية البسيطة.
    """
    w = normalize_alef(normalize_yaa(remove_diacritics(word)))

    # إزالة "ال" التعريف
    for prefix in ["وال", "بال", "كال", "فال", "ال"]:
        if w.startswith(prefix) and len(w) > len(prefix) + 1:
            w = w[len(prefix):]
            break

    # إزالة بادئة حرفية
    for prefix in ["و", "ف", "ب", "ل"]:
        if w.startswith(prefix) and len(w) > 2:
            w = w[len(prefix):]
            break

    # إزالة لاحقة
    for suffix in sorted(ARABIC_SUFFIXES, key=len, reverse=True):
        if w.endswith(suffix) and len(w) > len(suffix) + 2:
            w = w[: -len(suffix)]
            break

    return w


@dataclass
class Keyword:
    """كلمة مفتاحية مكتشفة."""

    text: str
    stem: str
    count: int
    score: float
    positions: list[int]  # مواقع الظهور في النص

    def to_dict(self) -> dict:
        return asdict(self)


class KeywordExtractor:
    """مستخرج الكلمات المفتاحية باستخدام TF + فلترة stopwords + تجميع جذعي."""

    def __init__(
        self,
        *,
        stopwords: set[str] | None = None,
        min_word_length: int = 3,
        ngram_range: tuple[int, int] = (1, 2),
    ):
        """
        Args:
            stopwords: كلمات وقف إضافية فوق المدمجة.
            min_word_length: أقل طول مقبول لكلمة.
            ngram_range: (min, max) لحجم العبارات المستخرجة (1=كلمات، 2=ثنائيات).
        """
        self.stopwords = ARABIC_STOPWORDS | (stopwords or set())
        self.min_word_length = min_word_length
        self.ngram_min, self.ngram_max = ngram_range

    def extract(
        self,
        text: str,
        *,
        top_k: int = 20,
        min_count: int = 1,
    ) -> list[Keyword]:
        """استخراج أهم الكلمات المفتاحية.

        Args:
            text: النص.
            top_k: عدد الكلمات المرجَعة.
            min_count: أدنى عدد ظهور للكلمة لتؤخذ.

        Returns:
            قائمة Keyword مرتّبة بالأهمية تنازلياً.
        """
        if not text or not text.strip():
            return []

        # 1. تنظيف وتقسيم
        cleaned = clean_text(text)
        words = re.findall(r"[\u0600-\u06FF]+", cleaned)

        # 2. فلترة وتجذيع
        stems: dict[str, dict] = {}  # stem -> {text, count, positions}
        offset = 0
        for word in words:
            if len(word) < self.min_word_length:
                offset = cleaned.find(word, offset) + len(word)
                continue
            if word in self.stopwords:
                offset = cleaned.find(word, offset) + len(word)
                continue
            # إيجاد موقع الكلمة بدقة في النص الأصلي
            pos = text.find(word, offset)
            offset = pos + len(word) if pos != -1 else offset

            stem = light_stem(word)
            if stem in self.stopwords or len(stem) < 2:
                continue

            entry = stems.setdefault(
                stem, {"text": word, "count": 0, "positions": []}
            )
            entry["count"] += 1
            if pos != -1:
                entry["positions"].append(pos)
            # نُبقي على أقصر شكل كممثّل (عادة الجذع نفسه)
            if len(word) < len(entry["text"]):
                entry["text"] = word

        # 3. حساب النقاط: TF بسيط مع تعزيز للكلمات الطويلة
        total = sum(s["count"] for s in stems.values())
        results = []
        for stem, info in stems.items():
            if info["count"] < min_count:
                continue
            # tf + bonus للطول (الكلمات الطويلة عادة أكثر دلالة)
            tf = info["count"] / total if total > 0 else 0
            length_bonus = min(len(info["text"]) / 10, 0.5)
            score = tf * (1 + length_bonus)
            results.append(
                Keyword(
                    text=info["text"],
                    stem=stem,
                    count=info["count"],
                    score=round(score, 5),
                    positions=info["positions"][:10],  # أول 10 مواقع فقط
                )
            )

        results.sort(key=lambda k: (-k.count, -k.score, k.text))

        # 4. ngrams (إن طُلبت)
        if self.ngram_max > 1:
            ngrams = self._extract_ngrams(text, words)
            results.extend(ngrams)
            results.sort(key=lambda k: (-k.count, -k.score, k.text))

        return results[:top_k]

    def _extract_ngrams(
        self,
        text: str,
        words: list[str],
    ) -> list[Keyword]:
        """استخراج عبارات ثنائية وثلاثية معبّرة."""
        results: list[Keyword] = []
        for n in range(max(2, self.ngram_min), self.ngram_max + 1):
            ngram_counts: Counter[str] = Counter()
            for i in range(len(words) - n + 1):
                grams = words[i:i + n]
                # نتجاهل إذا كل الكلمات stopwords
                if all(g in self.stopwords for g in grams):
                    continue
                # على الأقل كلمة واحدة طولها كافٍ
                if not any(len(g) >= self.min_word_length for g in grams):
                    continue
                phrase = " ".join(grams)
                ngram_counts[phrase] += 1

            for phrase, count in ngram_counts.items():
                if count < 2:  # العبارات يجب أن تتكرر للأهمية
                    continue
                positions = []
                pos = 0
                while True:
                    pos = text.find(phrase, pos)
                    if pos == -1:
                        break
                    positions.append(pos)
                    pos += 1
                    if len(positions) >= 10:
                        break
                results.append(
                    Keyword(
                        text=phrase,
                        stem=" ".join(light_stem(g) for g in phrase.split()),
                        count=count,
                        score=round(count * 0.05 * (len(phrase) / 10), 5),
                        positions=positions,
                    )
                )
        return results


@dataclass
class WatchlistMatch:
    """تطابق مصطلح من قائمة المتابعة في النص."""

    term: str           # المصطلح في القائمة
    matched_text: str   # النص المطابق فعلاً (قد يختلف بسبب التطبيع)
    start: int
    end: int
    line_index: int = -1  # إن مُرّر نص متعدد الأسطر
    note: str = ""        # ملاحظة من القائمة (سبب التعقّب)

    def to_dict(self) -> dict:
        return asdict(self)


class Watchlist:
    """قائمة متابعة لمصطلحات مُحدّدة سلفاً.

    تطابق مرنة: تتجاهل الحركات وتوحّد أشكال الألف/الياء.
    """

    def __init__(
        self,
        terms: list[str] | None = None,
        *,
        notes: dict[str, str] | None = None,
    ):
        """
        Args:
            terms: قائمة المصطلحات.
            notes: قاموس term → ملاحظة (سبب التعقّب).
        """
        self.terms: list[str] = []
        self.notes: dict[str, str] = notes or {}
        self._normalized: list[tuple[str, str]] = []  # [(term, normalized)]

        for t in terms or []:
            self.add(t)

    def __len__(self) -> int:
        return len(self.terms)

    def add(self, term: str, note: str = "") -> None:
        """إضافة مصطلح للقائمة."""
        if not term or not term.strip():
            return
        term = term.strip()
        if term in self.terms:
            return
        self.terms.append(term)
        self._normalized.append((term, self._normalize(term)))
        if note:
            self.notes[term] = note

    def _normalize(self, s: str) -> str:
        return normalize_yaa(normalize_alef(remove_diacritics(s))).strip()

    def scan(self, text: str) -> list[WatchlistMatch]:
        """البحث عن مصطلحات القائمة في نص.

        Args:
            text: النص للبحث فيه.

        Returns:
            قائمة WatchlistMatch.
        """
        if not text:
            return []

        results = []
        for term, norm_term in self._normalized:
            # نولّد قائمة متغيرات نصية محتملة للمصطلح ثم نبحث عنها في النص الأصلي
            variants = self._term_variants(term)

            for variant in variants:
                pattern = (
                    r"(?<![\u0600-\u06FF])"
                    + re.escape(variant)
                    + r"(?![\u0600-\u06FF])"
                )
                for m in re.finditer(pattern, text):
                    # تجنب التكرار: نفس الموقع
                    already = any(
                        r.start == m.start() and r.term == term
                        for r in results
                    )
                    if not already:
                        results.append(
                            WatchlistMatch(
                                term=term,
                                matched_text=m.group(),
                                start=m.start(),
                                end=m.end(),
                                note=self.notes.get(term, ""),
                            )
                        )

        # إزالة التداخلات
        results.sort(key=lambda r: (r.start, -(r.end - r.start)))
        cleaned: list[WatchlistMatch] = []
        for r in results:
            overlaps = any(
                not (r.end <= c.start or r.start >= c.end)
                for c in cleaned
            )
            if not overlaps:
                cleaned.append(r)
        return cleaned

    def _term_variants(self, term: str) -> list[str]:
        """توليد متغيرات نصية محتملة للمصطلح (مع/بدون حركات، أشكال ألف).

        نُولّد:
        - النص الأصلي
        - النص بدون حركات
        - النص بدون حركات + مع ألف بسيطة (إن وُجدت همزات)
        """
        variants = {term}
        no_diacritics = remove_diacritics(term)
        variants.add(no_diacritics)
        # تطبيع الألف
        variants.add(normalize_alef(no_diacritics))
        variants.add(normalize_yaa(normalize_alef(no_diacritics)))

        # نُعطي الأطول أولاً ليفوز عند التداخل
        return sorted(variants, key=len, reverse=True)

    def scan_lines(self, lines: list[str]) -> list[WatchlistMatch]:
        """مسح قائمة من الأسطر، مع تتبّع رقم السطر.

        مفيد لمسح transcripts بصيغة diarized.
        """
        results = []
        for i, line in enumerate(lines):
            for m in self.scan(line):
                m.line_index = i
                results.append(m)
        return results

    def save(self, path) -> None:
        """حفظ القائمة لـ JSON."""
        import json
        from pathlib import Path

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "terms": [
                {"term": t, "note": self.notes.get(t, "")}
                for t in self.terms
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path) -> "Watchlist":
        """تحميل من JSON."""
        import json
        from pathlib import Path

        path = Path(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        wl = cls()
        for item in data.get("terms", []):
            wl.add(item["term"], item.get("note", ""))
        return wl
