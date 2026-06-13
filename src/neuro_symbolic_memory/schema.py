"""Explicit γ(3,4) schema for the neuro-symbolic memory prototype.

The assignment asked for a γ(3,4)-typed directed graph.  In this prototype we
operationalize that as the Semantic-Spacetime style grammar:

    γ(3,4) = 3 node kinds x 4 primitive edge families

Node kinds
----------
Event   : things that happen over time (incidents, traces, predictions).
Thing   : persistent operational objects (services, databases, pipelines,
          tables, columns, gateways).
Concept : abstract properties/explanations/actions (signals, metrics, causes,
          remediations, hypotheses, patterns).

Edge families
-------------
NEAR      : similarity / neighborhood, not truth.
LEADS_TO  : causal, temporal, explanatory, or remediation flow.
CONTAINS  : part-whole, dependency, structural membership.
EXPRESSES : an event/thing expresses an observed property, signal, metric, or
            status.

The point is not just to name 3 and 4 classes.  The schema constrains memory
updates so a retrieved table cannot be promoted as a root cause, a similarity
edge is not treated as proof, and learned memories carry proof/provenance.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, Tuple, List, Union

# ---------------------------------------------------------------------------
# γ(3): node kind mapping
# ---------------------------------------------------------------------------
NODE_TYPE_TO_GAMMA_CLASS: Dict[str, str] = {
    # Events
    "Incident": "Event",
    "Trace": "Event",
    "OutcomeTrace": "Event",
    "PredictionEvent": "Event",
    "Alert": "Event",
    "ChangeEvent": "Event",
    "ForecastCase": "Event",
    "MathProblem": "Event",

    # Things
    "Service": "Thing",
    "Database": "Thing",
    "Pipeline": "Thing",
    "Table": "Thing",
    "Column": "Thing",
    "Gateway": "Thing",
    "Component": "Thing",
    "System": "Thing",
    "Entity": "Thing",
    "Place": "Thing",
    "Organization": "Thing",
    "Country": "Thing",
    "City": "Thing",
    "Continent": "Thing",
    "Variable": "Thing",

    # Concepts
    "Signal": "Concept",
    "Metric": "Concept",
    "Symptom": "Concept",
    "Cause": "Concept",
    "Risk": "Concept",
    "Solution": "Concept",
    "Remediation": "Concept",
    "Hypothesis": "Concept",
    "Pattern": "Concept",
    "Equation": "Concept",
    "Trend": "Concept",
    "Abstraction": "Concept",
    "Status": "Concept",
}

# ---------------------------------------------------------------------------
# γ(4): relation family mapping
# ---------------------------------------------------------------------------
RELATION_TO_FAMILY: Dict[str, str] = {
    # Similarity / neighborhood
    "SIMILAR_TO": "NEAR",
    "ASSOCIATED_WITH": "NEAR",
    "WORKS_IN": "NEAR",
    "STUDIED_IN": "NEAR",
    "CAPITAL_CONTINENT": "NEAR",

    # Causal / temporal / explanatory / remediation flow
    "SIGNAL_POINTS_TO": "LEADS_TO",
    "HAS_ROOT_CAUSE": "LEADS_TO",
    "HAS_REMEDIATION": "LEADS_TO",
    "EQUATION_SOLVES_TO": "LEADS_TO",
    "HAS_SOLUTION": "LEADS_TO",
    "TREND_IMPLIES_RISK": "LEADS_TO",
    "FORECAST_RISK": "LEADS_TO",

    # Part-whole / dependency / structure
    "CONTAINS": "CONTAINS",
    "DEPENDS_ON": "CONTAINS",
    "LOCATED_IN": "CONTAINS",
    "ORG_LOCATED_IN": "CONTAINS",
    "UNIVERSITY_LOCATED_IN": "CONTAINS",

    # Observed properties / evidence / metadata
    "AFFECTS_SERVICE": "EXPRESSES",
    "AFFECTS_PIPELINE": "EXPRESSES",
    "HAS_SIGNAL": "EXPRESSES",
    "HAS_METRIC": "EXPRESSES",
    "HAS_SYMPTOM": "EXPRESSES",
    "HAS_STATUS": "EXPRESSES",
    "HAS_CONFIDENCE": "EXPRESSES",
    "HAS_CAPITAL": "EXPRESSES",
    "BORN_IN": "EXPRESSES",
    "WORKS_AT": "EXPRESSES",
    "STUDIED_AT": "EXPRESSES",
    "LIVES_IN": "EXPRESSES",
    "HAS_EQUATION": "EXPRESSES",
    "HAS_TREND": "EXPRESSES",
}

# Specific task-level signatures.  These are stricter than the γ family checks
# and are used by the validator for learned candidate relations.
ALLOWED_RELATION_TYPES: Dict[str, Union[Tuple[str, str], List[Tuple[str, str]]]] = {
    # RCA / data observability
    "AFFECTS_SERVICE": ("Incident", "Service"),
    "AFFECTS_PIPELINE": ("Incident", "Pipeline"),
    "HAS_SIGNAL": ("Incident", "Signal"),
    "HAS_METRIC": ("Incident", "Metric"),
    "HAS_SYMPTOM": ("Incident", "Symptom"),
    "SIGNAL_POINTS_TO": ("Signal", "Cause"),
    "HAS_ROOT_CAUSE": ("Incident", "Cause"),
    "HAS_REMEDIATION": ("Cause", "Solution"),
    "SIMILAR_TO": ("Incident", "Incident"),
    "DEPENDS_ON": [("Service", "Database"), ("Service", "Gateway"), ("Pipeline", "Database")],
    "CONTAINS": [("Pipeline", "Table"), ("Table", "Column"), ("Service", "Gateway")],

    # Legacy/evaluation relations kept for compatibility
    "HAS_CAPITAL": ("Country", "City"),
    "LOCATED_IN": ("City", "Continent"),
    "CAPITAL_CONTINENT": ("Country", "Continent"),
    "BORN_IN": ("Entity", "Place"),
    "WORKS_AT": ("Entity", "Organization"),
    "ORG_LOCATED_IN": ("Organization", "Place"),
    "STUDIED_AT": ("Entity", "Organization"),
    "UNIVERSITY_LOCATED_IN": ("Organization", "Place"),
    "LIVES_IN": ("Entity", "Place"),
    "ASSOCIATED_WITH": ("Entity", "Place"),
    "WORKS_IN": ("Entity", "Place"),
    "STUDIED_IN": ("Entity", "Place"),
    "HAS_EQUATION": ("MathProblem", "Equation"),
    "EQUATION_SOLVES_TO": ("Equation", "Solution"),
    "HAS_SOLUTION": ("MathProblem", "Solution"),
    "HAS_TREND": ("ForecastCase", "Trend"),
    "TREND_IMPLIES_RISK": ("Trend", "Risk"),
    "FORECAST_RISK": ("ForecastCase", "Risk"),
}

# Family-level constraints.  These make γ(3,4) more than a label.
ALLOWED_GAMMA_TRANSITIONS = {
    "NEAR": {("Event", "Event"), ("Thing", "Thing"), ("Concept", "Concept")},
    "LEADS_TO": {("Event", "Event"), ("Event", "Concept"), ("Concept", "Concept"), ("Concept", "Event")},
    "CONTAINS": {("Thing", "Thing"), ("Thing", "Concept"), ("Event", "Thing")},
    "EXPRESSES": {("Event", "Concept"), ("Event", "Thing"), ("Thing", "Concept"), ("Concept", "Concept")},
}


def gamma_class(node_type: str) -> str:
    return NODE_TYPE_TO_GAMMA_CLASS.get(node_type, "Thing")


def relation_family(relation: str) -> str:
    return RELATION_TO_FAMILY.get(relation, "EXPRESSES")


def gamma_transition_allowed(src_gamma: str, relation: str, dst_gamma: str) -> bool:
    family = relation_family(relation)
    return (src_gamma, dst_gamma) in ALLOWED_GAMMA_TRANSITIONS.get(family, set())


def gamma_transition_reason(src_gamma: str, relation: str, dst_gamma: str) -> str:
    family = relation_family(relation)
    allowed = sorted(ALLOWED_GAMMA_TRANSITIONS.get(family, set()))
    return f"gamma34_family_{family}_disallows_{src_gamma}_to_{dst_gamma}; allowed={allowed}"


def summarize_gamma34(nodes: Iterable, edges: Iterable) -> dict:
    node_counts = Counter(getattr(n, "gamma_class", "Thing") for n in nodes)
    edge_counts = Counter(getattr(e, "relation_family", "EXPRESSES") for e in edges)
    return {
        "node_kinds_used": {k: node_counts.get(k, 0) for k in ["Event", "Thing", "Concept"]},
        "relation_families_used": {k: edge_counts.get(k, 0) for k in ["NEAR", "LEADS_TO", "CONTAINS", "EXPRESSES"]},
        "schema": {
            "gamma_3_node_kinds": ["Event", "Thing", "Concept"],
            "gamma_4_relation_families": ["NEAR", "LEADS_TO", "CONTAINS", "EXPRESSES"],
        },
    }
