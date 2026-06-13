from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional


@dataclass
class Hypothesis:
    """A provisional memory created by the engine before an outcome is known.

    This is not manual confirmation. The engine stores its own prediction and later
    updates it from an observed resolved outcome trace.
    """
    case_id: str
    domain: str
    features: List[str]
    predicted_root_cause: str
    support_case_id: str
    support_proof: str
    similarity_score: float
    vector_score: float
    overlap_score: float
    confidence: float
    status: str = "provisional"
    provenance: str = "similar_case_self_prediction"
    created_batch: int = 0
    outcome_root_cause: str = ""
    feedback_count: int = 0
    error_count: int = 0


class HypothesisMemory:
    """Stores self-generated predictions and updates them from future outcome traces."""

    def __init__(self) -> None:
        self.hypotheses: Dict[str, Hypothesis] = {}

    def add(self, hypothesis: Hypothesis) -> Hypothesis:
        self.hypotheses[hypothesis.case_id] = hypothesis
        return hypothesis

    def get(self, case_id: str) -> Optional[Hypothesis]:
        return self.hypotheses.get(case_id)

    def promote(self, case_id: str, actual_root_cause: str, confidence_increment: float = 0.16) -> Hypothesis:
        hypothesis = self.hypotheses[case_id]
        hypothesis.status = "promoted"
        hypothesis.outcome_root_cause = actual_root_cause
        hypothesis.feedback_count += 1
        hypothesis.confidence = min(0.99, hypothesis.confidence + confidence_increment)
        return hypothesis

    def contradict(self, case_id: str, actual_root_cause: str, confidence_penalty: float = 0.30) -> Hypothesis:
        hypothesis = self.hypotheses[case_id]
        hypothesis.status = "contradicted"
        hypothesis.outcome_root_cause = actual_root_cause
        hypothesis.feedback_count += 1
        hypothesis.error_count += 1
        hypothesis.confidence = max(0.05, hypothesis.confidence - confidence_penalty)
        return hypothesis

    def to_records(self) -> List[dict]:
        return [asdict(h) for h in self.hypotheses.values()]

    @classmethod
    def from_records(cls, records: List[dict]) -> "HypothesisMemory":
        memory = cls()
        for record in records:
            memory.add(Hypothesis(**record))
        return memory

    def report(self) -> Dict[str, int]:
        counts = {"provisional": 0, "promoted": 0, "contradicted": 0}
        for hypothesis in self.hypotheses.values():
            counts[hypothesis.status] = counts.get(hypothesis.status, 0) + 1
        counts["total"] = len(self.hypotheses)
        return counts
