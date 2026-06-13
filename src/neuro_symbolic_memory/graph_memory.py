from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from .models import Node, Edge
from .schema import gamma_class, relation_family, summarize_gamma34

class SymbolicGraphMemory:
    def __init__(self) -> None:
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.edge_index: Dict[Tuple[str, str, str], Edge] = {}

    def add_node(self, label: str, node_type: str, provenance: str = "seed") -> Node:
        if label not in self.nodes:
            self.nodes[label] = Node(label=label, node_type=node_type, gamma_class=gamma_class(node_type), provenance=provenance)
        return self.nodes[label]

    def add_edge(self, src: str, relation: str, dst: str, domain: str, provenance: str = "seed", proof: str = "", rule_id: str = "seed", confidence: float = 1.0, batch_num: int = 0) -> Edge:
        key = (src, relation, dst)
        if key in self.edge_index:
            edge = self.edge_index[key]
            edge.active = True
            edge.last_refreshed_batch = batch_num
            return edge
        if src not in self.nodes:
            raise ValueError(f"Missing source node: {src}")
        if dst not in self.nodes:
            raise ValueError(f"Missing destination node: {dst}")
        edge = Edge(src=src, relation=relation, dst=dst, domain=domain, relation_family=relation_family(relation), confidence=confidence, provenance=provenance, proof=proof, rule_id=rule_id, last_refreshed_batch=batch_num)
        self.edges.append(edge)
        self.edge_index[key] = edge
        return edge

    def add_edge_object(self, edge: Edge) -> Edge:
        key = (edge.src, edge.relation, edge.dst)
        if key in self.edge_index:
            return self.edge_index[key]
        self.edges.append(edge)
        self.edge_index[key] = edge
        return edge

    def edge_exists(self, src: str, relation: str, dst: str) -> bool:
        return (src, relation, dst) in self.edge_index

    def get_edge(self, src: str, relation: str, dst: str) -> Optional[Edge]:
        return self.edge_index.get((src, relation, dst))

    def outgoing(self, src: str, relation: Optional[str] = None, active_only: bool = False) -> List[Edge]:
        return [e for e in self.edges if e.src == src and (relation is None or e.relation == relation) and (not active_only or e.active)]

    def find_two_hop_path(self, src: str, rel1: str, rel2: str, active_only: bool = False) -> Optional[List[Edge]]:
        for first in self.outgoing(src, rel1, active_only=active_only):
            for second in self.outgoing(first.dst, rel2, active_only=active_only):
                return [first, second]
        return None

    def verify_edge(self, src: str, relation: str, dst: str, active_only: bool = False) -> Optional[Edge]:
        edge = self.get_edge(src, relation, dst)
        if edge is not None and (not active_only or edge.active):
            return edge
        return None

    def reinforce_edges(self, edges: List[Edge], increment: float = 0.10, batch_num: int = 0) -> None:
        for edge in edges:
            edge.use_count += 1
            edge.importance += increment
            edge.last_refreshed_batch = batch_num
            if edge.importance >= 1.20:
                edge.absorbed = True
                edge.active = True

    def decay_without_replay(self, batch_num: int, max_staleness: int = 2) -> None:
        """Simulates forgetting in the associative/retrieval layer when replay is disabled.
        Seed facts remain available, but old learned shortcuts can become inactive.
        """
        for edge in self.edges:
            if self.is_memory_edge(edge) and (batch_num - edge.last_refreshed_batch) > max_staleness:
                edge.active = False

    @staticmethod
    def is_memory_edge(edge: Edge) -> bool:
        """Edges created by learning or confirmed memory transfer, not raw seed facts."""
        return (
            edge.provenance.startswith("learned_from_trace")
            or edge.provenance.startswith("confirmed_from_similar_case")
            or edge.provenance.startswith("auto_promoted_from_outcome_trace")
        )


    def gamma34_summary(self) -> dict:
        """Return evidence that the graph is using all γ(3,4) roles."""
        return summarize_gamma34(self.nodes.values(), self.edges)

    def learned_edges(self) -> List[Edge]:
        return [e for e in self.edges if self.is_memory_edge(e)]

    def absorbed_edges(self) -> List[Edge]:
        return [e for e in self.learned_edges() if e.absorbed and e.active]
