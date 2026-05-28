from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from neuro_symbolic_memory.integration import MemoryEngine, ReasoningFrameworkAdapter
from neuro_symbolic_memory.models import Trace


def build_demo_engine() -> ReasoningFrameworkAdapter:
    engine = MemoryEngine()

    examples = [
        {
            "nodes": [("India", "Country"), ("New Delhi", "City"), ("Asia", "Continent")],
            "facts": [("India", "HAS_CAPITAL", "New Delhi"), ("New Delhi", "LOCATED_IN", "Asia")],
            "trace": Trace(
                "interactive_geo_trace",
                "interactive_geo",
                "Which continent is India's capital located in?",
                [("India", "HAS_CAPITAL", "New Delhi"), ("New Delhi", "LOCATED_IN", "Asia")],
                "Asia",
                True,
            ),
        },
        {
            "nodes": [("math_problem_x_plus_2_eq_5", "MathProblem"), ("equation_x_plus_2_eq_5", "Equation"), ("x_equals_3", "Solution")],
            "facts": [("math_problem_x_plus_2_eq_5", "HAS_EQUATION", "equation_x_plus_2_eq_5"), ("equation_x_plus_2_eq_5", "EQUATION_SOLVES_TO", "x_equals_3")],
            "trace": Trace(
                "interactive_math_trace",
                "interactive_math",
                "Solve x + 2 = 5.",
                [("math_problem_x_plus_2_eq_5", "HAS_EQUATION", "equation_x_plus_2_eq_5"), ("equation_x_plus_2_eq_5", "EQUATION_SOLVES_TO", "x_equals_3")],
                "x_equals_3",
                True,
            ),
        },
        {
            "nodes": [("incident_checkout_latency", "Incident"), ("signal_db_cpu_spike", "Signal"), ("cause_database_bottleneck", "Cause")],
            "facts": [("incident_checkout_latency", "HAS_SIGNAL", "signal_db_cpu_spike"), ("signal_db_cpu_spike", "SIGNAL_POINTS_TO", "cause_database_bottleneck")],
            "trace": Trace(
                "interactive_rca_trace",
                "interactive_rca",
                "What caused checkout latency?",
                [("incident_checkout_latency", "HAS_SIGNAL", "signal_db_cpu_spike"), ("signal_db_cpu_spike", "SIGNAL_POINTS_TO", "cause_database_bottleneck")],
                "cause_database_bottleneck",
                True,
            ),
        },
        {
            "nodes": [("forecast_case_churn_q3", "ForecastCase"), ("trend_usage_drop", "Trend"), ("risk_high_churn", "Risk")],
            "facts": [("forecast_case_churn_q3", "HAS_TREND", "trend_usage_drop"), ("trend_usage_drop", "TREND_IMPLIES_RISK", "risk_high_churn")],
            "trace": Trace(
                "interactive_forecast_trace",
                "interactive_forecast",
                "What is the churn forecast risk?",
                [("forecast_case_churn_q3", "HAS_TREND", "trend_usage_drop"), ("trend_usage_drop", "TREND_IMPLIES_RISK", "risk_high_churn")],
                "risk_high_churn",
                True,
            ),
        },
    ]

    for item in examples:
        for label, node_type in item["nodes"]:
            engine.add_node(label, node_type)
        for src, rel, dst in item["facts"]:
            engine.add_fact(src, rel, dst, domain=item["trace"].domain)
        engine.ingest_trace(item["trace"])
    engine.consolidate()
    return ReasoningFrameworkAdapter(engine)


def main() -> None:
    adapter = build_demo_engine()
    tool = adapter.as_tool()
    menu = {
        "1": {
            "label": "What continent is India's capital in?",
            "query": {"subject": "India", "target_relation": "CAPITAL_CONTINENT", "expected": "Asia", "domain": "interactive_geo"},
        },
        "2": {
            "label": "Solve x + 2 = 5",
            "query": {"subject": "math_problem_x_plus_2_eq_5", "target_relation": "HAS_SOLUTION", "expected": "x_equals_3", "domain": "interactive_math"},
        },
        "3": {
            "label": "What caused checkout latency?",
            "query": {"subject": "incident_checkout_latency", "target_relation": "HAS_ROOT_CAUSE", "expected": "cause_database_bottleneck", "domain": "interactive_rca"},
        },
        "4": {
            "label": "What is the forecast risk for Q3 churn?",
            "query": {"subject": "forecast_case_churn_q3", "target_relation": "FORECAST_RISK", "expected": "risk_high_churn", "domain": "interactive_forecast"},
        },
    }

    print("Neuro-symbolic memory interactive demo")
    print("Choose a structured query. This avoids brittle NLP parsing and tests the memory/reasoning API directly.\n")
    for key, value in menu.items():
        print(f"{key}. {value['label']}")
    print("q. Quit")

    while True:
        choice = input("\nChoice: ").strip().lower()
        if choice == "q":
            break
        if choice not in menu:
            print("Invalid choice.")
            continue
        result = tool(menu[choice]["query"])
        print("\nAnswer:", result["answer"])
        print("Retrieved context:")
        for row in result["context"][:3]:
            print(" -", row)


if __name__ == "__main__":
    main()
