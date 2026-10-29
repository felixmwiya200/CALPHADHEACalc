"""
environmental_view.py - Environmental Durability & Degradation View
Renders Wagner high-temperature parabolic oxidation mass gain vs. time
and Stern-Geary potentiodynamic polarization (Tafel) curves in 3.5 wt% NaCl.
"""

from typing import Dict, Any
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGridLayout
from PyQt6.QtGui import QFont


class EnvironmentalView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("Environmental Durability: Oxidation & Corrosion Kinetics")
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
        grid.addWidget(self.plot_ox, 0, 0)

        # 2. Tafel Polarization
        self.plot_corr = pg.PlotWidget()
        self.plot_corr.setBackground("#1E1E1E")
        self.plot_corr.showGrid(x=True, y=True, alpha=0.3)
        self.plot_corr.setLabel("left", "Potential E", units="V vs SCE")
        self.plot_corr.setLabel("bottom", "Log Current Density log₁₀(i)", units="μA/cm²")
        grid.addWidget(self.plot_corr, 0, 1)

    def update_data(self, results: Dict[str, Any]):
        self.plot_ox.clear()
        self.plot_corr.clear()

        ox = results.get("oxidation", {})
        corr = results.get("corrosion", {})

        kp = ox.get("Oxidation_kp", 5.0e-9)
        ecorr = corr.get("Corrosion_Ecorr_V", -0.28)
        icorr = corr.get("Corrosion_icorr_uA", 0.42)
        crate = corr.get("CorrosionRate_mm_yr", 0.005)

        self.metrics_label.setText(f"kp: {kp:.2e} g²/(cm⁴·s) | Ecorr: {ecorr:.3f} V | icorr: {icorr:.2f} μA/cm² | Rate: {crate:.4f} mm/yr")

        # 1. Wagner Parabolic Mass Gain vs Time (0 to 100 hours at 1000 °C)
        t_hours = np.linspace(0.0, 100.0, 150)
        t_seconds = t_hours * 3600.0
        # (Delta m / A)^2 = kp * t  =>  Delta m / A = sqrt(kp * t) (g/cm^2) * 1000 (mg/cm^2)
        mass_gain = np.sqrt(kp * t_seconds) * 1000.0

        self.plot_ox.plot(t_hours, mass_gain, pen=pg.mkPen("#FF9800", width=2.5), name="1000 °C Parabolic Kinetics")

        # 2. Tafel Polarization in 3.5 wt% NaCl
        # E - Ecorr = beta_a * log(i/icorr) for anodic branch
        # E - Ecorr = -beta_c * log(i/icorr) for cathodic branch
        beta_a = 0.120  # V/decade
        beta_c = 0.120  # V/decade

        log_i = np.linspace(np.log10(icorr) - 3.0, np.log10(icorr) + 3.0, 200)
        i_ratio = 10.0**(log_i - np.log10(icorr))

        # Butler-Volmer synthetic polarization curve
        E_anodic = ecorr + beta_a * np.log10(np.maximum(i_ratio - 1.0, 1e-6))
        E_cathodic = ecorr - beta_c * np.log10(np.maximum(1.0 / i_ratio - 1.0, 1e-6))
        
        # Combine smoothly
        E_tafel = np.where(log_i >= np.log10(icorr),
                           ecorr + beta_a * (log_i - np.log10(icorr)),
                           ecorr - beta_c * (np.log10(icorr) - log_i))

        self.plot_corr.plot(log_i, E_tafel, pen=pg.mkPen("#4CAF50", width=2.5), name="Tafel Polarization")
        self.plot_corr.plot([np.log10(icorr)], [ecorr], pen=None, symbol='star', symbolSize=12,
                            symbolBrush=pg.mkBrush("#FFEB3B"), name="Corrosion Point (Ecorr, icorr)")
        self.plot_corr.addLine(y=ecorr, pen=pg.mkPen("#2196F3", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine))
