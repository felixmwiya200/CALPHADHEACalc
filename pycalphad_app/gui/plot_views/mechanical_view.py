"""
mechanical_view.py - Mechanical Behavior & Strengthening Mechanisms View
Renders Yield Strength vs. Temperature and Ramberg-Osgood Stress-Strain curves.
"""

from typing import Dict, Any
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGridLayout
from PyQt6.QtGui import QFont


class MechanicalView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("Mechanical Behavior & Constitutive Modeling")
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
        grid.addWidget(self.plot_sy, 0, 0)

        # 2. Ramberg-Osgood Stress-Strain Curve
        self.plot_ss = pg.PlotWidget()
        self.plot_ss.setBackground("#1E1E1E")
        self.plot_ss.showGrid(x=True, y=True, alpha=0.3)
        self.plot_ss.setLabel("left", "True Stress σ", units="MPa")
        self.plot_ss.setLabel("bottom", "True Strain ε", units="[-]")
        grid.addWidget(self.plot_ss, 0, 1)

    def update_data(self, results: Dict[str, Any]):
        self.plot_sy.clear()
        self.plot_ss.clear()

        mech = results.get("mechanical", {})
        sy_0 = mech.get("YieldStrength_MPa", 350.0)
        uts_0 = mech.get("UTS_MPa", 700.0)
        hv = mech.get("Hardness_HV", 200.0)
        elong = mech.get("Elongation_pct", 30.0)

        self.metrics_label.setText(f"Yield: {sy_0:.1f} MPa | UTS: {uts_0:.1f} MPa | Hardness: {hv:.1f} HV | Elongation: {elong:.1f}%")

        # 1. Yield Strength vs T (77 K to 1400 K)
        T = np.linspace(77.0, 1400.0, 150)
        # Thermally activated dislocation bypass / Varshni-type decay
        # sy(T) = sy_0 * (1 - 0.7 * (T - 298)/(1400 - 298))
        sy_T = sy_0 * np.exp(-0.0009 * (T - 77.0))
        sy_T = np.maximum(sy_T, 40.0)

        self.plot_sy.plot(T, sy_T, pen=pg.mkPen("#2196F3", width=2.5), name="Yield Strength σ_y(T)")
        self.plot_sy.plot([298.15], [sy_0], pen=None, symbol='o', symbolSize=8,
                          symbolBrush=pg.mkBrush("#FFEB3B"), name="Room Temp (298 K)")

        # 2. Ramberg-Osgood True Stress-Strain Curve
        # epsilon = sigma/E + (sigma/K)^(1/n)
        E = mech.get("YoungsModulus_GPa", 200.0) * 1000.0  # MPa
        max_strain = elong / 100.0
        strains = np.linspace(0.0, max(max_strain, 0.05), 200)

        n_hardening = 0.18
        K_strength = uts_0 * 1.35
        # Invert Ramberg-Osgood approximately for plotting
        stresses = []
        for eps in strains:
            # Elastic portion
            sig_el = E * eps
            # Plastic hardening
            sig_pl = K_strength * (eps**n_hardening) if eps > 0 else 0.0
            sig = min(sig_el, sig_pl) if eps < 0.005 else sig_pl
            stresses.append(min(sig, uts_0 * 1.05))

        self.plot_ss.plot(strains, stresses, pen=pg.mkPen("#E91E63", width=2.5), name="Ramberg-Osgood Flow")
        self.plot_ss.addLine(y=sy_0, pen=pg.mkPen("#FF9800", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine))
        self.plot_ss.addLine(y=uts_0, pen=pg.mkPen("#F44336", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine))
