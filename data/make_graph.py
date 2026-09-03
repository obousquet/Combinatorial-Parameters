from typing import Dict, Any, List
import copy
from collections import defaultdict, deque
import re


LINEAR_TYPES = {"larger", "larger_c", "equivalence"}
BASE_VARIANT = "base"
# Exact identities eligible to be represented by one graph node.  This is
# deliberately narrower than every relationship record marked ``equivalence``:
# a qualified identity (for example one holding only for finite classes) must
# remain an edge until the graph has a way to display its scope.
COLLAPSIBLE_EQUIVALENCE_IDS = {
    9,  # Largest shattered set = VC dimension (definition)
    14, 22,  # Projected maximal degree = star number = maximum projected TS
    40, 125, 137,  # Teaching dimension = relative hitting size = maximum TS
    100,  # Equivalence-query complexity = Littlestone dimension
    136,  # Recursive teaching dimension = monotonic minimum teaching-set size
}


def graph_label(name: str, max_line_length: int = 26) -> str:
    """Make graph-only labels compact, then balance them over two DOT lines.

    This leaves catalogue names untouched: the full name remains available in
    the popup and on the parameter page.  The graph uses the conventional
    short forms for recurring qualifiers so its hierarchy is legible without
    depending on obstacle-avoiding edge routes.
    """
    name = re.sub(r"\s+(?:complexity|size)\s*$", "", name, flags=re.IGNORECASE)
    abbreviations = {
        "sample compression": "SC",
        "projected": "Proj",
        "projection": "Proj",
        "maximum": "Max",
        "maximal": "Max",
        "minimum": "Min",
        "monotonic": "Mon",
        "dimension": "Dim",
        "equivalence": "Eq",
        "membership": "Memb",
    }
    for long_form, short_form in abbreviations.items():
        name = re.sub(
            rf"\b{long_form}\b", short_form, name, flags=re.IGNORECASE
        )
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


def is_homogeneous_linear(relationship: Dict[str, Any]) -> bool:
    """Whether a relation is safe for the Hasse-like dominance backbone.

    ``larger_c`` encompasses both homogeneous constant-factor bounds and
    affine bounds.  A nonzero additive term cannot safely impose a vertical
    order or participate in transitive reduction, so it remains an overlay.
    """
    return (
        relationship["relationship_type"] in LINEAR_TYPES
        and not relationship.get("additive_constant")
    )


def exact_equivalence_components(
    parameters: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
) -> tuple[Dict[str, List[str]], Dict[str, str]]:
    """Group parameters joined by stated, base-variant exact equalities.

    A constant-factor relationship is intentionally *not* an equality here.
    Nor is an equality that is asserted only for a parameter variant: merging
    such nodes would incorrectly identify the underlying parameters.
    """
    parent = {
        f'#parameters/{parameter["short_name"]}': f'#parameters/{parameter["short_name"]}'
        for parameter in parameters
        if parameter.get("short_name")
    }

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(first: str, second: str) -> None:
        first_root, second_root = find(first), find(second)
        if first_root != second_root:
            parent[second_root] = first_root

    for relationship in relationships:
        if (
            relationship["relationship_type"] == "equivalence"
            and variant_of(relationship) == BASE_VARIANT
            and relationship["id"] in COLLAPSIBLE_EQUIVALENCE_IDS
        ):
            first, second = relation_endpoints(relationship)
            union(first, second)

    components: Dict[str, List[str]] = defaultdict(list)
    for parameter_ref in parent:
        components[find(parameter_ref)].append(parameter_ref)
    for component in components.values():
        component.sort()

    component_of = {
        parameter_ref: component_root
        for component_root, component in components.items()
        for parameter_ref in component
    }
    return dict(components), component_of


def quotient_relationships(
    relationships: List[Dict[str, Any]], component_of: Dict[str, str]
) -> List[Dict[str, Any]]:
    """Move displayed relationships to equality components before reduction.

    Reducing first is unsound: two relations with endpoints identified by an
    equality can each appear redundant through the other.  On the quotient,
    duplicate component-to-component relations are reduced to one representative
    without losing the resulting relation.
    """
    quotient = []
    for relationship in relationships:
        collapsed = copy.copy(relationship)
        collapsed["_witness_parameter_1_id"] = relationship["parameter_1_id"]
        collapsed["_witness_parameter_2_id"] = relationship["parameter_2_id"]
        source = component_of[relationship["parameter_1_id"]]
        target = component_of[relationship["parameter_2_id"]]
        if source == target:
            continue
        collapsed["parameter_1_id"] = source
        collapsed["parameter_2_id"] = target
        quotient.append(collapsed)
    return quotient


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
        if (
            relationship is excluded
            or relationship["relationship_type"] not in allowed
            or not is_homogeneous_linear(relationship)
        ):
            continue
        source, target = relation_endpoints(relationship)
        adjacency[source].add(target)
        if relationship["relationship_type"] == "equivalence":
            adjacency[target].add(source)
    return adjacency


def rank_adjacency(relationships: List[Dict[str, Any]]) -> Dict[str, set[str]]:
    """Build the dominance graph used solely for vertical placement.

    Every established base-variant affine inequality has the same direction
    of growth as a plain ``A >= B`` relation: if ``A >= c B - d`` with
    ``c>0``, then A belongs no lower than B in the hierarchy.  Additive terms
    prevent a relation from being safely *reduced* as a homogeneous Hasse
    edge, but they do not change that direction.  Consequently ranks use the
    transitive closure of all ``larger`` and ``larger_c`` records, including
    affine ones; exact equalities are traversable in both directions.
    """
    adjacency: Dict[str, set[str]] = defaultdict(set)
    for relationship in relationships:
        relation_type = relationship["relationship_type"]
        if relation_type not in LINEAR_TYPES:
            continue
        source, target = relation_endpoints(relationship)
        adjacency[source].add(target)
        if relation_type == "equivalence":
            adjacency[target].add(source)
    return adjacency


def is_redundant_linear_relation(
    relationship: Dict[str, Any], relationships: List[Dict[str, Any]]
) -> bool:
    """Whether another safe linear proof establishes this direct relationship."""
    relation_type = relationship["relationship_type"]
    if not is_homogeneous_linear(relationship):
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
        if not is_homogeneous_linear(relationship):
            continue
        source, target = relation_endpoints(relationship)
        canonical.setdefault((source, target, relationship["relationship_type"]), relationship)
    return list(canonical.values())


def literal_integer(value: str | None) -> int | None:
    """Return an unambiguous displayed nonnegative integer, if available."""
    if not value:
        return None
    value = value.strip()
    if value.startswith("$") and value.endswith("$"):
        value = value[1:-1].strip()
    return int(value) if re.fullmatch(r"\d+", value) else None


def witness_priority(relationship: Dict[str, Any], exact_values: Dict[tuple[str, str], int]) -> tuple[int, int, int]:
    """Rank a displayed fact by the strength of its witness evidence.

    An unbounded family separation is stronger than a finite strict example.
    Among finite examples, use the literal endpoint gap when it is available.
    The last component gives a stable mathematical-type tie-breaker only; the
    caller resolves the remaining tie by record ID.
    """
    strength = {"unbounded": 2, "strict": 1}.get(
        relationship.get("witness_strength"), 0
    )
    gap = 0
    witness = relationship.get("witness")
    if witness:
        first = exact_values.get((
            witness,
            relationship.get("_witness_parameter_1_id", relationship["parameter_1_id"]),
        ))
        second = exact_values.get((
            witness,
            relationship.get("_witness_parameter_2_id", relationship["parameter_2_id"]),
        ))
        if first is not None and second is not None:
            gap = abs(first - second)
    type_priority = {"larger": 2, "larger_c": 1}.get(
        relationship.get("relationship_type"), 0
    )
    return strength, gap, type_priority


def strongest_displayed_relationships(
    displayed_relationships: List[tuple[Dict[str, Any], str, bool]],
    exact_values: Dict[tuple[str, str], int],
) -> List[tuple[Dict[str, Any], str, bool]]:
    """Keep one graph edge per ordered endpoint pair.

    Several direct facts can become the same pair after equality collapse.
    The graph displays a single witness card for such a pair, so pick the
    strongest supported witness rather than emitting parallel copies.  The
    constraint flag is retained whenever any candidate was a backbone edge.
    """
    selected: Dict[tuple[str, str], tuple[Dict[str, Any], str, bool]] = {}
    for relationship, variant, constrains_layout in displayed_relationships:
        source, target = relation_endpoints(relationship)
        key = (source, target)
        existing = selected.get(key)
        if existing is None:
            selected[key] = (relationship, variant, constrains_layout)
            continue
        previous, _, previous_constraint = existing
        candidate_key = witness_priority(relationship, exact_values) + (-relationship["id"],)
        previous_key = witness_priority(previous, exact_values) + (-previous["id"],)
        chosen = relationship if candidate_key > previous_key else previous
        selected[key] = (chosen, variant, constrains_layout or previous_constraint)
    return sorted(selected.values(), key=lambda item: item[0]["id"])


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
    """Assign ranks from the affine-dominance transitive closure.

    Strongly connected components handle reciprocal bounds without claiming
    that their endpoints are equal parameters.  The longest-path ranks of the
    condensed DAG are exactly the layer numbers induced by the closure.
    """
    adjacency = rank_adjacency(relationships)
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
        "larger_c": {"arrowhead": "normal", "style": "dashed", "color": "#FF4136"},   # red, including affine bounds
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
        "larger": "A ≥ B", "larger_c": "A ≥ cB − d", "equivalence": "A = B", "log": "A ≥ c log B", "sqrt": "A ≥ c√B", "inv_log": "A ≥ cB/log n"
        }
    cat_values = cache.get_enum_values("parameters", "category")
    cat_values = {val: display for val, display in cat_values}

    legend = [{"type": "node", "label": t, "text": cat_values[t], **v} for t, v in category_map.items()]
    legend.extend([{"type": "node", "label": t, "text": shape_values[t], "shape": v} for t, v in shape_map.items()])
    legend.extend([{"type": "edge", "label": t, "text": arrow_values[t], **v} for t, v in arrow_map.items()])
    legend.extend([
        {
            "type": "node",
            "label": "C",
            "text": "Strict-separation witness (refutes the reverse inequality)",
            "shape": "box",
            "color": "#888888",
            "fillcolor": "#f0f0f0",
        },
        {
            "type": "node",
            "label": "C∞",
            "text": "Unbounded-gap witness (rules out every reverse affine-linear bound)",
            "shape": "doubleoctagon",
            "color": "#D35400",
            "fillcolor": "#FFF0D9",
        },
    ])

    parameters = cache.get_table_entries("parameters")
    # Non-established records are retained in the catalogue with their warning
    # and counterexample, but must not create graph edges, influence equality
    # collapse, or affect ranks in the Hasse-like diagram.
    relationships = [
        relationship
        for relationship in cache.get_table_entries("relationships")
        if relationship.get("status") not in {
            "needs_verification", "conjectured", "open", "refuted"
        }
    ]
    equivalence_components, equivalence_component_of = exact_equivalence_components(
        parameters, relationships
    )
    collapsed_relationships = quotient_relationships(
        relationships, equivalence_component_of
    )
    parameters_by_ref = {
        f'#parameters/{parameter["short_name"]}': parameter
        for parameter in parameters
        if parameter.get("short_name")
    }
    relationships_by_variant: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for relationship in collapsed_relationships:
        relationships_by_variant[variant_of(relationship)].append(relationship)

    # The reduced homogeneous graph is the visible Hasse-like backbone.  Ranks
    # are broader: every base-variant affine dominance fact contributes its
    # direction, and the transitive closure is condensed before layering.
    # Thus an $A >= cB-d$ fact need not be drawn as a backbone edge to place A
    # above B.  A homogeneous linear fact that is implied by another displayed
    # path is deliberately absent: it remains in the catalogue and parameter
    # pages, but would only duplicate an arrow in the Hasse-like view.
    reduced_by_variant = {
        variant: reduced_linear_relations(variant_relationships)
        for variant, variant_relationships in relationships_by_variant.items()
    }
    base_backbone = reduced_by_variant.get(BASE_VARIANT, [])
    base_rank_relations = relationships_by_variant.get(BASE_VARIANT, [])
    ranks = hierarchy_ranks(base_rank_relations)

    # Add one node for each exact-equality component.  The first record is the
    # clickable representative; the combined label makes every identification
    # visible without retaining equality arrows or loops.
    for component_root, component in equivalence_components.items():
        # Use the union-find representative for the displayed node as well as
        # every quotient edge.  Choosing the lexicographically first member
        # here would create a node ID different from the endpoints below.
        member_refs = [component_root] + [
            parameter_ref for parameter_ref in component if parameter_ref != component_root
        ]
        members = [parameters_by_ref[parameter_ref] for parameter_ref in member_refs]
        m = members[0]
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
            "label": " /\\n".join(
                graph_label(member.get("name", member.get("short_name", str(member["id"]))))
                for member in members
            ),
            "ref": f'#parameters/{m["id"]}',
            "type": "parameter",
            "shape": shape,
            **color,
            "style": "filled",
        }
        member_ranks = [ranks[member_ref] for member_ref in component if member_ref in ranks]
        if member_ranks:
            node["rank"] = member_ranks[0]
        nodes.append(node)

    displayed_relationships = []
    for variant, variant_relationships in relationships_by_variant.items():
        reduced_linear = reduced_by_variant[variant]
        nonlinear = [
            relationship
            for relationship in variant_relationships
            if not is_homogeneous_linear(relationship)
        ]
        displayed_relationships.extend(
            (relationship, variant, True)
            for relationship in reduced_linear
        )
        # Nonlinear and affine facts cannot safely take part in a homogeneous
        # transitive reduction, so retain them as non-constraining overlays.
        displayed_relationships.extend(
            (relationship, variant, False)
            for relationship in nonlinear
        )

    exact_values = {}
    for value in cache.get_table_entries("values"):
        if value.get("status") != "established":
            continue
        integer = literal_integer(value.get("value"))
        if integer is not None:
            exact_values[(value["class_id"], value["parameter_id"])] = integer
    displayed_relationships = strongest_displayed_relationships(
        displayed_relationships, exact_values
    )

    displayed_edge_keys = set()
    for r, variant, constrains_layout in displayed_relationships:
        source_component, target_component = relation_endpoints(r)
        source = parameters_by_ref[source_component]
        target = parameters_by_ref[target_component]
        if source_component == target_component:
            continue
        edge_key = (source_component, target_component, variant)
        if edge_key in displayed_edge_keys:
            continue
        displayed_edge_keys.add(edge_key)
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
        witness_strength = r.get("witness_strength")
        edge = {
            "source": f'#parameters/{source["id"]}',
            "target": f'#parameters/{target["id"]}',
            "ref": f'#relationships/{r["id"]}',
            "label": label,
            "label_ref": label_ref,
            "witness_strength": witness_strength,
            **arrow
        }
        if witness_strength == "unbounded":
            edge.update({
                "label_shape": "doubleoctagon",
                "label_color": "#D35400",
                "label_fillcolor": "#FFF0D9",
            })
        elif witness_strength == "strict":
            edge.update({
                "label_shape": "box",
                "label_color": "#888888",
                "label_fillcolor": "#f0f0f0",
            })
        if not constrains_layout:
            edge["constraint"] = False
        if label:
            source_rank = ranks.get(source_component)
            target_rank = ranks.get(target_component)
            if source_rank is not None and target_rank is not None and source_rank < target_rank:
                edge["label_rank"] = (source_rank + target_rank) / 2
        edges.append(edge)
    merged_nodes = sum(len(component) - 1 for component in equivalence_components.values())
    print(
        "graph relationships: "
        f"{len(relationships)} direct, {len(edges)} displayed after collapsing "
        f"{merged_nodes} exact-equality parameters ({len(base_backbone)} in the base homogeneous backbone; "
        f"{len(base_rank_relations)} base relations used for affine ranks)"
    )
    return {"nodes": nodes, "edges": edges, "legend": legend}
