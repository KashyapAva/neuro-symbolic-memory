# Submission Note

This final version removes the confusing country-capital/math shortcut story from the main demo and focuses on a coherent data-observability RCA memory engine.

The major update is that the γ(3,4) graph is now explicit and tested. The examples use all three node kinds — Event, Thing, Concept — and all four relation families — NEAR, LEADS_TO, CONTAINS, EXPRESSES. The validator checks both γ-family compatibility and task-specific type constraints before memory is accepted.

The demo shows resolved traces teaching memory, similar unresolved incidents producing provisional hypotheses, future outcomes promoting or contradicting those hypotheses, invalid memory rejection, baseline contrast, repeated-access replay/decay, persistence, integration, and γ(3,4) coverage counts.

Run:

```bash
python3 demo.py
python3 -m unittest discover -s tests -v
```
