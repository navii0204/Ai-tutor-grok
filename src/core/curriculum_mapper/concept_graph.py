"""In-memory concept graph backed by networkx for prerequisite/successor traversal.

Scalability note: For >10k concepts (university-level), replace networkx with
a graph DB (Neo4j) or a simple adjacency-list in Postgres with recursive CTEs.
"""

from __future__ import annotations

from typing import Any

import networkx as nx

from src.core.logging_config import get_logger
from .interfaces import ConceptNode

log = get_logger(__name__)


class ConceptGraph:
    """Directed acyclic graph of curriculum concepts.

    Edges point FROM prerequisite TO dependent concept.
    """

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._nodes: dict[str, ConceptNode] = {}

    def add_concept(self, node: ConceptNode) -> None:
        self._nodes[node.id] = node
        self._graph.add_node(node.id, **{"name": node.name, "grade": node.grade})
        for prereq_id in node.prerequisites:
            self._graph.add_edge(prereq_id, node.id)

    def add_concepts(self, nodes: list[ConceptNode]) -> None:
        for node in nodes:
            self.add_concept(node)

    def get_concept(self, concept_id: str) -> ConceptNode | None:
        return self._nodes.get(concept_id)

    def get_prerequisites(self, concept_id: str) -> list[str]:
        if concept_id not in self._graph:
            return []
        return list(self._graph.predecessors(concept_id))

    def get_all_prerequisites(self, concept_id: str) -> list[str]:
        """All transitive prerequisites in topological order."""
        if concept_id not in self._graph:
            return []
        try:
            ancestors = list(nx.ancestors(self._graph, concept_id))
            subgraph = self._graph.subgraph(ancestors)
            return list(nx.topological_sort(subgraph))
        except nx.NetworkXError:
            return []

    def get_next_concepts(self, concept_id: str, mastered: set[str]) -> list[str]:
        """Return successors whose prerequisites are all mastered."""
        if concept_id not in self._graph:
            return []
        successors = list(self._graph.successors(concept_id))
        ready = []
        for s in successors:
            prereqs = set(self._graph.predecessors(s))
            if prereqs.issubset(mastered):
                ready.append(s)
        return ready

    def get_learning_path(
        self, from_id: str, to_id: str
    ) -> list[str]:
        """Shortest prerequisite path from one concept to another."""
        try:
            return list(nx.shortest_path(self._graph, from_id, to_id))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def list_concepts_for_grade(
        self, grade: str, subject: str | None = None
    ) -> list[ConceptNode]:
        result = [
            node
            for node in self._nodes.values()
            if (not grade or node.grade == grade)
            and (subject is None or node.subject == subject)
        ]
        return sorted(result, key=lambda n: n.name)

    def concept_count(self) -> int:
        return len(self._nodes)
