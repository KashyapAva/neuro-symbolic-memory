from __future__ import annotations
from typing import Any, Dict, List

from .case_memory import CaseEpisode, CaseMemory
from .graph_memory import SymbolicGraphMemory
from .hypervector_memory import HypervectorMemory
from .hypothesis_memory import Hypothesis, HypothesisMemory
from .memory_store import MemoryStore
from .models import QueryTask, Trace
from .pattern_memory import PatternMemory
from .reasoner import Reasoner
from .replay import ReplayBuffer
from .trace_learner import TraceLearner
from .validator import Validator


class MemoryEngine:
    """Integration-facing neuro-symbolic memory engine.

    This class exposes all mechanisms required by the assignment:
    - typed symbolic graph memory with proof/provenance;
    - vector-symbolic/hypervector retrieval;
    - trace-based learning from successful/resolved episodes;
    - case memory for similar-episode recall;
    - hypothesis memory for self-generated provisional predictions;
    - pattern memory for reusable feature->cause abstractions;
    - replay/decay and persistence.

    Human review can be layered on top in production, but the prototype's core
    self-learning loop uses resolved outcome traces, not manual confirmation.
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
        self.episodic_traces: List[Trace] = []
        self.case_memory = CaseMemory(dim=dim, seed=seed + 101)
        self.hypotheses = HypothesisMemory()
        self.pattern_memory = PatternMemory()
        self.dim = dim
        self.seed = seed

    # ------------------------------------------------------------------
    # Core graph / vector memory API
    # ------------------------------------------------------------------
    def add_node(self, label: str, node_type: str, provenance: str = "integration") -> None:
        self.graph.add_node(label, node_type, provenance=provenance)

    def add_fact(self, src: str, relation: str, dst: str, domain: str = "external", provenance: str = "integration") -> None:
        edge = self.graph.add_edge(src, relation, dst, domain=domain, provenance=provenance, batch_num=self.batch_num)
        self.hv.add_or_refresh_edge(edge)

    def ingest_trace(self, trace: Trace) -> Dict[str, Any]:
        """Ingest a successful/failed reasoning episode and learn validated relations.

        Successful traces propose candidate semantic memories; the validator only
        allows type-correct/proof-backed candidates into graph + vector memory.
        """
        self.episodic_traces.append(trace)
        accepted, rejected = 0, 0
        for candidate in self.learner.propose(trace):
            ok, reason = self.validator.validate(candidate)
            record = {
                "candidate": f"{candidate.src} --{candidate.relation}--> {candidate.dst}",
                "reason": reason,
                "trace": candidate.source_trace_id,
                "proof": candidate.proof,
            }
            if ok:
                edge = self.graph.add_edge(
                    candidate.src,
                    candidate.relation,
                    candidate.dst,
                    domain=candidate.domain,
                    provenance=candidate.provenance,
                    proof=candidate.proof,
                    rule_id=candidate.rule_id,
                    confidence=candidate.confidence,
                    batch_num=self.batch_num,
                )
                self.hv.add_or_refresh_edge(edge)
                self.accepted.append(record)
                accepted += 1
            else:
                self.rejected.append(record)
                rejected += 1
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

    # ------------------------------------------------------------------
    # Self-learning RCA memory loop
    # ------------------------------------------------------------------
    def ingest_resolved_episode(
        self,
        case_id: str,
        signal_id: str,
        root_cause: str,
        features: List[str],
        domain: str = "data_observability_rca",
        remediation: str = "",
        provenance: str = "resolved_outcome_trace",
    ) -> Dict[str, Any]:
        """Ingest a solved incident and automatically learn from it.

        A resolved trace teaches exact graph memory, case memory, and a reusable
        feature-pattern memory. This is not a manual confirmation step: the
        resolved trace itself is the learning signal.
        """
        self.add_node(case_id, "Incident", provenance=provenance)
        self.add_node(signal_id, "Signal", provenance=provenance)
        self.add_node(root_cause, "Cause", provenance=provenance)
        if remediation:
            self.add_node(remediation, "Solution", provenance=provenance)

        if not self.graph.edge_exists(case_id, "HAS_SIGNAL", signal_id):
            self.add_fact(case_id, "HAS_SIGNAL", signal_id, domain=domain, provenance=provenance)
        if not self.graph.edge_exists(signal_id, "SIGNAL_POINTS_TO", root_cause):
            self.add_fact(signal_id, "SIGNAL_POINTS_TO", root_cause, domain=domain, provenance=provenance)
        if remediation and not self.graph.edge_exists(root_cause, "HAS_REMEDIATION", remediation):
            self.add_fact(root_cause, "HAS_REMEDIATION", remediation, domain=domain, provenance=provenance)

        trace = Trace(
            trace_id=f"resolved_trace:{case_id}",
            domain=domain,
            question=f"Resolved outcome trace for {case_id}",
            reasoning_path=[(case_id, "HAS_SIGNAL", signal_id), (signal_id, "SIGNAL_POINTS_TO", root_cause)],
            answer=root_cause,
            success=True,
        )
        result = self.ingest_trace(trace)
        support_edge = self.graph.verify_edge(case_id, "HAS_ROOT_CAUSE", root_cause, active_only=True)
        proof = support_edge.proof if support_edge else f"{case_id} --HAS_SIGNAL--> {signal_id}; {signal_id} --SIGNAL_POINTS_TO--> {root_cause}"
        self.store_case_episode(
            case_id=case_id,
            features=features,
            root_cause=root_cause,
            domain=domain,
            remediation=remediation,
            proof=proof,
            provenance=provenance,
            confidence=0.86,
        )
        pattern = self.pattern_memory.observe(features, root_cause)
        result.update({
            "case_memory_stored": True,
            "semantic_memory": f"{case_id} --HAS_ROOT_CAUSE--> {root_cause}",
            "pattern_memory": {
                "signature": list(pattern.signature),
                "root_cause": pattern.root_cause,
                "support_count": pattern.support_count,
                "confidence": pattern.confidence,
            },
        })
        return result

    def store_case_episode(
        self,
        case_id: str,
        features: List[str],
        root_cause: str,
        domain: str = "rca",
        remediation: str = "",
        proof: str = "",
        provenance: str = "resolved_episode",
        confidence: float = 1.0,
    ) -> None:
        if root_cause not in self.graph.nodes:
            raise ValueError(f"Root cause node must exist in graph before storing case: {root_cause}")
        episode = CaseEpisode(
            case_id=case_id,
            domain=domain,
            features=features,
            root_cause=root_cause,
            remediation=remediation,
            proof=proof,
            provenance=provenance,
            confidence=confidence,
            created_batch=self.batch_num,
        )
        self.case_memory.add_episode(episode)

    def predict_from_memory(self, case_id: str, features: List[str], top_k: int = 3, min_score: float = 0.20) -> Dict[str, Any]:
        """Create a provisional prediction from case + pattern memory.

        The prediction is stored immediately as a hypothesis. A later resolved
        outcome trace automatically promotes or contradicts it.
        """
        matches = self.case_memory.query(features, top_k=top_k)
        pattern_pred = self.pattern_memory.predict(features)

        if (not matches or float(matches[0]["score"]) < min_score) and not pattern_pred:
            return {
                "answer": None,
                "mode": "memory_prediction_not_found",
                "hypothesis_status": "none_created",
                "faithful_to_memory": False,
                "support": "",
                "similarity_score": 0.0,
                "similar_case": None,
                "pattern_prediction": None,
            }

        best = matches[0] if matches else None
        episode: CaseEpisode | None = best["case"] if best else None  # type: ignore[index]
        verified = None
        if episode is not None:
            verified = self.graph.verify_edge(episode.case_id, "HAS_ROOT_CAUSE", episode.root_cause, active_only=True)

        if episode is not None and verified is not None:
            root_cause = episode.root_cause
            similarity_score = float(best["score"])
            vector_score = float(best["vector_score"])
            overlap_score = float(best["overlap_score"])
            support_case_id = episode.case_id
            support_proof = episode.proof or verified.proof
            overlap_tokens = best["overlap_tokens"]
            self.case_memory.reinforce(episode.case_id)
            self.graph.reinforce_edges([verified], increment=0.05, batch_num=self.batch_num)
            source = "case_memory+graph_proof"
        elif pattern_pred is not None:
            root_cause = pattern_pred["root_cause"]
            similarity_score = float(pattern_pred["pattern_score"])
            vector_score = 0.0
            overlap_score = float(pattern_pred["pattern_score"])
            support_case_id = "pattern_memory"
            support_proof = f"pattern_signature={pattern_pred['pattern_signature']}; support_count={pattern_pred['pattern_support_count']}; confidence={pattern_pred['pattern_confidence']}"
            overlap_tokens = pattern_pred["pattern_signature"]
            source = "pattern_memory"
        else:
            return {
                "answer": None,
                "mode": "similar_case_found_but_not_symbolically_verified",
                "hypothesis_status": "none_created",
                "faithful_to_memory": False,
                "support": "retrieved case existed but its graph proof was inactive/missing",
                "similarity_score": float(best["score"]) if best else 0.0,
                "similar_case": episode.case_id if episode else None,
                "pattern_prediction": pattern_pred,
            }

        pattern_conf = float(pattern_pred["pattern_confidence"]) if pattern_pred else 0.50
        confidence = round(min(0.95, 0.30 + 0.38 * similarity_score + 0.17 * pattern_conf), 4)
        hypothesis = Hypothesis(
            case_id=case_id,
            domain="data_observability_rca",
            features=features,
            predicted_root_cause=root_cause,
            support_case_id=support_case_id,
            support_proof=support_proof,
            similarity_score=similarity_score,
            vector_score=vector_score,
            overlap_score=overlap_score,
            confidence=confidence,
            provenance=f"self_prediction_from_{source}",
            created_batch=self.batch_num,
        )
        self.hypotheses.add(hypothesis)
        return {
            "answer": root_cause,
            "mode": "memory_retrieved_then_stored_as_provisional_hypothesis",
            "hypothesis_status": "provisional_memory_pending_outcome_trace",
            "faithful_to_memory": True,
            "support": f"source={source}; support_case={support_case_id}; overlap_tokens={overlap_tokens}; support_proof={support_proof}",
            "confidence": confidence,
            "similarity_score": round(similarity_score, 4),
            "vector_score": round(vector_score, 4),
            "overlap_score": round(overlap_score, 4),
            "similar_case": support_case_id,
            "pattern_prediction": pattern_pred,
        }

    def observe_outcome_trace(
        self,
        case_id: str,
        actual_root_cause: str,
        features: List[str],
        signal_id: str | None = None,
        domain: str = "data_observability_rca",
        remediation: str = "",
    ) -> Dict[str, Any]:
        """Update memory from a future resolved outcome trace.

        This is the self-learning feedback step: the engine compares its own
        stored hypothesis against the later outcome and promotes or weakens it.
        """
        hypothesis = self.hypotheses.get(case_id)
        self.add_node(case_id, "Incident", provenance="outcome_trace")
        self.add_node(actual_root_cause, "Cause", provenance="outcome_trace")
        if remediation:
            self.add_node(remediation, "Solution", provenance="outcome_trace")

        if signal_id:
            self.add_node(signal_id, "Signal", provenance="outcome_trace")
            if not self.graph.edge_exists(case_id, "HAS_SIGNAL", signal_id):
                self.add_fact(case_id, "HAS_SIGNAL", signal_id, domain=domain, provenance="outcome_trace")
            if not self.graph.edge_exists(signal_id, "SIGNAL_POINTS_TO", actual_root_cause):
                self.add_fact(signal_id, "SIGNAL_POINTS_TO", actual_root_cause, domain=domain, provenance="outcome_trace")

        if hypothesis is None:
            self.store_case_episode(
                case_id=case_id,
                features=features,
                root_cause=actual_root_cause,
                domain=domain,
                remediation=remediation,
                proof=f"resolved_outcome_trace:{case_id}",
                provenance="resolved_without_prior_hypothesis",
                confidence=0.72,
            )
            pattern = self.pattern_memory.observe(features, actual_root_cause)
            return {
                "case_id": case_id,
                "status": "stored_resolved_case_without_prior_prediction",
                "actual_root_cause": actual_root_cause,
                "pattern_updated": {"signature": list(pattern.signature), "support_count": pattern.support_count, "confidence": pattern.confidence},
            }

        if hypothesis.predicted_root_cause == actual_root_cause:
            promoted = self.hypotheses.promote(case_id, actual_root_cause)
            proof = (
                f"auto_promoted_from_outcome_trace:{case_id}; "
                f"predicted={hypothesis.predicted_root_cause}; "
                f"support_case={hypothesis.support_case_id}; "
                f"outcome_root_cause={actual_root_cause}; "
                f"support_proof={hypothesis.support_proof}"
            )
            edge = self.graph.add_edge(
                case_id,
                "HAS_ROOT_CAUSE",
                actual_root_cause,
                domain=domain,
                provenance=f"auto_promoted_from_outcome_trace:{case_id}",
                proof=proof,
                rule_id="self_prediction + resolved_outcome_trace -> HAS_ROOT_CAUSE",
                confidence=promoted.confidence,
                batch_num=self.batch_num,
            )
            self.hv.add_or_refresh_edge(edge)
            if hypothesis.support_case_id in self.graph.nodes and not self.graph.edge_exists(case_id, "SIMILAR_TO", hypothesis.support_case_id):
                sim_edge = self.graph.add_edge(
                    case_id,
                    "SIMILAR_TO",
                    hypothesis.support_case_id,
                    domain=domain,
                    provenance="case_memory_similarity",
                    proof=proof,
                    rule_id="similar_case_retrieval",
                    confidence=hypothesis.similarity_score,
                    batch_num=self.batch_num,
                )
                self.hv.add_or_refresh_edge(sim_edge)
            self.store_case_episode(
                case_id=case_id,
                features=features,
                root_cause=actual_root_cause,
                domain=domain,
                remediation=remediation,
                proof=proof,
                provenance=f"auto_promoted_from_outcome_trace:{case_id}",
                confidence=promoted.confidence,
            )
            pattern = self.pattern_memory.observe(features, actual_root_cause, correct_prediction=True)
            return {
                "case_id": case_id,
                "prediction": hypothesis.predicted_root_cause,
                "actual_root_cause": actual_root_cause,
                "prediction_correct": True,
                "hypothesis_status": promoted.status,
                "confidence_after_feedback": round(promoted.confidence, 4),
                "promoted_edge": f"{case_id} --HAS_ROOT_CAUSE--> {actual_root_cause}",
                "pattern_updated": {"signature": list(pattern.signature), "support_count": pattern.support_count, "confidence": pattern.confidence},
                "memory_update": "auto_promoted_to_semantic_graph_memory",
            }

        contradicted = self.hypotheses.contradict(case_id, actual_root_cause)
        self.store_case_episode(
            case_id=case_id,
            features=features,
            root_cause=actual_root_cause,
            domain=domain,
            remediation=remediation,
            proof=f"contradicted_prediction={hypothesis.predicted_root_cause}; outcome_root_cause={actual_root_cause}",
            provenance=f"counterexample_outcome_trace:{case_id}",
            confidence=0.70,
        )
        pattern = self.pattern_memory.observe(features, actual_root_cause, correct_prediction=False)
        return {
            "case_id": case_id,
            "prediction": hypothesis.predicted_root_cause,
            "actual_root_cause": actual_root_cause,
            "prediction_correct": False,
            "hypothesis_status": contradicted.status,
            "confidence_after_feedback": round(contradicted.confidence, 4),
            "pattern_updated": {"signature": list(pattern.signature), "support_count": pattern.support_count, "confidence": pattern.confidence},
            "memory_update": "wrong_prediction_not_promoted_counterexample_stored",
        }

    # Backwards-compatible alias for earlier realistic demo language.
    def suggest_from_similar_case(self, case_id: str, features: List[str], top_k: int = 3, min_score: float = 0.20) -> Dict[str, Any]:
        return self.predict_from_memory(case_id, features, top_k=top_k, min_score=min_score)

    # ------------------------------------------------------------------
    # Reporting and persistence
    # ------------------------------------------------------------------
    def memory_report(self) -> Dict[str, Any]:
        report = MemoryStore.report(self.graph)
        report["gamma34"] = self.graph.gamma34_summary()
        report["episodic_traces"] = len(self.episodic_traces)
        report["case_episodes"] = len(self.case_memory.episodes)
        report["hypotheses"] = self.hypotheses.report()
        report["patterns"] = self.pattern_memory.report()[:5]
        report["accepted_updates"] = len(self.accepted)
        report["rejected_updates"] = len(self.rejected)
        return report

    def save_memory(self, path: str) -> str:
        return str(MemoryStore.save_engine_state(
            self.graph,
            path,
            self.case_memory.to_records(),
            self.hypotheses.to_records(),
            self.pattern_memory.to_records(),
        ))

    def load_memory(self, path: str) -> None:
        self.graph, self.hv, case_records, hypothesis_records, pattern_records = MemoryStore.load_engine_state(path, dim=self.dim, seed=self.seed)
        self.case_memory = CaseMemory.from_records(case_records, dim=self.dim, seed=self.seed + 101)
        self.hypotheses = HypothesisMemory.from_records(hypothesis_records)
        self.pattern_memory = PatternMemory.from_records(pattern_records)
        self.validator = Validator(self.graph)

    def advance_time_without_replay(self, batch_num: int, max_staleness: int = 1) -> None:
        self.batch_num = batch_num
        self.graph.decay_without_replay(batch_num=batch_num, max_staleness=max_staleness)
        self.hv.remove_inactive_edges()


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
        def tool(query: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "answer": self.answer(query),
                "context": self.retrieve({"symbols": [query["subject"], query["target_relation"], query.get("expected", "")], "top_k": 5}),
            }
        return tool
