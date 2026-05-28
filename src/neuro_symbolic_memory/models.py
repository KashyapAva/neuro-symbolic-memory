from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
import time

@dataclass
class Node:
    label: str
    node_type: str
    gamma_class: str
    provenance: str = "seed"
    importance: float = 1.0
    absorbed: bool = False

@dataclass
class Edge:
    src: str
    relation: str
    dst: str
    domain: str
    relation_family: str
    confidence: float = 1.0
    provenance: str = "seed"
    proof: str = ""
    rule_id: str = "seed"
    importance: float = 1.0
    absorbed: bool = False
    use_count: int = 0
    replay_count: int = 0
    active: bool = True
    created_at: float = field(default_factory=time.time)
    last_refreshed_batch: int = 0

@dataclass
class Trace:
    trace_id: str
    domain: str
    question: str
    reasoning_path: List[Tuple[str, str, str]]
    answer: str
    success: bool = True

@dataclass
class CandidateRelation:
    src: str
    relation: str
    dst: str
    domain: str
    confidence: float
    provenance: str
    proof: str
    source_trace_id: str
    rule_id: str

@dataclass
class QueryTask:
    task_id: str
    domain: str
    subject: str
    target_relation: str
    expected: str
    batch: str

@dataclass
class Batch:
    name: str
    domain: str
    nodes: List[tuple]
    edges: List[tuple]
    traces: List[Trace]
    tasks: List[QueryTask]
