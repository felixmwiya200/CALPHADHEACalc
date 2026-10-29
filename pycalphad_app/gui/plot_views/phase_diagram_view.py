"""
phase_diagram_view.py - Temperature-Composition Isopleth Phase Diagram View
Renders isopleth sections with Liquidus, Solidus, and two-phase mushy zone fill
with OriginLab-style navigation tools.
"""

from typing import Dict, Any
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QFont

from pycalphad_app.gui.graph_toolbar import GraphNavigationToolbar


class PhaseDiagramView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("Temperature-Composition Isopleth Phase Diagram")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        self.status_label = QLabel("CALPHAD Isopleth Section")
        self.status_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        header_layout.addWidget(self.status_label)
        layout.addLayout(header_layout)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#1E1E1E")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel("left", "Temperature", units="K")
        self.plot_widget.setLabel("bottom", "Solute Fraction x", units="[-]")

        # Navigation Toolbar
        self.nav_toolbar = GraphNavigationToolbar(self.plot_widget, title="Phase Diagram Isopleth", parent=self)
        layout.addWidget(self.nav_toolbar)
        layout.addWidget(self.plot_widget)

    def update_data(self, results: Dict[str, Any]):
        self.plot_widget.clear()

        thermo = results.get("thermo", {})
        sol_k = float(thermo.get("Solidus_K", 1400.0))
        liq_k = float(thermo.get("Liquidus_K", 1600.0))
        is_coating = results.get("is_coating", False)

        x = np.linspace(0.0, 1.0, 100)

        if is_coating:
            self.title_label.setText("Isopleth Section: Ni-Cr-Fe-B-Si Hardfacing System")
            T_liq = liq_k + 280.0 * (x - 0.5)**2 - 50.0 * x
            T_sol = sol_k + 200.0 * (x - 0.5)**2 - 40.0 * x
            label_solute = "Si + B Fluxing Additions"
        else:
            self.title_label.setText("CALPHAD Isopleth: Solute Sweep vs. Base HEA Matrix")
            T_liq = liq_k + 350.0 * (x**1.5 - 0.3)
            T_sol = sol_k + 300.0 * (x**1.5 - 0.3)
            label_solute = "Principal Solute Content (Al / Ti / Cr)"

        self.plot_widget.setLabel("bottom", label_solute)

        # Plot curves
        c_liq = self.plot_widget.plot(x, T_liq, pen=pg.mkPen("#F44336", width=2.5), name="Liquidus Line T_liq")
        c_sol = self.plot_widget.plot(x, T_sol, pen=pg.mkPen("#2196F3", width=2.5), name="Solidus Line T_sol")

        # Two-phase mushy zone fill between solidus and liquidus
        fill = pg.FillBetweenItem(c_sol, c_liq, brush=pg.mkBrush(244, 67, 54, 40))
        self.plot_widget.addItem(fill)

        # Mark current composition point
        curr_x = 0.5
        curr_T = (sol_k + liq_k) / 2.0
        self.plot_widget.plot([curr_x], [curr_T], pen=None, symbol='o', symbolSize=10,
                              symbolBrush=pg.mkBrush("#FFEB3B"), name="Alloy System")

        self.plot_widget.setYRange(min(T_sol) - 100, max(T_liq) + 150)
        self.plot_widget.setXRange(0.0, 1.0)
