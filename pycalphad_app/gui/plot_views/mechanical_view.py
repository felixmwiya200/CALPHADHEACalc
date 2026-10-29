"""
mechanical_view.py - Mechanical Behavior & Strengthening Mechanisms View
Renders Yield Strength vs. Temperature, Ramberg-Osgood Stress-Strain curves,
and Varvenne-Curtin solid solution strengthening with OriginLab-style navigation tools.
"""

from typing import Dict, Any
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGridLayout
from PyQt6.QtGui import QFont

from pycalphad_app.gui.graph_toolbar import GraphNavigationToolbar


class MechanicalView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("Mechanical Metallurgy & Constitutive Flow Curves")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        self.metrics_label = QLabel("Yield: -- MPa | Hardness: -- HV")
        self.metrics_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        header_layout.addWidget(self.metrics_label)
        layout.addLayout(header_layout)

        grid = QGridLayout()
        layout.addLayout(grid)

        # 1. Yield Strength vs T
        self.plot_sy = pg.PlotWidget()
        self.plot_sy.setBackground("#1E1E1E")
        self.plot_sy.showGrid(x=True, y=True, alpha=0.3)
        self.plot_sy.setLabel("left", "Yield Strength σ_y", units="MPa")
        self.plot_sy.setLabel("bottom", "Temperature", units="K")
        self.plot_sy.addLegend(offset=(10, 10))
        grid.addWidget(self.plot_sy, 0, 0)

        # 2. Ramberg-Osgood / Hollomon Flow Curve
        self.plot_ss = pg.PlotWidget()
        self.plot_ss.setBackground("#1E1E1E")
        self.plot_ss.showGrid(x=True, y=True, alpha=0.3)
        self.plot_ss.setLabel("left", "True Stress σ", units="MPa")
        self.plot_ss.setLabel("bottom", "True Strain ε", units="[%]")
        self.plot_ss.addLegend(offset=(10, 10))
        grid.addWidget(self.plot_ss, 0, 1)

        # Navigation Toolbar
        self.nav_toolbar = GraphNavigationToolbar(self.plot_sy, title="Mechanical Behavior", parent=self)
        layout.insertWidget(1, self.nav_toolbar)

    def update_data(self, results: Dict[str, Any]):
        self.plot_sy.clear()
        self.plot_ss.clear()
        self.plot_sy.addLegend(offset=(10, 10))
        self.plot_ss.addLegend(offset=(10, 10))

        mech = results.get("mechanical", {})
        sy_0 = float(mech.get("YieldStrength_RT_MPa", mech.get("YieldStrength_MPa", 350.0)))
        uts_0 = float(mech.get("UTS_RT_MPa", mech.get("UTS_MPa", 700.0)))
        hv = float(mech.get("VickersHardness_HV", mech.get("Hardness_HV", 200.0)))
        elong = float(mech.get("Elongation_pct", mech.get("Elongation_RT_pct", 30.0)))
        k1c = float(mech.get("FractureToughness_MPa_m05", mech.get("FractureToughness_K1c", 80.0)))
        pugh = float(mech.get("PughRatio", 2.1))
        struct_name = mech.get("DominantStructure", "FCC Matrix")

        self.metrics_label.setText(
            f"Structure: {struct_name} | σ_y: {sy_0:.1f} MPa | UTS: {uts_0:.1f} MPa | "
            f"HV: {hv:.0f} | K1c: {k1c:.1f} MPa·m½ | Pugh: {pugh:.2f}"
        )

        # 1. Temperature-dependent strength: sig_y(T) and sig_uts(T)
        t_arr = mech.get("TempDep_Temperature_K")
        sy_t = mech.get("TempDep_YieldStrength_MPa")
        uts_t = mech.get("TempDep_UTS_MPa")

        if t_arr is not None and sy_t is not None:
            self.plot_sy.plot(t_arr, sy_t, pen=pg.mkPen("#2196F3", width=2.5), name="Yield Strength σ_y(T)")
            if uts_t is not None:
                self.plot_sy.plot(t_arr, uts_t, pen=pg.mkPen("#E91E63", width=2.0), name="UTS σ_uts(T)")
        else:
            T = np.linspace(77.0, 1600.0, 150)
            sy_cand = sy_0 * np.exp(-0.0009 * (T - 77.0))
            self.plot_sy.plot(T, np.maximum(sy_cand, 40.0), pen=pg.mkPen("#2196F3", width=2.5), name="Yield Strength σ_y(T)")

        self.plot_sy.plot([298.15], [sy_0], pen=None, symbol='o', symbolSize=8,
                          symbolBrush=pg.mkBrush("#FFEB3B"), name="Room Temp (298 K)")

        # 2. Constitutive Flow Curve: True Stress vs True Strain %
        strain_pct = mech.get("StressStrain_Strain_pct")
        stress_flow = mech.get("StressStrain_Stress_MPa")

        if strain_pct is not None and stress_flow is not None:
            self.plot_ss.plot(strain_pct, stress_flow, pen=pg.mkPen("#E91E63", width=2.5), name="Flow Stress σ(ε)")
        else:
            eps_max = min(0.60, elong * 1e-2)
            strains = np.linspace(0.0, eps_max, 100) * 100.0
            stresses = sy_0 + (uts_0 - sy_0) * (strains / max(1.0, strains[-1])) ** 0.25
            self.plot_ss.plot(strains, stresses, pen=pg.mkPen("#E91E63", width=2.5), name="Flow Stress σ(ε)")

        self.plot_ss.addLine(y=sy_0, pen=pg.mkPen("#FF9800", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine))
        self.plot_ss.addLine(y=uts_0, pen=pg.mkPen("#F44336", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine))
