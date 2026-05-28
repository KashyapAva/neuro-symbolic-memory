from __future__ import annotations
from typing import Any, Dict, Iterable, List, Tuple
from .graph_memory import SymbolicGraphMemory
from .hypervector_memory import HypervectorMemory
from .trace_learner import TraceLearner
from .validator import Validator
from .replay import ReplayBuffer
from .reasoner import Reasoner
from .models import Trace, QueryTask

class MemoryEngine:
    """Small integration-facing API for existing reasoning frameworks.

    A framework can use this object as a memory/retrieval tool:
    - add_fact(...)
    - ingest_trace(...)
    - query(...)
    - retrieve_context(...)

    This intentionally avoids a dependency on LangChain/LlamaIndex/DSPy while
    exposing the same tool-like surface those frameworks expect.
    """
    def __init__(self, dim: int = 4096, seed: int = 7) -> None:
        self.graph = SymbolicGraphMemory()
        self.hv = HypervectorMemory(dim=dim, seed=seed)
        self.learner = TraceLearner()
        self.validator = Validator(self.graph)
        self.replay_buffer = ReplayBuffer()
        self.batch_num = 0
        self.accepted: List[Dict[str, Any]] = []
        self.rejected: List[Dict[str, Any]] = []

    def add_node(self, label: str, node_type: str, provenance: str = "integration") -> None:
        self.graph.add_node(label, node_type, provenance=provenance)

    def add_fact(self, src: str, relation: str, dst: str, domain: str = "external", provenance: str = "integration") -> None:
        edge = self.graph.add_edge(src, relation, dst, domain=domain, provenance=provenance, batch_num=self.batch_num)
        self.hv.add_or_refresh_edge(edge)

    def ingest_trace(self, trace: Trace) -> Dict[str, Any]:
        accepted, rejected = 0, 0
        for candidate in self.learner.propose(trace):
            ok, reason = self.validator.validate(candidate)
            if ok:
                edge = self.graph.add_edge(candidate.src, candidate.relation, candidate.dst, domain=candidate.domain, provenance=candidate.provenance, proof=candidate.proof, rule_id=candidate.rule_id, confidence=candidate.confidence, batch_num=self.batch_num)
                self.hv.add_or_refresh_edge(edge)
                accepted += 1
                self.accepted.append({"candidate": f"{candidate.src} --{candidate.relation}--> {candidate.dst}", "reason": reason, "trace": candidate.source_trace_id})
            else:
                rejected += 1
                self.rejected.append({"candidate": f"{candidate.src} --{candidate.relation}--> {candidate.dst}", "reason": reason, "trace": candidate.source_trace_id})
        return {"accepted": accepted, "rejected": rejected}

    def query(self, task: QueryTask, mode: str = "hybrid") -> Dict[str, Any]:
        reasoner = Reasoner(self.graph, self.hv, batch_num=self.batch_num)
        return reasoner.answer(task, mode=mode)

    def retrieve_context(self, query_symbols: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        results = []
        for key, score, edge in self.hv.query(query_symbols, top_k=top_k):
            results.append({
                "key": key,
                "score": round(score, 4),
                "edge": f"{edge.src} --{edge.relation}--> {edge.dst}",
                "domain": edge.domain,
                "relation_family": edge.relation_family,
                "provenance": edge.provenance,
                "proof": edge.proof,
            })
        return results

    def consolidate(self) -> int:
        self.replay_buffer.update_from_graph(self.graph)
        return self.replay_buffer.replay(self.hv, batch_num=self.batch_num)

class ReasoningFrameworkAdapter:
    """Generic adapter showing how an outside reasoning framework would call the memory engine."""
    def __init__(self, engine: MemoryEngine) -> None:
        self.engine = engine

    def retrieve(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        symbols = query.get("symbols", [])
        top_k = int(query.get("top_k", 5))
        return self.engine.retrieve_context(symbols, top_k=top_k)

    def answer(self, query: Dict[str, Any]) -> Dict[str, Any]:
        task = QueryTask(
            task_id=query.get("task_id", "external_query"),
            domain=query.get("domain", "external"),
            subject=query["subject"],
            target_relation=query["target_relation"],
            expected=query.get("expected", ""),
            batch="integration_query",
        )
        return self.engine.query(task, mode=query.get("mode", "hybrid"))

    def as_tool(self):
        """Returns a callable that can be registered as a tool/retriever in an agent framework."""
        def tool(query: Dict[str, Any]) -> Dict[str, Any]:
            return {"answer": self.answer(query), "context": self.retrieve({"symbols": [query["subject"], query["target_relation"], query.get("expected", "")], "top_k": 5})}
        return tool
