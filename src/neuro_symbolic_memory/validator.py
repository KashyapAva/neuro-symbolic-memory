from __future__ import annotations
from typing import Tuple
from .models import CandidateRelation
from .graph_memory import SymbolicGraphMemory
from .schema import ALLOWED_RELATION_TYPES

class Validator:
    def __init__(self, graph: SymbolicGraphMemory) -> None:
        self.graph = graph

    def validate(self, candidate: CandidateRelation) -> Tuple[bool, str]:
        if candidate.confidence < 0.60:
            return False, "confidence_below_threshold"
        if self.graph.edge_exists(candidate.src, candidate.relation, candidate.dst):
            return False, "duplicate_relation"
        if candidate.src not in self.graph.nodes:
            return False, "missing_source_node"
        if candidate.dst not in self.graph.nodes:
            return False, "missing_target_node"
        if candidate.relation not in ALLOWED_RELATION_TYPES:
            return False, "unknown_relation_type"
        exp_src, exp_dst = ALLOWED_RELATION_TYPES[candidate.relation]
        actual_src = self.graph.nodes[candidate.src].node_type
        actual_dst = self.graph.nodes[candidate.dst].node_type
        if actual_src != exp_src or actual_dst != exp_dst:
            return False, f"type_mismatch_expected_{exp_src}_to_{exp_dst}_got_{actual_src}_to_{actual_dst}"
        if not candidate.proof:
            return False, "missing_proof"
        return True, "accepted"
