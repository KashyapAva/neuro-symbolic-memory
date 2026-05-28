# Architecture

## Main components

| Module | Responsibility |
|---|---|
| `models.py` | Dataclasses for nodes, edges, traces, candidate relations, query tasks, and batches. |
| `schema.py` | γ(3,4)-style node-class and relation-family mapping plus allowed relation types. |
| `graph_memory.py` | Symbolic typed graph memory with edge verification, traversal, reinforcement, and decay. |
| `hypervector_memory.py` | Vector-symbolic memory with symbol vectors, binding, bundling, similarity, and retrieval. |
| `trace_learner.py` | Mines successful traces into candidate learned relations. |
| `validator.py` | Validates candidate relations before memory update. |
| `reasoner.py` | Implements hybrid, graph-only, and vector-only reasoning modes. |
| `replay.py` | Maintains replay buffer for absorbed important learned edges. |
| `evaluation.py` | Computes accuracy, faithfulness, retention, and latency. |
| `benchmark_loader.py` | Loads the external geo KGQA benchmark file. |
| `scenarios.py` | Builds sequential evaluation batches. |
| `pipeline.py` | Runs the full experiment, baselines, replay, ablation, and CSV outputs. |
| `integration.py` | Provides the external `MemoryEngine` and `ReasoningFrameworkAdapter`. |

## Data flow

```text
Seed facts + successful traces
        |
        v
Typed symbolic graph  <------>  Hypervector memory
        |                             |
        |                             v
        |                    Fast associative retrieval
        |                             |
        v                             |
Trace learner proposes new relations  |
        |                             |
        v                             |
Validator checks type/proof/provenance|
        |                             |
        v                             |
Accepted relations update graph + hypervectors
        |
        v
Reasoner answers with vector retrieval + graph verification
        |
        v
Importance / absorption / replay
        |
        v
Evaluation: accuracy, faithfulness, retention, latency
```

## γ(3,4)-style graph schema

The prototype uses:

- **3 node classes**: `Thing`, `Event`, `Concept`
- **4 relation families**: `LEADS_TO`, `CONTAINS`, `EXPRESSES_PROPERTY`, `NEARTO`

Domain-specific node types and relations map into this schema. For example:

| Domain relation | Relation family |
|---|---|
| `HAS_CAPITAL` | `EXPRESSES_PROPERTY` |
| `LOCATED_IN` | `CONTAINS` |
| `CAPITAL_CONTINENT` | `NEARTO` |
| `HAS_SOLUTION` | `LEADS_TO` |
| `HAS_ROOT_CAUSE` | `LEADS_TO` |
| `FORECAST_RISK` | `LEADS_TO` |

## Reasoning modes

| Mode | Description |
|---|---|
| `hybrid` | Hypervector retrieval proposes a candidate edge; symbolic graph verification confirms it. |
| `graph_only` | Uses symbolic graph traversal/lookup only. |
| `vector_only` | Uses nearest vector memory item only, without proof verification. |

## Integration design

`MemoryEngine` exposes a minimal API:

- `add_node(...)`
- `add_fact(...)`
- `ingest_trace(...)`
- `query(...)`
- `retrieve_context(...)`
- `consolidate()`

`ReasoningFrameworkAdapter.as_tool()` returns a callable that can be registered as a tool/retriever in an external reasoning framework.
