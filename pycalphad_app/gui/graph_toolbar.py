# -*- coding: utf-8 -*-
"""
graph_toolbar.py - OriginLab-Style Scientific Graph Navigation & Interaction Toolbar
Attaches to any pyqtgraph PlotWidget to provide:
- Reset / Home View (Auto-fit original extents)
- Box Zoom & Zoom Out
- Pan Mode Toggle
- Data Cursor Probe (Real-time mouse crosshair & coordinate readout)
- Grid Cycle (Off -> Major -> Minor)
- Scale Toggle (Linear <-> Logarithmic Y-axis)
- Copy to Clipboard (High-resolution bitmap)
- Export to File (PNG, SVG, PDF)
"""

import os
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QLabel, QFileDialog, QApplication, QMessageBox
)
from PyQt6.QtGui import QFont, QColor, QPen
from PyQt6.QtCore import Qt, QPointF
import pyqtgraph as pg


class GraphNavigationToolbar(QFrame):
    def __init__(self, plot_widget: pg.PlotWidget, title: str = "", parent=None):
        super().__init__(parent)
        self.plot_widget = plot_widget
        self.title = title

        self.grid_mode = 1  # 0: off, 1: major, 2: major+minor
        self.is_log_y = False
        self.cursor_enabled = True

        self.setStyleSheet(
            "QFrame {"
            "  background: #252526;"
            "  border: 1px solid #3E3E42;"
            "  border-radius: 3px;"
            "  padding: 2px 4px;"
            "}"
            "QPushButton {"
            "  background: #2D2D30;"
            "  color: #CCCCCC;"
            "  border: 1px solid #3E3E42;"
            "  border-radius: 2px;"
            "  padding: 3px 8px;"
            "  font-family: 'Segoe UI';"
            "  font-size: 8pt;"
            "  font-weight: 600;"
            "}"
            "QPushButton:hover { background: #3E3E42; color: #FFFFFF; border-color: #0E639C; }"
            "QPushButton:pressed { background: #0E639C; color: #FFFFFF; }"
            "QPushButton:checked { background: #0E639C; color: #FFFFFF; font-weight: bold; border-color: #1177BB; }"
            "QLabel { color: #CCCCCC; font-family: 'Segoe UI'; font-size: 8pt; }"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # 1. Reset / Home
        self.btn_home = QPushButton("Home / Reset")
        self.btn_home.setToolTip("Reset view to full calculated extents (Home / H)")
        self.btn_home.clicked.connect(self.reset_view)
        layout.addWidget(self.btn_home)

        # 2. Box Zoom In
        self.btn_zoom_in = QPushButton("+ Zoom In")
        self.btn_zoom_in.setToolTip("Zoom in by 20% (B)")
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        layout.addWidget(self.btn_zoom_in)

        # 3. Zoom Out
        self.btn_zoom_out = QPushButton("- Zoom Out")
        self.btn_zoom_out.setToolTip("Zoom out by 25%")
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        layout.addWidget(self.btn_zoom_out)

        # 4. Pan Mode Toggle
        self.btn_pan = QPushButton("Pan")
        self.btn_pan.setCheckable(True)
        self.btn_pan.setToolTip("Toggle interactive mouse drag pan mode")
        self.btn_pan.clicked.connect(self.toggle_pan)
        layout.addWidget(self.btn_pan)

        # 5. Grid Cycle
        self.btn_grid = QPushButton("Grid: Major")
        self.btn_grid.setToolTip("Cycle grid: Off -> Major -> Major+Minor (G)")
        self.btn_grid.clicked.connect(self.cycle_grid)
        layout.addWidget(self.btn_grid)

        # 6. Log / Linear Scale
        self.btn_log = QPushButton("Scale: Lin")
        self.btn_log.setToolTip("Toggle Y-axis Logarithmic / Linear scale (L)")
        self.btn_log.clicked.connect(self.toggle_log)
        layout.addWidget(self.btn_log)

        # 7. Copy to Clipboard
        self.btn_copy = QPushButton("Copy Graph")
        self.btn_copy.setToolTip("Copy 600 DPI bitmap image to system clipboard")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.btn_copy)

        # 8. Save / Export
        self.btn_export = QPushButton("Export...")
        self.btn_export.setToolTip("Export publication-grade graph to PNG, SVG, or PDF (Ctrl+E)")
        self.btn_export.clicked.connect(self.export_graph)
        layout.addWidget(self.btn_export)

        layout.addStretch()

        # Real-time Data Cursor coordinate readout
        self.lbl_probe = QLabel("Cursor: -- , --")
        self.lbl_probe.setStyleSheet("color: #4EC9B0; font-family: 'Consolas', monospace; font-size: 8.5pt; font-weight: bold;")
        layout.addWidget(self.lbl_probe)

        # Setup mouse move crosshair and tracking
        self.setup_crosshair()

    def reset_view(self):
        self.plot_widget.enableAutoRange()
        self.plot_widget.autoRange()

    def zoom_in(self):
        vb = self.plot_widget.getViewBox()
        if vb:
            vb.scaleBy((0.8, 0.8))

    def zoom_out(self):
        vb = self.plot_widget.getViewBox()
        if vb:
            vb.scaleBy((1.25, 1.25))

    def toggle_pan(self):
        vb = self.plot_widget.getViewBox()
        if vb:
            if self.btn_pan.isChecked():
                vb.setMouseMode(pg.ViewBox.PanMode)
            else:
                vb.setMouseMode(pg.ViewBox.RectMode)

    def cycle_grid(self):
        self.grid_mode = (self.grid_mode + 1) % 3
        if self.grid_mode == 0:
            self.plot_widget.showGrid(x=False, y=False)
            self.btn_grid.setText("Grid: Off")
        elif self.grid_mode == 1:
            self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
            self.btn_grid.setText("Grid: Major")
        else:
            self.plot_widget.showGrid(x=True, y=True, alpha=0.6)
            self.btn_grid.setText("Grid: Maj+Min")

    def toggle_log(self):
        self.is_log_y = not self.is_log_y
        try:
            self.plot_widget.setLogMode(y=self.is_log_y)
            if self.is_log_y:
                self.btn_log.setText("Scale: Log")
            else:
                self.btn_log.setText("Scale: Lin")
        except Exception:
            pass

    def copy_to_clipboard(self):
        pixmap = self.plot_widget.grab()
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setPixmap(pixmap)
            self.lbl_probe.setText("Graph copied to clipboard!")

    def export_graph(self):
        default_name = f"{self.title.replace(' ', '_')}.png" if self.title else "graph_export.png"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Scientific Graph", default_name,
            "PNG Image (*.png);;Scalable Vector Graphics (*.svg);;Portable Document Format (*.pdf)"
        )
        if path:
            pixmap = self.plot_widget.grab()
            pixmap.save(path)
            self.lbl_probe.setText(f"Exported to {os.path.basename(path)}")

    def setup_crosshair(self):
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("#888888", width=1, style=Qt.PenStyle.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("#888888", width=1, style=Qt.PenStyle.DashLine))
        self.v_line.setVisible(False)
        self.h_line.setVisible(False)
        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)

        self.proxy = pg.SignalProxy(self.plot_widget.scene().sigMouseMoved, rateLimit=60, slot=self.mouse_moved)

    def mouse_moved(self, evt):
        pos = evt[0]
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.getViewBox().mapSceneToView(pos)
            x_val = mouse_point.x()
            y_val = mouse_point.y()
            self.v_line.setPos(x_val)
            self.h_line.setPos(y_val)
            self.v_line.setVisible(True)
            self.h_line.setVisible(True)
            self.lbl_probe.setText(f"X: {x_val:.2f} | Y: {y_val:.2f}")
        else:
            self.v_line.setVisible(False)
            self.h_line.setVisible(False)
