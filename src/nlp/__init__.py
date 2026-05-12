"""Call Intelligence Engine — وحدة معالجة اللغة الطبيعية."""

from src.nlp.coreference import EntityCluster, EntityResolver, normalize_person_name
from src.nlp.events import Event, EventExtractor, events_to_kg_triples
from src.nlp.keywords import Keyword, KeywordExtractor, Watchlist, WatchlistMatch
from src.nlp.ner import Entity, EntityExtractor, merge_duplicate_entities
from src.nlp.pipeline import NLPPipeline, NLPResult, analyze_text, analyze_transcript

__all__ = [
    "Entity",
    "EntityExtractor",
    "merge_duplicate_entities",
    "Keyword",
    "KeywordExtractor",
    "Watchlist",
    "WatchlistMatch",
    "Event",
    "EventExtractor",
    "events_to_kg_triples",
    "EntityCluster",
    "EntityResolver",
    "normalize_person_name",
    "NLPPipeline",
    "NLPResult",
    "analyze_text",
    "analyze_transcript",
]
