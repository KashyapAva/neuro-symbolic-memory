# Assumptions

This prototype is designed as a modular proof-of-concept for a neuro-symbolic memory engine and self-learning loop. The goal is to demonstrate the requested mechanisms clearly and reproducibly, not to claim a production-grade reasoning system.

## 1. Scope Assumptions

The prototype focuses on structured reasoning traces rather than open-ended natural language understanding. Inputs are represented as facts, traces, and tasks so the memory loop can be evaluated directly.

The included domains are:

* external geo KGQA-style compositional reasoning,
* toy mathematical reasoning,
* RCA/root-cause traces,
* forecast-style risk traces,
* invalid candidate stress testing.

Free-form natural language parsing is treated as an external wrapper that can be added later.

## 2. Graph Assumptions

Symbolic memory is implemented as a typed, directed graph. Nodes and edges carry metadata such as type, domain, provenance, proof path, confidence, importance, absorption status, use count, and replay count.

The γ(3,4)-typed graph requirement is implemented as a pragmatic schema inspired by the requested structure:

* three broad node classes: Thing, Event, Concept,
* four broad relation families: CONTAINS, LEADS_TO, EXPRESSES_PROPERTY, NEARTO.

Task-specific relations such as `HAS_CAPITAL`, `LOCATED_IN`, `HAS_SOLUTION`, `HAS_ROOT_CAUSE`, and `FORECAST_RISK` are mapped into these broader relation families.

This is a prototype-level schema mapping, not a full formal implementation of a specific γ(3,4) theory.

## 3. Hypervector Assumptions

The vector-symbolic layer uses randomly initialized high-dimensional hypervectors. These support neural-style associative operations:

* similarity search,
* binding,
* bundling/superposition,
* retrieval audit.

The hypervector layer is used for fast approximate retrieval. It does not determine truth on its own. Retrieved candidates are verified by the symbolic graph before being treated as faithful answers.

## 4. Self-Learning Assumptions

The self-learning loop operates on successful traces. A successful trace is a verified reasoning path, such as:

`Country --HAS_CAPITAL--> Capital; Capital --LOCATED_IN--> Continent`

The learner converts such traces into candidate learned relations, for example:

`Country --CAPITAL_CONTINENT--> Continent`

Candidate relations are only added to memory after validation.

## 5. Validation Assumptions

Validation checks include:

* relation type compatibility,
* source and target node type compatibility,
* duplicate relation checks,
* confidence threshold,
* provenance availability,
* lightweight proof path availability.

Invalid candidates are rejected and logged.

## 6. Continual-Learning Assumptions

Continual learning is simulated through sequential batches. After each new batch is added, earlier tasks are re-evaluated to measure retention.

Replay and absorption are implemented as lightweight memory-maintenance mechanisms:

* important learned relations receive higher importance,
* frequently used relations become absorbed,
* absorbed relations are replayed/refreshed in memory,
* no-replay ablation demonstrates forgetting behavior under controlled decay.

This is not intended to be a full neural catastrophic-forgetting benchmark.

## 7. Baseline Assumptions

The prototype compares:

* hybrid retrieval + symbolic verification,
* graph-only reasoning,
* vector-only retrieval,
* hybrid without replay.

The goal of the baseline comparison is not to claim that hybrid improves raw accuracy over graph-only in simple tasks. Instead, it shows that the hybrid approach preserves symbolic faithfulness while adding associative retrieval, and that vector-only retrieval lacks verifiable proof support.

## 8. Integration Assumptions

The `MemoryEngine` and `ReasoningFrameworkAdapter` provide an integration-style interface. They are designed so that an external reasoning framework, agent, or LLM workflow can call the memory engine as a retrieval and verification tool.

This prototype demonstrates the integration hook but does not depend on a specific external framework such as LangChain, LlamaIndex, or DSPy.

## 9. Evaluation Assumptions

Evaluation focuses on:

* accuracy,
* faithfulness,
* retention,
* replay counts,
* rejected candidate analysis,
* learned relation audit,
* retrieval audit,
* average query latency.

The benchmark is intentionally lightweight and reproducible. Larger public benchmarks and production-scale stress tests are future extensions.

## 10. Limitations

The prototype does not claim to solve all neuro-symbolic reasoning. Remaining extensions include:

* formal γ(3,4) alignment if a stricter definition is required,
* larger public KGQA/math benchmarks,
* real forecasting or RCA logs,
* natural language trace extraction,
* deeper proof checking,
* production database integration,
* direct integration with a chosen reasoning framework.
