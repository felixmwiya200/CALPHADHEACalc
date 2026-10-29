"""
environmental_view.py - Environmental Durability & Degradation View
Renders Wagner high-temperature parabolic oxidation mass gain vs. time
and Stern-Geary potentiodynamic polarization (Tafel) curves in 3.5 wt% NaCl
with OriginLab-style navigation tools.
"""

from typing import Dict, Any
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGridLayout
from PyQt6.QtGui import QFont

from pycalphad_app.gui.graph_toolbar import GraphNavigationToolbar


class EnvironmentalView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("Environmental Durability: High-Temperature Oxidation & Corrosion")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        self.metrics_label = QLabel("Oxidation kp: -- | Ecorr: -- V | icorr: -- μA/cm²")
        self.metrics_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        header_layout.addWidget(self.metrics_label)
        layout.addLayout(header_layout)

        grid = QGridLayout()
        layout.addLayout(grid)

        # 1. Wagner Parabolic Oxidation
        self.plot_ox = pg.PlotWidget()
        self.plot_ox.setBackground("#1E1E1E")
        self.plot_ox.showGrid(x=True, y=True, alpha=0.3)
        self.plot_ox.setLabel("left", "Mass Gain Δm/A", units="mg/cm²")
        self.plot_ox.setLabel("bottom", "Exposure Time", units="hours")
        self.plot_ox.addLegend(offset=(10, 10))
        grid.addWidget(self.plot_ox, 0, 0)

        # 2. Tafel Polarization
        self.plot_corr = pg.PlotWidget()
        self.plot_corr.setBackground("#1E1E1E")
        self.plot_corr.showGrid(x=True, y=True, alpha=0.3)
        self.plot_corr.setLabel("left", "Potential E", units="V vs SCE")
        self.plot_corr.setLabel("bottom", "Log Current Density log₁₀(i)", units="μA/cm²")
        self.plot_corr.addLegend(offset=(10, 10))
        grid.addWidget(self.plot_corr, 0, 1)

        # Navigation Toolbar
        self.nav_toolbar = GraphNavigationToolbar(self.plot_ox, title="Oxidation & Corrosion", parent=self)
        layout.insertWidget(1, self.nav_toolbar)

    def update_data(self, results: Dict[str, Any]):
        self.plot_ox.clear()
        self.plot_corr.clear()
        self.plot_ox.addLegend(offset=(10, 10))
        self.plot_corr.addLegend(offset=(10, 10))

        ox = results.get("oxidation", {})
        corr = results.get("corrosion", {})

        kp = float(ox.get("kp_g2_cm4_s", ox.get("Oxidation_kp", 5.0e-9)))
        regime = ox.get("Regime", ox.get("dominantOxide", "Protective Scale"))
        ecorr = float(corr.get("Corrosion_Ecorr_V", -0.28))
        icorr = float(corr.get("Corrosion_icorr_uA", 0.42))
        crate = float(corr.get("CorrosionRate_mm_yr", 0.005))
        pren = float(corr.get("PREN_val", 25.0))

        self.metrics_label.setText(
            f"Regime: {regime} | kp: {kp:.2e} g²/(cm⁴·s) | "
            f"Ecorr: {ecorr:.3f} V | icorr: {icorr:.2f} μA/cm² | PREN: {pren:.1f}"
        )

        # 1. Wagner Parabolic Mass Gain vs Time
        t_hours = ox.get("Time_Hours")
        mass_gain = ox.get("MassGainCurve_mg_cm2")

        if t_hours is not None and mass_gain is not None:
            self.plot_ox.plot(t_hours, mass_gain, pen=pg.mkPen("#FF9800", width=2.5), name=f"{regime}")
        else:
            t_h = np.linspace(0.0, 100.0, 150)
            t_sec = t_h * 3600.0
            mg = np.sqrt(kp * t_sec) * 1000.0
            self.plot_ox.plot(t_h, mg, pen=pg.mkPen("#FF9800", width=2.5), name="Parabolic Kinetics")

        # 2. Tafel Polarization
        beta_a = 0.120
        beta_c = 0.120
        log_i = np.linspace(np.log10(max(1e-4, icorr)) - 3.0, np.log10(max(1e-4, icorr)) + 3.0, 200)
        e_tafel = np.where(
            log_i >= np.log10(max(1e-4, icorr)),
            ecorr + beta_a * (log_i - np.log10(max(1e-4, icorr))),
            ecorr - beta_c * (np.log10(max(1e-4, icorr)) - log_i)
        )

        self.plot_corr.plot(log_i, e_tafel, pen=pg.mkPen("#4CAF50", width=2.5), name="Tafel Polarization")
        self.plot_corr.plot([np.log10(max(1e-4, icorr))], [ecorr], pen=None, symbol='star', symbolSize=12,
                            symbolBrush=pg.mkBrush("#FFEB3B"), name="Corrosion Point (Ecorr, icorr)")
        self.plot_corr.addLine(y=ecorr, pen=pg.mkPen("#2196F3", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine))
