# Requirement Checklist

## Project goal

Design, implement, and evaluate a modular prototype of a neuro-symbolic memory engine and self-learning loop that can be integrated with reasoning frameworks.

Status: **covered at prototype level**.

## Neuro-symbolic memory engine

- **Symbolic backbone**: `SymbolicGraphMemory` with typed nodes, directed edges, proof, provenance, confidence, importance, absorption, replay count, and active status.
- **γ(3,4) graph**: explicitly implemented in `schema.py` and explained in `GAMMA34_GRAPH.md`.
  - γ(3) node kinds: Event, Thing, Concept.
  - γ(4) relation families: NEAR, LEADS_TO, CONTAINS, EXPRESSES.
  - Demo prints coverage counts showing all three node kinds and all four relation families are used.
- **Vector-symbolic memory**: `HypervectorMemory` and `CaseMemory` support similarity-based associative retrieval.

## Trace-based self-learning pipeline

- Resolved RCA traces are ingested with `ingest_resolved_episode`.
- `TraceLearner` extracts candidate memory edges.
- `Validator` checks confidence, proof, task-specific type constraints, and γ-family compatibility.
- Accepted updates go into graph + hypervector memory.
- Case/pattern memory is updated from solved episodes.

## Dual-process reasoning integration

- Fast path: vector/case memory retrieves similar prior episodes.
- Slow path: graph memory verifies proof/provenance for trusted answers.
- New incidents create provisional hypotheses rather than trusted facts.
- Integration adapter exposes `retrieve` and `answer` methods for external reasoning frameworks.

## Knowledge maintenance and continual learning

- Hypotheses can be provisional, promoted, or contradicted.
- Correct predictions are promoted by later resolved traces.
- Wrong predictions become counterexamples.
- Replay and no-replay decay are included as a retention/forgetting stress test: the demo repeatedly queries promoted memories, absorbs them, replays them, and contrasts this with stale learned edges deactivated under no-replay decay.
- Memory is persisted to JSON and reloaded into a fresh engine.

## Evaluation and analysis

The main demo includes:

- varied RCA cases: database bottleneck, schema drift, auth degradation, payment gateway outage, cache-pressure counterexample;
- exact graph lookup before outcome (`not_found`);
- vector-only vs graph-only vs hybrid comparison;
- invalid task-type rejection;
- invalid γ-family rejection;
- γ(3,4) coverage summary;
- persistence/reload and replay/decay summary;
- integration adapter output.

## Honest limitations

- Synthetic prototype, not production-scale deployment.
- Outcome traces are simulated; in production they should come from trusted incident tickets, postmortems, monitoring labels, or reviewed RCA fields.
- The system performs trace-supervised self-learning, not unsupervised discovery of truth from nothing.
