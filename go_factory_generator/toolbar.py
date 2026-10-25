"""GO Factory Generator toolbar for IngeTrazo 0.5.9+.

Follows the same setup(app) + QToolBar pattern proven by GO RC Detailing.
Icons are painted in memory so the extension has no external image assets.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QToolBar, QMessageBox


def _icon(kind: str) -> QIcon:
    pix = QPixmap(44, 44)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    dark = QColor("#2F6387")
    accent = QColor("#C76A30")
    green = QColor("#278C66")
    p.setPen(QPen(dark, 2.6))
    p.setBrush(Qt.BrushStyle.NoBrush)

    if kind == "create":
        # factory portal + roof
        p.drawLine(7, 34, 7, 19); p.drawLine(37, 34, 37, 19)
        p.drawLine(7, 19, 22, 9); p.drawLine(22, 9, 37, 19)
        p.drawLine(12, 34, 12, 23); p.drawLine(32, 34, 32, 23)
        p.setPen(QPen(green, 2.0))
        p.drawLine(12, 23, 22, 16); p.drawLine(22, 16, 32, 23)
    elif kind == "settings":
        p.setPen(QPen(accent, 2.5))
        p.drawEllipse(12, 12, 20, 20)
        p.drawEllipse(18, 18, 8, 8)
        for x1,y1,x2,y2 in [(22,5,22,11),(22,33,22,39),(5,22,11,22),(33,22,39,22),
                            (10,10,14,14),(30,30,34,34),(30,14,34,10),(10,34,14,30)]:
            p.drawLine(x1,y1,x2,y2)
    elif kind == "takeoff":
        p.setPen(QPen(green, 2.2))
        p.drawRect(8, 8, 28, 28)
        for y in (16, 24, 32): p.drawLine(8, y, 36, y)
        p.drawLine(19, 8, 19, 36); p.drawLine(28, 8, 28, 36)
        p.setBrush(accent); p.drawRect(21, 26, 5, 4)
    else:  # rebuild
        p.setPen(QPen(dark, 2.8))
        p.drawArc(8, 8, 28, 28, 35*16, 275*16)
        p.setBrush(dark)
        poly = __import__('PySide6.QtGui', fromlist=['QPolygon']).QPolygon()
        from PySide6.QtCore import QPoint
        poly << QPoint(34, 8) << QPoint(39, 15) << QPoint(30, 15)
        p.drawPolygon(poly)
    p.end()
    return QIcon(pix)


def _dialog(app):
    from .ui import FactoryDialog
    dlg = getattr(app.window, "_go_factory_generator_dialog", None)
    if dlg is None:
        dlg = FactoryDialog(app.viewport)
        app.window._go_factory_generator_dialog = dlg
    return dlg


def _open_tab(app, index):
    try:
        _dialog(app).show_tab(index)
    except Exception as exc:
        QMessageBox.critical(app.window, "GO Factory Generator", f"Cannot open dialog:\n{type(exc).__name__}: {exc}")


def _takeoff(app):
    try:
        dlg = _dialog(app)
        count = dlg.load_scene_takeoff()
        dlg.show(); dlg.raise_(); dlg.activateWindow()
        app.window.statusBar().showMessage(f"GO Factory: takeoff loaded from {count} members", 5000)
    except Exception as exc:
        QMessageBox.critical(app.window, "GO Factory Takeoff", f"Cannot read takeoff:\n{type(exc).__name__}: {exc}")


def _rebuild(app):
    try:
        dlg = _dialog(app)
        answer = QMessageBox.question(
            app.window, "GO Factory Rebuild",
            "Rebuild the current Factory using the values currently stored in the GO Factory dialog?\n\n"
            "The operation is one Undo step."
        )
        if answer == QMessageBox.StandardButton.Yes:
            dlg.create()
    except Exception as exc:
        QMessageBox.critical(app.window, "GO Factory Rebuild", f"Cannot rebuild:\n{type(exc).__name__}: {exc}")


def install_toolbar(app):
    if getattr(app.window, "_go_factory_toolbar_installed", False):
        return

    tb = QToolBar("GO Factory", app.window)
    tb.setObjectName("go_factory_generator_toolbar")
    tb.setToolTip("GO Engineering | Parametric Steel Factory")
    tb.setIconSize(QSize(34, 34))
    tb.setMovable(True)
    tb.setFloatable(True)

    submenu = app.add_menu("GO Factory Generator")
    entries = [
        ("create", "Factory Builder", "Open the parametric steel factory builder", lambda: _open_tab(app, 0)),
        ("settings", "Settings", "Configure sections, layers, colors and modelling options", lambda: _open_tab(app, 2)),
        ("takeoff", "Quantity Takeoff", "Read BOQ / quantity takeoff from GO Factory members in the current scene", lambda: _takeoff(app)),
        ("rebuild", "Rebuild", "Rebuild the factory using the current dialog settings", lambda: _rebuild(app)),
    ]

    for i, (key, label, tip, callback) in enumerate(entries):
        if i == 3:
            tb.addSeparator()
            if submenu is not None:
                submenu.addSeparator()
        action = QAction(_icon(key), label, app.window)
        action.setToolTip(label + "\n" + tip)
        action.setStatusTip(tip)
        action.triggered.connect(lambda checked=False, cb=callback: cb())
        tb.addAction(action)
        if submenu is not None:
            ma = submenu.addAction(label)
            ma.setIcon(_icon(key))
            ma.setToolTip(tip)
            ma.triggered.connect(lambda checked=False, cb=callback: cb())

    app.window.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)
    app.window._go_factory_toolbar_installed = True
    if hasattr(app.window, "toolbars"):
        app.window.toolbars["go_factory_generator"] = tb
    tb.show()

    restore = getattr(app, "restore_toolbar_layout", None)
    if callable(restore):
        try:
            restore()
        except Exception:
            pass
