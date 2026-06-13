from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple
import re
import numpy as np

@dataclass
class CaseEpisode:
    """A solved reasoning episode stored for analogical/associative recall.

    This is episodic memory: it is not just a graph edge. It stores the case
    features that made an incident recognizable, plus the verified root cause
    and proof that came from the symbolic memory layer.
    """
    case_id: str
    domain: str
    features: List[str]
    root_cause: str
    remediation: str = ""
    proof: str = ""
    provenance: str = "resolved_outcome_trace"
    confidence: float = 1.0
    created_batch: int = 0
    use_count: int = 0

class CaseMemory:
    """Small vector-symbolic case memory for similar-episode retrieval.

    The earlier prototype could retrieve exact learned graph edges. This layer
    retrieves *related solved episodes* by feature overlap / hypervector
    similarity, allowing a new incident to be compared with past incidents.
    """
    def __init__(self, dim: int = 4096, seed: int = 13) -> None:
        self.dim = dim
        self.rng = np.random.default_rng(seed)
        self.token_vectors: Dict[str, np.ndarray] = {}
        self.episodes: Dict[str, CaseEpisode] = {}
        self.episode_vectors: Dict[str, np.ndarray] = {}

    def _new_vector(self) -> np.ndarray:
        return self.rng.choice([-1.0, 1.0], size=self.dim)

    def token_vector(self, token: str) -> np.ndarray:
        token = token.lower().strip()
        if token not in self.token_vectors:
            self.token_vectors[token] = self._new_vector()
        return self.token_vectors[token]

    @staticmethod
    def tokenize(features: List[str]) -> List[str]:
        tokens: List[str] = []
        for feature in features:
            cleaned = re.sub(r"[^A-Za-z0-9]+", " ", feature.lower())
            tokens.extend(t for t in cleaned.split() if t)
        return sorted(set(tokens))

    def encode_features(self, features: List[str]) -> np.ndarray:
        tokens = self.tokenize(features)
        if not tokens:
            return np.zeros(self.dim)
        summed = np.sum([self.token_vector(t) for t in tokens], axis=0)
        return np.where(summed >= 0, 1.0, -1.0)

    @staticmethod
    def cosine(left: np.ndarray, right: np.ndarray) -> float:
        denom = np.linalg.norm(left) * np.linalg.norm(right)
        if denom == 0:
            return 0.0
        return float(np.dot(left, right) / denom)

    @staticmethod
    def jaccard(left: List[str], right: List[str]) -> float:
        a, b = set(left), set(right)
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def add_episode(self, episode: CaseEpisode) -> None:
        self.episodes[episode.case_id] = episode
        self.episode_vectors[episode.case_id] = self.encode_features(episode.features)

    def query(self, features: List[str], top_k: int = 3) -> List[Dict[str, object]]:
        query_vector = self.encode_features(features)
        query_tokens = self.tokenize(features)
        results: List[Dict[str, object]] = []
        for case_id, episode in self.episodes.items():
            case_vector = self.episode_vectors[case_id]
            case_tokens = self.tokenize(episode.features)
            vector_score = self.cosine(query_vector, case_vector)
            overlap_score = self.jaccard(query_tokens, case_tokens)
            # Blend vector-symbolic similarity with transparent token overlap.
            score = 0.55 * vector_score + 0.45 * overlap_score
            overlap = sorted(set(query_tokens) & set(case_tokens))
            results.append({
                "case": episode,
                "score": round(score, 4),
                "vector_score": round(vector_score, 4),
                "overlap_score": round(overlap_score, 4),
                "overlap_tokens": overlap,
            })
        return sorted(results, key=lambda row: row["score"], reverse=True)[:top_k]

    def reinforce(self, case_id: str) -> None:
        if case_id in self.episodes:
            self.episodes[case_id].use_count += 1

    def to_records(self) -> List[dict]:
        return [asdict(ep) for ep in self.episodes.values()]

    @classmethod
    def from_records(cls, records: List[dict], dim: int = 4096, seed: int = 13) -> "CaseMemory":
        memory = cls(dim=dim, seed=seed)
        for record in records:
            memory.add_episode(CaseEpisode(**record))
        return memory
