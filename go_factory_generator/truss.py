"""Warehouse roof-truss systems for GO Factory Generator.

Main trusses (primary frames across the width) with selectable chord shape and
web pattern, secondary/sub trusses, roof bracing, eave overhang, ceiling
hangers, and per-member section roles (top / bottom / web).

Chord-driven and node-based: ``truss_nodes`` returns the panel points of the top
and bottom chords (including any eave overhang). The generator uses those nodes
for purlins, columns and bracing so every secondary member stays consistent with
the truss shape. All members are emitted through the caller's ``add`` closure so
they share metadata, layers, IFC tagging and undo.
"""
from __future__ import annotations
import math


def _z(pts, x):
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


TRUSS_TYPES = [
    "Pratt", "Howe", "Warren", "Fink",
    "Flat", "Sloping", "Dual-pitch",
    "Curved", "Under-camber", "Camber",
    "Scissor", "Bowstring", "North-light", "Multi-span",
]


def _roof_z(x, W, eave, ridge):
    return ridge - abs(x - W / 2) / max(W / 2, 1e-9) * (ridge - eave)


def _arc_top(x, W, eave, ridge):
    half = W / 2.0
    denom = 2 * (ridge - eave)
    if abs(denom) < 1e-9:
        return eave
    k = (ridge * ridge - eave * eave - half * half) / denom
    R = ridge - k
    return k + math.sqrt(max(R * R - (x - half) ** 2, 0.0))


def _profiles(ttype, W, eave, ridge, depth, rp):
    roof = lambda x: _roof_z(x, W, eave, ridge)
    flat_top = lambda x: ridge
    flat_bot = lambda x: eave
    if ttype == "Flat":
        return flat_top, flat_bot
    if ttype == "Sloping":
        rise = ridge - eave
        bot = lambda x: eave + max(rise - depth, 0.0) * (x / W)
        return (lambda x: bot(x) + depth), bot
    if ttype == "Dual-pitch":
        rp = min(max(rp, 0.15), 0.85)
        def top(x):
            if x <= rp * W:
                return eave + (ridge - eave) * (x / (rp * W))
            return eave + (ridge - eave) * ((W - x) / ((1 - rp) * W))
        return top, flat_bot
    if ttype == "Curved":
        return (lambda x: _arc_top(x, W, eave, ridge)), (lambda x: _arc_top(x, W, eave, ridge - depth))
    if ttype == "Camber":
        return (lambda x: _arc_top(x, W, eave, ridge)), flat_bot
    if ttype == "Under-camber":
        cam = depth
        bot = lambda x: eave + cam * (1 - (2 * x / W - 1) ** 2)
        return flat_top, bot
    if ttype == "Scissor":
        br = eave + 0.55 * (ridge - eave)
        bot = lambda x: br - abs(x - W / 2) / max(W / 2, 1e-9) * (br - eave)
        return roof, bot
    if ttype == "Bowstring":
        return (lambda x: _arc_top(x, W, eave, ridge)), flat_bot
    if ttype == "North-light":
        a = W * 0.12; hlo = eave + (ridge - eave) * 0.65; hhi = ridge; s = W / 2 - a
        def top(x):
            if x <= s:
                return eave + (hlo - eave) * (x / s)
            if x <= W / 2 + a:
                return hhi
            return eave + (hlo - eave) * ((W - x) / s)
        return top, flat_bot
    return roof, flat_bot


def truss_nodes(ttype, W, eave, ridge, cfg, n):
    """Panel points (xs, zt, zb) of the top/bottom chords, extended by the
    eave overhang on both sides. Supports sit at x=0 and x=W."""
    cfg = cfg or {}
    n = max(4, n)
    depth = float(cfg.get("truss_depth", max(0.5, (ridge - eave) * 0.35)))
    rp = float(cfg.get("ridge_pos", 0.35))
    oh = max(0.0, float(cfg.get("eave_overhang", 0.0)))
    topf, botf = _profiles(ttype, W, eave, ridge, depth, rp)
    xs = [W * i / n for i in range(n + 1)]
    zt = [topf(x) for x in xs]
    zb = [botf(x) for x in xs]
    if oh > 1e-9:
        sl = (zt[1] - zt[0]) / max(xs[1] - xs[0], 1e-9)
        sr = (zt[-1] - zt[-2]) / max(xs[-1] - xs[-2], 1e-9)
        bl = (zb[1] - zb[0]) / max(xs[1] - xs[0], 1e-9)
        br_ = (zb[-1] - zb[-2]) / max(xs[-1] - xs[-2], 1e-9)
        xs = [-oh] + xs + [W + oh]
        zt = [zt[0] - sl * oh] + zt + [zt[-1] + sr * oh]
        zb = [zb[0] - bl * oh] + zb + [zb[-1] + br_ * oh]
    return xs, zt, zb


def _interp(xs, vals, x):
    if x <= xs[0]:
        return vals[0]
    if x >= xs[-1]:
        return vals[-1]
    for i in range(len(xs) - 1):
        if xs[i] - 1e-9 <= x <= xs[i + 1] + 1e-9:
            t = (x - xs[i]) / max(xs[i + 1] - xs[i], 1e-9)
            return vals[i] + (vals[i + 1] - vals[i]) * t
    return vals[-1]


def truss_members(ttype, W, eave, ridge, cfg, n):
    """Single source of truth for one truss's members.

    Returns a list of (kind, prefix, x1, z1, x2, z2) in the frame plane (y=0).
    kind ∈ {top, bottom, web, support, hinge, hanger}. main_truss turns these
    into real members; the dialog preview draws the same list, so the preview
    always matches the generated geometry (including Warren/Fink/Scissor webs,
    overhang and hangers).
    """
    cfg = cfg or {}
    n = max(4, n)
    rp = float(cfg.get("ridge_pos", 0.35))
    hanger = bool(cfg.get("hanger")); hlen = float(cfg.get("hanger_length", 0.6))
    xs, zt, zb = truss_nodes(ttype, W, eave, ridge, cfg, n)
    m = len(xs) - 1; mid = m // 2
    mem = []
    for i in range(m):
        mem.append(("top", "TC", xs[i], zt[i], xs[i + 1], zt[i + 1]))
    for i in range(m):
        mem.append(("bottom", "BC", xs[i], zb[i], xs[i + 1], zb[i + 1]))

    if ttype == "Scissor":
        mem.append(("web", "KP", xs[mid], zb[mid], xs[mid], zt[mid]))
        mem.append(("web", "TD", xs[mid], zt[mid], xs[mid // 2], zb[mid // 2]))
        j = mid + (m - mid) // 2
        mem.append(("web", "TD", xs[mid], zt[mid], xs[j], zb[j]))
    elif ttype == "Warren":
        for i in range(m):
            if i % 2 == 0:
                mem.append(("web", "TD", xs[i], zb[i], xs[i + 1], zt[i + 1]))
            else:
                mem.append(("web", "TD", xs[i], zt[i], xs[i + 1], zb[i + 1]))
        mem.append(("web", "TW", xs[mid], zb[mid], xs[mid], zt[mid]))
    elif ttype == "Fink":
        mem.append(("web", "TD", xs[mid], zt[mid], W * 0.25, eave))
        mem.append(("web", "TD", xs[mid], zt[mid], W * 0.75, eave))
        mem.append(("web", "TD", W * 0.25, eave, W * 0.125, _interp(xs, zt, W * 0.125)))
        mem.append(("web", "TD", W * 0.75, eave, W * 0.875, _interp(xs, zt, W * 0.875)))
        mem.append(("web", "TD", W * 0.25, eave, W * 0.375, _interp(xs, zt, W * 0.375)))
        mem.append(("web", "TD", W * 0.75, eave, W * 0.625, _interp(xs, zt, W * 0.625)))
    else:
        if ttype == "Multi-span":
            mem.append(("support", "SUP", xs[mid], 0.0, xs[mid], zb[mid]))
            for h in (xs[mid // 2], xs[mid + (m - mid) // 2]):
                mem.append(("hinge", "HG", h, zb[mid // 2] - 0.15, h, zb[mid // 2] + 0.15))
        if ttype == "Howe":
            for i in range(1, m):
                mem.append(("web", "TW", xs[i], zb[i], xs[i], zt[i]))
            for i in range(m):
                if i < mid:
                    mem.append(("web", "TD", xs[i], zb[i], xs[i + 1], zt[i + 1]))
                else:
                    mem.append(("web", "TD", xs[i + 1], zb[i + 1], xs[i], zt[i]))
        else:
            for i in range(1, m):
                mem.append(("web", "TW", xs[i], zb[i], xs[i], zt[i]))
            for i in range(m):
                if i < mid:
                    mem.append(("web", "TD", xs[i], zt[i], xs[i + 1], zb[i + 1]))
                else:
                    mem.append(("web", "TD", xs[i + 1], zt[i + 1], xs[i], zb[i]))

    if hanger:
        for i in range(1, m):
            mem.append(("hanger", "HG", xs[i], zb[i], xs[i], zb[i] - hlen))
    return mem


def main_truss(add, W, eave, ridge, pts, y, n, ttype, cfg=None):
    """One primary truss spanning the width at frame station y."""
    cfg = cfg or {}
    top_role = cfg.get("truss_top_role", "truss_top")
    bot_role = cfg.get("truss_bottom_role", "truss_bottom")
    web_role = cfg.get("truss_web_role", "truss_web")
    role_of = {"top": top_role, "bottom": bot_role, "web": web_role,
               "support": top_role, "hinge": web_role, "hanger": web_role}
    ifc_of = {"top": "IfcBeam", "bottom": "IfcBeam", "support": "IfcColumn"}
    for kind, prefix, x1, z1, x2, z2 in truss_members(ttype, W, eave, ridge, cfg, n):
        add("Main Truss", role_of[kind], (x1, y, z1), (x2, y, z2), prefix, ifc_of.get(kind, "IfcMember"))


def top_bracing(add, xs, zt, ys, style="X"):
    """Ridge/eave struts + X or staggered bracing in the roof planes, using the
    actual top-chord nodes."""
    pk = max(range(len(zt)), key=lambda i: zt[i])
    for j in range(len(ys) - 1):
        y0, y1 = ys[j], ys[j + 1]
        add("Roof Bracing", "bracing", (xs[pk], y0, zt[pk]), (xs[pk], y1, zt[pk]), "RS", "IfcStrut")
        add("Roof Bracing", "bracing", (xs[0], y0, zt[0]), (xs[0], y1, zt[0]), "ES", "IfcStrut")
        add("Roof Bracing", "bracing", (xs[-1], y0, zt[-1]), (xs[-1], y1, zt[-1]), "ES", "IfcStrut")
        if style == "Staggered":
            if j % 2 == 0:
                add("Roof Bracing", "bracing", (xs[pk], y0, zt[pk]), (xs[0], y1, zt[0]), "RB")
                add("Roof Bracing", "bracing", (xs[pk], y0, zt[pk]), (xs[-1], y1, zt[-1]), "RB")
            else:
                add("Roof Bracing", "bracing", (xs[0], y0, zt[0]), (xs[pk], y1, zt[pk]), "RB")
                add("Roof Bracing", "bracing", (xs[-1], y0, zt[-1]), (xs[pk], y1, zt[pk]), "RB")
        else:
            add("Roof Bracing", "bracing", (xs[pk], y0, zt[pk]), (xs[0], y1, zt[0]), "RB")
            add("Roof Bracing", "bracing", (xs[0], y0, zt[0]), (xs[pk], y1, zt[pk]), "RB")
            add("Roof Bracing", "bracing", (xs[pk], y0, zt[pk]), (xs[-1], y1, zt[-1]), "RB")
            add("Roof Bracing", "bracing", (xs[-1], y0, zt[-1]), (xs[pk], y1, zt[pk]), "RB")


def bottom_bracing(add, xs, zb, ys):
    """X-bracing in the horizontal ceiling (bottom-chord) plane."""
    for j in range(len(ys) - 1):
        y0, y1 = ys[j], ys[j + 1]
        add("Roof Bracing", "bracing", (xs[0], y0, zb[0]), (xs[-1], y1, zb[-1]), "BB")
        add("Roof Bracing", "bracing", (xs[-1], y0, zb[-1]), (xs[0], y1, zb[0]), "BB")


def vertical_bracing(add, xs, zb, ys):
    """Edge / vertical-plane X-bracing along both eave lines, every bay."""
    for j in range(len(ys) - 1):
        y0, y1 = ys[j], ys[j + 1]
        for xe, ze in ((xs[0], zb[0]), (xs[-1], zb[-1])):
            add("Roof Bracing", "bracing", (xe, y0, 0), (xe, y1, ze), "VB")
            add("Roof Bracing", "bracing", (xe, y1, 0), (xe, y0, ze), "VB")


def sub_truss(add, W, eave, ridge, pts, ys, depth=0.6, positions=(0.25, 0.75)):
    """Secondary trusses spanning between adjacent main trusses at given
    width fractions, carrying the purlins."""
    for frac in positions:
        x = W * frac
        zt = _z(pts, x); zb = zt - max(depth, 0.1)
        for j in range(len(ys) - 1):
            y0, y1 = ys[j], ys[j + 1]
            add("Sub Truss", "truss", (x, y0, zt), (x, y1, zt), "STC", "IfcBeam")
            add("Sub Truss", "truss", (x, y0, zb), (x, y1, zb), "STB", "IfcBeam")
            add("Sub Truss", "truss", (x, y0, zb), (x, y1, zt), "STD")
