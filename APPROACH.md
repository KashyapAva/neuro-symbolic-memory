# Approach

## Problem interpretation

I interpreted the assignment as a memory-system design problem rather than a model-training problem. The core challenge is to let a system store structured knowledge, retrieve relevant memory quickly, learn new relations from successful reasoning episodes, and retain earlier knowledge as new batches arrive.

The implementation separates the system into two complementary memory layers:

1. **Symbolic graph memory**: typed directed graph with provenance, proof paths, confidence, importance, absorption, and replay metadata.
2. **Vector-symbolic memory**: hypervectors for approximate associative retrieval using similarity, binding, and bundling/superposition.

The final answer is not trusted just because the vector layer retrieves something. The vector layer proposes candidates; the graph layer verifies them.

## Design choices

### 1. Start with typed graph memory

I used a typed directed graph because the assignment emphasizes faithfulness, provenance, proofs, absorption metadata, and type consistency. A graph makes those constraints explicit and inspectable.

### 2. Add hypervector memory as fast retrieval

Each symbolic edge is encoded into a hypervector representation. This allows approximate retrieval of relevant memories before symbolic verification.

### 3. Learn from successful traces

A successful trace is a two-hop reasoning path that produced the correct answer. The trace learner mines this path and proposes a reusable shortcut relation.

Example:

```text
India --HAS_CAPITAL--> New Delhi
New Delhi --LOCATED_IN--> Asia
```

proposes:

```text
India --CAPITAL_CONTINENT--> Asia
```

### 4. Validate before absorption

A learned relation is only added if it passes checks for:

- relation schema;
- source/target type compatibility;
- confidence threshold;
- duplicate relation;
- proof path presence;
- provenance.

Invalid candidates are logged, not silently ignored.

### 5. Evaluate continual learning

Knowledge is added in sequential batches: external KGQA, math, RCA, forecast, invalid stress test. After each batch, all earlier tasks are re-evaluated. This measures whether old knowledge remains accessible after new learning.

### 6. Add replay and ablation

Replay refreshes important absorbed learned relations. A no-replay/decay ablation tests whether old knowledge degrades without maintenance.

### 7. Add integration hook

The `MemoryEngine` and `ReasoningFrameworkAdapter` expose a tool-like API so external reasoning systems can add facts, ingest traces, query memory, and retrieve verified context.

## Scope

The repository is a modular prototype. It demonstrates the required mechanisms and evaluation structure but is not positioned as a finished production system.
