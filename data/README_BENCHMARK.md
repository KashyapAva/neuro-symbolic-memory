# External KGQA Benchmark File

`external_geo_kgqa.csv` is a small packaged real-world KGQA-style benchmark using actual country, capital, and continent facts.

The benchmark task is compositional:

Country --HAS_CAPITAL--> Capital --LOCATED_IN--> Continent

The memory engine learns the shortcut relation:

Country --CAPITAL_CONTINENT--> Continent

This is intentionally lightweight so the project can be run offline, but it is no longer only the synthetic Alice/Bob toy setup. It is a real-world external-domain benchmark file included with the repository.
