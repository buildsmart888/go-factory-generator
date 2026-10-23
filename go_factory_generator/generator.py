from __future__ import annotations
import math
from collections import defaultdict
from dataclasses import asdict
from core.group import Group
from core.layers import Layer
from core import bim
from .constants import PLUGIN_KEY, PLUGIN_VERSION, CATEGORY_TO_LAYER
from .geometry import v, make_prototype, place_member
from .models import MemberRecord


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


def roof_z(x, W, eave, ridge, roof_type):
    if roof_type == "Mono-slope":
        return eave + (ridge-eave) * (x/W)
    half = W/2.0
    return ridge - abs(x-half)/max(half,1e-9) * (ridge-eave)


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
        length = (b-a).length()
        if length < 1e-6:
            return None
        sec = sections[role]
        layer_name = layer or CATEGORY_TO_LAYER[category]
        ensure_layer(scene, layer_name)
        key = (sec.name, round(length,6), layer_name, tuple(colors[layer_name]))
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
            "weight_kg": float(length*sec.unit_weight_kg_m),
            "start": [a.x(),a.y(),a.z()], "end": [b.x(),b.y(),b.z()],
            "container": "Component" if as_component else "Group",
        }
        g.ext = {PLUGIN_KEY: meta}
        try: bim.tag_group(g, ifc_class, mark)
        except Exception: pass
        scene.groups.append(g)
        records.append(MemberRecord(g.uid, project, mark, category, layer_name, sec.name, sec.family,
                                    tuple(meta["start"]), tuple(meta["end"]), length,
                                    sec.unit_weight_kg_m, ifc_class, meta["container"]))
        return g

    W,L,eave,ridge = cfg["width"],cfg["length"],cfg["eave"],cfg["ridge"]
    bays = cfg["bays"]
    ys = [L*i/bays for i in range(bays+1)]
    frame_type = cfg["frame_type"]
    roof_type = cfg["roof_type"]

    for y in ys:
        for x in (0.0,W):
            add("Column","column",(x,y,0),(x,y,eave),"C","IfcColumn")
        if cfg["center_columns"]:
            ztop = roof_z(W/2,W,eave,ridge,roof_type)
            add("Column","column",(W/2,y,0),(W/2,y,ztop),"CC","IfcColumn")

    for y in ys:
        if roof_type == "Mono-slope":
            roof_pts = [v(0,y,eave), v(W,y,ridge)]
            add("Rafter","rafter",roof_pts[0],roof_pts[1],"R","IfcBeam")
        else:
            roof_pts = [v(0,y,eave),v(W/2,y,ridge),v(W,y,eave)]
            if frame_type in ("Portal Frame","Hybrid"):
                add("Rafter","rafter",roof_pts[0],roof_pts[1],"R","IfcBeam")
                add("Rafter","rafter",roof_pts[1],roof_pts[2],"R","IfcBeam")
            if frame_type in ("Roof Truss","Hybrid"):
                add("Truss","truss",roof_pts[0],roof_pts[1],"TC")
                add("Truss","truss",roof_pts[1],roof_pts[2],"TC")
                add("Truss","truss",(0,y,eave),(W,y,eave),"BC")
                n=max(2,cfg["truss_panels"])
                for i in range(n+1):
                    x=W*i/n; z=roof_z(x,W,eave,ridge,roof_type)
                    add("Truss","truss",(x,y,eave),(x,y,z),"TW")
                for i in range(n):
                    x0=W*i/n; x1=W*(i+1)/n
                    z1=roof_z(x1,W,eave,ridge,roof_type)
                    if i%2==0: add("Truss","truss",(x0,y,eave),(x1,y,z1),"TD")
                    else: add("Truss","truss",(x0,y,roof_z(x0,W,eave,ridge,roof_type)),(x1,y,eave),"TD")

    rows=max(1,cfg["purlin_rows"])
    roof_xs=[]
    if roof_type == "Mono-slope":
        roof_xs=[W*i/rows for i in range(rows+1)]
    else:
        for side in ((0,W/2),(W/2,W)):
            for i in range(rows+1):
                roof_xs.append(side[0]+(side[1]-side[0])*i/rows)
    for x in sorted(set(round(x,6) for x in roof_xs)):
        add("Purlin","purlin",(x,0,roof_z(x,W,eave,ridge,roof_type)),
            (x,L,roof_z(x,W,eave,ridge,roof_type)),"P","IfcMember")

    for k in range(1,cfg["girt_rows"]+1):
        z=eave*k/(cfg["girt_rows"]+1)
        add("Girt","girt",(0,0,z),(0,L,z),"G")
        add("Girt","girt",(W,0,z),(W,L,z),"G")

    if cfg["bracing"] and bays>=1:
        for y0,y1 in ((ys[0],ys[1]),(ys[-2],ys[-1])):
            for x in (0,W):
                add("Bracing","bracing",(x,y0,0),(x,y1,eave),"B")
                add("Bracing","bracing",(x,y0,eave),(x,y1,0),"B")

    if cfg["crane_beam"]:
        z=min(cfg["crane_height"],eave-.25)
        add("Crane Beam","crane",(0,0,z),(0,L,z),"CR","IfcBeam")
        add("Crane Beam","crane",(W,0,z),(W,L,z),"CR","IfcBeam")

    if cfg["mezzanine"]:
        z=cfg["mezz_level"]; mw=min(cfg["mezz_width"],W)
        x0=(W-mw)/2; x1=x0+mw
        for x in (x0,x1):
            add("Mezzanine Beam","mezz",(x,0,z),(x,L,z),"MZ","IfcBeam")
        for y in ys:
            add("Mezzanine Beam","mezz",(x0,y,z),(x1,y,z),"MZ","IfcBeam")

    if cfg["endwall_framing"]:
        door_w = min(cfg["door_width"], W*.8); door_h=min(cfg["door_height"],eave*.9)
        cx=W/2; dl=cx-door_w/2; dr=cx+door_w/2
        for endy in (0,L):
            for x in (dl,dr):
                add("End-wall Member","endwall",(x,endy,0),(x,endy,door_h),"EW")
            add("End-wall Member","endwall",(dl,endy,door_h),(dr,endy,door_h),"EW")
            for x in (0,W):
                add("End-wall Member","endwall",(x,endy,0),(x,endy,eave),"EW")

    if cfg["lean_to"]:
        side = -1 if cfg["lean_side"]=="Left" else 1
        x_main = 0 if side<0 else W
        x_out = x_main + side*cfg["lean_width"]
        z_out = max(2.2,eave-cfg["lean_drop"])
        for y in ys:
            add("Lean-to Member","lean",(x_out,y,0),(x_out,y,z_out),"LT","IfcColumn")
            add("Lean-to Member","lean",(x_main,y,eave),(x_out,y,z_out),"LT","IfcBeam")
        for k in range(cfg["purlin_rows"]+1):
            t=k/max(cfg["purlin_rows"],1)
            x=x_main+(x_out-x_main)*t; z=eave+(z_out-eave)*t
            add("Lean-to Member","purlin",(x,0,z),(x,L,z),"LTP", layer="GO-FAC-LEAN")

    scene.version += 1
    return records
