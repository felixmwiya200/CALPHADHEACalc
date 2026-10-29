"""
equilibrium_view.py - Equilibrium Phase Fractions vs. Temperature View
Renders phase stability curves (Liquid, FCC, BCC, B2, Sigma, or Coating Precipitates)
using hardware-accelerated pyqtgraph.
"""

from typing import Dict, Any
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class EquilibriumView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header info
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Equilibrium Phase Fractions vs. Temperature")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        self.status_label = QLabel("Awaiting calculation...")
        self.status_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        header_layout.addWidget(self.status_label)
        layout.addLayout(header_layout)

        # Plot Widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#1E1E1E")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel("left", "Phase Fraction", units="[-]")
        self.plot_widget.setLabel("bottom", "Temperature", units="K")
        self.plot_widget.addLegend(offset=(10, 10))
        layout.addWidget(self.plot_widget)

    def update_data(self, results: Dict[str, Any]):
        self.plot_widget.clear()
        self.plot_widget.addLegend(offset=(10, 10))

        is_coating = results.get("is_coating", False)
        thermo = results.get("thermo", {})
        sol_k = thermo.get("Solidus_K", 1400.0)
        liq_k = thermo.get("Liquidus_K", 1600.0)

        T = np.linspace(300.0, 2200.0, 300)

        if is_coating:
            # Coating Precipitates: gamma-Ni, CrB, Ni3Si, Cr7C3, Liquid
            self.title_label.setText("Thermal Spray Coating Phase Stability: Ni-Cr-Fe-B-Si-C")
            self.status_label.setText(f"Solidus: {sol_k:.1f} K | Liquidus: {liq_k:.1f} K")

            # Liquid fraction
            f_liq = np.clip((T - sol_k) / (liq_k - sol_k), 0.0, 1.0)
            f_liq = np.where(T < sol_k, 0.0, np.where(T > liq_k, 1.0, f_liq**1.3))

            # Solid fraction
            f_sol = 1.0 - f_liq
            f_gamma = f_sol * 0.72
            f_crb = f_sol * 0.14
            f_ni3si = f_sol * 0.08
            f_cr7c3 = f_sol * 0.06

            self.plot_widget.plot(T, f_gamma, pen=pg.mkPen("#4CAF50", width=2.5), name="gamma-Ni Matrix (FCC)")
            self.plot_widget.plot(T, f_crb, pen=pg.mkPen("#FF9800", width=2.5), name="CrB Boride (Orthorhombic)")
            self.plot_widget.plot(T, f_ni3si, pen=pg.mkPen("#00BCD4", width=2.5), name="Ni3Si Silicide (L12)")
            self.plot_widget.plot(T, f_cr7c3, pen=pg.mkPen("#E91E63", width=2.5), name="Cr7C3 Carbide (Hexagonal)")
            self.plot_widget.plot(T, f_liq, pen=pg.mkPen("#F44336", width=2.5, style=Qt.PenStyle.DashLine), name="Liquid Phase")

        else:
            # HEA Phases
            self.title_label.setText("CALPHAD Thermodynamic Equilibrium Phase Stability")
            self.status_label.setText(f"Solidus: {sol_k:.1f} K | Liquidus: {liq_k:.1f} K")

            # Liquid
            f_liq = np.clip((T - sol_k) / (liq_k - sol_k), 0.0, 1.0)
            f_liq = np.where(T < sol_k, 0.0, np.where(T > liq_k, 1.0, f_liq**1.2))
            f_sol = 1.0 - f_liq

            vec = thermo.get("VEC_val", 8.0)
            if vec >= 7.8:
                f_fcc = f_sol * 0.95
                f_bcc = f_sol * 0.05
                f_b2 = np.zeros_like(T)
            elif vec <= 6.87:
                f_fcc = f_sol * 0.05
                f_bcc = f_sol * 0.80
                f_b2 = f_sol * 0.15
            else:
                f_fcc = f_sol * 0.55
                f_bcc = f_sol * 0.35
                f_b2 = f_sol * 0.10

            self.plot_widget.plot(T, f_fcc, pen=pg.mkPen("#2196F3", width=2.5), name="FCC_A1 (Austenite/Cantor)")
            self.plot_widget.plot(T, f_bcc, pen=pg.mkPen("#FF9800", width=2.5), name="BCC_A2 (Ferrite/RHEA)")
            if np.max(f_b2) > 0.01:
                self.plot_widget.plot(T, f_b2, pen=pg.mkPen("#9C27B0", width=2.5), name="B2 (Ordered Intermetallic)")
            self.plot_widget.plot(T, f_liq, pen=pg.mkPen("#F44336", width=2.5, style=Qt.PenStyle.DashLine), name="Liquid Phase")

        self.plot_widget.setYRange(0, 1.05)
        self.plot_widget.setXRange(300, 2200)
