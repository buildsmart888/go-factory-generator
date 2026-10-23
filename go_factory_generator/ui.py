from __future__ import annotations
import csv
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QCheckBox,QColorDialog,QComboBox,QDialog,QDoubleSpinBox,
    QFileDialog,QFormLayout,QGridLayout,QHeaderView,QHBoxLayout,QLabel,QLineEdit,QMessageBox,
    QPushButton,QSpinBox,QTabWidget,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget)
from core.history import SnapshotImport
from .constants import LAYER_COLORS
from .sections import SECTION_LIBRARY, DEFAULT_SECTION_BY_ROLE
from .generator import build_factory
from .takeoff import summarize, collect_scene_records


def dbl(v,lo,hi,step=.1):
    w=QDoubleSpinBox(); w.setRange(lo,hi); w.setValue(v); w.setSingleStep(step); w.setDecimals(3); return w

def integer(v,lo,hi):
    w=QSpinBox(); w.setRange(lo,hi); w.setValue(v); return w

class FactoryDialog(QDialog):
    def __init__(self, viewport):
        super().__init__(viewport.window()); self.viewport=viewport; self.records=[]
        self.setWindowTitle("GO Engineering — Factory Generator v0.2.3"); self.resize(980,780); self._build()

    def _build(self):
        root=QVBoxLayout(self)
        root.addWidget(QLabel("<b>GO Factory Generator v0.2.3</b> — maintainable parametric steel factory"))
        self.tabs=QTabWidget(); root.addWidget(self.tabs,1)

        g=QWidget(); f=QFormLayout(g)
        self.project=QLineEdit("Factory 01")
        self.width=dbl(18,3,200,.5); self.length=dbl(36,3,500,1); self.eave=dbl(6,2,50,.25); self.rise=dbl(2.5,.1,20,.1)
        self.bays=integer(6,1,50); self.frame_type=QComboBox(); self.frame_type.addItems(["Portal Frame","Roof Truss","Hybrid"])
        self.roof_type=QComboBox(); self.roof_type.addItems(["Gable","Mono-slope"])
        self.truss_panels=integer(8,2,40); self.purlins=integer(5,1,30); self.girts=integer(3,0,20)
        self.center_columns=QCheckBox(); self.bracing=QCheckBox(); self.bracing.setChecked(True)
        self.container_mode=QComboBox(); self.container_mode.addItems(["Component","Group"])
        for a,b in [("Project / Factory name",self.project),("Factory width X (m)",self.width),("Factory length Y (m)",self.length),
                    ("Eave height (m)",self.eave),("Roof rise (m)",self.rise),("Longitudinal bays",self.bays),
                    ("Main frame system",self.frame_type),("Roof shape",self.roof_type),("Truss panels",self.truss_panels),
                    ("Purlin rows / roof side",self.purlins),("Wall girt rows",self.girts),("Centre column line",self.center_columns),
                    ("X bracing",self.bracing),("Generated member type",self.container_mode)]: f.addRow(a,b)
        note=QLabel("Component = shared prototype mesh for repeated identical members (recommended for performance). Group = independent geometry per member.")
        note.setWordWrap(True); f.addRow(note); self.tabs.addTab(g,"Geometry")

        opt=QWidget(); of=QFormLayout(opt)
        self.crane=QCheckBox(); self.crane_h=dbl(4.5,2,30,.25)
        self.mezz=QCheckBox(); self.mezz_level=dbl(3,1,20,.25); self.mezz_width=dbl(8,1,100,.5)
        self.endwall=QCheckBox(); self.endwall.setChecked(True); self.door_w=dbl(5,1,30,.25); self.door_h=dbl(4.5,2,15,.25)
        self.lean=QCheckBox(); self.lean_side=QComboBox(); self.lean_side.addItems(["Left","Right"]); self.lean_w=dbl(5,1,30,.5); self.lean_drop=dbl(1.5,.2,10,.25)
        for a,b in [("Crane runway beam",self.crane),("Crane beam height (m)",self.crane_h),("Mezzanine",self.mezz),
                    ("Mezzanine level (m)",self.mezz_level),("Mezzanine width (m)",self.mezz_width),("End-wall framing",self.endwall),
                    ("Central door width (m)",self.door_w),("Central door height (m)",self.door_h),("Lean-to",self.lean),
                    ("Lean-to side",self.lean_side),("Lean-to width (m)",self.lean_w),("Lean-to drop (m)",self.lean_drop)]: of.addRow(a,b)
        self.tabs.addTab(opt,"Options")

        s=QWidget(); sg=QGridLayout(s); headers=["Role","Section","Family","Depth","Width","kg/m"]
        for i,h in enumerate(headers): sg.addWidget(QLabel(f"<b>{h}</b>"),0,i)
        self.sec_boxes={}
        self._sections_grid = sg
        roles=["column","rafter","truss","purlin","girt","bracing","crane","mezz","lean","endwall"]
        for r,role in enumerate(roles,1):
            box=QComboBox(); box.addItems(list(SECTION_LIBRARY)); box.setCurrentText(DEFAULT_SECTION_BY_ROLE[role]); box.currentTextChanged.connect(lambda _x, rr=r, bb=box:self._sync_sec_row(rr,bb))
            self.sec_boxes[role]=box; sg.addWidget(QLabel(role.title()),r,0); sg.addWidget(box,r,1)
            for c in range(2,6): sg.addWidget(QLabel(""),r,c)
            self._sync_sec_row(r,box)
        self.tabs.addTab(s,"Sections")

        c=QWidget(); cg=QGridLayout(c); self.color_btn={}; cg.addWidget(QLabel("<b>Layer</b>"),0,0); cg.addWidget(QLabel("<b>Color</b>"),0,1)
        for r,(layer,rgb) in enumerate(LAYER_COLORS.items(),1):
            cg.addWidget(QLabel(layer),r,0); b=QPushButton(); b.setProperty("rgb",rgb); self._style_color(b,rgb); b.clicked.connect(lambda _=False,bb=b:self._pick_color(bb)); self.color_btn[layer]=b; cg.addWidget(b,r,1)
        self.tabs.addTab(c,"Layers & Colors")

        t=QWidget(); tv=QVBoxLayout(t); self.table=QTableWidget(0,7); self.table.setHorizontalHeaderLabels(["Category","Section","Layer","Type","Qty","Length (m)","Weight (kg)"]); self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents); tv.addWidget(self.table)
        ex=QPushButton("Export Takeoff CSV…"); ex.clicked.connect(self.export_csv); tv.addWidget(ex); self.tabs.addTab(t,"Takeoff")

        row=QHBoxLayout(); b=QPushButton("Create / Rebuild Factory"); b.clicked.connect(self.create); row.addWidget(b); row.addStretch(); cl=QPushButton("Close"); cl.clicked.connect(self.close); row.addWidget(cl); root.addLayout(row)

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
        return {"project":self.project.text().strip() or "Factory 01","width":self.width.value(),"length":self.length.value(),"eave":self.eave.value(),"ridge":self.eave.value()+self.rise.value(),
                "bays":self.bays.value(),"frame_type":self.frame_type.currentText(),"roof_type":self.roof_type.currentText(),"truss_panels":self.truss_panels.value(),"purlin_rows":self.purlins.value(),"girt_rows":self.girts.value(),
                "center_columns":self.center_columns.isChecked(),"bracing":self.bracing.isChecked(),"container_mode":self.container_mode.currentText(),
                "crane_beam":self.crane.isChecked(),"crane_height":self.crane_h.value(),"mezzanine":self.mezz.isChecked(),"mezz_level":self.mezz_level.value(),"mezz_width":self.mezz_width.value(),
                "endwall_framing":self.endwall.isChecked(),"door_width":self.door_w.value(),"door_height":self.door_h.value(),"lean_to":self.lean.isChecked(),"lean_side":self.lean_side.currentText(),"lean_width":self.lean_w.value(),"lean_drop":self.lean_drop.value(),
                "sections":{k:SECTION_LIBRARY[b.currentText()] for k,b in self.sec_boxes.items()},"colors":{k:tuple(b.property("rgb")) for k,b in self.color_btn.items()}}

    def create(self):
        holder={}
        try:
            self.viewport.history.execute(SnapshotImport(lambda scene: holder.setdefault("records",build_factory(scene,self.config()))))
            self.viewport.notify_scene_changed(); self.records=holder.get("records",[]); self.refresh(); self.tabs.setCurrentIndex(4); self.viewport.flash_status(f"GO Factory v0.2.3: {len(self.records)} members",4000)
        except Exception as e: QMessageBox.critical(self,"GO Factory Generator",f"Generation failed:\n{e}")

    def refresh(self):
        rows=summarize(self.records); self.table.setRowCount(len(rows))
        for r,((cat,sec,layer,typ),q) in enumerate(sorted(rows.items())):
            vals=[cat,sec,layer,typ,str(q['qty']),f"{q['length']:.3f}",f"{q['weight']:.1f}"]
            for c,x in enumerate(vals): self.table.setItem(r,c,QTableWidgetItem(x))
    def export_csv(self):
        if not self.records: QMessageBox.information(self,"GO Factory","Create the factory first."); return
        p,_=QFileDialog.getSaveFileName(self,"Export Takeoff","go_factory_takeoff.csv","CSV (*.csv)")
        if not p:return
        rows=summarize(self.records)
        with open(p,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f); w.writerow(["Category","Section","Layer","Type","Qty","Total Length (m)","Estimated Weight (kg)"])
            for (cat,sec,layer,typ),q in sorted(rows.items()): w.writerow([cat,sec,layer,typ,q['qty'],f"{q['length']:.3f}",f"{q['weight']:.1f}"])
        QMessageBox.information(self,"GO Factory",f"Exported:\n{p}")
