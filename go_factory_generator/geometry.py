from __future__ import annotations
import math
from PySide6.QtGui import QMatrix4x4, QVector3D, QVector4D
from core.mesh import Mesh
from core.group import Group, transformed_mesh


def v(x, y, z):
    return QVector3D(float(x), float(y), float(z))


def member_frame(a: QVector3D, b: QVector3D) -> QMatrix4x4:
    x = b - a
    if x.length() < 1e-9:
        raise ValueError("zero-length member")
    x = x.normalized()
    ref = QVector3D(0, 0, 1)
    if abs(QVector3D.dotProduct(x, ref)) > .95:
        ref = QVector3D(0, 1, 0)
    y = QVector3D.crossProduct(ref, x).normalized()
    z = QVector3D.crossProduct(x, y).normalized()
    m = QMatrix4x4()
    m.setColumn(0, QVector4D(x, 0.0))
    m.setColumn(1, QVector4D(y, 0.0))
    m.setColumn(2, QVector4D(z, 0.0))
    m.setColumn(3, QVector4D(a, 1.0))
    return m


def _face(mesh, pts, attrs):
    f = mesh.add_face(pts)
    if f is not None:
        f.attrs.update(attrs)
    return f


def _box(mesh, length, width, depth, attrs):
    y = width / 2.0
    z = depth / 2.0
    p = [v(0,-y,-z), v(0,y,-z), v(0,y,z), v(0,-y,z),
         v(length,-y,-z), v(length,y,-z), v(length,y,z), v(length,-y,z)]
    faces = [(0,3,2,1),(4,5,6,7),(0,4,7,3),(1,2,6,5),(0,1,5,4),(3,7,6,2)]
    for q in faces:
        _face(mesh, [p[i] for i in q], attrs)


def _i_section(mesh, length, depth, width, web, flange, attrs):
    _box_offset(mesh, length, width, flange, 0, +(depth-flange)/2, attrs)
    _box_offset(mesh, length, width, flange, 0, -(depth-flange)/2, attrs)
    _box_offset(mesh, length, web, max(depth-2*flange, .001), 0, 0, attrs)


def _box_offset(mesh, length, width, depth, oy, oz, attrs):
    y = width / 2.0
    z = depth / 2.0
    p = [v(0,oy-y,oz-z), v(0,oy+y,oz-z), v(0,oy+y,oz+z), v(0,oy-y,oz+z),
         v(length,oy-y,oz-z), v(length,oy+y,oz-z), v(length,oy+y,oz+z), v(length,oy-y,oz+z)]
    faces = [(0,3,2,1),(4,5,6,7),(0,4,7,3),(1,2,6,5),(0,1,5,4),(3,7,6,2)]
    for q in faces:
        _face(mesh, [p[i] for i in q], attrs)


def _pipe(mesh, length, diameter, t, attrs, seg=16):
    ro = diameter/2.0
    ri = max(ro-t, ro*.55)
    for i in range(seg):
        a0 = 2*math.pi*i/seg; a1 = 2*math.pi*(i+1)/seg
        yo0, zo0 = ro*math.cos(a0), ro*math.sin(a0)
        yo1, zo1 = ro*math.cos(a1), ro*math.sin(a1)
        yi0, zi0 = ri*math.cos(a0), ri*math.sin(a0)
        yi1, zi1 = ri*math.cos(a1), ri*math.sin(a1)
        _face(mesh, [v(0,yo0,zo0),v(length,yo0,zo0),v(length,yo1,zo1),v(0,yo1,zo1)], attrs)
        _face(mesh, [v(0,yi1,zi1),v(length,yi1,zi1),v(length,yi0,zi0),v(0,yi0,zi0)], attrs)
        _face(mesh, [v(0,yi0,zi0),v(0,yo0,zo0),v(0,yo1,zo1),v(0,yi1,zi1)], attrs)
        _face(mesh, [v(length,yi1,zi1),v(length,yo1,zo1),v(length,yo0,zo0),v(length,yi0,zi0)], attrs)


def _angle(mesh, length, depth, width, t, attrs):
    _box_offset(mesh, length, t, depth, -(width-t)/2, 0, attrs)
    _box_offset(mesh, length, width, t, 0, -(depth-t)/2, attrs)


def _channel(mesh, length, depth, width, t, attrs, zed=False):
    _box_offset(mesh, length, t, depth, -width/2+t/2, 0, attrs)
    sign = -1 if zed else 1
    _box_offset(mesh, length, width, t, sign*0, +(depth-t)/2, attrs)
    _box_offset(mesh, length, width, t, -sign*0, -(depth-t)/2, attrs)


def make_prototype(section, length: float, color, layer: str, material: str) -> Mesh:
    mesh = Mesh()
    attrs = {"color": tuple(color), "layer": layer, "mat": material}
    fam = section.family
    if fam == "H":
        _i_section(mesh, length, section.depth_m, section.width_m,
                   max(section.web_m,.003), max(section.flange_m,.004), attrs)
    elif fam in ("C", "Z"):
        _channel(mesh, length, section.depth_m, section.width_m,
                 max(section.thickness_m,.002), attrs, zed=(fam=="Z"))
    elif fam == "L":
        _angle(mesh, length, section.depth_m, section.width_m,
               max(section.thickness_m,.003), attrs)
    elif fam == "PIPE":
        _pipe(mesh, length, section.width_m, max(section.thickness_m,.002), attrs)
    elif fam == "PLATE":
        _box(mesh, length, section.width_m, section.depth_m, attrs)
    else:
        _box(mesh, length, section.width_m, section.depth_m, attrs)
    return mesh


def place_member(prototype: Mesh, a: QVector3D, b: QVector3D, name: str,
                 as_component: bool) -> Group:
    xf = member_frame(a, b)
    if as_component:
        g = Group(prototype, name=name)
        g.xform = xf
        g.component = True
        return g
    return Group(transformed_mesh(prototype, xf), name=name)
