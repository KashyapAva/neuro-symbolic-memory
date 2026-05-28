from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np
from .models import Edge

class HypervectorMemory:
    def __init__(self, dim: int = 4096, seed: int = 7) -> None:
        self.dim = dim
        self.rng = np.random.default_rng(seed)
        self.symbol_vectors: Dict[str, np.ndarray] = {}
        self.memory_items: Dict[str, Tuple[np.ndarray, Edge]] = {}

    def _new_vector(self) -> np.ndarray:
        return self.rng.choice([-1.0, 1.0], size=self.dim)

    def symbol(self, name: str) -> np.ndarray:
        if name not in self.symbol_vectors:
            self.symbol_vectors[name] = self._new_vector()
        return self.symbol_vectors[name]

    def bind(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        return left * right

    def permute(self, vector: np.ndarray, shift: int = 1) -> np.ndarray:
        return np.roll(vector, shift)

    def bundle(self, vectors: List[np.ndarray]) -> np.ndarray:
        summed = np.sum(vectors, axis=0)
        return np.where(summed >= 0, 1.0, -1.0)

    def encode_edge(self, edge: Edge) -> np.ndarray:
        src_v = self.symbol(edge.src)
        rel_v = self.symbol(edge.relation)
        dst_v = self.symbol(edge.dst)
        fam_v = self.symbol(edge.relation_family)
        role_dst = self.bind(rel_v, dst_v)
        ordered = self.bind(self.permute(src_v, 1), self.permute(role_dst, 2))
        return self.bundle([src_v, rel_v, dst_v, fam_v, role_dst, ordered])

    def add_or_refresh_edge(self, edge: Edge) -> None:
        if not edge.active:
            return
        key = f"{edge.src}-{edge.relation}-{edge.dst}"
        self.memory_items[key] = (self.encode_edge(edge), edge)

    def remove_inactive_edges(self) -> None:
        for key, (_, edge) in list(self.memory_items.items()):
            if not edge.active:
                del self.memory_items[key]

    def encode_query(self, symbols: List[str]) -> np.ndarray:
        return self.bundle([self.symbol(s) for s in symbols])

    @staticmethod
    def similarity(left: np.ndarray, right: np.ndarray) -> float:
        denom = np.linalg.norm(left) * np.linalg.norm(right)
        if denom == 0:
            return 0.0
        return float(np.dot(left, right) / denom)

    def query(self, symbols: List[str], top_k: int = 5) -> List[Tuple[str, float, Edge]]:
        qv = self.encode_query(symbols)
        scored = [(key, self.similarity(qv, vec), edge) for key, (vec, edge) in self.memory_items.items() if edge.active]
        return sorted(scored, key=lambda x: x[1], reverse=True)[:top_k]
