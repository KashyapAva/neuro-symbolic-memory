from __future__ import annotations
from typing import Tuple
from .models import CandidateRelation
from .graph_memory import SymbolicGraphMemory
from .schema import ALLOWED_RELATION_TYPES, gamma_transition_allowed, gamma_transition_reason

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

        # γ(3,4) family-level validation: edge family must be compatible with
        # the source/destination gamma node kinds before more specific typing.
        src_gamma = self.graph.nodes[candidate.src].gamma_class
        dst_gamma = self.graph.nodes[candidate.dst].gamma_class
        if not gamma_transition_allowed(src_gamma, candidate.relation, dst_gamma):
            return False, gamma_transition_reason(src_gamma, candidate.relation, dst_gamma)

        # Task-specific relation signature validation.
        allowed_specific = ALLOWED_RELATION_TYPES[candidate.relation]
        allowed_pairs = allowed_specific if isinstance(allowed_specific, list) else [allowed_specific]
        actual_src = self.graph.nodes[candidate.src].node_type
        actual_dst = self.graph.nodes[candidate.dst].node_type
        if (actual_src, actual_dst) not in allowed_pairs:
            expected = "_or_".join([f"{a}_to_{b}" for a, b in allowed_pairs])
            return False, f"type_mismatch_expected_{expected}_got_{actual_src}_to_{actual_dst}"
        if not candidate.proof:
            return False, "missing_proof"
        return True, "accepted"
