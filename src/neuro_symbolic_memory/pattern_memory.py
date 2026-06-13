from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

from .case_memory import CaseMemory


@dataclass
class LearnedPattern:
    """A compact abstraction mined from resolved cases.

    This gives the self-learning loop more than case lookup: repeated resolved
    episodes can build a reusable cause pattern such as
    database + cpu + slow + queries -> cause_database_bottleneck.
    """
    signature: Tuple[str, ...]
    root_cause: str
    support_count: int = 0
    contradiction_count: int = 0
    confidence: float = 0.50
    provenance: str = "resolved_trace_pattern_mining"


class PatternMemory:
    """Learns reusable feature→cause abstractions from resolved outcome traces."""

    def __init__(self) -> None:
        self.patterns: Dict[Tuple[Tuple[str, ...], str], LearnedPattern] = {}

    @staticmethod
    def signature(features: List[str]) -> Tuple[str, ...]:
        tokens = CaseMemory.tokenize(features)
        # Keep a compact, readable RCA signature; fall back to all tokens if no preferred tokens occur.
        preferred = {
            "database", "db", "cpu", "queries", "query", "latency", "slow",
            "schema", "missing", "column", "change", "cache", "evictions", "hit", "rate",
            "gateway", "timeout", "auth", "5xx", "fraud", "inventory", "churn", "demand",
        }
        selected = tuple(sorted(t for t in tokens if t in preferred))
        return selected if selected else tuple(tokens)

    def observe(self, features: List[str], root_cause: str, correct_prediction: bool | None = None) -> LearnedPattern:
        sig = self.signature(features)
        key = (sig, root_cause)
        pattern = self.patterns.get(key)
        if pattern is None:
            pattern = LearnedPattern(signature=sig, root_cause=root_cause)
            self.patterns[key] = pattern
        if correct_prediction is False:
            pattern.contradiction_count += 1
        else:
            pattern.support_count += 1
        total = pattern.support_count + pattern.contradiction_count
        pattern.confidence = round((pattern.support_count + 1) / (total + 2), 4)
        return pattern

    def predict(self, features: List[str]) -> dict | None:
        query_sig = set(self.signature(features))
        if not query_sig:
            return None
        best = None
        best_score = 0.0
        for pattern in self.patterns.values():
            sig = set(pattern.signature)
            if not sig:
                continue
            overlap = len(query_sig & sig) / len(query_sig | sig)
            score = 0.65 * overlap + 0.35 * pattern.confidence
            if score > best_score:
                best_score = score
                best = pattern
        if best is None:
            return None
        return {
            "root_cause": best.root_cause,
            "pattern_signature": list(best.signature),
            "pattern_confidence": best.confidence,
            "pattern_support_count": best.support_count,
            "pattern_contradiction_count": best.contradiction_count,
            "pattern_score": round(best_score, 4),
        }

    def to_records(self) -> List[dict]:
        return [asdict(p) for p in self.patterns.values()]

    @classmethod
    def from_records(cls, records: List[dict]) -> "PatternMemory":
        memory = cls()
        for record in records:
            record = dict(record)
            record["signature"] = tuple(record["signature"])
            pattern = LearnedPattern(**record)
            memory.patterns[(pattern.signature, pattern.root_cause)] = pattern
        return memory

    def report(self) -> List[dict]:
        return [
            {
                "signature": list(p.signature),
                "root_cause": p.root_cause,
                "support_count": p.support_count,
                "contradiction_count": p.contradiction_count,
                "confidence": p.confidence,
            }
            for p in sorted(self.patterns.values(), key=lambda x: (x.support_count, x.confidence), reverse=True)
        ]
