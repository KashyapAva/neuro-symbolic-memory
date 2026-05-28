from __future__ import annotations
from typing import Dict, Tuple
from .graph_memory import SymbolicGraphMemory
from .hypervector_memory import HypervectorMemory
from .models import Edge

class ReplayBuffer:
    def __init__(self) -> None:
        self.items: Dict[Tuple[str, str, str], Edge] = {}

    def update_from_graph(self, graph: SymbolicGraphMemory) -> None:
        for edge in graph.absorbed_edges():
            self.items[(edge.src, edge.relation, edge.dst)] = edge

    def replay(self, hv_memory: HypervectorMemory, batch_num: int) -> int:
        replayed = 0
        for edge in self.items.values():
            edge.replay_count += 1
            edge.importance += 0.02
            edge.active = True
            edge.last_refreshed_batch = batch_num
            hv_memory.add_or_refresh_edge(edge)
            replayed += 1
        return replayed
