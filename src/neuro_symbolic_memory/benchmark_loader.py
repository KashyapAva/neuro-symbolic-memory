from __future__ import annotations
import csv
from pathlib import Path
from typing import List, Tuple
from .models import Trace, QueryTask

class ExternalBenchmarkLoader:
    """Loads a real-world KGQA-style benchmark packaged as CSV files.

    The included benchmark uses real geography facts (countries, capitals, continents)
    and asks compositional KGQA questions that require two-hop reasoning:
    Country --HAS_CAPITAL--> City --LOCATED_IN--> Continent.
    """
    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)

    def load_geo_benchmark(self) -> tuple[list[tuple], list[tuple], list[Trace], list[QueryTask]]:
        nodes: list[tuple] = []
        node_seen = set()
        edges: list[tuple] = []
        traces: list[Trace] = []
        tasks: list[QueryTask] = []
        with open(self.data_dir / "external_geo_kgqa.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                country = row["country"]
                capital = row["capital"]
                continent = row["continent"]
                for label, node_type in [(country, "Country"), (capital, "City"), (continent, "Continent")]:
                    if label not in node_seen:
                        nodes.append((label, node_type))
                        node_seen.add(label)
                edges.append((country, "HAS_CAPITAL", capital, "external_geo"))
                edges.append((capital, "LOCATED_IN", continent, "external_geo"))
                trace_id = f"external_geo_trace_{i:03d}"
                traces.append(Trace(
                    trace_id=trace_id,
                    domain="external_geo_kgqa",
                    question=f"Which continent is the capital of {country} located in?",
                    reasoning_path=[(country, "HAS_CAPITAL", capital), (capital, "LOCATED_IN", continent)],
                    answer=continent,
                    success=True,
                ))
                tasks.append(QueryTask(
                    task_id=f"external_geo_t{i:03d}",
                    domain="external_geo_kgqa",
                    subject=country,
                    target_relation="CAPITAL_CONTINENT",
                    expected=continent,
                    batch="External Geo KGQA",
                ))
        return nodes, edges, traces, tasks
