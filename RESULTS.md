# Sample Results

## 1. Main demo coverage
External Geo KGQA, Math, RCA, Forecast, Invalid Stress Test.

## 2. Key learned relations
- India --CAPITAL_CONTINENT--> Asia
- math_problem_x_plus_2_eq_5 --HAS_SOLUTION--> x_equals_3
- incident_checkout_latency --HAS_ROOT_CAUSE--> cause_database_bottleneck
- forecast_case_churn_q3 --FORECAST_RISK--> risk_high_churn

## 3. Baseline comparison
Hybrid and graph-only preserve faithfulness; vector-only retrieves candidates but lacks proof support.

## 4. Integration hook
MemoryEngine + ReasoningFrameworkAdapter expose the memory system as a callable retrieval/verification tool.
