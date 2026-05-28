# Demo Report

## Summary

This project implements a modular neuro-symbolic memory engine and self-learning loop. It demonstrates the requested mechanisms across external KGQA, toy mathematical reasoning, RCA traces, forecast-style traces, invalid candidate validation, baseline comparisons, no-replay ablation, and a framework-style integration hook.

## What the prototype demonstrates

1. **Hybrid memory substrate**
   - Symbolic graph memory stores typed directed facts with provenance, proof paths, confidence, importance, absorption, and replay metadata.
   - Hypervector memory stores vector-symbolic encodings of the same facts for fast associative retrieval.

2. **Trace-based learning**
   - Successful traces are mined into learned shortcut relations.
   - Examples include `CAPITAL_CONTINENT`, `HAS_SOLUTION`, `HAS_ROOT_CAUSE`, and `FORECAST_RISK`.

3. **Validation before absorption**
   - Candidate learned relations must pass type checks, duplicate checks, confidence checks, and proof/provenance checks.
   - The invalid stress test demonstrates rejection of a bad relation.

4. **Dual-process reasoning**
   - The hybrid mode retrieves candidate edges using hypervectors and then verifies the candidate symbolically.
   - Returned answers include support paths.

5. **Continual learning and replay**
   - Knowledge is added sequentially in batches.
   - Earlier tasks are re-evaluated after later batches.
   - Replay refreshes absorbed important learned relations.

6. **Evaluation and baselines**
   - The demo compares hybrid, graph-only, vector-only, and no-replay variants.
   - It reports accuracy, faithfulness, retention, latency, replay counts, accepted/rejected candidates, and retrieval audits.

7. **Integration hook**
   - `MemoryEngine` and `ReasoningFrameworkAdapter` expose the prototype as a memory/retrieval/verification tool for external reasoning systems.

## How to interpret the baselines

- `graph_only` is expected to be strong on clean graph tasks because the required facts are explicitly available.
- `vector_only` can retrieve plausible memory items but does not verify them, so it is not considered faithful.
- `hybrid` combines vector retrieval with graph verification.
- `hybrid_no_replay_decay` demonstrates what happens when learned relations are not refreshed under forgetting pressure.

## What is intentionally not overclaimed

This is not a production system and not a full formal theorem prover. It is a modular prototype that makes the requested components concrete and auditable.

## Recommended next extensions

- Use a larger public KGQA benchmark.
- Add a real LLM-only baseline.
- Replace rule-based trace mining with LLM-assisted or learned trace parsing.
- Add direct LangChain/LlamaIndex/DSPy wrappers around the adapter.
- Add richer conflict-resolution and adversarial continual-learning tests.
