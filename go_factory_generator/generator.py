from __future__ import annotations
import math
from collections import defaultdict
from core.group import Group
from core.layers import Layer
from core import bim
from .constants import PLUGIN_KEY, PLUGIN_VERSION, CATEGORY_TO_LAYER
from .geometry import v, make_prototype, place_member
from .models import MemberRecord
from .engineering_core import section_identity
from .truss import main_truss, top_bracing, bottom_bracing, vertical_bracing, sub_truss, truss_nodes


def ensure_layer(scene, name):
    if not any(getattr(x, "name", None) == name for x in scene.layers):
        scene.layers.append(Layer(name))


def purge_project(scene, project_name: str):
    keep = []
    for g in scene.groups:
        meta = (getattr(g, "ext", None) or {}).get(PLUGIN_KEY, {})
        if meta.get("project") == project_name:
            continue
        keep.append(g)
    scene.groups[:] = keep


# --------------------------------------------------------------------------- #
# Roof profiles. A profile is a polyline of (x, z) across the building width
# for one transverse frame. Gable/Mono keep their historic behaviour; the new
# types (Hip, Gambrel, Arched, Sawtooth) are expressed the same way so purlins
# and trusses reuse the interpolation. Hip additionally adds 3D hip rafters.
# --------------------------------------------------------------------------- #
def _arch_profile(W, eave, ridge, seg):
    """Circular arc through (0,eave), (W/2,ridge), (W,eave)."""
    half = W / 2.0
    denom = 2 * (ridge - eave)
    if abs(denom) < 1e-9:
        return [(0, eave), (W, eave)]
    k = (ridge * ridge - eave * eave - half * half) / denom
    R = ridge - k
    pts = []
    for i in range(seg + 1):
        x = W * i / seg
        val = R * R - (x - half) ** 2
        pts.append((x, k + math.sqrt(max(val, 0.0))))
    return pts


def _sawtooth_profile(W, eave, ridge, teeth):
    """Repeated steep glazing face + shallow roof face across the width."""
    pts = []
    tw = W / teeth
    for i in range(teeth):
        x0 = i * tw
        if i == 0:
            pts.append((x0, eave))
        pts.append((x0 + tw * 0.20, ridge))
        pts.append((x0 + tw, eave))
    return pts


def profile_points(roof_type, W, eave, ridge, cfg):
    if roof_type == "Mono-slope":
        return [(0, eave), (W, ridge)]
    if roof_type == "Gambrel":
        mid = eave + (ridge - eave) * 0.60
        return [(0, eave), (W * 0.25, mid), (W / 2, ridge), (W * 0.75, mid), (W, eave)]
    if roof_type == "Arched":
        return _arch_profile(W, eave, ridge, max(6, int(cfg.get("arch_segments", 16))))
    if roof_type == "Sawtooth":
        return _sawtooth_profile(W, eave, ridge, max(1, int(cfg.get("sawtooth_teeth", 3))))
    # Gable and Hip share the transverse gable profile.
    return [(0, eave), (W / 2, ridge), (W, eave)]


def profile_z(pts, x):
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for i in range(len(pts) - 1):
        x0, z0 = pts[i]; x1, z1 = pts[i + 1]
        if x0 - 1e-9 <= x <= x1 + 1e-9:
            t = (x - x0) / max(x1 - x0, 1e-9)
            return z0 + (z1 - z0) * t
    return pts[-1][1]


def roof_z(x, W, eave, ridge, roof_type):
    """Backward-compatible single-point height (Gable / Mono-slope only)."""
    if roof_type == "Mono-slope":
        return eave + (ridge - eave) * (x / W)
    half = W / 2.0
    return ridge - abs(x - half) / max(half, 1e-9) * (ridge - eave)


# ---- Hip helpers: taper the gable frame toward each end and trim purlins ---- #
def hip_frame(y, W, L, eave, ridge, hy):
    """Transverse profile for a hip roof at station y.

    Inside the hip zone (y<hy or y>L-hy) the ridge shortens and lowers so the
    roof tapers to the corner — these shortened common/jack rafters are what
    make the hip read correctly instead of a full gable at every frame.
    """
    if hy <= 1e-9:
        return [(0, eave), (W / 2, ridge), (W, eave)]
    if y <= hy:
        f = y / hy
    elif y >= L - hy:
        f = (L - y) / hy
    else:
        f = 1.0
    half = (W / 2.0) * f
    apex = eave + (ridge - eave) * f
    return [(W / 2 - half, eave), (W / 2, apex), (W / 2 + half, eave)]


def hip_purlin_span(x, W, L, hy):
    """Longitudinal (y) extent where a purlin at width position x exists on a
    hip roof's long face. At the eave (x=0 or W) the purlin runs the full
    length; it shortens toward the ridge where the hip rafters cut it back."""
    if hy <= 1e-9 or W <= 1e-9:
        return (0.0, L)
    inset = hy * (W / 2.0 - abs(x - W / 2.0)) / (W / 2.0)
    inset = max(0.0, min(inset, L / 2.0))
    return (inset, L - inset)


def build_factory(scene, cfg):
    project = cfg["project"]
    purge_project(scene, project)
    for layer in cfg["colors"]:
        ensure_layer(scene, layer)

    sections = cfg["sections"]
    colors = cfg["colors"]
    as_component = cfg["container_mode"] == "Component"
    prototypes = {}
    counters = defaultdict(int)
    records = []

    def next_mark(prefix):
        counters[prefix] += 1
        return f"{prefix}{counters[prefix]:03d}"

    def add(category, role, a, b, prefix, ifc_class="IfcMember", layer=None):
        a, b = v(*a) if not hasattr(a, "x") else a, v(*b) if not hasattr(b, "x") else b
        length = (b - a).length()
        if length < 1e-6:
            return None
        sec = sections[role]
        layer_name = layer or CATEGORY_TO_LAYER[category]
        ensure_layer(scene, layer_name)
        key = (sec.name, round(length, 6), layer_name, tuple(colors[layer_name]))
        proto = prototypes.get(key)
        if proto is None:
            proto = make_prototype(sec, length, colors[layer_name], layer_name, sec.material)
            prototypes[key] = proto
        mark = next_mark(prefix)
        g = place_member(proto, a, b, f"{mark} | {sec.name}", as_component)
        g.layer = layer_name
        g.material = {"color": tuple(colors[layer_name]), "mat": sec.material}
        meta = {
            "plugin_version": PLUGIN_VERSION, "project": project, "kind": "SteelMember",
            "mark": mark, "category": category, "role": role, "section": sec.name,
            "family": sec.family, "length_m": float(length),
            "unit_weight_kg_m": float(sec.unit_weight_kg_m),
            "weight_kg": float(length * sec.unit_weight_kg_m),
            "start": [a.x(), a.y(), a.z()], "end": [b.x(), b.y(), b.z()],
            "container": "Component" if as_component else "Group",
            **section_identity(sec.name),
        }
        g.ext = {PLUGIN_KEY: meta}
        try:
            bim.tag_group(g, ifc_class, mark)
        except Exception:
            pass
        scene.groups.append(g)
        records.append(MemberRecord(g.uid, project, mark, category, layer_name, sec.name, sec.family,
                                    tuple(meta["start"]), tuple(meta["end"]), length,
                                    sec.unit_weight_kg_m, ifc_class, meta["container"]))
        return g

    W, L, eave, ridge = cfg["width"], cfg["length"], cfg["eave"], cfg["ridge"]
    bays = cfg["bays"]
    ys = [L * i / bays for i in range(bays + 1)]
    frame_type = cfg["frame_type"]
    roof_type = cfg["roof_type"]
    pts = profile_points(roof_type, W, eave, ridge, cfg)
    # Trusses only make sense on straight-slope roofs; curved/segmented fall back to rafters.
    truss_ok = roof_type in ("Gable", "Mono-slope")
    hip_zone = roof_type == "Hip"
    cross_zone = roof_type == "Cross Gable"
    hip_sb = float(cfg.get("hip_setback", 1.0))
    hy = min(hip_sb * (W / 2.0), L / 2.0) if hip_zone else 0.0
    use_truss = truss_ok and frame_type in ("Roof Truss", "Hybrid")
    use_rafters = (not use_truss) or frame_type in ("Portal Frame", "Hybrid")

    # When the roof is carried by trusses, secondary members follow the truss
    # chords (not the nominal roof profile) so purlins/bracing stay consistent.
    xs_t = zt_t = zb_t = None
    if use_truss:
        xs_t, zt_t, zb_t = truss_nodes(cfg.get("truss_type", "Pratt"), W, eave, ridge, cfg, cfg["truss_panels"])
    truss_only = use_truss and frame_type == "Roof Truss"
    roof_pts = list(zip(xs_t, zt_t)) if truss_only else pts   # purlins / top bracing
    col_pts = list(zip(xs_t, zb_t)) if truss_only else pts     # columns / girts

    # Columns (support) + optional centre line. Tops follow the (truss) bottom
    # chord so eave/mono-slope/asymmetric roofs get a full-height high-side post.
    for y in ys:
        for x in (0.0, W):
            add("Column", "column", (x, y, 0), (x, y, profile_z(col_pts, x)), "C", "IfcColumn")
        if cfg["center_columns"]:
            ztop = profile_z(col_pts, W / 2)
            add("Column", "column", (W / 2, y, 0), (W / 2, y, ztop), "CC", "IfcColumn")

    # Transverse frame system (one profile polyline per frame station)
    if not cross_zone:
        for y in ys:
            if use_rafters:
                prof = hip_frame(y, W, L, eave, ridge, hy) if hip_zone else pts
                for i in range(len(prof) - 1):
                    add("Rafter", "rafter", (prof[i][0], y, prof[i][1]),
                        (prof[i + 1][0], y, prof[i + 1][1]), "R", "IfcBeam")
            if use_truss:
                main_truss(add, W, eave, ridge, pts, y,
                           cfg["truss_panels"], cfg.get("truss_type", "Pratt"), cfg)

    # Hip rafters + ridge beam (3D extras on the gable profile)
    if hip_zone:
        ra = (W / 2, hy, ridge); rb = (W / 2, L - hy, ridge)
        add("Hip/Valley Rafter", "rafter", ra, rb, "RR", "IfcBeam", layer="GO-FAC-HIP")
        for (cx, cy) in ((0, 0), (W, 0), (0, L), (W, L)):
            apex = (W / 2, hy, ridge) if cy == 0 else (W / 2, L - hy, ridge)
            add("Hip/Valley Rafter", "rafter", (cx, cy, eave), apex, "HR", "IfcBeam", layer="GO-FAC-HIP")

    # Cross gable: main gable (ridge along Y) crossed by a perpendicular wing
    # (ridge along X). Equal slopes make the 4 valleys exact 45-degree lines
    # from the central ridge node to the wing-eave corners; main and wing
    # rafters are trimmed to those valley lines (jack rafters).
    if cross_zone:
        m = (ridge - eave) / max(W / 2.0, 1e-9)
        yc = L / 2.0
        wD = min(W / 2.0, L / 2.0)
        # Main frames: full gable outside the crossing; inside, only the ridge
        # band that stays above the wing roof is exposed (rafters ridge->valley).
        for y in ys:
            dy = abs(y - yc)
            if dy >= wD - 1e-9:
                add("Rafter", "rafter", (0, y, eave), (W / 2, y, ridge), "R", "IfcBeam")
                add("Rafter", "rafter", (W / 2, y, ridge), (W, y, eave), "R", "IfcBeam")
            else:
                zv = ridge - m * dy
                add("Rafter", "rafter", (W / 2 - dy, y, zv), (W / 2, y, ridge), "R", "IfcBeam")
                add("Rafter", "rafter", (W / 2, y, ridge), (W / 2 + dy, y, zv), "R", "IfcBeam")
        # Wing frames (ridge along X): exposed band around yc, rafters ridge->valley.
        nwx = max(2, bays)
        for i in range(nwx + 1):
            xw = W * i / nwx
            ddx = abs(xw - W / 2.0); zv = ridge - m * ddx
            add("Rafter", "rafter", (xw, yc - ddx, zv), (xw, yc, ridge), "R", "IfcBeam")
            add("Rafter", "rafter", (xw, yc, ridge), (xw, yc + ddx, zv), "R", "IfcBeam")
        add("Rafter", "rafter", (0, yc, ridge), (W, yc, ridge), "RR", "IfcBeam")        # wing ridge
        add("Rafter", "rafter", (W / 2, 0, ridge), (W / 2, L, ridge), "RR", "IfcBeam")  # main ridge
        node = (W / 2, yc, ridge)
        for (vx, vy) in ((0, yc - wD), (W, yc - wD), (0, yc + wD), (W, yc + wD)):
            add("Hip/Valley Rafter", "rafter", node, (vx, vy, eave), "V", "IfcBeam", layer="GO-FAC-HIP")

    # Purlins — longitudinal members following the (truss) roof profile
    rows = max(1, cfg["purlin_rows"])
    if not cross_zone:
        purlin_xs = set()
        for i in range(len(roof_pts) - 1):
            x0 = roof_pts[i][0]; x1 = roof_pts[i + 1][0]
            for k in range(rows + 1):
                purlin_xs.add(round(x0 + (x1 - x0) * k / rows, 6))
        for x in sorted(purlin_xs):
            z = profile_z(roof_pts, x)
            y0, y1 = (0.0, L)
            if hip_zone:
                y0, y1 = hip_purlin_span(x, W, L, hy)
            if y1 - y0 > 1e-6:
                add("Purlin", "purlin", (x, y0, z), (x, y1, z), "P", "IfcMember")
        # Hip end faces (the two triangular hips): purlins parallel to the end
        # eave, shortening toward the hip apex, so all 4 roof faces get purlins.
        if hip_zone and hy > 1e-6:
            for j in range(1, rows):
                t = j / rows
                z = eave + (ridge - eave) * t
                xl = (W / 2.0) * t; xr = W - (W / 2.0) * t
                yf = hy * t; yb = L - hy * t
                if xr - xl > 1e-6:
                    add("Purlin", "purlin", (xl, yf, z), (xr, yf, z), "P", "IfcMember")
                    add("Purlin", "purlin", (xl, yb, z), (xr, yb, z), "P", "IfcMember")
    else:
        m = (ridge - eave) / max(W / 2.0, 1e-9); yc = L / 2.0; wD = min(W / 2.0, L / 2.0)
        for i in range(rows + 1):
            x = W * i / rows
            z = ridge - m * abs(x - W / 2.0)
            off = abs(x - W / 2.0)
            add("Purlin", "purlin", (x, 0, z), (x, yc - off, z), "P", "IfcMember")
            add("Purlin", "purlin", (x, yc + off, z), (x, L, z), "P", "IfcMember")
        for i in range(rows + 1):
            y = yc - wD + 2 * wD * i / rows
            z = ridge - m * abs(y - yc)
            off = abs(y - yc)
            add("Purlin", "purlin", (0, y, z), (W / 2.0 - off, y, z), "P", "IfcMember")
            add("Purlin", "purlin", (W / 2.0 + off, y, z), (W, y, z), "P", "IfcMember")

    # Truss bracing and secondary (sub) trusses
    if use_truss:
        if cfg.get("top_bracing"):
            top_bracing(add, xs_t, zt_t, ys, cfg.get("brace_style", "X"))
        if cfg.get("bottom_bracing"):
            bottom_bracing(add, xs_t, zb_t, ys)
        if cfg.get("eave_bracing"):
            vertical_bracing(add, xs_t, zb_t, ys)
        if cfg.get("sub_truss"):
            sub_truss(add, W, eave, ridge, roof_pts, ys, cfg.get("sub_truss_depth", 0.6))

    # Side-wall girts (each side follows its own wall height, e.g. mono-slope)
    h0 = profile_z(col_pts, 0.0); hW = profile_z(col_pts, W)
    for k in range(1, cfg["girt_rows"] + 1):
        add("Girt", "girt", (0, 0, h0 * k / (cfg["girt_rows"] + 1)),
            (0, L, h0 * k / (cfg["girt_rows"] + 1)), "G")
        add("Girt", "girt", (W, 0, hW * k / (cfg["girt_rows"] + 1)),
            (W, L, hW * k / (cfg["girt_rows"] + 1)), "G")

    # X bracing in first and last bay
    if cfg["bracing"] and bays >= 1:
        for y0, y1 in ((ys[0], ys[1]), (ys[-2], ys[-1])):
            for x in (0, W):
                add("Bracing", "bracing", (x, y0, 0), (x, y1, eave), "B")
                add("Bracing", "bracing", (x, y0, eave), (x, y1, 0), "B")

    # Crane runway beams
    if cfg["crane_beam"]:
        z = min(cfg["crane_height"], eave - .25)
        add("Crane Beam", "crane", (0, 0, z), (0, L, z), "CR", "IfcBeam")
        add("Crane Beam", "crane", (W, 0, z), (W, L, z), "CR", "IfcBeam")

    # Mezzanine
    if cfg["mezzanine"]:
        z = cfg["mezz_level"]; mw = min(cfg["mezz_width"], W)
        x0 = (W - mw) / 2; x1 = x0 + mw
        for x in (x0, x1):
            add("Mezzanine Beam", "mezz", (x, 0, z), (x, L, z), "MZ", "IfcBeam")
        for y in ys:
            add("Mezzanine Beam", "mezz", (x0, y, z), (x1, y, z), "MZ", "IfcBeam")

    # End-wall framing with a central opening on each end
    if cfg["endwall_framing"]:
        door_w = min(cfg["door_width"], W * .8); door_h = min(cfg["door_height"], eave * .9)
        cx = W / 2; dl = cx - door_w / 2; dr = cx + door_w / 2
        for endy in (0, L):
            for x in (dl, dr):
                add("End-wall Member", "endwall", (x, endy, 0), (x, endy, door_h), "EW")
            add("End-wall Member", "endwall", (dl, endy, door_h), (dr, endy, door_h), "EW")
            for x in (0, W):
                add("End-wall Member", "endwall", (x, endy, 0), (x, endy, eave), "EW")

    # Gable-end wall framing above the eave (studs + top plate following profile)
    if cfg.get("gable_wall"):
        for endy in (0, L):
            for fx in (W * 0.25, W * 0.5, W * 0.75):
                zt = profile_z(pts, fx)
                if zt - eave > 1e-3:
                    add("Gable Wall Frame", "endwall", (fx, endy, eave), (fx, endy, zt), "GW",
                        layer="GO-FAC-GABLEWALL")
            for i in range(len(pts) - 1):
                add("Gable Wall Frame", "endwall", (pts[i][0], endy, pts[i][1]),
                    (pts[i + 1][0], endy, pts[i + 1][1]), "GW", layer="GO-FAC-GABLEWALL")

    # Skylight / roof-light curbs laid on the roof plane
    if cfg.get("skylight"):
        n = max(1, int(cfg.get("skylight_count", 2)))
        x0 = W * 0.20; x1 = W * 0.35
        z0 = profile_z(pts, x0); z1 = profile_z(pts, x1)
        w = min(2.4, L / max(n + 1, 1) * 0.6)
        for j in range(n):
            yc = L * (j + 1) / (n + 1)
            a = (x0, yc - w / 2, z0); b = (x1, yc - w / 2, z1)
            c = (x1, yc + w / 2, z1); d = (x0, yc + w / 2, z0)
            for (p, q) in ((a, b), (b, c), (c, d), (d, a)):
                add("Skylight", "endwall", p, q, "SK", layer="GO-FAC-SKYLIGHT")

    # Lean-to on selected side
    if cfg["lean_to"]:
        side = -1 if cfg["lean_side"] == "Left" else 1
        x_main = 0 if side < 0 else W
        x_out = x_main + side * cfg["lean_width"]
        z_out = max(2.2, eave - cfg["lean_drop"])
        for y in ys:
            add("Lean-to Member", "lean", (x_out, y, 0), (x_out, y, z_out), "LT", "IfcColumn")
            add("Lean-to Member", "lean", (x_main, y, eave), (x_out, y, z_out), "LT", "IfcBeam")
        for k in range(cfg["purlin_rows"] + 1):
            t = k / max(cfg["purlin_rows"], 1)
            x = x_main + (x_out - x_main) * t; z = eave + (z_out - eave) * t
            add("Lean-to Member", "purlin", (x, 0, z), (x, L, z), "LTP", layer="GO-FAC-LEAN")

    scene.version += 1
    return records
