import unittest

from src.neuro_symbolic_memory.integration import MemoryEngine
from src.neuro_symbolic_memory.models import QueryTask, CandidateRelation


class RobustSystemTests(unittest.TestCase):
    def test_resolved_trace_prediction_and_outcome_promotion(self):
        engine = MemoryEngine()
        engine.ingest_resolved_episode(
            case_id="incident_checkout_latency",
            signal_id="signal_db_cpu_spike",
            root_cause="cause_database_bottleneck",
            remediation="remediation_tune_queries_and_pool",
            features=["service:checkout", "component:database", "signal:db_cpu_spike", "metric:query_latency_high", "symptom:slow_queries"],
        )

        before = engine.query(QueryTask("t0", "data_observability_rca", "incident_orders_latency", "HAS_ROOT_CAUSE", "cause_database_bottleneck", "pre"))
        self.assertIsNone(before["answer"])

        pred = engine.predict_from_memory(
            "incident_orders_latency",
            ["service:orders", "component:database", "signal:db_cpu_saturation", "metric:query_latency_high", "symptom:slow_queries"],
        )
        self.assertEqual(pred["answer"], "cause_database_bottleneck")
        self.assertEqual(pred["hypothesis_status"], "provisional_memory_pending_outcome_trace")

        update = engine.observe_outcome_trace(
            case_id="incident_orders_latency",
            actual_root_cause="cause_database_bottleneck",
            signal_id="signal_db_cpu_saturation",
            features=["service:orders", "component:database", "signal:db_cpu_saturation", "metric:query_latency_high", "symptom:slow_queries"],
        )
        self.assertTrue(update["prediction_correct"])
        self.assertEqual(update["hypothesis_status"], "promoted")

        after = engine.query(QueryTask("t1", "data_observability_rca", "incident_orders_latency", "HAS_ROOT_CAUSE", "cause_database_bottleneck", "post"))
        self.assertEqual(after["answer"], "cause_database_bottleneck")
        self.assertTrue(after["faithful"])

    def test_validator_rejects_wrong_target_type(self):
        engine = MemoryEngine()
        engine.add_node("incident_bad_candidate", "Incident")
        engine.add_node("table_customer_orders", "System")
        candidate = CandidateRelation(
            src="incident_bad_candidate",
            relation="HAS_ROOT_CAUSE",
            dst="table_customer_orders",
            domain="data_observability_rca",
            confidence=0.9,
            provenance="test",
            proof="has text but wrong target type",
            source_trace_id="test",
            rule_id="test",
        )
        ok, reason = engine.validator.validate(candidate)
        self.assertFalse(ok)
        self.assertTrue("type_mismatch" in reason or "gamma34_family" in reason)

    def test_gamma34_schema_uses_three_node_kinds_and_four_families(self):
        engine = MemoryEngine()
        engine.add_node("incident_a", "Incident")
        engine.add_node("service_a", "Service")
        engine.add_node("database_a", "Database")
        engine.add_node("metric_a", "Metric")
        engine.add_node("cause_a", "Cause")
        engine.add_node("incident_b", "Incident")
        engine.add_fact("incident_a", "AFFECTS_SERVICE", "service_a", domain="test")
        engine.add_fact("service_a", "DEPENDS_ON", "database_a", domain="test")
        engine.add_fact("incident_a", "HAS_METRIC", "metric_a", domain="test")
        engine.add_fact("metric_a", "SIGNAL_POINTS_TO", "cause_a", domain="test")
        engine.add_fact("incident_b", "SIMILAR_TO", "incident_a", domain="test")
        summary = engine.graph.gamma34_summary()
        self.assertGreater(summary["node_kinds_used"]["Event"], 0)
        self.assertGreater(summary["node_kinds_used"]["Thing"], 0)
        self.assertGreater(summary["node_kinds_used"]["Concept"], 0)
        self.assertGreater(summary["relation_families_used"]["NEAR"], 0)
        self.assertGreater(summary["relation_families_used"]["LEADS_TO"], 0)
        self.assertGreater(summary["relation_families_used"]["CONTAINS"], 0)
        self.assertGreater(summary["relation_families_used"]["EXPRESSES"], 0)


if __name__ == "__main__":
    unittest.main()
