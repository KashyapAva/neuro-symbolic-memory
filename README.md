# Neuro-Symbolic Memory Engine and Self-Learning Loop

This repository implements a modular prototype of a neuro-symbolic memory engine that combines:

1. **Symbolic graph memory** for typed, verifiable knowledge with provenance, proof paths, confidence, importance, absorption, and replay metadata.
2. **Vector-symbolic / hypervector memory** for fast associative retrieval using similarity, binding, bundling/superposition, and permutation-style operations.
3. **Trace-based self-learning** that mines successful reasoning, math, RCA, and forecast traces into new validated relations.
4. **Dual-process reasoning** where hypervector retrieval proposes candidates and symbolic graph verification decides whether an answer is faithful.
5. **Continual-learning maintenance** using importance scoring, absorption-aware triggers, replay, and no-replay ablation.
6. **Integration hook** through `MemoryEngine` and `ReasoningFrameworkAdapter`, so an external reasoning framework can call the memory layer as a tool/retriever.

The project is intentionally designed as a **prototype**: the goal is to demonstrate the required mechanisms clearly and reproducibly, not to claim a production-grade research framework.

---

## Quick start

```bash
python3 -m pip install -r requirements.txt
python3 demo.py
```

Optional structured interactive demo:

```bash
python3 demo_interactive.py
```

Optional smoke test:

```bash
python3 -m unittest discover -s tests
```

---

## What the main demo runs

`demo.py` runs five sequential batches:

1. **External geo KGQA benchmark** from `data/external_geo_kgqa.csv`
   - Example path: `India --HAS_CAPITAL--> New Delhi --LOCATED_IN--> Asia`
   - Learned relation: `India --CAPITAL_CONTINENT--> Asia`
2. **Toy mathematical reasoning traces**
   - Example path: `problem --HAS_EQUATION--> equation --EQUATION_SOLVES_TO--> solution`
   - Learned relation: `problem --HAS_SOLUTION--> solution`
3. **RCA / root-cause traces**
   - Example path: `incident --HAS_SIGNAL--> signal --SIGNAL_POINTS_TO--> cause`
   - Learned relation: `incident --HAS_ROOT_CAUSE--> cause`
4. **Forecast-style traces**
   - Example path: `case --HAS_TREND--> trend --TREND_IMPLIES_RISK--> risk`
   - Learned relation: `case --FORECAST_RISK--> risk`
5. **Invalid stress test**
   - Demonstrates rejection of an invalid learned relation through type validation.

After each batch, all previously seen tasks are re-evaluated to measure retention.

---

## Baselines and ablations

The demo evaluates:

| Mode | Purpose |
|---|---|
| `hybrid` | Hypervector retrieval followed by symbolic verification. |
| `graph_only` | Symbolic graph traversal/lookup without vector retrieval. |
| `vector_only` | Approximate vector retrieval without symbolic verification. |
| `hybrid_no_replay_decay` | Hybrid mode with replay disabled and stale learned edges decayed to demonstrate forgetting pressure. |

Important interpretation:

- Hybrid is not claimed to beat graph-only accuracy on controlled graph tasks.
- Hybrid preserves graph-level faithfulness while adding fast associative retrieval.
- Vector-only may retrieve plausible answers but does not provide verified support, so its faithfulness is intentionally reported as low.
- No-replay ablation demonstrates the role of replay/consolidation in retaining earlier learned relations.

---

## Repository structure

```text
.
├── README.md
├── APPROACH.md
├── ARCHITECTURE.md
├── DEMO_REPORT.md
├── REQUIREMENT_CHECKLIST.md
├── demo.py
├── demo_interactive.py
├── requirements.txt
├── pyproject.toml
├── data/
│   ├── external_geo_kgqa.csv
│   └── README_BENCHMARK.md
├── outputs/
│   └── generated CSVs after running demo.py
├── src/neuro_symbolic_memory/
│   ├── models.py
│   ├── schema.py
│   ├── graph_memory.py
│   ├── hypervector_memory.py
│   ├── trace_learner.py
│   ├── validator.py
│   ├── reasoner.py
│   ├── replay.py
│   ├── evaluation.py
│   ├── benchmark_loader.py
│   ├── scenarios.py
│   ├── integration.py
│   └── pipeline.py
└── tests/
    └── test_smoke.py
```

---

## Output files

Running `python3 demo.py` writes CSVs under `outputs/`:

- `summary_hybrid_with_replay.csv`
- `summary_hybrid_no_replay_decay.csv`
- `combined_baseline_summary.csv`
- `task_results_hybrid_with_replay.csv`
- `final_learned_relations_hybrid_with_replay.csv`
- `learned_candidates_hybrid_with_replay.csv`
- `rejected_candidates_hybrid_with_replay.csv`
- `retrieval_audit_hybrid_with_replay.csv`
- `abstraction_summary_hybrid_with_replay.csv`

These files make the prototype auditable: accepted/rejected relations, proof paths, retrieval scores, task outcomes, retention, faithfulness, and latency are all inspectable.

---

## Integration hook

The integration-facing API is in `src/neuro_symbolic_memory/integration.py`.

External systems can use:

```python
from neuro_symbolic_memory.integration import MemoryEngine, ReasoningFrameworkAdapter

engine = MemoryEngine()
engine.add_node(...)
engine.add_fact(...)
engine.ingest_trace(...)
engine.consolidate()

adapter = ReasoningFrameworkAdapter(engine)
memory_tool = adapter.as_tool()
result = memory_tool({
    "subject": "India",
    "target_relation": "CAPITAL_CONTINENT",
    "expected": "Asia",
    "mode": "hybrid",
})
```

This adapter can be wrapped by an LLM agent, planner, rule engine, or external reasoning framework as a retrieval/verification tool.

---

## Honest limitations

This prototype implements all requested mechanisms at demonstration scale. Remaining production/research extensions include:

- using a larger public KGQA benchmark such as MetaQA/WebQuestionsSP-style data;
- replacing rule-based trace mining with a learned or LLM-assisted trace parser;
- integrating with a specific framework such as LangChain, LlamaIndex, or DSPy;
- adding a real LLM-only baseline if API access is available;
- expanding the formal γ(3,4) alignment if a precise formal reference is supplied;
- adding stronger adversarial continual-learning and conflict-resolution tests.
