from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
from .models import Batch, CandidateRelation, QueryTask
from .graph_memory import SymbolicGraphMemory
from .hypervector_memory import HypervectorMemory
from .trace_learner import TraceLearner
from .validator import Validator
from .replay import ReplayBuffer
from .reasoner import Reasoner
from .evaluation import Evaluator
from .schema import relation_family

class ExperimentRunner:
    def __init__(self, batches: List[Batch], output_dir: str | Path, replay_enabled: bool = True, decay_without_replay: bool = False, run_label: str = "hybrid_replay") -> None:
        self.batches = batches
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.replay_enabled = replay_enabled
        self.decay_without_replay = decay_without_replay
        self.run_label = run_label
        self.graph = SymbolicGraphMemory()
        self.hv = HypervectorMemory(dim=4096, seed=7)
        self.learner = TraceLearner()
        self.validator = Validator(self.graph)
        self.replay = ReplayBuffer()
        self.all_tasks: List[QueryTask] = []
        self.summary_rows: List[Dict[str, Any]] = []
        self.task_rows: List[Dict[str, Any]] = []
        self.learned_rows: List[Dict[str, Any]] = []
        self.rejected_rows: List[Dict[str, Any]] = []
        self.retrieval_rows: List[Dict[str, Any]] = []
        self.abstraction_rows: List[Dict[str, Any]] = []

    def add_batch_facts(self, batch: Batch, batch_num: int) -> None:
        for label, node_type in batch.nodes:
            self.graph.add_node(label, node_type, provenance=batch.name)
        for src, rel, dst, domain in batch.edges:
            edge = self.graph.add_edge(src, rel, dst, domain=domain, provenance=batch.name, batch_num=batch_num)
            self.hv.add_or_refresh_edge(edge)

    def learn_from_batch(self, batch: Batch, batch_num: int) -> None:
        print("\nTrace learning:")
        for trace in batch.traces:
            candidates = self.learner.propose(trace)
            if not candidates:
                print(f"{trace.trace_id}: no candidates proposed")
            for c in candidates:
                ok, reason = self.validator.validate(c)
                if ok:
                    edge = self.graph.add_edge(c.src, c.relation, c.dst, domain=c.domain, provenance=c.provenance, proof=c.proof, rule_id=c.rule_id, confidence=c.confidence, batch_num=batch_num)
                    self.hv.add_or_refresh_edge(edge)
                    print(f"ACCEPTED: {c.src} --{c.relation}--> {c.dst} | domain={c.domain} | reason={reason}")
                    self.learned_rows.append({
                        "run": self.run_label,
                        "batch": batch.name,
                        "src": c.src,
                        "relation": c.relation,
                        "dst": c.dst,
                        "domain": c.domain,
                        "relation_family": relation_family(c.relation),
                        "confidence": c.confidence,
                        "reason": reason,
                        "trace": c.source_trace_id,
                        "rule": c.rule_id,
                        "proof": c.proof,
                    })
                else:
                    print(f"REJECTED: {c.src} --{c.relation}--> {c.dst} | domain={c.domain} | reason={reason}")
                    self.rejected_rows.append({
                        "run": self.run_label,
                        "batch": batch.name,
                        "candidate": f"{c.src} --{c.relation}--> {c.dst}",
                        "domain": c.domain,
                        "confidence": c.confidence,
                        "reason": reason,
                        "trace": c.source_trace_id,
                        "rule": c.rule_id,
                        "proof": c.proof,
                    })

    def run(self, modes: List[str] | None = None) -> Dict[str, Any]:
        if modes is None:
            modes = ["hybrid", "graph_only", "vector_only"]
        previous_task_ids: set[str] = set()
        for batch_num, batch in enumerate(self.batches, start=1):
            print(f"\n=== {batch.name}: add facts ===")
            self.add_batch_facts(batch, batch_num)
            self.learn_from_batch(batch, batch_num)
            self.all_tasks.extend(batch.tasks)

            # Replay run: evaluate once to reinforce useful edges, then replay absorbed memories.
            # No-replay ablation: intentionally skip this warmup reinforcement and decay stale
            # learned shortcuts to expose retention loss in the associative retrieval layer.
            replayed = 0
            if self.replay_enabled:
                warm_reasoner = Reasoner(self.graph, self.hv, batch_num=batch_num, reinforce=True)
                Evaluator.evaluate_tasks(warm_reasoner, self.all_tasks, phase=f"{batch.name} warmup", mode="hybrid")
                self.replay.update_from_graph(self.graph)
                replayed = self.replay.replay(self.hv, batch_num=batch_num)
            elif self.decay_without_replay:
                self.graph.decay_without_replay(batch_num=batch_num, max_staleness=1)
                self.hv.remove_inactive_edges()

            print("\nTask results after learning/replay:")
            for mode in modes:
                reasoner = Reasoner(self.graph, self.hv, batch_num=batch_num, reinforce=self.replay_enabled)
                ev = Evaluator.evaluate_tasks(reasoner, self.all_tasks, phase=f"{batch.name} after replay", mode=mode)
                retention = Evaluator.retention(ev["rows"], previous_task_ids)
                self.summary_rows.append({
                    "run": self.run_label,
                    "phase": f"{batch.name} after replay",
                    "mode": mode,
                    "tasks": ev["tasks"],
                    "accuracy": ev["accuracy"],
                    "faithfulness": ev["faithfulness"],
                    "retention": retention,
                    "avg_ms": ev["avg_ms"],
                    "replayed_edges": replayed if mode == "hybrid" else 0,
                })
                self.task_rows.extend(ev["rows"])
                if mode == "hybrid":
                    for row in ev["rows"]:
                        print({"task": row["task_id"], "domain": row["domain"], "expected": row["expected"], "actual": row["actual"], "mode": row["reasoning_mode"], "correct": row["correct"], "support": row["support"]})
            previous_task_ids.update(t.task_id for t in self.all_tasks)

        self.make_retrieval_audit()
        self.abstraction_rows = self.learner.abstraction_summary()
        return self.write_outputs()

    def make_retrieval_audit(self) -> None:
        sample_tasks = [t for t in self.all_tasks if t.expected][:10]
        for task in sample_tasks:
            query_symbols = [task.subject, task.target_relation, task.expected]
            for key, score, edge in self.hv.query(query_symbols, top_k=3):
                self.retrieval_rows.append({
                    "run": self.run_label,
                    "query_symbols": " + ".join(query_symbols),
                    "retrieved_key": key,
                    "score": round(score, 4),
                    "edge": f"{edge.src} --{edge.relation}--> {edge.dst}",
                    "domain": edge.domain,
                    "relation_family": edge.relation_family,
                    "active": edge.active,
                })

    def learned_relation_state_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for e in self.graph.learned_edges():
            rows.append({
                "run": self.run_label,
                "relation": f"{e.src} --{e.relation}--> {e.dst}",
                "domain": e.domain,
                "relation_family": e.relation_family,
                "confidence": e.confidence,
                "importance": round(e.importance, 3),
                "absorbed": e.absorbed,
                "active": e.active,
                "use_count": e.use_count,
                "replay_count": e.replay_count,
                "provenance": e.provenance,
                "proof": e.proof,
                "rule_id": e.rule_id,
            })
        return rows

    def write_outputs(self) -> Dict[str, Any]:
        outputs = {
            "summary": pd.DataFrame(self.summary_rows),
            "task_results": pd.DataFrame(self.task_rows),
            "learned_candidates": pd.DataFrame(self.learned_rows),
            "rejected_candidates": pd.DataFrame(self.rejected_rows),
            "retrieval_audit": pd.DataFrame(self.retrieval_rows),
            "final_learned_relations": pd.DataFrame(self.learned_relation_state_rows()),
            "abstraction_summary": pd.DataFrame(self.abstraction_rows),
        }
        for name, df in outputs.items():
            df.to_csv(self.output_dir / f"{name}_{self.run_label}.csv", index=False)
        return outputs
