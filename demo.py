from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from neuro_symbolic_memory.scenarios import build_batches
from neuro_symbolic_memory.pipeline import ExperimentRunner
from neuro_symbolic_memory.integration import MemoryEngine, ReasoningFrameworkAdapter
from neuro_symbolic_memory.models import Trace

DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"


def print_summary(df: pd.DataFrame, title: str) -> None:
    print(f"\n=== {title} ===")
    cols = ["run", "phase", "mode", "tasks", "accuracy", "faithfulness", "retention", "avg_ms", "replayed_edges"]
    print(
        df[cols].to_string(
            index=False,
            formatters={
                "accuracy": "{:.2f}".format,
                "faithfulness": "{:.2f}".format,
                "retention": "{:.2f}".format,
                "avg_ms": "{:.3f}".format,
            },
        )
    )


def run_main_experiment() -> None:
    print("=== Neuro-symbolic memory engine: external benchmark + baselines + integration demo ===")
    print("Domains: external real-world geo KGQA, toy math, RCA traces, forecast-style traces")

    batches = build_batches(DATA_DIR)

    runner = ExperimentRunner(
        batches=batches,
        output_dir=OUTPUT_DIR,
        replay_enabled=True,
        decay_without_replay=False,
        run_label="hybrid_with_replay",
    )
    outputs = runner.run(modes=["hybrid", "graph_only", "vector_only"])
    summary = outputs["summary"]
    print_summary(summary, "Baseline comparison: hybrid vs graph-only vs vector-only")

    print("\n=== No-replay ablation run ===")
    no_replay_runner = ExperimentRunner(
        batches=batches,
        output_dir=OUTPUT_DIR,
        replay_enabled=False,
        decay_without_replay=True,
        run_label="hybrid_no_replay_decay",
    )
    no_replay_outputs = no_replay_runner.run(modes=["hybrid"])
    no_replay_summary = no_replay_outputs["summary"]
    print_summary(no_replay_summary, "No-replay ablation")

    combined = pd.concat([summary, no_replay_summary], ignore_index=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    combined.to_csv(OUTPUT_DIR / "combined_baseline_summary.csv", index=False)

    print("\n=== Final learned relation examples ===")
    learned = outputs["final_learned_relations"]
    print(
        learned[
            ["relation", "domain", "relation_family", "importance", "absorbed", "use_count", "replay_count", "proof"]
        ]
        .head(12)
        .to_string(index=False)
    )

    print("\n=== Rejected candidate examples ===")
    rejected = outputs["rejected_candidates"]
    if len(rejected):
        print(rejected[["batch", "candidate", "domain", "reason", "trace", "proof"]].to_string(index=False))
    else:
        print("No rejected candidates.")

    print("\n=== Integration hook demo ===")
    demo_integration_hook()

    print("\nWrote CSV outputs to ./outputs/")
    print(
        "Interpretation: This version adds an external real-world KGQA benchmark file, "
        "explicit baselines (hybrid, graph-only, vector-only, no-replay), and a framework-style "
        "MemoryEngine/Adapter integration hook."
    )


def demo_integration_hook() -> None:
    engine = MemoryEngine()
    engine.add_node("India", "Country")
    engine.add_node("New Delhi", "City")
    engine.add_node("Asia", "Continent")
    engine.add_fact("India", "HAS_CAPITAL", "New Delhi", domain="integration_demo")
    engine.add_fact("New Delhi", "LOCATED_IN", "Asia", domain="integration_demo")

    trace = Trace(
        trace_id="integration_trace_001",
        domain="integration_demo",
        question="Which continent is India's capital located in?",
        reasoning_path=[("India", "HAS_CAPITAL", "New Delhi"), ("New Delhi", "LOCATED_IN", "Asia")],
        answer="Asia",
        success=True,
    )
    print("ingest_trace:", engine.ingest_trace(trace))
    engine.consolidate()

    adapter = ReasoningFrameworkAdapter(engine)
    tool = adapter.as_tool()
    result = tool(
        {
            "task_id": "integration_q1",
            "domain": "integration_demo",
            "subject": "India",
            "target_relation": "CAPITAL_CONTINENT",
            "expected": "Asia",
            "mode": "hybrid",
        }
    )
    print("adapter_tool_result:", result)


if __name__ == "__main__":
    run_main_experiment()
