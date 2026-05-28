from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from .graph_memory import SymbolicGraphMemory
from .hypervector_memory import HypervectorMemory
from .models import Edge, QueryTask

# Direct learned relation -> supporting seed path patterns.
SUPPORT_PATTERNS = {
    "CAPITAL_CONTINENT": ("HAS_CAPITAL", "LOCATED_IN"),
    "ASSOCIATED_WITH": [("BORN_IN", "LOCATED_IN"), ("LIVES_IN", "LOCATED_IN")],
    "WORKS_IN": ("WORKS_AT", "ORG_LOCATED_IN"),
    "STUDIED_IN": ("STUDIED_AT", "UNIVERSITY_LOCATED_IN"),
    "HAS_SOLUTION": ("HAS_EQUATION", "EQUATION_SOLVES_TO"),
    "HAS_ROOT_CAUSE": ("HAS_SIGNAL", "SIGNAL_POINTS_TO"),
    "FORECAST_RISK": ("HAS_TREND", "TREND_IMPLIES_RISK"),
}

class Reasoner:
    def __init__(self, graph: SymbolicGraphMemory, hv: HypervectorMemory, batch_num: int = 0, reinforce: bool = True) -> None:
        self.graph = graph
        self.hv = hv
        self.batch_num = batch_num
        self.reinforce = reinforce

    def _support_path_for_edge(self, edge: Edge, active_only: bool = False) -> Optional[List[Edge]]:
        patterns = SUPPORT_PATTERNS.get(edge.relation)
        if not patterns:
            return [edge]
        if isinstance(patterns, tuple):
            patterns = [patterns]
        for rel1, rel2 in patterns:
            path = self.graph.find_two_hop_path(edge.src, rel1, rel2, active_only=False)
            if path and path[-1].dst == edge.dst:
                return path
        return [edge]

    def _format_support(self, edges: List[Edge]) -> str:
        return "; ".join([f"{e.src} --{e.relation}--> {e.dst}" for e in edges])

    def hybrid_answer(self, task: QueryTask, top_k: int = 5) -> Dict[str, Any]:
        # Fast path: vector retrieval proposes candidate memory edges.
        retrieved = self.hv.query([task.subject, task.target_relation, task.expected], top_k=top_k)
        for key, score, edge in retrieved:
            if edge.src == task.subject and edge.relation == task.target_relation:
                verified = self.graph.verify_edge(edge.src, edge.relation, edge.dst, active_only=True)
                if verified:
                    support_edges = self._support_path_for_edge(verified)
                    if self.reinforce:
                        self.graph.reinforce_edges([verified], increment=0.10, batch_num=self.batch_num)
                    return {
                        "answer": verified.dst,
                        "mode": "vector_retrieved_then_symbolically_verified",
                        "faithful": True,
                        "support": self._format_support(support_edges),
                        "retrieval_score": round(score, 4),
                    }
        # Slow fallback: symbolic graph traversal/lookup.
        direct = self.graph.outgoing(task.subject, task.target_relation, active_only=True)
        if direct:
            edge = direct[0]
            support_edges = self._support_path_for_edge(edge)
            if self.reinforce:
                self.graph.reinforce_edges([edge], increment=0.08, batch_num=self.batch_num)
            return {"answer": edge.dst, "mode": "symbolic_verified_fallback", "faithful": True, "support": self._format_support(support_edges), "retrieval_score": 0.0}
        return {"answer": None, "mode": "not_found", "faithful": False, "support": "", "retrieval_score": 0.0}

    def graph_only_answer(self, task: QueryTask) -> Dict[str, Any]:
        direct = self.graph.outgoing(task.subject, task.target_relation, active_only=False)
        if direct:
            edge = direct[0]
            support_edges = self._support_path_for_edge(edge)
            return {"answer": edge.dst, "mode": "graph_only", "faithful": True, "support": self._format_support(support_edges), "retrieval_score": 0.0}
        # Try 2-hop support pattern if learned shortcut is missing.
        patterns = SUPPORT_PATTERNS.get(task.target_relation)
        if isinstance(patterns, tuple):
            patterns = [patterns]
        if patterns:
            for rel1, rel2 in patterns:
                path = self.graph.find_two_hop_path(task.subject, rel1, rel2, active_only=False)
                if path:
                    return {"answer": path[-1].dst, "mode": "graph_only_two_hop", "faithful": True, "support": self._format_support(path), "retrieval_score": 0.0}
        return {"answer": None, "mode": "graph_only_not_found", "faithful": False, "support": "", "retrieval_score": 0.0}

    def vector_only_answer(self, task: QueryTask, top_k: int = 1) -> Dict[str, Any]:
        retrieved = self.hv.query([task.subject, task.target_relation, task.expected], top_k=top_k)
        if not retrieved:
            return {"answer": None, "mode": "vector_only_not_found", "faithful": False, "support": "", "retrieval_score": 0.0}
        key, score, edge = retrieved[0]
        # Vector-only does not verify the retrieved relation against graph constraints.
        return {"answer": edge.dst, "mode": "vector_only_unverified", "faithful": False, "support": f"retrieved:{key}", "retrieval_score": round(score, 4)}

    def answer(self, task: QueryTask, mode: str = "hybrid") -> Dict[str, Any]:
        if mode == "hybrid":
            return self.hybrid_answer(task)
        if mode == "graph_only":
            return self.graph_only_answer(task)
        if mode == "vector_only":
            return self.vector_only_answer(task)
        raise ValueError(f"Unknown mode: {mode}")
