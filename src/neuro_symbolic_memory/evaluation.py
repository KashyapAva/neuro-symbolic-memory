from __future__ import annotations
import time
from typing import Any, Dict, List
from .models import QueryTask
from .reasoner import Reasoner

class Evaluator:
    @staticmethod
    def evaluate_tasks(reasoner: Reasoner, tasks: List[QueryTask], phase: str, mode: str) -> Dict[str, Any]:
        rows = []
        start = time.perf_counter()
        for task in tasks:
            t0 = time.perf_counter()
            out = reasoner.answer(task, mode=mode)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            correct = out["answer"] == task.expected
            rows.append({
                "phase": phase,
                "mode": mode,
                "task_id": task.task_id,
                "domain": task.domain,
                "batch": task.batch,
                "subject": task.subject,
                "target_relation": task.target_relation,
                "expected": task.expected,
                "actual": out["answer"],
                "reasoning_mode": out["mode"],
                "correct": correct,
                "faithful": bool(out["faithful"] and correct),
                "support": out["support"],
                "retrieval_score": out.get("retrieval_score", 0.0),
                "elapsed_ms": elapsed_ms,
            })
        total_ms = (time.perf_counter() - start) * 1000
        n = len(rows) or 1
        return {
            "phase": phase,
            "mode": mode,
            "tasks": len(rows),
            "accuracy": sum(r["correct"] for r in rows) / n,
            "faithfulness": sum(r["faithful"] for r in rows) / n,
            "avg_ms": total_ms / n,
            "rows": rows,
        }

    @staticmethod
    def retention(current_rows: List[Dict[str, Any]], previous_task_ids: set[str]) -> float:
        old_rows = [r for r in current_rows if r["task_id"] in previous_task_ids]
        if not old_rows:
            return 1.0
        return sum(r["correct"] for r in old_rows) / len(old_rows)
