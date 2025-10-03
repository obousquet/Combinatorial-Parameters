from typing import Dict, Any, List
import copy

def generate(cache) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate nodes and edges for the graph.
    """
    nodes = []
    edges = []
    print('generating graph...')
    values = cache.get_enum_values("relationships", "relationship_type")
    type_map = {v[0]: v[1] for v in values}
    values = cache.get_enum_values("relationships", "variant")
    variant_map = {v[0]: v[1] for v in values}
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
    # Add mathematician nodes
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
        nodes.append({
            "id": f'#parameters/{m["id"]}',
            "label": m.get("name", m.get("short_name", str(m["id"]))),
            "ref": f'#parameters/{m["id"]}',
            "type": "parameter",
            "shape": shape,
            **color,
            "style": "filled",
        })
    for r in cache.get_table_entries("relationships"):
        _, p1 = cache.lookup(r["parameter_1_id"])
        _, p2 = cache.lookup(r["parameter_2_id"])
        label = ''
        arrow = arrow_map.get(r.get("relationship_type", ""),{
                "arrowhead": "normal",
                "style": "solid",
                "color": "#000000",
            })
        label_ref = ''
        if r.get("witness"):
            _, w = cache.lookup(r["witness"])
            if w:
                label = w.get("short_name", w.get("name", str(w["id"])))
                label_ref = f'#classes/{w["id"]}'
                arrow = copy.copy(arrow)
                arrow["style"] = "solid"
        edges.append({
            "source": f'#parameters/{p1["id"]}',
            "target": f'#parameters/{p2["id"]}',
            "ref": f'#relationships/{r["id"]}',
            "label": label,
            "label_ref": label_ref,
            **arrow
        })
    return {"nodes": nodes, "edges": edges}
