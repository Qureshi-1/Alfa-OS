"""Perception Engine — raw input processing, feature extraction, intent detection.

Stage 1 of the cognition pipeline. Transforms raw user input into a structured
PerceptionResult with detected intents, entities, and context.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from prototype.common import Event, EventBus

logger = logging.getLogger("alfa.cognition.perception")

# ── Intent taxonomy ────────────────────────────────────────────────────────

INTENT_PATTERNS: Dict[str, List[str]] = {
    "query": [r"\bwhat\b", r"\bhow\b", r"\bwhy\b", r"\bwhen\b", r"\bwhere\b", r"\bwho\b", r"\bis\b", r"\bare\b", r"\bcan\b", r"\bcould\b"],
    "command": [r"\brun\b", r"\bexecute\b", r"\bstart\b", r"\bstop\b", r"\bcreate\b", r"\bdelete\b", r"\bupdate\b", r"\bset\b", r"\bopen\b", r"\bclose\b"],
    "conversation": [r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bthanks\b", r"\bthank you\b", r"\bplease\b"],
    "analysis": [r"\banalyze\b", r"\bcompare\b", r"\bevaluate\b", r"\breview\b", r"\bcheck\b", r"\bverify\b"],
    "generation": [r"\bgenerate\b", r"\bwrite\b", r"\bcreate\b", r"\bmake\b", r"\bbuild\b", r"\bproduce\b"],
}

ENTITY_PATTERNS: Dict[str, str] = {
    "file": r'(?:file|path|directory)\s+["\']?([^\s"\']+)["\']?',
    "number": r'\b(\d+(?:\.\d+)?)\b',
    "url": r'(https?://[^\s]+)',
    "code": r'```[\s\S]*?```',
}


@dataclass
class PerceptionResult:
    """Output of the perception stage."""
    id: str = field(default_factory=lambda: str(uuid4()))
    raw_input: str = ""
    normalized_input: str = ""
    intents: List[Dict[str, Any]] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    features: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    context_signals: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerceptionPlugin:
    """Base class for perception stage plugins.

    Plugins can:
    - Pre-process raw input before intent detection
    - Override intent detection
    - Add custom entity extraction
    - Post-process the PerceptionResult
    """

    def pre_process(self, raw_input: str, context: Dict[str, Any]) -> str:
        """Optionally transform raw input before processing. Return modified input."""
        return raw_input

    def detect_intents(self, normalized: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optionally override intent detection. Return None to use default."""
        return []

    def extract_entities(self, normalized: str, context: Dict[str, Any]) -> Dict[str, List[str]]:
        """Optionally add custom entity extraction."""
        return {}

    def post_process(self, result: PerceptionResult, context: Dict[str, Any]) -> PerceptionResult:
        """Optionally modify the final result."""
        return result


class PerceptionEngine:
    """Stage 1: transforms raw input into structured perception data.

    Supports plugin-based extension for custom intent/entity handling.
    Emits: PerceptionStarted, PerceptionProcessed
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus
        self._plugins: List[PerceptionPlugin] = []
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("PerceptionEngine loaded: %d plugins", len(self._plugins))

    def is_loaded(self) -> bool:
        return self._loaded

    def register_plugin(self, plugin: PerceptionPlugin) -> None:
        self._plugins.append(plugin)

    def unregister_plugin(self, plugin: PerceptionPlugin) -> bool:
        if plugin in self._plugins:
            self._plugins.remove(plugin)
            return True
        return False

    def process(self, raw_input: str, context: Optional[Dict[str, Any]] = None) -> PerceptionResult:
        """Process raw input through the perception pipeline.

        Args:
            raw_input: The raw user input string.
            context: Optional context dict for additional signals.

        Returns:
            PerceptionResult with intents, entities, and features.
        """
        ctx = context or {}
        start = time.time()

        self._emit("PerceptionStarted", {"input_length": len(raw_input)})

        # Plugin pre-processing
        processed_input = raw_input
        for plugin in self._plugins:
            processed_input = plugin.pre_process(processed_input, ctx)

        # Normalize
        normalized = self._normalize(processed_input)

        # Intent detection (plugins can override)
        intents = []
        for plugin in self._plugins:
            plugin_intents = plugin.detect_intents(normalized, ctx)
            if plugin_intents:
                intents = plugin_intents
                break
        if not intents:
            intents = self._detect_intents(normalized)

        # Entity extraction (plugins can add)
        entities = self._extract_entities(normalized)
        for plugin in self._plugins:
            plugin_entities = plugin.extract_entities(normalized, ctx)
            for key, values in plugin_entities.items():
                entities.setdefault(key, []).extend(values)

        # Feature extraction
        features = self._extract_features(raw_input, normalized, intents, entities)

        # Confidence scoring
        confidence = self._score_confidence(intents, entities, features)

        # Build result
        result = PerceptionResult(
            raw_input=raw_input,
            normalized_input=normalized,
            intents=intents,
            entities=entities,
            features=features,
            confidence=confidence,
            context_signals=ctx,
            latency_ms=round((time.time() - start) * 1000, 2),
        )

        # Plugin post-processing
        for plugin in self._plugins:
            result = plugin.post_process(result, ctx)

        self._emit("PerceptionProcessed", {
            "intents": [i["name"] for i in intents],
            "confidence": confidence,
            "entity_count": sum(len(v) for v in entities.values()),
            "latency_ms": result.latency_ms,
        })

        return result

    def _normalize(self, text: str) -> str:
        """Lowercase, strip, collapse whitespace."""
        return re.sub(r"\s+", " ", text.lower().strip())

    def _detect_intents(self, normalized: str) -> List[Dict[str, Any]]:
        """Rule-based intent detection from pattern taxonomy."""
        detected = []
        for intent_name, patterns in INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, normalized):
                    score += 1
            if score > 0:
                detected.append({
                    "name": intent_name,
                    "confidence": min(score / len(patterns), 1.0),
                    "method": "pattern",
                })
        # Sort by confidence descending
        detected.sort(key=lambda x: x["confidence"], reverse=True)
        return detected

    def _extract_entities(self, normalized: str) -> Dict[str, List[str]]:
        """Extract entities from normalized text."""
        entities: Dict[str, List[str]] = {}
        for entity_type, pattern in ENTITY_PATTERNS.items():
            matches = re.findall(pattern, normalized, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches
        return entities

    def _extract_features(self, raw: str, normalized: str,
                          intents: List[Dict], entities: Dict) -> Dict[str, Any]:
        """Extract structural features from the input."""
        return {
            "length": len(raw),
            "word_count": len(normalized.split()),
            "has_code": bool(re.search(r"```", raw)),
            "has_question": "?" in raw,
            "has_exclamation": "!" in raw,
            "primary_intent": intents[0]["name"] if intents else "unknown",
            "entity_types": list(entities.keys()),
        }

    def _score_confidence(self, intents: List[Dict], entities: Dict,
                          features: Dict) -> float:
        """Score overall perception confidence."""
        if not intents:
            return 0.1
        intent_conf = intents[0]["confidence"]
        entity_bonus = min(len(entities) * 0.1, 0.3)
        length_factor = min(features.get("word_count", 0) / 20, 0.2)
        return min(intent_conf + entity_bonus + length_factor, 1.0)

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._event_bus:
            self._event_bus.publish(Event(
                event_type=event_type, payload=payload, source="perception",
            ))
