from __future__ import annotations

from copy import deepcopy
from pprint import pprint

from src.neuro_symbolic_memory.integration import MemoryEngine, ReasoningFrameworkAdapter
from src.neuro_symbolic_memory.models import CandidateRelation, QueryTask

DOMAIN = "data_observability_rca"


def show(title: str, obj=None) -> None:
    print(f"\n--- {title} ---")
    if obj is not None:
        pprint(obj, sort_dicts=False)


def compact_prediction(result: dict) -> dict:
    return {
        "answer": result.get("answer"),
        "mode": result.get("mode"),
        "status": result.get("hypothesis_status"),
        "confidence": result.get("confidence"),
        "similar_case": result.get("similar_case"),
        "support": result.get("support"),
    }


def compact_outcome(result: dict) -> dict:
    return {
        "case_id": result.get("case_id"),
        "prediction": result.get("prediction"),
        "actual_root_cause": result.get("actual_root_cause"),
        "prediction_correct": result.get("prediction_correct"),
        "hypothesis_status": result.get("hypothesis_status"),
        "confidence_after_feedback": result.get("confidence_after_feedback"),
        "memory_update": result.get("memory_update"),
        "promoted_edge": result.get("promoted_edge"),
        "pattern_updated": result.get("pattern_updated"),
    }


def add_graph_context(engine: MemoryEngine, case: dict) -> None:
    """Add explicit γ(3,4) context for the resolved case.

    This is where the examples stop being only incident->signal->cause.  Each
    case now uses Event/Thing/Concept nodes and all four relation families:
    EXPRESSES, CONTAINS, LEADS_TO, and later NEAR.
    """
    for label, node_type in case.get("nodes", []):
        engine.add_node(label, node_type, provenance="gamma34_context")
    for src, relation, dst in case.get("facts", []):
        engine.add_fact(src, relation, dst, domain=DOMAIN, provenance="gamma34_context")


def train_resolved_cases(engine: MemoryEngine) -> None:
    """Resolved traces are the training signal, not a manual confirmation button."""
    cases = [
        {
            "case_id": "incident_checkout_latency",
            "signal_id": "signal_db_cpu_spike",
            "root_cause": "cause_database_bottleneck",
            "remediation": "remediation_tune_queries_and_pool",
            "features": [
                "service:checkout",
                "component:database",
                "signal:db_cpu_spike",
                "metric:query_latency_high",
                "symptom:slow_queries",
            ],
            "nodes": [
                ("service_checkout", "Service"),
                ("database_primary", "Database"),
                ("metric_query_latency_high", "Metric"),
                ("symptom_slow_queries", "Symptom"),
            ],
            "facts": [
                ("incident_checkout_latency", "AFFECTS_SERVICE", "service_checkout"),        # Event -> Thing, EXPRESSES
                ("service_checkout", "DEPENDS_ON", "database_primary"),                     # Thing -> Thing, CONTAINS
                ("incident_checkout_latency", "HAS_METRIC", "metric_query_latency_high"),   # Event -> Concept, EXPRESSES
                ("incident_checkout_latency", "HAS_SYMPTOM", "symptom_slow_queries"),       # Event -> Concept, EXPRESSES
            ],
        },
        {
            "case_id": "incident_sales_missing_customer_id",
            "signal_id": "signal_missing_customer_id_column",
            "root_cause": "cause_schema_drift",
            "remediation": "remediation_update_transformation_mapping",
            "features": [
                "pipeline:sales_daily",
                "component:etl",
                "signal:missing_column_customer_id",
                "event:upstream_schema_change",
                "schema:customer_id",
            ],
            "nodes": [
                ("pipeline_sales_daily", "Pipeline"),
                ("table_customers", "Table"),
                ("column_customer_id", "Column"),
                ("metric_missing_column_rate", "Metric"),
                ("event_upstream_schema_change", "ChangeEvent"),
            ],
            "facts": [
                ("incident_sales_missing_customer_id", "AFFECTS_PIPELINE", "pipeline_sales_daily"),  # Event -> Thing, EXPRESSES
                ("pipeline_sales_daily", "CONTAINS", "table_customers"),                            # Thing -> Thing, CONTAINS
                ("table_customers", "CONTAINS", "column_customer_id"),                              # Thing -> Thing, CONTAINS
                ("incident_sales_missing_customer_id", "HAS_METRIC", "metric_missing_column_rate"),  # Event -> Concept, EXPRESSES
                ("event_upstream_schema_change", "SIGNAL_POINTS_TO", "cause_schema_drift"),          # Event -> Concept, LEADS_TO
            ],
        },
        {
            "case_id": "incident_login_api_errors",
            "signal_id": "signal_auth_timeout_spike",
            "root_cause": "cause_auth_service_degradation",
            "remediation": "remediation_scale_auth_service",
            "features": [
                "service:api",
                "component:auth",
                "signal:auth_timeout",
                "metric:5xx_spike",
                "symptom:login_failures",
            ],
            "nodes": [
                ("service_api", "Service"),
                ("database_auth_sessions", "Database"),
                ("metric_5xx_spike", "Metric"),
                ("symptom_login_failures", "Symptom"),
            ],
            "facts": [
                ("incident_login_api_errors", "AFFECTS_SERVICE", "service_api"),
                ("service_api", "DEPENDS_ON", "database_auth_sessions"),
                ("incident_login_api_errors", "HAS_METRIC", "metric_5xx_spike"),
                ("incident_login_api_errors", "HAS_SYMPTOM", "symptom_login_failures"),
            ],
        },
        {
            "case_id": "incident_payment_failures",
            "signal_id": "signal_gateway_5xx_spike",
            "root_cause": "cause_payment_gateway_outage",
            "remediation": "remediation_route_to_backup_gateway",
            "features": [
                "service:payments",
                "component:gateway",
                "signal:gateway_5xx",
                "metric:payment_failure_rate_high",
                "symptom:checkout_payment_errors",
            ],
            "nodes": [
                ("service_payments", "Service"),
                ("gateway_primary_payment", "Gateway"),
                ("metric_payment_failure_rate_high", "Metric"),
                ("symptom_checkout_payment_errors", "Symptom"),
            ],
            "facts": [
                ("incident_payment_failures", "AFFECTS_SERVICE", "service_payments"),
                ("service_payments", "CONTAINS", "gateway_primary_payment"),
                ("incident_payment_failures", "HAS_METRIC", "metric_payment_failure_rate_high"),
                ("incident_payment_failures", "HAS_SYMPTOM", "symptom_checkout_payment_errors"),
            ],
        },
    ]
    learned = []
    for case in cases:
        # Need the incident/cause nodes first because context facts refer to them.
        engine.add_node(case["case_id"], "Incident", provenance="resolved_outcome_trace")
        engine.add_node(case["root_cause"], "Cause", provenance="resolved_outcome_trace")
        add_graph_context(engine, case)
        result = engine.ingest_resolved_episode(
            case_id=case["case_id"],
            signal_id=case["signal_id"],
            root_cause=case["root_cause"],
            features=case["features"],
            remediation=case["remediation"],
        )
        learned.append(
            {
                "case_id": case["case_id"],
                "root_cause": case["root_cause"],
                "accepted_trace_candidates": result["accepted"],
                "semantic_memory": result["semantic_memory"],
                "pattern": result["pattern_memory"],
            }
        )
    show("1) Resolved outcome traces teach graph, case, vector, and pattern memory", learned)
    show("2) γ(3,4) graph coverage after resolved traces", engine.graph.gamma34_summary())


def run_predictions(engine: MemoryEngine) -> None:
    exact_before = engine.query(
        QueryTask(
            task_id="orders_before_memory_transfer",
            domain=DOMAIN,
            subject="incident_orders_latency",
            target_relation="HAS_ROOT_CAUSE",
            expected="cause_database_bottleneck",
            batch="pre_outcome",
        )
    )
    show("3) New incident exact graph query before outcome: no direct fact is preloaded", exact_before)

    # Add γ context for unresolved incidents too; root-cause is not added yet.
    engine.add_node("incident_orders_latency", "Incident", provenance="new_incident")
    engine.add_node("service_orders", "Service", provenance="new_incident")
    engine.add_node("database_orders", "Database", provenance="new_incident")
    engine.add_node("metric_orders_query_latency_high", "Metric", provenance="new_incident")
    engine.add_fact("incident_orders_latency", "AFFECTS_SERVICE", "service_orders", domain=DOMAIN, provenance="new_incident")
    engine.add_fact("service_orders", "DEPENDS_ON", "database_orders", domain=DOMAIN, provenance="new_incident")
    engine.add_fact("incident_orders_latency", "HAS_METRIC", "metric_orders_query_latency_high", domain=DOMAIN, provenance="new_incident")

    predictions = []
    new_cases = [
        (
            "incident_orders_latency",
            [
                "service:orders",
                "component:database",
                "signal:db_cpu_saturation",
                "metric:query_latency_high",
                "symptom:slow_queries",
            ],
        ),
        (
            "incident_orders_missing_status",
            [
                "pipeline:orders_daily",
                "component:etl",
                "signal:missing_column_order_status",
                "event:upstream_schema_change",
                "schema:order_status",
            ],
        ),
        (
            "incident_login_timeout_wave",
            [
                "service:api",
                "component:auth",
                "signal:auth_timeout",
                "metric:5xx_spike",
                "symptom:login_failures",
            ],
        ),
    ]
    for case_id, features in new_cases:
        pred = engine.predict_from_memory(case_id, features, top_k=3, min_score=0.20)
        predictions.append({"case_id": case_id, **compact_prediction(pred)})
    show("4) Memory-based predictions across varied new incidents", predictions)


def observe_outcomes(engine: MemoryEngine) -> None:
    outcomes = []
    for args in [
        {
            "case_id": "incident_orders_latency",
            "actual_root_cause": "cause_database_bottleneck",
            "signal_id": "signal_db_cpu_saturation",
            "features": [
                "service:orders",
                "component:database",
                "signal:db_cpu_saturation",
                "metric:query_latency_high",
                "symptom:slow_queries",
            ],
            "remediation": "remediation_tune_queries_and_pool",
        },
        {
            "case_id": "incident_orders_missing_status",
            "actual_root_cause": "cause_schema_drift",
            "signal_id": "signal_missing_order_status_column",
            "features": [
                "pipeline:orders_daily",
                "component:etl",
                "signal:missing_column_order_status",
                "event:upstream_schema_change",
                "schema:order_status",
            ],
            "remediation": "remediation_update_transformation_mapping",
        },
        {
            "case_id": "incident_login_timeout_wave",
            "actual_root_cause": "cause_auth_service_degradation",
            "signal_id": "signal_auth_timeout_wave",
            "features": [
                "service:api",
                "component:auth",
                "signal:auth_timeout",
                "metric:5xx_spike",
                "symptom:login_failures",
            ],
            "remediation": "remediation_scale_auth_service",
        },
    ]:
        outcomes.append(compact_outcome(engine.observe_outcome_trace(domain=DOMAIN, **args)))
    show("5) Future resolved traces automatically promote correct hypotheses", outcomes)

    analytics_features = [
        "service:analytics_dashboard",
        "component:cache",
        "signal:cache_evictions",
        "metric:latency_spike",
        "symptom:slow_dashboard",
    ]
    weak_pred = engine.predict_from_memory("incident_analytics_latency", analytics_features, top_k=3, min_score=0.20)
    contradicted = engine.observe_outcome_trace(
        case_id="incident_analytics_latency",
        actual_root_cause="cause_cache_eviction_pressure",
        signal_id="signal_cache_evictions",
        features=analytics_features,
        domain=DOMAIN,
        remediation="remediation_increase_cache_ttl_and_capacity",
    )
    show(
        "6) Counterexample handling: wrong provisional memory is weakened, not promoted",
        {"weak_prediction": compact_prediction(weak_pred), "outcome_update": compact_outcome(contradicted)},
    )


def validate_and_compare(engine: MemoryEngine) -> None:
    # Invalid candidate 1: exact task type mismatch.
    engine.add_node("incident_bad_candidate", "Incident", provenance="validator_demo")
    engine.add_node("table_customer_orders", "Table", provenance="validator_demo")
    bad = CandidateRelation(
        src="incident_bad_candidate",
        relation="HAS_ROOT_CAUSE",
        dst="table_customer_orders",
        domain=DOMAIN,
        confidence=0.92,
        provenance="bad_candidate_demo",
        proof="retrieved table name but table is not a Cause node",
        source_trace_id="bad_candidate_demo",
        rule_id="invalid_type_demo",
    )
    ok, reason = engine.validator.validate(bad)

    # Invalid candidate 2: γ family mismatch, NEAR cannot link Event -> Thing.
    bad_gamma = CandidateRelation(
        src="incident_bad_candidate",
        relation="SIMILAR_TO",
        dst="table_customer_orders",
        domain=DOMAIN,
        confidence=0.92,
        provenance="bad_gamma_candidate_demo",
        proof="event looked textually close to a table name, but γ(3,4) forbids Event->Thing NEAR",
        source_trace_id="bad_gamma_candidate_demo",
        rule_id="invalid_gamma_family_demo",
    )
    ok_gamma, reason_gamma = engine.validator.validate(bad_gamma)
    show(
        "7) γ(3,4) typed validator rejects invalid memory",
        {
            "task_type_candidate": f"{bad.src} --{bad.relation}--> {bad.dst}",
            "task_type_accepted": ok,
            "task_type_reason": reason,
            "gamma_family_candidate": f"{bad_gamma.src} --{bad_gamma.relation}--> {bad_gamma.dst}",
            "gamma_family_accepted": ok_gamma,
            "gamma_family_reason": reason_gamma,
        },
    )

    novel_features = [
        "pipeline:inventory_daily",
        "component:etl",
        "signal:missing_column_sku_status",
        "event:upstream_schema_change",
        "schema:sku_status",
    ]
    graph_before = engine.query(
        QueryTask(
            task_id="inventory_before_prediction",
            domain=DOMAIN,
            subject="incident_inventory_missing_sku_status",
            target_relation="HAS_ROOT_CAUSE",
            expected="cause_schema_drift",
            batch="baseline",
        ),
        mode="hybrid",
    )
    vector_case = engine.case_memory.query(novel_features, top_k=1)[0]
    hybrid_pred = engine.predict_from_memory("incident_inventory_missing_sku_status", novel_features, top_k=3)
    show(
        "8) Baseline contrast on a novel but related incident",
        {
            "graph_exact_before_outcome": graph_before,
            "case_vector_only_unverified": {
                "answer": vector_case["case"].root_cause,
                "similar_case": vector_case["case"].case_id,
                "score": vector_case["score"],
                "faithful": False,
                "why_not_enough": "retrieval alone has no typed proof/promotion status for the new incident",
            },
            "hybrid_memory_engine": compact_prediction(hybrid_pred),
        },
    )


def replay_warmup(engine: MemoryEngine) -> dict:
    """Repeatedly reuse a few learned memories so replay has something meaningful to retain.

    In a real incident system this would happen naturally when the same learned
    RCA memories are queried by monitors, analysts, or downstream agents.  The
    demo makes the repeated access explicit so the absorption/replay mechanism is
    visible instead of reporting replayed_edges=0.
    """
    tasks = [
        QueryTask(
            task_id="warmup_orders_latency",
            domain=DOMAIN,
            subject="incident_orders_latency",
            target_relation="HAS_ROOT_CAUSE",
            expected="cause_database_bottleneck",
            batch="replay_warmup",
        ),
        QueryTask(
            task_id="warmup_orders_missing_status",
            domain=DOMAIN,
            subject="incident_orders_missing_status",
            target_relation="HAS_ROOT_CAUSE",
            expected="cause_schema_drift",
            batch="replay_warmup",
        ),
        QueryTask(
            task_id="warmup_login_timeout_wave",
            domain=DOMAIN,
            subject="incident_login_timeout_wave",
            target_relation="HAS_ROOT_CAUSE",
            expected="cause_auth_service_degradation",
            batch="replay_warmup",
        ),
    ]
    results = []
    # Two passes are enough because query-time reinforcement adds importance.
    for pass_id in range(2):
        for task in tasks:
            result = engine.query(task)
            results.append({
                "pass": pass_id + 1,
                "subject": task.subject,
                "answer": result.get("answer"),
                "mode": result.get("mode"),
                "faithful": result.get("faithful"),
            })

    absorbed = [
        f"{edge.src} --{edge.relation}--> {edge.dst}"
        for edge in engine.graph.absorbed_edges()
    ]
    return {
        "why": "Repeated access simulates recurring analyst/agent queries so important learned memories cross the absorption threshold.",
        "queries_run": len(results),
        "absorbed_edges_after_warmup": absorbed,
    }


def persistence_and_replay(engine: MemoryEngine) -> None:
    warmup = replay_warmup(engine)
    replayed = engine.consolidate()
    before_decay = engine.memory_report()
    saved = engine.save_memory("outputs/robust_gamma34_memory_snapshot.json")

    fresh = MemoryEngine()
    fresh.load_memory(saved)
    fresh_query = fresh.query(
        QueryTask(
            task_id="orders_after_reload",
            domain=DOMAIN,
            subject="incident_orders_latency",
            target_relation="HAS_ROOT_CAUSE",
            expected="cause_database_bottleneck",
            batch="reload",
        )
    )

    # Ablation: same memory state, but time passes and replay is disabled.
    no_replay = deepcopy(engine)
    no_replay.advance_time_without_replay(batch_num=10, max_staleness=1)
    decayed_report = no_replay.memory_report()

    # Retention path: time passes, but absorbed memories are replayed/refreshed.
    with_replay = deepcopy(engine)
    with_replay.batch_num = 10
    replayed_after_delay = with_replay.consolidate()
    replay_report = with_replay.memory_report()
    show(
        "9) Persistence and replay/decay summary",
        {
            "replay_warmup": warmup,
            "replayed_edges_initial": replayed,
            "replayed_edges_after_delay": replayed_after_delay,
            "saved_snapshot": saved,
            "fresh_engine_query_for_promoted_memory": fresh_query,
            "active_learned_edges_before_decay": before_decay["active_learned_edges"],
            "absorbed_edges_before_decay": before_decay["absorbed_edges"],
            "active_learned_edges_after_no_replay_decay": decayed_report["active_learned_edges"],
            "active_learned_edges_after_replay_refresh": replay_report["active_learned_edges"],
            "gamma34_after_reload": fresh.graph.gamma34_summary(),
            "note": "Repeatedly used memories are absorbed and replayed; without replay, stale learned edges are deactivated in the forgetting stress test.",
        },
    )

    adapter = ReasoningFrameworkAdapter(fresh).as_tool()
    adapter_result = adapter(
        {
            "task_id": "adapter_orders_root_cause",
            "domain": DOMAIN,
            "subject": "incident_orders_latency",
            "target_relation": "HAS_ROOT_CAUSE",
            "expected": "cause_database_bottleneck",
            "mode": "hybrid",
        }
    )
    show("10) Integration adapter output", adapter_result)


def main() -> None:
    print("=== Robust γ(3,4) neuro-symbolic memory engine demo ===")
    print("One coherent domain: data observability / RCA.")
    print("The examples deliberately exercise all 3 node kinds and all 4 γ relation families: Event, Thing, Concept x NEAR, LEADS_TO, CONTAINS, EXPRESSES.\n")
    engine = MemoryEngine()
    train_resolved_cases(engine)
    run_predictions(engine)
    observe_outcomes(engine)
    validate_and_compare(engine)
    persistence_and_replay(engine)
    show("Final memory report", engine.memory_report())
    print("\n=== Interpretation ===")
    print("γ(3,4) is used as a constraint system, not a label: events, things, and concepts can only be linked by semantically valid NEAR, LEADS_TO, CONTAINS, or EXPRESSES edges.")
    print("NEAR supports similar-case retrieval; LEADS_TO supports causal/remediation reasoning; CONTAINS supports system structure; EXPRESSES stores observed evidence and metadata.")
    print("The memory engine is a typed graph validator + vector-symbolic case retriever + pattern memory + hypothesis memory + replay/persistence layer.")
    print("It is not vanilla Graph RAG: memory is mutable, audited, promoted/contradicted, and replayed over time instead of only retrieved as context.")


if __name__ == "__main__":
    main()
