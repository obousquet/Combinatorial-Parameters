from typing import Dict, Any, List
import copy
from collections import defaultdict, deque
import re


LINEAR_TYPES = {"larger", "larger_c", "equivalence"}
BASE_VARIANT = "base"


def graph_label(name: str, max_line_length: int = 26) -> str:
    """Shorten implicit suffixes and balance a long label across two DOT lines."""
    name = re.sub(r"\s+(?:complexity|size)\s*$", "", name, flags=re.IGNORECASE)
    if len(name) <= max_line_length or " " not in name:
        return name

    words = name.split()
    splits = range(1, len(words))
    split = min(
        splits,
        key=lambda index: abs(
            len(" ".join(words[:index])) - len(" ".join(words[index:]))
        ),
    )
    return f"{' '.join(words[:split])}\\n{' '.join(words[split:])}"


def variant_of(relationship: Dict[str, Any]) -> str:
    """Return a value suitable for separating incomparable parameter variants."""
    return relationship.get("variant", BASE_VARIANT)


def relation_endpoints(relationship: Dict[str, Any]) -> tuple[str, str]:
    return relationship["parameter_1_id"], relationship["parameter_2_id"]


def proof_adjacency(
    relationships: List[Dict[str, Any]],
    target_type: str,
    excluded: Dict[str, Any] | None = None,
) -> Dict[str, set[str]]:
    """Build the conservative proof graph for one kind of linear inequality.

    A path proving ``A >= B`` may use only exact inequalities and identities.
    A path proving ``A >= cB`` may additionally use constant-factor inequalities.
    Identities are usable in both directions.  Nonlinear bounds deliberately do
    not enter this graph: composing them does not in general preserve any of
    the six relationship types represented by the database.
    """
    allowed = {"equivalence", "larger"}
    if target_type == "larger_c":
        allowed.add("larger_c")
    elif target_type == "equivalence":
        allowed = {"equivalence"}

    adjacency: Dict[str, set[str]] = defaultdict(set)
    for relationship in relationships:
        if relationship is excluded or relationship["relationship_type"] not in allowed:
            continue
        source, target = relation_endpoints(relationship)
        adjacency[source].add(target)
        if relationship["relationship_type"] == "equivalence":
            adjacency[target].add(source)
    return adjacency


def is_redundant_linear_relation(
    relationship: Dict[str, Any], relationships: List[Dict[str, Any]]
) -> bool:
    """Whether another safe linear proof establishes this direct relationship."""
    relation_type = relationship["relationship_type"]
    if relation_type not in LINEAR_TYPES:
        return False

    source, target = relation_endpoints(relationship)
    adjacency = proof_adjacency(relationships, relation_type, excluded=relationship)
    pending = [source]
    seen = set()
    while pending:
        node = pending.pop()
        if node == target:
            return True
        if node in seen:
            continue
        seen.add(node)
        pending.extend(adjacency[node] - seen)
    return False


def canonical_linear_relations(
    relationships: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Keep one representative for duplicate displayed linear relationships."""
    canonical: Dict[tuple[str, str, str], Dict[str, Any]] = {}
    for relationship in sorted(relationships, key=lambda item: item["id"]):
        if relationship["relationship_type"] not in LINEAR_TYPES:
            continue
        source, target = relation_endpoints(relationship)
        canonical.setdefault((source, target, relationship["relationship_type"]), relationship)
    return list(canonical.values())


def reduced_linear_relations(
    relationships: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Transitive reduction of one variant's linear-dominance preorder.

    This is intentionally a reduction of displayed *direct* facts, not an
    attempt to manufacture new database facts from the transitive closure.
    """
    canonical = canonical_linear_relations(relationships)
    return [
        relationship
        for relationship in canonical
        if not is_redundant_linear_relation(relationship, canonical)
    ]


def hierarchy_ranks(relationships: List[Dict[str, Any]]) -> Dict[str, int]:
    """Assign top-to-bottom ranks after condensing strongly connected components."""
    adjacency = proof_adjacency(relationships, "larger_c")
    vertices = set(adjacency)
    vertices.update(target for targets in adjacency.values() for target in targets)

    # Tarjan's algorithm condenses the preorder to a DAG.  A cycle need not be
    # an identity in the source data, so the individual nodes remain visible.
    index = 0
    indices: Dict[str, int] = {}
    lowlinks: Dict[str, int] = {}
    stack: List[str] = []
    on_stack = set()
    components: List[List[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for neighbour in adjacency[node]:
            if neighbour not in indices:
                visit(neighbour)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbour])
            elif neighbour in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[neighbour])
        if lowlinks[node] == indices[node]:
            component = []
            while True:
                neighbour = stack.pop()
                on_stack.remove(neighbour)
                component.append(neighbour)
                if neighbour == node:
                    break
            components.append(component)

    for vertex in vertices:
        if vertex not in indices:
            visit(vertex)

    component_of = {
        vertex: component_index
        for component_index, component in enumerate(components)
        for vertex in component
    }
    dag: Dict[int, set[int]] = defaultdict(set)
    indegree = {component_index: 0 for component_index in range(len(components))}
    for source, targets in adjacency.items():
        for target in targets:
            source_component = component_of[source]
            target_component = component_of[target]
            if source_component != target_component and target_component not in dag[source_component]:
                dag[source_component].add(target_component)
                indegree[target_component] += 1

    ranks = {component_index: 0 for component_index in indegree}
    queue = deque(component_index for component_index, degree in indegree.items() if degree == 0)
    while queue:
        component = queue.popleft()
        for successor in dag[component]:
            ranks[successor] = max(ranks[successor], ranks[component] + 1)
            indegree[successor] -= 1
            if indegree[successor] == 0:
                queue.append(successor)
    return {vertex: ranks[component_of[vertex]] for vertex in vertices}

def generate(cache) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate nodes and edges for the graph.
    """
    nodes = []
    edges = []
    print('generating graph...')
    arrow_map = {
        "larger": {"arrowhead": "normal", "style": "dashed", "color": "#0074D9"},      # blue
        "larger_c": {"arrowhead": "normal", "style": "dashed", "color": "#FF4136"},   # red
        "equivalence": {"arrowhead": "normal", "style": "dashed", "color": "#2ECC40"}, # green
        "log": {"arrowhead": "normal", "style": "dashed", "color": "#FFDC00"},        # yellow
        "sqrt": {"arrowhead": "normal", "style": "dashed", "color": "#B10DC9"},       # purple
        "inv_log": {"arrowhead": "normal", "style": "dotted", "color": "#FF851B"},   # orange
    }
    category_map = {
        "basic": {"color": "#0074D9", "fillcolor": "#E6F7FF"},         # blue
        "graph-based": {"color": "#7FDBFF", "fillcolor": "#F0FBFF"},   # light blue
        "shattering": {"color": "#2ECC40", "fillcolor": "#E8F8EF"},   # green
        "algebraic": {"color": "#B10DC9", "fillcolor": "#F5E6F7"},    # purple
        "compression": {"color": "#FFDC00", "fillcolor": "#FFFBE6"},  # yellow
        "teaching": {"color": "#FF851B", "fillcolor": "#FFF3E6"},     # orange
        "queries": {"color": "#FF4136", "fillcolor": "#FFE6E6"},      # red
        "holes": {"color": "#AAAAAA", "fillcolor": "#F5F5F5"}         # gray
    }
    shape_map = {
        "none": "octagon",
        "sym": "box",
        "mon": "diamond",
        "pmon": "hexagon",
        "dmon": "ellipse",
        "smon": "doublecircle"
    }
    shape_values = {
        "none": "No special properties", "sym": "Symmetric", "mon": "Monotonic", "pmon": "Piecewise Monotonic", "dmon": "Doubly Monotonic", "smon": "Strictly Monotonic"
        }
    arrow_values = {
        "larger": "A ≥ B", "larger_c": "A ≥ cB", "equivalence": "A = B", "log": "A ≥ c log B", "sqrt": "A ≥ c√B", "inv_log": "A ≥ cB/log n"
        }
    cat_values = cache.get_enum_values("parameters", "category")
    cat_values = {val: display for val, display in cat_values}

    legend = [{"type": "node", "label": t, "text": cat_values[t], **v} for t, v in category_map.items()]
    legend.extend([{"type": "node", "label": t, "text": shape_values[t], "shape": v} for t, v in shape_map.items()])
    legend.extend([{"type": "edge", "label": t, "text": arrow_values[t], **v} for t, v in arrow_map.items()])

    relationships = cache.get_table_entries("relationships")
    relationships_by_variant: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for relationship in relationships:
        relationships_by_variant[variant_of(relationship)].append(relationship)

    # Only the reduced base linear graph defines vertical position.  Variant
    # relations and nonlinear bounds are still displayed, but are overlays:
    # they cannot create false cycles or move a node to an unjustified rank.
    reduced_by_variant = {
        variant: reduced_linear_relations(variant_relationships)
        for variant, variant_relationships in relationships_by_variant.items()
    }
    base_backbone = reduced_by_variant.get(BASE_VARIANT, [])
    ranks = hierarchy_ranks(base_backbone)

    # Add parameter nodes.
    for m in cache.get_table_entries("parameters"):
        category = m.get("category", "unknown")
        color = category_map.get(category, {"color": "#AAAAAA", "fillcolor": "#F5F5F5"})
        mon_type = "none"
        if m.get("symmetric", False):
            mon_type = "sym"
        if m.get("monotonic", False):
            mon_type = "mon"
        if m.get("p_monotonic", False):
            mon_type = "pmon"
        if m.get("doubly_monotonic", False):
            mon_type = "dmon"
        if m.get("strictly_monotonic", False):
            mon_type = "smon"
        shape = shape_map.get(mon_type, "box")
        node = {
            "id": f'#parameters/{m["id"]}',
            "label": graph_label(m.get("name", m.get("short_name", str(m["id"])))),
            "ref": f'#parameters/{m["id"]}',
            "type": "parameter",
            "shape": shape,
            **color,
            "style": "filled",
        }
        relation_ref = f'#parameters/{m.get("short_name", m["id"])}'
        if relation_ref in ranks:
            node["rank"] = ranks[relation_ref]
        nodes.append(node)

    displayed_relationships = []
    for variant, variant_relationships in relationships_by_variant.items():
        reduced_linear = reduced_by_variant[variant]
        nonlinear = [
            relationship
            for relationship in variant_relationships
            if relationship["relationship_type"] not in LINEAR_TYPES
        ]
        displayed_relationships.extend((relationship, variant) for relationship in reduced_linear + nonlinear)

    print(
        "graph relationships: "
        f"{len(relationships)} direct, {len(displayed_relationships)} displayed "
        f"({len(base_backbone)} in the base linear backbone)"
    )
    for r, variant in displayed_relationships:
        _, p1 = cache.lookup(r["parameter_1_id"])
        _, p2 = cache.lookup(r["parameter_2_id"])
        label = ''
        arrow = copy.copy(arrow_map.get(r.get("relationship_type", ""), {
                "arrowhead": "normal",
                "style": "solid",
                "color": "#000000",
            }))
        label_ref = ''
        if r.get("witness"):
            _, w = cache.lookup(r["witness"])
            if w:
                label = w.get("short_name", w.get("name", str(w["id"])))
                label_ref = f'#classes/{w["id"]}'
                arrow = copy.copy(arrow)
                arrow["style"] = "solid"
        edge = {
            "source": f'#parameters/{p1["id"]}',
            "target": f'#parameters/{p2["id"]}',
            "ref": f'#relationships/{r["id"]}',
            "label": label,
            "label_ref": label_ref,
            **arrow
        }
        if variant != BASE_VARIANT or r["relationship_type"] not in LINEAR_TYPES:
            edge["constraint"] = False
        edges.append(edge)
    return {"nodes": nodes, "edges": edges, "legend": legend}
