from collections import defaultdict
from .constants import PLUGIN_KEY
from .models import MemberRecord


def summarize(records):
    out = defaultdict(lambda: {"qty": 0, "length": 0.0, "weight": 0.0})
    for r in records:
        k = (r.category, r.section, r.layer, r.container)
        out[k]["qty"] += 1
        out[k]["length"] += r.length_m
        out[k]["weight"] += r.weight_kg
    return dict(out)


def collect_scene_records(scene, project=None):
    """Read GO Factory member metadata without recalculating model geometry."""
    records = []
    for g in getattr(scene, "groups", ()):
        meta = (getattr(g, "ext", None) or {}).get(PLUGIN_KEY)
        if not meta or meta.get("kind") != "SteelMember":
            continue
        if project and meta.get("project") != project:
            continue
        start = tuple(meta.get("start", (0.0, 0.0, 0.0)))
        end = tuple(meta.get("end", (0.0, 0.0, 0.0)))
        records.append(MemberRecord(
            getattr(g, "uid", ""),
            str(meta.get("project", "")),
            str(meta.get("mark", "")),
            str(meta.get("category", "")),
            str(getattr(g, "layer", None) or meta.get("layer", "")),
            str(meta.get("section", "")),
            str(meta.get("family", "")),
            start, end,
            float(meta.get("length_m", 0.0)),
            float(meta.get("unit_weight_kg_m", 0.0)),
            str((getattr(g, "ifc", None) or {}).get("class", "IfcMember")),
            str(meta.get("container", "Group")),
        ))
    return records
