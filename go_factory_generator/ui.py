from __future__ import annotations
import csv
import json
import math
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox,QColorDialog,QComboBox,QDialog,QDoubleSpinBox,
    QFileDialog,QFormLayout,QGridLayout,QHeaderView,QHBoxLayout,QLabel,QLineEdit,QMessageBox,
    QPushButton,QScrollArea,QSpinBox,QTabWidget,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget)
from core.history import SnapshotImport
from .constants import LAYER_COLORS, PLUGIN_VERSION
from .sections import SECTION_LIBRARY, DEFAULT_SECTION_BY_ROLE
from .engineering_core import catalog_info
from .generator import build_factory
from .truss import TRUSS_TYPES, truss_nodes, truss_members, _interp
from .takeoff import summarize, collect_scene_records

ROOF_TYPES = ["Gable", "Mono-slope", "Hip", "Gambrel", "Arched", "Sawtooth", "Cross Gable"]


def dbl(v,lo,hi,step=.1):
    w=QDoubleSpinBox(); w.setRange(lo,hi); w.setValue(v); w.setSingleStep(step); w.setDecimals(3); return w

def integer(v,lo,hi):
    w=QSpinBox(); w.setRange(lo,hi); w.setValue(v); return w

class _TrussPreview(QWidget):
    """Live truss preview: elevation (chords + real web + supports + hangers +
    purlins) with part labels and dimensions, a layer legend, and a plan inset
    showing the bracing pattern. Driven by truss_members() so it matches the model."""
    COLORS = {"top": "#1a5fb4", "bottom": "#26a269", "web": "#e66100",
              "support": "#1a5fb4", "hinge": "#c01c28", "hanger": "#8b3fb0"}
    def __init__(self, data_fn, parent=None):
        super().__init__(parent); self.data_fn=data_fn; self.setMinimumHeight(250)
    @staticmethod
    def _lc(name):
        r,g,b=LAYER_COLORS[name]; return QColor(int(r*255),int(g*255),int(b*255))
    def _arrow(self, p, x, y, dx, dy):
        import math as _m
        a=_m.atan2(dy,dx); s=6
        for t in (a+2.6, a-2.6):
            p.drawLine(int(x),int(y),int(x+s*_m.cos(t)),int(y+s*_m.sin(t)))
    def _label(self, p, x, y, text, col="#333"):
        p.setPen(QColor(col)); p.drawText(int(x), int(y), text)
    def paintEvent(self, _e):
        from PySide6.QtGui import QPolygon
        from PySide6.QtCore import QPoint
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing, True)
        w=self.width(); h=self.height()
        p.fillRect(0,0,w,h,QColor("#f7f8fa"))
        try: d=self.data_fn()
        except Exception: d=None
        if not d or not d.get("mem"):
            p.setPen(QColor("#888")); p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "—"); p.end(); return
        mem=d["mem"]; W=d["W"]; eave=d["eave"]; ridge=d["ridge"]; oh=d["oh"]
        purlin_col=self._lc("GO-FAC-PURLIN"); brace_col=self._lc("GO-FAC-ROOFBRACE")
        # ---- ELEVATION ----
        ex0=40; ex1=int(w*0.60); ey0=42; ey1=h-70
        xs=[c for k,_,x1,z1,x2,z2 in mem for c in (x1,x2)]
        zs=[c for k,_,x1,z1,x2,z2 in mem for c in (z1,z2)]
        xmin=min(xs+[0.0]); xmax=max(xs+[W]); zmin=min(zs); zmax=max(zs)
        if zmax-zmin<1e-6: zmax=zmin+1.0
        sx=(ex1-ex0)/(xmax-xmin); sy=(ey1-ey0)/(zmax-zmin)
        def px(x): return ex0+(x-xmin)*sx
        def py(z): return ey1-(z-zmin)*sy
        for k,_,x1,z1,x2,z2 in mem:
            if k=="hinge":
                p.setBrush(QColor(self.COLORS["hinge"])); p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(int(px(x1))-3,int(py((z1+z2)/2))-3,6,6); continue
            p.setPen(QPen(QColor(self.COLORS.get(k,"#888")), 3 if k in ("top","bottom") else 1.6))
            p.drawLine(int(px(x1)),int(py(z1)),int(px(x2)),int(py(z2)))
        # purlin dots on top-chord nodes (purlin layer colour)
        topn=sorted({(round(x1,3),round(z1,3)) for k,_,x1,z1,x2,z2 in mem if k=="top"} |
                    {(round(x2,3),round(z2,3)) for k,_,x1,z1,x2,z2 in mem if k=="top"})
        p.setBrush(purlin_col); p.setPen(QPen(QColor("#ffffff"),1))
        for x,z in topn: p.drawEllipse(int(px(x))-3,int(py(z))-3,6,6)
        # supports
        p.setBrush(QColor("#444")); p.setPen(QPen(QColor("#444")))
        for sx0 in (0.0, W):
            bx=px(sx0); by=py(eave)
            p.drawPolygon(QPolygon([QPoint(int(bx),int(by)),QPoint(int(bx)-7,int(by)+12),QPoint(int(bx)+7,int(by)+12)]))
        # ---- part labels ----
        f=p.font(); f.setPointSize(9); p.setFont(f)
        midx=W/2.0
        self._label(p, px(W*0.22)-14, py(_interp_top(mem,W*0.22))-8, "Top chord", self.COLORS["top"])
        self._label(p, px(W*0.30), py(eave)-8, "Bottom chord", self.COLORS["bottom"])
        self._label(p, px(W*0.40), py((eave+ridge)/2), "Web", self.COLORS["web"])
        if topn:
            px0,pz0=topn[len(topn)//2]
            self._label(p, px(px0)+6, py(pz0)-8, "Purlin", purlin_col.name())
        hg=[m for m in mem if m[0]=="hanger"]
        if hg:
            self._label(p, px(hg[0][2])+6, py(hg[0][4])+12, "Hanger", self.COLORS["hanger"])
        # ---- dimensions ----
        p.setPen(QColor("#555"))
        yb=ey1+20
        p.drawLine(int(px(0)),int(yb),int(px(W)),int(yb)); self._arrow(p,px(0),yb,-1,0); self._arrow(p,px(W),yb,1,0)
        p.drawText(int((px(0)+px(W))/2-30), int(yb)+13, f"Span {W:g} m")
        xe=ex0-24; p.drawLine(int(xe),int(py(zmin)),int(xe),int(py(eave)))
        p.drawText(int(xe)-2, int(py(eave))-6, f"Eave {eave:g}")
        xr=px(W)+14; p.drawLine(int(xr),int(py(eave)),int(xr),int(py(ridge)))
        p.drawText(int(xr)+3, int((py(eave)+py(ridge))/2), f"Rise {ridge-eave:g}")
        if oh>1e-6: p.drawText(int(px(-oh))-4, int(py(eave))+26, f"ovh {oh:g}")
        # header
        f.setPointSize(10); f.setBold(True); p.setFont(f); p.setPen(QColor("#1a1a1a"))
        p.drawText(ex0, 16, f"{d['ttype']}  ·  panels={d['panels']}  ·  bays={d['bays']}")
        # ---- PLAN inset (bracing) ----
        f.setBold(False); f.setPointSize(9); p.setFont(f)
        bx0=int(w*0.66); by0=48; bw=int(w*0.32); bh=int(h*0.5)
        p.setPen(QColor("#888")); p.drawRect(bx0,by0,bw,bh)
        p.setPen(QColor("#333")); p.drawText(bx0, by0-6, "Plan — bracing")
        nb=min(max(d["bays"],2),6)+1
        gx=[bx0+bw*k/(nb-1) for k in range(nb)]
        p.setPen(QPen(QColor("#26a269"),2))
        for x in gx: p.drawLine(int(x),by0,int(x),by0+bh)
        p.setPen(QPen(brace_col,1.8))
        for k in range(nb-1):
            x0,x1=gx[k],gx[k+1]
            if d["brace_style"]=="Staggered":
                if k%2==0: p.drawLine(int(x0),by0,int(x1),by0+bh)
                else: p.drawLine(int(x0),by0+bh,int(x1),by0)
            else:
                p.drawLine(int(x0),by0,int(x1),by0+bh); p.drawLine(int(x0),by0+bh,int(x1),by0)
        en=[]
        if d["top_brace"]: en.append("top")
        if d["bottom_brace"]: en.append("bottom")
        if d["eave_brace"]: en.append("edge")
        p.setPen(QColor("#555"))
        p.drawText(bx0, by0+bh+16, f"{d['brace_style']} · on: {', '.join(en) if en else 'none'}")
        # ---- layer legend (bottom) ----
        ly=h-16; lx=ex0
        items=[("Top/Bottom/Web", self.COLORS["top"], "GO-FAC-TRUSS"),
               ("Purlin", purlin_col.name(), "GO-FAC-PURLIN"),
               ("Bracing", brace_col.name(), "GO-FAC-ROOFBRACE")]
        f.setPointSize(8); p.setFont(f)
        for name,col,layer in items:
            p.setPen(QPen(QColor(col),3)); p.drawLine(int(lx),int(ly-4),int(lx+18),int(ly-4))
            p.setPen(QColor("#444")); p.drawText(int(lx+22), int(ly), f"{name} · {layer}")
            lx += 22 + 7*len(f"{name} · {layer}") + 22
        p.end()


def _interp_top(mem, x):
    # rough top-chord height at x for label placement
    pts=sorted({(x1,z1) for k,_,x1,z1,x2,z2 in mem if k=="top"} | {(x2,z2) for k,_,x1,z1,x2,z2 in mem if k=="top"})
    if not pts: return 0.0
    xs=[p[0] for p in pts]; zs=[p[1] for p in pts]
    return _interp(xs,zs,x)


class FactoryDialog(QDialog):
    def __init__(self, viewport):
        super().__init__(viewport.window()); self.viewport=viewport; self.records=[]
        self.setWindowTitle(f"GO Engineering — Factory Generator v{PLUGIN_VERSION}")
        self.resize(1080, 760); self.setMinimumSize(820, 560); self._build()

    def _scroll(self, inner):
        sa=QScrollArea(); sa.setWidget(inner); sa.setWidgetResizable(True)
        sa.setFrameShape(QScrollArea.Shape.NoFrame)
        return sa

    def _build(self):
        self.setStyleSheet(
            "QDialog{font-size:14px;}"
            "QLabel{font-size:14px;}"
            "QLineEdit,QDoubleSpinBox,QSpinBox,QComboBox{font-size:14px;min-height:26px;padding:2px 6px;}"
            "QCheckBox{font-size:14px;spacing:8px;}"
            "QPushButton{font-size:14px;padding:7px 14px;}"
            "QTabBar::tab{font-size:14px;padding:9px 16px;}"
            "QTableWidget,QHeaderView{font-size:13px;}"
        )
        root=QVBoxLayout(self)
        root.addWidget(QLabel(f"<b>GO Factory Generator v{PLUGIN_VERSION}</b> — parametric steel factory (roof types, JIS sections, takeoff)"))
        self.tabs=QTabWidget(); root.addWidget(self.tabs,1)

        g=QWidget(); f=QFormLayout(g); f.setVerticalSpacing(9); f.setHorizontalSpacing(18); f.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.project=QLineEdit("Factory 01")
        self.width=dbl(18,3,200,.5); self.length=dbl(36,3,500,1); self.eave=dbl(6,2,50,.25); self.rise=dbl(2.5,.1,20,.1)
        self.bays=integer(6,1,50); self.frame_type=QComboBox(); self.frame_type.addItems(["Portal Frame","Roof Truss","Hybrid"])
        self.frame_type.currentTextChanged.connect(lambda _x: self._update_truss_enabled())
        self.roof_type=QComboBox(); self.roof_type.addItems(ROOF_TYPES)
        self.roof_type.currentTextChanged.connect(self._roof_changed)
        self.truss_panels=integer(8,2,40); self.purlins=integer(5,1,30); self.girts=integer(3,0,20)
        self.truss_type=QComboBox(); self.truss_type.addItems(TRUSS_TYPES)
        self.truss_depth=dbl(1.0,0.2,6,.05); self.ridge_pos=dbl(0.35,0.15,0.85,.05)
        self.overhang=dbl(0.0,0.0,4,.1); self.hanger=QCheckBox(); self.hanger_len=dbl(0.6,0.1,3,.05)
        self.brace_style=QComboBox(); self.brace_style.addItems(["X","Staggered"])
        self.top_brace=QCheckBox(); self.top_brace.setChecked(True)
        self.bottom_brace=QCheckBox(); self.eave_brace=QCheckBox(); self.sub_truss=QCheckBox(); self.sub_depth=dbl(0.6,0.1,3,.05)
        self.sub_truss.toggled.connect(lambda _c: self._update_truss_enabled())
        self.center_columns=QCheckBox(); self.bracing=QCheckBox(); self.bracing.setChecked(True)
        self.container_mode=QComboBox(); self.container_mode.addItems(["Component","Group"])
        # slope-by-angle + curved/toothed controls
        self.use_angle=QCheckBox(); self.roof_angle=dbl(15,0,60,.5)
        self.arch_segments=integer(16,6,60); self.sawtooth_teeth=integer(4,1,12)
        self.hip_setback=dbl(1.0,0.2,1.5,.05)
        self.preview=_TrussPreview(self._preview_data)
        f.addRow("Truss shape preview", self.preview)
        for _w in (self.width,self.eave,self.rise,self.truss_depth,self.ridge_pos,self.overhang,self.truss_panels,self.roof_angle):
            _w.valueChanged.connect(lambda _v=None: self.preview.update())
        self.truss_type.currentTextChanged.connect(lambda _x: self.preview.update())
        self.use_angle.toggled.connect(lambda _c: self.preview.update())
        self.hanger.toggled.connect(lambda _c: self.preview.update())
        self.hanger_len.valueChanged.connect(lambda _v=None: self.preview.update())
        self.bays.valueChanged.connect(lambda _v=None: self.preview.update())
        self.brace_style.currentTextChanged.connect(lambda _x: self.preview.update())
        for _cb in (self.top_brace,self.bottom_brace,self.eave_brace):
            _cb.toggled.connect(lambda _c: self.preview.update())
        for a,b in [("Project / Factory name",self.project),("Factory width X (m)",self.width),("Factory length Y (m)",self.length),
                    ("Eave height (m)",self.eave),("Roof rise (m)",self.rise),("Longitudinal bays",self.bays),
                    ("Main frame system",self.frame_type),("Roof shape",self.roof_type),("Truss web type",self.truss_type),
                    ("Truss depth (m)",self.truss_depth),("Ridge position (Dual-pitch)",self.ridge_pos),
                    ("Eave overhang (m)",self.overhang),("Ceiling hangers",self.hanger),("Hanger length (m)",self.hanger_len),
                    ("Truss panels",self.truss_panels),("Top-chord bracing",self.top_brace),("Brace style",self.brace_style),("Bottom-chord bracing",self.bottom_brace),
                    ("Edge/vertical bracing",self.eave_brace),("Sub-trusses",self.sub_truss),("Sub-truss depth (m)",self.sub_depth),
                    ("Purlin rows / roof side",self.purlins),("Wall girt rows",self.girts),("Centre column line",self.center_columns),
                    ("X bracing",self.bracing),("Generated member type",self.container_mode),
                    ("Define slope by angle",self.use_angle),("Roof pitch angle (deg)",self.roof_angle),
                    ("Arch segments (Arched)",self.arch_segments),("Sawtooth teeth (Sawtooth)",self.sawtooth_teeth),
                    ("Hip setback / (W/2) (Hip)",self.hip_setback)]: f.addRow(a,b)
        note=QLabel("Component = shared prototype mesh for repeated identical members (recommended for performance). Group = independent geometry per member. Hip/Gambrel/Arched/Sawtooth are rafter-only (truss falls back to rafters).")
        note.setWordWrap(True); f.addRow(note); self.tabs.addTab(self._scroll(g),"Geometry")

        opt=QWidget(); of=QFormLayout(opt); of.setVerticalSpacing(9); of.setHorizontalSpacing(18); of.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.crane=QCheckBox(); self.crane_h=dbl(4.5,2,30,.25)
        self.mezz=QCheckBox(); self.mezz_level=dbl(3,1,20,.25); self.mezz_width=dbl(8,1,100,.5)
        self.endwall=QCheckBox(); self.endwall.setChecked(True); self.door_w=dbl(5,1,30,.25); self.door_h=dbl(4.5,2,15,.25)
        self.gable_wall=QCheckBox(); self.skylight=QCheckBox(); self.skylight_count=integer(2,1,20)
        self.lean=QCheckBox(); self.lean_side=QComboBox(); self.lean_side.addItems(["Left","Right"]); self.lean_w=dbl(5,1,30,.5); self.lean_drop=dbl(1.5,.2,10,.25)
        for a,b in [("Crane runway beam",self.crane),("Crane beam height (m)",self.crane_h),("Mezzanine",self.mezz),
                    ("Mezzanine level (m)",self.mezz_level),("Mezzanine width (m)",self.mezz_width),("End-wall framing",self.endwall),
                    ("Central door width (m)",self.door_w),("Central door height (m)",self.door_h),
                    ("Gable-end wall framing",self.gable_wall),("Skylight / roof lights",self.skylight),
                    ("Skylight count",self.skylight_count),("Lean-to",self.lean),
                    ("Lean-to side",self.lean_side),("Lean-to width (m)",self.lean_w),("Lean-to drop (m)",self.lean_drop)]: of.addRow(a,b)
        self.tabs.addTab(self._scroll(opt),"Options")

        s=QWidget(); sg=QGridLayout(s); headers=["Role","Section","Family","Depth","Width","kg/m*"]
        for i,h in enumerate(headers): sg.addWidget(QLabel(f"<b>{h}</b>"),0,i)
        self.sec_boxes={}
        self._sections_grid = sg
        roles=["column","rafter","truss_top","truss_bottom","truss_web","truss","purlin","girt","bracing","crane","mezz","lean","endwall"]
        for r,role in enumerate(roles,1):
            box=QComboBox(); box.addItems(list(SECTION_LIBRARY)); box.setCurrentText(DEFAULT_SECTION_BY_ROLE[role]); box.currentTextChanged.connect(lambda _x, rr=r, bb=box:self._sync_sec_row(rr,bb))
            self.sec_boxes[role]=box; sg.addWidget(QLabel(role.title()),r,0); sg.addWidget(box,r,1)
            for c in range(2,6): sg.addWidget(QLabel(""),r,c)
            self._sync_sec_row(r,box)
        catalog_label = QLabel(
            f"GO Engineering Core {catalog_info()['version']} / {catalog_info()['count']} nominal profiles. "
            "All listed kg/m values are APPROXIMATE/UNVERIFIED; dimensional "
            "section properties and source documentation must be checked before design or procurement."
        )
        catalog_label.setWordWrap(True)
        sg.addWidget(catalog_label, len(roles) + 1, 0, 1, 6)
        self.tabs.addTab(self._scroll(s),"Sections")

        c=QWidget(); cg=QGridLayout(c); self.color_btn={}; cg.addWidget(QLabel("<b>Layer</b>"),0,0); cg.addWidget(QLabel("<b>Color</b>"),0,1)
        for r,(layer,rgb) in enumerate(LAYER_COLORS.items(),1):
            cg.addWidget(QLabel(layer),r,0); b=QPushButton(); b.setProperty("rgb",rgb); self._style_color(b,rgb); b.clicked.connect(lambda _=False,bb=b:self._pick_color(bb)); self.color_btn[layer]=b; cg.addWidget(b,r,1)
        self.tabs.addTab(self._scroll(c),"Layers & Colors")

        t=QWidget(); tv=QVBoxLayout(t)
        frow=QHBoxLayout(); frow.addWidget(QLabel("Connection allowance %:")); self.conn_pct=dbl(5,0,100,.5); frow.addWidget(self.conn_pct)
        frow.addWidget(QLabel("Wastage %:")); self.waste_pct=dbl(5,0,100,.5); frow.addWidget(self.waste_pct); frow.addStretch()
        self.conn_pct.valueChanged.connect(lambda _=None: self.refresh()); self.waste_pct.valueChanged.connect(lambda _=None: self.refresh())
        tv.addLayout(frow)
        self.table=QTableWidget(0,9); self.table.setHorizontalHeaderLabels(["Category","Section","Layer","Type","Qty","Length (m)","Weight (kg)","Conn (kg)","Total (kg)"]); self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents); tv.addWidget(self.table)
        ex=QPushButton("Export Takeoff CSV…"); ex.clicked.connect(self.export_csv); tv.addWidget(ex); self.tabs.addTab(t,"Takeoff")

        row=QHBoxLayout(); b=QPushButton("Create / Rebuild Factory"); b.clicked.connect(self.create); row.addWidget(b)
        sp=QPushButton("Save Preset…"); sp.clicked.connect(self.save_preset); row.addWidget(sp)
        lp=QPushButton("Load Preset…"); lp.clicked.connect(self.load_preset); row.addWidget(lp)
        row.addStretch(); cl=QPushButton("Close"); cl.clicked.connect(self.close); row.addWidget(cl); root.addLayout(row)
        self._roof_changed(self.roof_type.currentText())

    def _roof_changed(self, name):
        curved = name in ("Arched", "Sawtooth", "Cross Gable")
        self.frame_type.setEnabled(not curved)
        self.arch_segments.setEnabled(name == "Arched")
        self.sawtooth_teeth.setEnabled(name == "Sawtooth")
        self.hip_setback.setEnabled(name == "Hip")
        self._update_truss_enabled()

    def _update_truss_enabled(self):
        truss_on = (self.frame_type.currentText() in ("Roof Truss", "Hybrid")
                    and self.roof_type.currentText() in ("Gable", "Mono-slope"))
        for w in (self.truss_type, self.truss_depth, self.ridge_pos, self.overhang, self.hanger, self.hanger_len, self.truss_panels, self.top_brace, self.brace_style, self.bottom_brace, self.eave_brace, self.sub_truss):
            w.setEnabled(truss_on)
        self.hanger_len.setEnabled(truss_on and self.hanger.isChecked())
        self.sub_depth.setEnabled(truss_on and self.sub_truss.isChecked())

    def _ridge(self):
        eave=self.eave.value()
        if self.use_angle.isChecked():
            W=self.width.value()
            half = W if self.roof_type.currentText()=="Mono-slope" else W/2.0
            return eave + math.tan(math.radians(self.roof_angle.value()))*half
        return eave + self.rise.value()

    def _preview_data(self):
        cfg={"truss_depth":self.truss_depth.value(),"ridge_pos":self.ridge_pos.value(),
             "eave_overhang":self.overhang.value(),"hanger":self.hanger.isChecked(),"hanger_length":self.hanger_len.value()}
        Wd=self.width.value(); eave=self.eave.value(); ridge=self._ridge(); tt=self.truss_type.currentText()
        mem=truss_members(tt, Wd, eave, ridge, cfg, self.truss_panels.value())
        return {"mem":mem,"W":Wd,"eave":eave,"ridge":ridge,"oh":self.overhang.value(),"ttype":tt,
                "panels":self.truss_panels.value(),"bays":self.bays.value(),
                "top_brace":self.top_brace.isChecked(),"bottom_brace":self.bottom_brace.isChecked(),
                "eave_brace":self.eave_brace.isChecked(),"brace_style":self.brace_style.currentText()}

    def _sync_sec_row(self,row,box):
        sec=SECTION_LIBRARY[box.currentText()]; layout=self._sections_grid
        vals=[sec.family,f"{sec.depth_m:.3f}",f"{sec.width_m:.3f}",f"{sec.unit_weight_kg_m:.2f}"]
        for j,val in enumerate(vals,2):
            w=layout.itemAtPosition(row,j).widget(); w.setText(val)

    def _style_color(self,b,rgb):
        R,G,B=[int(x*255) for x in rgb]; b.setText(f"RGB {R}, {G}, {B}"); b.setStyleSheet(f"background: rgb({R},{G},{B});")
    def _pick_color(self,b):
        rgb=b.property("rgb"); q=QColorDialog.getColor(QColor.fromRgbF(*rgb),self,"Member color")
        if q.isValid():
            rgb=(q.redF(),q.greenF(),q.blueF()); b.setProperty("rgb",rgb); self._style_color(b,rgb)

    def show_tab(self, index):
        self.tabs.setCurrentIndex(max(0, min(index, self.tabs.count()-1)))
        self.show(); self.raise_(); self.activateWindow()

    def load_scene_takeoff(self):
        self.records = collect_scene_records(self.viewport.scene)
        self.refresh()
        self.tabs.setCurrentIndex(4)
        return len(self.records)

    def config(self):
        return {"project":self.project.text().strip() or "Factory 01","width":self.width.value(),"length":self.length.value(),"eave":self.eave.value(),"ridge":self._ridge(),
                "bays":self.bays.value(),"frame_type":self.frame_type.currentText(),"roof_type":self.roof_type.currentText(),"truss_panels":self.truss_panels.value(),"purlin_rows":self.purlins.value(),"girt_rows":self.girts.value(),
                "truss_type":self.truss_type.currentText(),"truss_depth":self.truss_depth.value(),"ridge_pos":self.ridge_pos.value(),"eave_overhang":self.overhang.value(),"hanger":self.hanger.isChecked(),"hanger_length":self.hanger_len.value(),"top_bracing":self.top_brace.isChecked(),"bottom_bracing":self.bottom_brace.isChecked(),"eave_bracing":self.eave_brace.isChecked(),"brace_style":self.brace_style.currentText(),"sub_truss":self.sub_truss.isChecked(),"sub_truss_depth":self.sub_depth.value(),
                "center_columns":self.center_columns.isChecked(),"bracing":self.bracing.isChecked(),"container_mode":self.container_mode.currentText(),
                "arch_segments":self.arch_segments.value(),"sawtooth_teeth":self.sawtooth_teeth.value(),"hip_setback":self.hip_setback.value(),
                "crane_beam":self.crane.isChecked(),"crane_height":self.crane_h.value(),"mezzanine":self.mezz.isChecked(),"mezz_level":self.mezz_level.value(),"mezz_width":self.mezz_width.value(),
                "endwall_framing":self.endwall.isChecked(),"door_width":self.door_w.value(),"door_height":self.door_h.value(),
                "gable_wall":self.gable_wall.isChecked(),"skylight":self.skylight.isChecked(),"skylight_count":self.skylight_count.value(),
                "lean_to":self.lean.isChecked(),"lean_side":self.lean_side.currentText(),"lean_width":self.lean_w.value(),"lean_drop":self.lean_drop.value(),
                "sections":{k:SECTION_LIBRARY[b.currentText()] for k,b in self.sec_boxes.items()},"colors":{k:tuple(b.property("rgb")) for k,b in self.color_btn.items()}}

    def create(self):
        holder={}
        try:
            self.viewport.history.execute(SnapshotImport(lambda scene: holder.setdefault("records",build_factory(scene,self.config()))))
            self.viewport.notify_scene_changed(); self.records=holder.get("records",[]); self.refresh(); self.tabs.setCurrentIndex(4); self.viewport.flash_status(f"GO Factory v{PLUGIN_VERSION}: {len(self.records)} members",4000)
        except Exception as e: QMessageBox.critical(self,"GO Factory Generator",f"Generation failed:\n{e}")

    def refresh(self):
        rows=summarize(self.records, self.conn_pct.value(), self.waste_pct.value()); self.table.setRowCount(len(rows))
        for r,((cat,sec,layer,typ),q) in enumerate(sorted(rows.items())):
            vals=[cat,sec,layer,typ,str(q['qty']),f"{q['length']:.3f}",f"{q['weight']:.1f}",f"{q.get('conn_kg',0):.1f}",f"{q.get('total_kg',q['weight']):.1f}"]
            for c,x in enumerate(vals): self.table.setItem(r,c,QTableWidgetItem(x))
    def export_csv(self):
        if not self.records: QMessageBox.information(self,"GO Factory","Create the factory first."); return
        p,_=QFileDialog.getSaveFileName(self,"Export Takeoff","go_factory_takeoff.csv","CSV (*.csv)")
        if not p:return
        rows=summarize(self.records, self.conn_pct.value(), self.waste_pct.value())
        with open(p,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f); w.writerow(["Category","Section","Layer","Type","Qty","Total Length (m)","Member Weight (kg)","Connection (kg)","Total incl. waste (kg)"])
            for (cat,sec,layer,typ),q in sorted(rows.items()):
                w.writerow([cat,sec,layer,typ,q['qty'],f"{q['length']:.3f}",f"{q['weight']:.1f}",f"{q.get('conn_kg',0):.1f}",f"{q.get('total_kg',q['weight']):.1f}"])
        QMessageBox.information(self,"GO Factory",f"Exported:\n{p}")

    # ---- presets -------------------------------------------------------- #
    def _state(self):
        return {"project":self.project.text(),"width":self.width.value(),"length":self.length.value(),
                "eave":self.eave.value(),"rise":self.rise.value(),"bays":self.bays.value(),
                "frame_type":self.frame_type.currentText(),"roof_type":self.roof_type.currentText(),
                "truss_panels":self.truss_panels.value(),"purlins":self.purlins.value(),"girts":self.girts.value(),
                "truss_type":self.truss_type.currentText(),"truss_depth":self.truss_depth.value(),"ridge_pos":self.ridge_pos.value(),
                "overhang":self.overhang.value(),"hanger":self.hanger.isChecked(),"hanger_len":self.hanger_len.value(),
                "top_brace":self.top_brace.isChecked(),"bottom_brace":self.bottom_brace.isChecked(),
                "eave_brace":self.eave_brace.isChecked(),"brace_style":self.brace_style.currentText(),
                "sub_truss":self.sub_truss.isChecked(),"sub_depth":self.sub_depth.value(),
                "center_columns":self.center_columns.isChecked(),"bracing":self.bracing.isChecked(),
                "container_mode":self.container_mode.currentText(),"use_angle":self.use_angle.isChecked(),
                "roof_angle":self.roof_angle.value(),"arch_segments":self.arch_segments.value(),
                "sawtooth_teeth":self.sawtooth_teeth.value(),"hip_setback":self.hip_setback.value(),"crane":self.crane.isChecked(),"crane_h":self.crane_h.value(),
                "mezz":self.mezz.isChecked(),"mezz_level":self.mezz_level.value(),"mezz_width":self.mezz_width.value(),
                "endwall":self.endwall.isChecked(),"door_w":self.door_w.value(),"door_h":self.door_h.value(),
                "gable_wall":self.gable_wall.isChecked(),"skylight":self.skylight.isChecked(),"skylight_count":self.skylight_count.value(),
                "lean":self.lean.isChecked(),"lean_side":self.lean_side.currentText(),"lean_w":self.lean_w.value(),"lean_drop":self.lean_drop.value(),
                "conn_pct":self.conn_pct.value(),"waste_pct":self.waste_pct.value(),
                "sections":{r:b.currentText() for r,b in self.sec_boxes.items()},
                "colors":{k:list(b.property("rgb")) for k,b in self.color_btn.items()}}

    def _set_combo(self, cb, text):
        i=cb.findText(text)
        if i>=0: cb.setCurrentIndex(i)

    def _apply(self, d):
        try:
            self.project.setText(d.get("project",self.project.text()))
            for key,w in [("width",self.width),("length",self.length),("eave",self.eave),("rise",self.rise),
                          ("roof_angle",self.roof_angle),("crane_h",self.crane_h),("mezz_level",self.mezz_level),
                          ("mezz_width",self.mezz_width),("door_w",self.door_w),("door_h",self.door_h),
                          ("lean_w",self.lean_w),("lean_drop",self.lean_drop),("conn_pct",self.conn_pct),("waste_pct",self.waste_pct),
                          ("hip_setback",self.hip_setback),("sub_depth",self.sub_depth),("truss_depth",self.truss_depth),("ridge_pos",self.ridge_pos),
                          ("overhang",self.overhang),("hanger_len",self.hanger_len)]:
                if key in d: w.setValue(d[key])
            for key,w in [("bays",self.bays),("truss_panels",self.truss_panels),("purlins",self.purlins),("girts",self.girts),
                          ("arch_segments",self.arch_segments),("sawtooth_teeth",self.sawtooth_teeth),("skylight_count",self.skylight_count)]:
                if key in d: w.setValue(int(d[key]))
            if "frame_type" in d: self._set_combo(self.frame_type,d["frame_type"])
            if "roof_type" in d: self._set_combo(self.roof_type,d["roof_type"])
            if "truss_type" in d: self._set_combo(self.truss_type,d["truss_type"])
            if "brace_style" in d: self._set_combo(self.brace_style,d["brace_style"])
            if "container_mode" in d: self._set_combo(self.container_mode,d["container_mode"])
            if "lean_side" in d: self._set_combo(self.lean_side,d["lean_side"])
            for key,w in [("center_columns",self.center_columns),("bracing",self.bracing),("use_angle",self.use_angle),
                          ("top_brace",self.top_brace),("bottom_brace",self.bottom_brace),("eave_brace",self.eave_brace),("sub_truss",self.sub_truss),("hanger",self.hanger),
                          ("crane",self.crane),("mezz",self.mezz),("endwall",self.endwall),("gable_wall",self.gable_wall),
                          ("skylight",self.skylight),("lean",self.lean)]:
                if key in d: w.setChecked(bool(d[key]))
            for role,name in (d.get("sections") or {}).items():
                box=self.sec_boxes.get(role)
                if box is not None: self._set_combo(box,name)
            for layer,rgb in (d.get("colors") or {}).items():
                b=self.color_btn.get(layer)
                if b is not None and isinstance(rgb,(list,tuple)) and len(rgb)==3:
                    rgb=tuple(float(x) for x in rgb); b.setProperty("rgb",rgb); self._style_color(b,rgb)
        except Exception as e:
            QMessageBox.warning(self,"GO Factory","Some preset values could not be applied:\n"+str(e))

    def save_preset(self):
        p,_=QFileDialog.getSaveFileName(self,"Save Preset","go_factory_preset.json","JSON (*.json)")
        if not p: return
        try:
            with open(p,"w",encoding="utf-8") as f: json.dump(self._state(),f,indent=2)
            QMessageBox.information(self,"GO Factory",f"Preset saved:\n{p}")
        except Exception as e: QMessageBox.critical(self,"GO Factory",f"Save failed:\n{e}")

    def load_preset(self):
        p,_=QFileDialog.getOpenFileName(self,"Load Preset","","JSON (*.json)")
        if not p: return
        try:
            with open(p,encoding="utf-8") as f: d=json.load(f)
            self._apply(d); QMessageBox.information(self,"GO Factory",f"Preset loaded:\n{p}")
        except Exception as e: QMessageBox.critical(self,"GO Factory",f"Load failed:\n{e}")
