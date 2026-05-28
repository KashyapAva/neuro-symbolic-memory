from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from neuro_symbolic_memory.integration import MemoryEngine, ReasoningFrameworkAdapter
from neuro_symbolic_memory.models import Trace


class SmokeTest(unittest.TestCase):
    def test_memory_engine_learns_and_answers(self):
        engine = MemoryEngine(dim=1024, seed=11)
        engine.add_node("India", "Country")
        engine.add_node("New Delhi", "City")
        engine.add_node("Asia", "Continent")
        engine.add_fact("India", "HAS_CAPITAL", "New Delhi", domain="test")
        engine.add_fact("New Delhi", "LOCATED_IN", "Asia", domain="test")
        trace = Trace(
            trace_id="test_trace",
            domain="test",
            question="Which continent is India's capital in?",
            reasoning_path=[("India", "HAS_CAPITAL", "New Delhi"), ("New Delhi", "LOCATED_IN", "Asia")],
            answer="Asia",
            success=True,
        )
        result = engine.ingest_trace(trace)
        self.assertEqual(result["accepted"], 1)
        engine.consolidate()
        adapter = ReasoningFrameworkAdapter(engine)
        output = adapter.as_tool()({
            "subject": "India",
            "target_relation": "CAPITAL_CONTINENT",
            "expected": "Asia",
            "domain": "test",
            "mode": "hybrid",
        })
        self.assertEqual(output["answer"]["answer"], "Asia")
        self.assertTrue(output["answer"]["faithful"])


if __name__ == "__main__":
    unittest.main()
