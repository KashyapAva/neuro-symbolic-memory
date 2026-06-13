# Neuro-Symbolic Memory Engine — Robust γ(3,4) Prototype

This repository contains a modular prototype of a neuro-symbolic memory engine and trace-supervised self-learning loop.

Run the main demo:

```bash
python3 demo.py
python3 -m unittest discover -s tests -v
```

## What the demo shows

The demo uses one coherent domain: **data observability / RCA**. The examples are varied enough to exercise the graph constraints, not just one `incident -> signal -> cause` shape.

It demonstrates:

1. **γ(3,4)-typed graph memory** with Event, Thing, Concept nodes and NEAR, LEADS_TO, CONTAINS, EXPRESSES edge families.
2. **Resolved trace learning**: solved incidents create trusted graph memory, case memory, vector memory, and pattern memory.
3. **Fast associative retrieval + slow symbolic verification**: similar cases are retrieved by vector/case memory, but trusted answers require graph proof/provenance.
4. **Hypothesis memory**: new unresolved incidents produce provisional hypotheses, not trusted facts.
5. **Outcome-based self-learning**: later resolved traces promote correct hypotheses or store counterexamples for wrong predictions.
6. **Type and γ-family validation**: invalid memory candidates are rejected.
7. **Replay/decay and persistence**: repeatedly reused memories are absorbed, replayed, saved/reloaded, and contrasted with a no-replay forgetting stress test.
8. **Integration adapter**: an external reasoning framework can call the engine as a retrieval/verification tool.

## Why it is not just Graph RAG

A basic Graph RAG system retrieves context from a graph. This prototype also retrieves, but adds a memory lifecycle:

```text
resolved trace -> candidate memory -> validation -> graph/case/vector/pattern update
new incident -> provisional hypothesis -> future outcome -> promote / contradict / decay
```

The graph is not just context. It is mutable, audited memory with typed constraints, proof/provenance, importance, replay, and active/inactive status.

## Key files

- `demo.py` — main runnable demo.
- `demo_robust_system.py` — end-to-end robust demo logic.
- `GAMMA34_GRAPH.md` — explicit γ(3,4) schema explanation.
- `src/neuro_symbolic_memory/schema.py` — γ(3,4) node kinds, edge families, and constraints.
- `src/neuro_symbolic_memory/graph_memory.py` — trusted symbolic graph memory.
- `src/neuro_symbolic_memory/hypervector_memory.py` — vector-symbolic associative retrieval.
- `src/neuro_symbolic_memory/case_memory.py` — solved-case memory.
- `src/neuro_symbolic_memory/pattern_memory.py` — reusable feature→cause patterns.
- `src/neuro_symbolic_memory/hypothesis_memory.py` — provisional/promoted/contradicted hypotheses.
- `src/neuro_symbolic_memory/integration.py` — integrated memory engine and adapter.
- `tests/test_robust_system.py` — smoke tests for learning, promotion, validation, and γ(3,4) coverage.

## Limitations

This is a controlled prototype, not a production RCA system. It uses synthetic traces to demonstrate the required mechanisms. In production, resolved traces would come from trusted sources such as postmortems, incident tickets, monitoring labels, or analyst-reviewed RCA fields.
