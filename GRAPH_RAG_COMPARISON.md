# Difference from Graph RAG

A typical Graph RAG system retrieves graph/text context and passes it to a generator.

This prototype instead treats the graph as **mutable semantic memory**:

1. Resolved traces create candidate memories.
2. Candidate memories are type/proof validated.
3. Similar solved cases and learned patterns create provisional hypotheses.
4. Future outcome traces promote or contradict those hypotheses.
5. Updated memory is persisted and replayed.

The graph is therefore not only retrieval context; it is an audited memory state that changes over time.
