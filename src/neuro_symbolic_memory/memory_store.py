from __future__ import annotations

"""Persistence and reporting helpers for the explicit memory lifecycle.

The core prototype already keeps memory in three runtime structures:
- SymbolicGraphMemory: trusted semantic memory.
- HypervectorMemory: associative retrieval index over active memories.
- ReplayBuffer: consolidation / maintenance buffer.

This module makes that lifecycle explicit by saving and loading the memory state.
The saved snapshot is intentionally JSON so reviewers can inspect what was remembered.
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List
import json

from .graph_memory import SymbolicGraphMemory
from .hypervector_memory import HypervectorMemory
from .models import Edge, Node
from .schema import gamma_class, relation_family


class MemoryStore:
    """Serialize and restore the engine's external memory state.

    This is not model-weight persistence. It is explicit external memory:
    nodes, seed facts, learned relations, proof/provenance, importance,
    absorption, replay counts, and active/inactive state. On load, the
    hypervector index is rebuilt from the active graph edges.
    """

    @staticmethod
    def snapshot(graph: SymbolicGraphMemory) -> Dict[str, Any]:
        return {
            "nodes": [asdict(node) for node in graph.nodes.values()],
            "edges": [asdict(edge) for edge in graph.edges],
            "stats": {
                "node_count": len(graph.nodes),
                "edge_count": len(graph.edges),
                "learned_edge_count": len(graph.learned_edges()),
                "active_learned_edge_count": len([e for e in graph.learned_edges() if e.active]),
                "absorbed_edge_count": len(graph.absorbed_edges()),
            },
        }

    @staticmethod
    def save(graph: SymbolicGraphMemory, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(MemoryStore.snapshot(graph), indent=2), encoding="utf-8")
        return path

    @staticmethod
    def load(path: str | Path, dim: int = 4096, seed: int = 7) -> tuple[SymbolicGraphMemory, HypervectorMemory]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        graph = SymbolicGraphMemory()
        for item in data.get("nodes", []):
            node = Node(
                label=item["label"],
                node_type=item["node_type"],
                gamma_class=item.get("gamma_class") or gamma_class(item["node_type"]),
                provenance=item.get("provenance", "loaded"),
                importance=float(item.get("importance", 1.0)),
                absorbed=bool(item.get("absorbed", False)),
            )
            graph.nodes[node.label] = node
        hv = HypervectorMemory(dim=dim, seed=seed)
        for item in data.get("edges", []):
            edge = Edge(
                src=item["src"],
                relation=item["relation"],
                dst=item["dst"],
                domain=item.get("domain", "loaded"),
                relation_family=item.get("relation_family") or relation_family(item["relation"]),
                confidence=float(item.get("confidence", 1.0)),
                provenance=item.get("provenance", "loaded"),
                proof=item.get("proof", ""),
                rule_id=item.get("rule_id", "loaded"),
                importance=float(item.get("importance", 1.0)),
                absorbed=bool(item.get("absorbed", False)),
                use_count=int(item.get("use_count", 0)),
                replay_count=int(item.get("replay_count", 0)),
                active=bool(item.get("active", True)),
                created_at=float(item.get("created_at", 0.0)),
                last_refreshed_batch=int(item.get("last_refreshed_batch", 0)),
            )
            graph.add_edge_object(edge)
            if edge.active:
                hv.add_or_refresh_edge(edge)
        return graph, hv


    @staticmethod
    def save_engine_state(graph: SymbolicGraphMemory, path: str | Path, case_episodes: List[dict] | None = None, hypotheses: List[dict] | None = None, patterns: List[dict] | None = None) -> Path:
        """Save semantic graph memory plus optional episodic/case memories.

        The graph remains the durable source of truth for verified relations.
        Case episodes are saved alongside it so similarity-based recall can
        survive a fresh engine instance too.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = MemoryStore.snapshot(graph)
        data["case_episodes"] = case_episodes or []
        data["hypotheses"] = hypotheses or []
        data["patterns"] = patterns or []
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    @staticmethod
    def load_engine_state(path: str | Path, dim: int = 4096, seed: int = 7) -> tuple[SymbolicGraphMemory, HypervectorMemory, List[dict], List[dict], List[dict]]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        graph, hv = MemoryStore.load(path, dim=dim, seed=seed)
        return graph, hv, data.get("case_episodes", []), data.get("hypotheses", []), data.get("patterns", [])

    @staticmethod
    def report(graph: SymbolicGraphMemory) -> Dict[str, Any]:
        learned = graph.learned_edges()
        return {
            "nodes": len(graph.nodes),
            "edges": len(graph.edges),
            "learned_edges": len(learned),
            "active_learned_edges": len([e for e in learned if e.active]),
            "absorbed_edges": len(graph.absorbed_edges()),
            "top_learned_memories": [
                {
                    "memory": f"{e.src} --{e.relation}--> {e.dst}",
                    "active": e.active,
                    "importance": round(e.importance, 3),
                    "use_count": e.use_count,
                    "replay_count": e.replay_count,
                    "provenance": e.provenance,
                    "proof": e.proof,
                }
                for e in sorted(learned, key=lambda x: x.importance, reverse=True)[:10]
            ],
        }
