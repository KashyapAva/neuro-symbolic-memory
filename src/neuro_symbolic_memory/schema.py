"""γ(3,4)-style schema used by the prototype.

This is a pragmatic implementation of the requested graph typing idea:
- 3 high-level node classes: Thing, Event, Concept
- 4 high-level relation families: LEADS_TO, CONTAINS, EXPRESSES_PROPERTY, NEARTO

Task-specific relations are mapped into these families so the graph remains typed
and auditable while still supporting KGQA, math, RCA, and forecast traces.
"""

NODE_TYPE_TO_GAMMA_CLASS = {
    # Things
    "Entity": "Thing",
    "Place": "Thing",
    "Organization": "Thing",
    "Country": "Thing",
    "City": "Thing",
    "Continent": "Thing",
    "System": "Thing",
    "Metric": "Thing",
    "Risk": "Thing",
    "Cause": "Thing",
    "Variable": "Thing",
    "Solution": "Thing",
    # Events
    "Incident": "Event",
    "ForecastCase": "Event",
    "MathProblem": "Event",
    "Trace": "Event",
    # Concepts
    "Equation": "Concept",
    "Trend": "Concept",
    "Signal": "Concept",
    "Abstraction": "Concept",
}

RELATION_TO_FAMILY = {
    # KGQA / real-world geo
    "HAS_CAPITAL": "EXPRESSES_PROPERTY",
    "LOCATED_IN": "CONTAINS",
    "BORN_IN": "EXPRESSES_PROPERTY",
    "WORKS_AT": "EXPRESSES_PROPERTY",
    "ORG_LOCATED_IN": "CONTAINS",
    "STUDIED_AT": "EXPRESSES_PROPERTY",
    "UNIVERSITY_LOCATED_IN": "CONTAINS",
    "LIVES_IN": "EXPRESSES_PROPERTY",
    "ASSOCIATED_WITH": "NEARTO",
    "WORKS_IN": "NEARTO",
    "STUDIED_IN": "NEARTO",
    "CAPITAL_CONTINENT": "NEARTO",
    # Math
    "HAS_EQUATION": "EXPRESSES_PROPERTY",
    "EQUATION_SOLVES_TO": "LEADS_TO",
    "HAS_SOLUTION": "LEADS_TO",
    # RCA
    "HAS_SIGNAL": "EXPRESSES_PROPERTY",
    "SIGNAL_POINTS_TO": "LEADS_TO",
    "HAS_ROOT_CAUSE": "LEADS_TO",
    # Forecast
    "HAS_TREND": "EXPRESSES_PROPERTY",
    "TREND_IMPLIES_RISK": "LEADS_TO",
    "FORECAST_RISK": "LEADS_TO",
}

ALLOWED_RELATION_TYPES = {
    # Real-world KGQA and generic KGQA
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
    # Math
    "HAS_EQUATION": ("MathProblem", "Equation"),
    "EQUATION_SOLVES_TO": ("Equation", "Solution"),
    "HAS_SOLUTION": ("MathProblem", "Solution"),
    # RCA
    "HAS_SIGNAL": ("Incident", "Signal"),
    "SIGNAL_POINTS_TO": ("Signal", "Cause"),
    "HAS_ROOT_CAUSE": ("Incident", "Cause"),
    # Forecast
    "HAS_TREND": ("ForecastCase", "Trend"),
    "TREND_IMPLIES_RISK": ("Trend", "Risk"),
    "FORECAST_RISK": ("ForecastCase", "Risk"),
}

def gamma_class(node_type: str) -> str:
    return NODE_TYPE_TO_GAMMA_CLASS.get(node_type, "Thing")

def relation_family(relation: str) -> str:
    return RELATION_TO_FAMILY.get(relation, "EXPRESSES_PROPERTY")
