# Explicit γ(3,4) Graph Design

This submission treats γ(3,4) as a **typed semantic grammar** for memory, not as a cosmetic label.

## γ(3): three node kinds

| γ kind | Meaning | Examples in the demo |
|---|---|---|
| Event | Something that happens over time | `incident_checkout_latency`, `incident_orders_latency`, `resolved_trace:*` |
| Thing | Persistent operational object | `service_checkout`, `database_primary`, `pipeline_sales_daily`, `table_customers`, `column_customer_id` |
| Concept | Abstract property/explanation/action | `signal_db_cpu_spike`, `metric_query_latency_high`, `cause_database_bottleneck`, `remediation_tune_queries_and_pool` |

## γ(4): four relation families

| γ family | Meaning | Examples in the demo |
|---|---|---|
| NEAR | Similarity / neighborhood, not truth | `incident_orders_latency --SIMILAR_TO--> incident_checkout_latency` |
| LEADS_TO | Causal/explanatory/remediation flow | `signal_db_cpu_spike --SIGNAL_POINTS_TO--> cause_database_bottleneck`; `cause_database_bottleneck --HAS_REMEDIATION--> remediation_tune_queries_and_pool` |
| CONTAINS | Structure, dependency, part-whole | `service_checkout --DEPENDS_ON--> database_primary`; `pipeline_sales_daily --CONTAINS--> table_customers` |
| EXPRESSES | Evidence, observed properties, metrics, symptoms | `incident_checkout_latency --HAS_METRIC--> metric_query_latency_high`; `incident_checkout_latency --HAS_SIGNAL--> signal_db_cpu_spike` |

## Why this matters

A normal graph can connect almost anything to anything. The γ(3,4) schema prevents unsafe memory promotion by checking both:

1. **Family constraints**: for example, a `NEAR` edge cannot link an `Event` to a `Thing`.
2. **Task-specific type constraints**: for example, `HAS_ROOT_CAUSE` must link an `Incident` to a `Cause`, not to a `Table`.

In the demo, invalid memory is rejected in both ways:

- `incident_bad_candidate --HAS_ROOT_CAUSE--> table_customer_orders` is rejected because the target is not a root-cause concept.
- `incident_bad_candidate --SIMILAR_TO--> table_customer_orders` is rejected because γ(3,4) forbids an Event→Thing similarity edge.

## How the demo proves coverage

`python3 demo.py` prints a γ(3,4) summary like:

```text
node_kinds_used: Event, Thing, Concept
relation_families_used: NEAR, LEADS_TO, CONTAINS, EXPRESSES
```

This demonstrates the examples are not just one relation shape such as `incident -> signal -> cause`. They include:

- event evidence (`Incident --HAS_SIGNAL/HAS_METRIC--> Signal/Metric`),
- system structure (`Service/Pipeline --DEPENDS_ON/CONTAINS--> Database/Table/Column`),
- causal reasoning (`Signal --SIGNAL_POINTS_TO--> Cause`),
- similarity retrieval (`Incident --SIMILAR_TO--> Incident`), and
- memory maintenance metadata on learned/promoted edges.
