from __future__ import annotations
from collections import Counter
from typing import Dict, List, Tuple
from .models import Trace, CandidateRelation

class TraceLearner:
    """Mines successful reasoning / math / RCA / forecast traces into reusable relations."""
    def __init__(self) -> None:
        self.pattern_rules: Dict[Tuple[str, str], Tuple[str, str]] = {
            ("HAS_CAPITAL", "LOCATED_IN"): ("CAPITAL_CONTINENT", "capital_to_continent"),
            ("BORN_IN", "LOCATED_IN"): ("ASSOCIATED_WITH", "location_chain_to_association"),
            ("WORKS_AT", "ORG_LOCATED_IN"): ("WORKS_IN", "organization_location_to_work_location"),
            ("STUDIED_AT", "UNIVERSITY_LOCATED_IN"): ("STUDIED_IN", "university_location_to_study_location"),
            ("LIVES_IN", "LOCATED_IN"): ("ASSOCIATED_WITH", "residence_chain_to_association"),
            ("HAS_EQUATION", "EQUATION_SOLVES_TO"): ("HAS_SOLUTION", "equation_trace_to_solution"),
            ("HAS_SIGNAL", "SIGNAL_POINTS_TO"): ("HAS_ROOT_CAUSE", "signal_trace_to_root_cause"),
            ("HAS_TREND", "TREND_IMPLIES_RISK"): ("FORECAST_RISK", "trend_trace_to_forecast_risk"),
        }
        self.abstraction_counts: Counter[str] = Counter()

    def propose(self, trace: Trace) -> List[CandidateRelation]:
        if not trace.success:
            return []
        candidates: List[CandidateRelation] = []
        for i in range(len(trace.reasoning_path) - 1):
            src1, rel1, mid1 = trace.reasoning_path[i]
            src2, rel2, dst2 = trace.reasoning_path[i + 1]
            if mid1 != src2:
                continue
            mapped = self.pattern_rules.get((rel1, rel2))
            if not mapped:
                continue
            implied_relation, abstraction = mapped
            self.abstraction_counts[abstraction] += 1
            candidates.append(
                CandidateRelation(
                    src=src1,
                    relation=implied_relation,
                    dst=dst2,
                    domain=trace.domain,
                    confidence=0.80,
                    provenance=f"learned_from_trace:{trace.trace_id}",
                    proof=f"{src1} --{rel1}--> {mid1}; {src2} --{rel2}--> {dst2}",
                    source_trace_id=trace.trace_id,
                    rule_id=f"({rel1}, {rel2}) -> {implied_relation}",
                )
            )
        return candidates

    def abstraction_summary(self) -> List[dict]:
        return [
            {"abstraction": abstraction, "support_count": count}
            for abstraction, count in sorted(self.abstraction_counts.items())
        ]
