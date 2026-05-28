from __future__ import annotations
from pathlib import Path
from .models import Batch, Trace, QueryTask
from .benchmark_loader import ExternalBenchmarkLoader

def build_batches(data_dir: str | Path) -> list[Batch]:
    loader = ExternalBenchmarkLoader(data_dir)
    geo_nodes, geo_edges, geo_traces, geo_tasks = loader.load_geo_benchmark()
    batches: list[Batch] = [
        Batch("Batch 1 External Geo KGQA", "external_geo_kgqa", geo_nodes, geo_edges, geo_traces, geo_tasks),
        Batch(
            "Batch 2 Math",
            "math",
            [
                ("math_problem_x_plus_2_eq_5", "MathProblem"), ("equation_x_plus_2_eq_5", "Equation"), ("x_equals_3", "Solution"),
                ("math_problem_2x_eq_10", "MathProblem"), ("equation_2x_eq_10", "Equation"), ("x_equals_5", "Solution"),
                ("math_problem_x_minus_4_eq_2", "MathProblem"), ("equation_x_minus_4_eq_2", "Equation"), ("x_equals_6", "Solution"),
            ],
            [
                ("math_problem_x_plus_2_eq_5", "HAS_EQUATION", "equation_x_plus_2_eq_5", "math"),
                ("equation_x_plus_2_eq_5", "EQUATION_SOLVES_TO", "x_equals_3", "math"),
                ("math_problem_2x_eq_10", "HAS_EQUATION", "equation_2x_eq_10", "math"),
                ("equation_2x_eq_10", "EQUATION_SOLVES_TO", "x_equals_5", "math"),
                ("math_problem_x_minus_4_eq_2", "HAS_EQUATION", "equation_x_minus_4_eq_2", "math"),
                ("equation_x_minus_4_eq_2", "EQUATION_SOLVES_TO", "x_equals_6", "math"),
            ],
            [
                Trace("math_trace_001", "math", "Solve x + 2 = 5", [("math_problem_x_plus_2_eq_5", "HAS_EQUATION", "equation_x_plus_2_eq_5"), ("equation_x_plus_2_eq_5", "EQUATION_SOLVES_TO", "x_equals_3")], "x_equals_3", True),
                Trace("math_trace_002", "math", "Solve 2x = 10", [("math_problem_2x_eq_10", "HAS_EQUATION", "equation_2x_eq_10"), ("equation_2x_eq_10", "EQUATION_SOLVES_TO", "x_equals_5")], "x_equals_5", True),
                Trace("math_trace_003", "math", "Solve x - 4 = 2", [("math_problem_x_minus_4_eq_2", "HAS_EQUATION", "equation_x_minus_4_eq_2"), ("equation_x_minus_4_eq_2", "EQUATION_SOLVES_TO", "x_equals_6")], "x_equals_6", True),
            ],
            [
                QueryTask("math_t1", "math", "math_problem_x_plus_2_eq_5", "HAS_SOLUTION", "x_equals_3", "Batch 2 Math"),
                QueryTask("math_t2", "math", "math_problem_2x_eq_10", "HAS_SOLUTION", "x_equals_5", "Batch 2 Math"),
                QueryTask("math_t3", "math", "math_problem_x_minus_4_eq_2", "HAS_SOLUTION", "x_equals_6", "Batch 2 Math"),
            ],
        ),
        Batch(
            "Batch 3 RCA",
            "rca",
            [
                ("incident_checkout_latency", "Incident"), ("signal_db_cpu_spike", "Signal"), ("cause_database_bottleneck", "Cause"),
                ("incident_api_errors", "Incident"), ("signal_auth_timeout", "Signal"), ("cause_auth_service_degradation", "Cause"),
                ("incident_payment_failures", "Incident"), ("signal_gateway_5xx", "Signal"), ("cause_payment_gateway_outage", "Cause"),
            ],
            [
                ("incident_checkout_latency", "HAS_SIGNAL", "signal_db_cpu_spike", "rca"),
                ("signal_db_cpu_spike", "SIGNAL_POINTS_TO", "cause_database_bottleneck", "rca"),
                ("incident_api_errors", "HAS_SIGNAL", "signal_auth_timeout", "rca"),
                ("signal_auth_timeout", "SIGNAL_POINTS_TO", "cause_auth_service_degradation", "rca"),
                ("incident_payment_failures", "HAS_SIGNAL", "signal_gateway_5xx", "rca"),
                ("signal_gateway_5xx", "SIGNAL_POINTS_TO", "cause_payment_gateway_outage", "rca"),
            ],
            [
                Trace("rca_trace_001", "rca", "Root cause of checkout latency", [("incident_checkout_latency", "HAS_SIGNAL", "signal_db_cpu_spike"), ("signal_db_cpu_spike", "SIGNAL_POINTS_TO", "cause_database_bottleneck")], "cause_database_bottleneck", True),
                Trace("rca_trace_002", "rca", "Root cause of API errors", [("incident_api_errors", "HAS_SIGNAL", "signal_auth_timeout"), ("signal_auth_timeout", "SIGNAL_POINTS_TO", "cause_auth_service_degradation")], "cause_auth_service_degradation", True),
                Trace("rca_trace_003", "rca", "Root cause of payment failures", [("incident_payment_failures", "HAS_SIGNAL", "signal_gateway_5xx"), ("signal_gateway_5xx", "SIGNAL_POINTS_TO", "cause_payment_gateway_outage")], "cause_payment_gateway_outage", True),
            ],
            [
                QueryTask("rca_t1", "rca", "incident_checkout_latency", "HAS_ROOT_CAUSE", "cause_database_bottleneck", "Batch 3 RCA"),
                QueryTask("rca_t2", "rca", "incident_api_errors", "HAS_ROOT_CAUSE", "cause_auth_service_degradation", "Batch 3 RCA"),
                QueryTask("rca_t3", "rca", "incident_payment_failures", "HAS_ROOT_CAUSE", "cause_payment_gateway_outage", "Batch 3 RCA"),
            ],
        ),
        Batch(
            "Batch 4 Forecast",
            "forecast",
            [
                ("forecast_case_churn_q3", "ForecastCase"), ("trend_usage_drop", "Trend"), ("risk_high_churn", "Risk"),
                ("forecast_case_inventory", "ForecastCase"), ("trend_demand_spike", "Trend"), ("risk_stockout", "Risk"),
                ("forecast_case_fraud", "ForecastCase"), ("trend_anomaly_spike", "Trend"), ("risk_fraud_escalation", "Risk"),
            ],
            [
                ("forecast_case_churn_q3", "HAS_TREND", "trend_usage_drop", "forecast"),
                ("trend_usage_drop", "TREND_IMPLIES_RISK", "risk_high_churn", "forecast"),
                ("forecast_case_inventory", "HAS_TREND", "trend_demand_spike", "forecast"),
                ("trend_demand_spike", "TREND_IMPLIES_RISK", "risk_stockout", "forecast"),
                ("forecast_case_fraud", "HAS_TREND", "trend_anomaly_spike", "forecast"),
                ("trend_anomaly_spike", "TREND_IMPLIES_RISK", "risk_fraud_escalation", "forecast"),
            ],
            [
                Trace("forecast_trace_001", "forecast", "Forecast churn risk", [("forecast_case_churn_q3", "HAS_TREND", "trend_usage_drop"), ("trend_usage_drop", "TREND_IMPLIES_RISK", "risk_high_churn")], "risk_high_churn", True),
                Trace("forecast_trace_002", "forecast", "Forecast inventory risk", [("forecast_case_inventory", "HAS_TREND", "trend_demand_spike"), ("trend_demand_spike", "TREND_IMPLIES_RISK", "risk_stockout")], "risk_stockout", True),
                Trace("forecast_trace_003", "forecast", "Forecast fraud risk", [("forecast_case_fraud", "HAS_TREND", "trend_anomaly_spike"), ("trend_anomaly_spike", "TREND_IMPLIES_RISK", "risk_fraud_escalation")], "risk_fraud_escalation", True),
                Trace("forecast_trace_failed", "forecast", "Failed trace ignored", [("forecast_case_inventory", "HAS_TREND", "trend_demand_spike"), ("trend_demand_spike", "TREND_IMPLIES_RISK", "risk_stockout")], "wrong", False),
            ],
            [
                QueryTask("forecast_t1", "forecast", "forecast_case_churn_q3", "FORECAST_RISK", "risk_high_churn", "Batch 4 Forecast"),
                QueryTask("forecast_t2", "forecast", "forecast_case_inventory", "FORECAST_RISK", "risk_stockout", "Batch 4 Forecast"),
                QueryTask("forecast_t3", "forecast", "forecast_case_fraud", "FORECAST_RISK", "risk_fraud_escalation", "Batch 4 Forecast"),
            ],
        ),
        Batch(
            "Batch 5 Invalid Stress Test",
            "kgqa",
            [("London", "Place"), ("Cambridge", "Place"), ("Dave", "Entity")],
            [],
            [Trace("invalid_trace_001", "kgqa", "Invalid type mismatch", [("London", "BORN_IN", "Dave"), ("Dave", "LOCATED_IN", "Cambridge")], "Cambridge", True)],
            [],
        )
    ]
    return batches
