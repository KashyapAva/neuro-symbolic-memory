# Approach

The project goal is to demonstrate a neuro-symbolic memory engine, not only a static graph query system.

## Design choice

The final prototype focuses on one realistic domain: **data observability / RCA**. The examples are coherent but varied: database bottleneck, schema drift, auth degradation, payment gateway outage, and cache-pressure counterexample.

## γ(3,4) graph backbone

The symbolic graph is explicitly constrained as γ(3,4):

- **γ(3) node kinds**: Event, Thing, Concept.
- **γ(4) relation families**: NEAR, LEADS_TO, CONTAINS, EXPRESSES.

The examples deliberately use all of them:

- Event: incidents and outcome traces.
- Thing: services, databases, pipelines, tables, columns, gateways.
- Concept: signals, metrics, symptoms, causes, remediations, hypotheses, patterns.
- NEAR: similar incident links.
- LEADS_TO: signal→cause, cause→remediation, incident→root-cause.
- CONTAINS: service/pipeline/database/table structure and dependencies.
- EXPRESSES: incident symptoms, metrics, signals, affected services/pipelines.

This is not just a graph rename. The validator checks both γ-family compatibility and task-specific type constraints before learned memory is accepted.

## Memory layers

- **Episodic/case memory** stores solved incidents and their features.
- **Semantic graph memory** stores accepted root-cause relations with proof and provenance.
- **Vector-symbolic memory** retrieves related graph edges and solved cases using high-dimensional feature encodings.
- **Pattern memory** abstracts repeated feature signatures into reusable feature→cause patterns.
- **Hypothesis memory** stores provisional predictions before the future outcome is known.

## Self-learning

The system does not use a manual confirmation button as the learning mechanism. A later resolved outcome trace acts as the feedback signal. If a provisional prediction matches the resolved outcome, it is promoted into graph memory. If not, it becomes a counterexample and its confidence is reduced. If no trusted outcome arrives, the hypothesis remains provisional and is not promoted.

## Robustness checks

The demo includes correct promotions, a wrong prediction/counterexample, invalid task-type rejection, invalid γ-family rejection, graph/vector/hybrid contrast, a repeated-access replay warmup that absorbs important memories, no-replay decay, persistence, integration adapter output, and explicit γ(3,4) coverage counts.
