# Architecture

```text
MemoryEngine
├── SymbolicGraphMemory      # γ(3,4) typed graph, proof, provenance, active/absorbed flags
├── HypervectorMemory        # vector-symbolic retrieval over graph edges
├── CaseMemory               # vector-symbolic retrieval over solved incidents
├── PatternMemory            # feature signature -> root cause abstractions
├── HypothesisMemory         # provisional/promoted/contradicted predictions
├── TraceLearner             # resolved trace -> candidate relation
├── Validator                # confidence + proof + γ-family + task-type checks
├── ReplayBuffer             # reinforce important memories
└── MemoryStore              # save/load graph + case + pattern + hypothesis state
```

## γ(3,4) schema

```text
Node kinds:
  Event   = incidents, traces, prediction events
  Thing   = services, databases, pipelines, tables, columns, gateways
  Concept = signals, metrics, symptoms, causes, remediations, patterns

Relation families:
  NEAR      = similarity, not truth
  LEADS_TO  = causal/explanatory/remediation flow
  CONTAINS  = system structure, dependency, part-whole
  EXPRESSES = evidence, observed properties, metrics, symptoms
```

The validator uses this schema to prevent unsafe memory updates. For example:

- `Incident --HAS_ROOT_CAUSE--> Table` is rejected.
- `Incident --SIMILAR_TO--> Table` is rejected because NEAR requires compatible γ kinds.

## Flow

1. A resolved incident trace enters the engine.
2. The trace learner proposes a root-cause memory relation.
3. The validator accepts only confidence-valid, proof-backed, γ-compatible, type-correct relations.
4. Accepted relations are stored in graph memory and indexed by hypervectors.
5. The solved case is also stored as case memory.
6. Pattern memory updates feature→cause abstractions.
7. Future unresolved incidents retrieve similar cases and learned patterns.
8. The engine stores provisional hypotheses, not trusted facts.
9. Future resolved traces promote or contradict hypotheses automatically.
10. Repeated access raises importance; absorbed memories enter replay, are refreshed across time, and are contrasted with no-replay decay before persistence/reload.
