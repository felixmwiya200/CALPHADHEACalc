"""
equilibrium_view.py - Equilibrium Phase Fractions vs. Temperature View
Renders phase stability curves (Liquid, FCC, BCC, B2, Sigma, or Coating Precipitates)
using hardware-accelerated pyqtgraph with OriginLab-style navigation tools.
"""

from typing import Dict, Any
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from pycalphad_app.gui.graph_toolbar import GraphNavigationToolbar


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

        # OriginLab Navigation Toolbar
        self.nav_toolbar = GraphNavigationToolbar(self.plot_widget, title="Equilibrium Phases", parent=self)
        layout.addWidget(self.nav_toolbar)
        layout.addWidget(self.plot_widget)

    def update_data(self, results: Dict[str, Any]):
        self.plot_widget.clear()
        self.plot_widget.addLegend(offset=(10, 10))

        is_coating = results.get("is_coating", False)
        thermo = results.get("thermo", {})
        sol_k = float(thermo.get("Solidus_K", 1400.0))
        liq_k = float(thermo.get("Liquidus_K", 1600.0))
        pf = thermo.get("PhaseFractions", {})

        if is_coating:
            self.title_label.setText("Thermal Spray Coating Phase Stability: Ni-Cr-Fe-B-Si-C")
            self.status_label.setText(f"Solidus: {sol_k:.1f} K | Liquidus: {liq_k:.1f} K")

            if isinstance(pf, dict) and "T_K" in pf:
                t_k = pf["T_K"]
                self.plot_widget.plot(t_k, pf.get("gamma_Ni_FCC", np.zeros_like(t_k)), pen=pg.mkPen("#4CAF50", width=2.5), name="γ-Ni Matrix (FCC)")
                self.plot_widget.plot(t_k, pf.get("CrB_Boride", np.zeros_like(t_k)), pen=pg.mkPen("#FF9800", width=2.5), name="CrB Boride (Orthorhombic)")
                self.plot_widget.plot(t_k, pf.get("Ni3Si_Silicide", np.zeros_like(t_k)), pen=pg.mkPen("#00BCD4", width=2.5), name="Ni3Si Silicide (L12)")
                self.plot_widget.plot(t_k, pf.get("Cr7C3_Carbide", np.zeros_like(t_k)), pen=pg.mkPen("#E91E63", width=2.5), name="Cr7C3 Carbide (Hexagonal)")
                self.plot_widget.plot(t_k, pf.get("Liquid", np.zeros_like(t_k)), pen=pg.mkPen("#F44336", width=2.5, style=Qt.PenStyle.DashLine), name="Liquid Phase")
            else:
                T = np.linspace(300.0, 2200.0, 300)
                f_liq = np.clip((T - sol_k) / max(1.0, (liq_k - sol_k)), 0.0, 1.0) ** 1.3
                f_sol = 1.0 - f_liq
                self.plot_widget.plot(T, f_sol * 0.72, pen=pg.mkPen("#4CAF50", width=2.5), name="γ-Ni Matrix (FCC)")
                self.plot_widget.plot(T, f_sol * 0.14, pen=pg.mkPen("#FF9800", width=2.5), name="CrB Boride (Orthorhombic)")
                self.plot_widget.plot(T, f_sol * 0.08, pen=pg.mkPen("#00BCD4", width=2.5), name="Ni3Si Silicide (L12)")
                self.plot_widget.plot(T, f_sol * 0.06, pen=pg.mkPen("#E91E63", width=2.5), name="Cr7C3 Carbide (Hexagonal)")
                self.plot_widget.plot(T, f_liq, pen=pg.mkPen("#F44336", width=2.5, style=Qt.PenStyle.DashLine), name="Liquid Phase")

        else:
            solver_info = pf.get("Solver", "CALPHAD Equilibrium Minimizer") if isinstance(pf, dict) else "CALPHAD Model"
            self.title_label.setText(f"Equilibrium Phase Stability ({solver_info})")
            self.status_label.setText(f"Solidus: {sol_k:.1f} K | Liquidus: {liq_k:.1f} K")

            if isinstance(pf, dict) and "T_K" in pf:
                t_k = pf["T_K"]
                if "FCC" in pf and np.any(pf["FCC"] > 0):
                    self.plot_widget.plot(t_k, pf["FCC"], pen=pg.mkPen("#2196F3", width=2.5), name="FCC_A1 (Austenite/Cantor)")
                if "BCC" in pf and np.any(pf["BCC"] > 0):
                    self.plot_widget.plot(t_k, pf["BCC"], pen=pg.mkPen("#FF9800", width=2.5), name="BCC_A2 (Ferrite/RHEA)")
                if "B2" in pf and np.any(pf["B2"] > 0):
                    self.plot_widget.plot(t_k, pf["B2"], pen=pg.mkPen("#00BCD4", width=2.5), name="B2 Ordered (CsCl)")
                if "Sigma" in pf and np.any(pf["Sigma"] > 0):
                    self.plot_widget.plot(t_k, pf["Sigma"], pen=pg.mkPen("#9C27B0", width=2.0), name="Sigma Phase (TCP)")
                if "Liquid" in pf:
                    self.plot_widget.plot(t_k, pf["Liquid"], pen=pg.mkPen("#F44336", width=2.5, style=Qt.PenStyle.DashLine), name="Liquid Phase")
            else:
                T = np.linspace(300.0, 2200.0, 300)
                f_liq = np.clip((T - sol_k) / max(1.0, (liq_k - sol_k)), 0.0, 1.0) ** 1.2
                f_sol = 1.0 - f_liq
                vec = float(thermo.get("VEC", thermo.get("VEC_val", 8.0)))
                f_fcc = f_sol * (0.95 if vec >= 7.8 else (0.05 if vec <= 6.87 else 0.55))
                f_bcc = f_sol * (0.05 if vec >= 7.8 else (0.80 if vec <= 6.87 else 0.35))
                f_b2 = f_sol * (0.0 if vec >= 7.8 else (0.15 if vec <= 6.87 else 0.10))

                self.plot_widget.plot(T, f_fcc, pen=pg.mkPen("#2196F3", width=2.5), name="FCC_A1 (Austenite/Cantor)")
                self.plot_widget.plot(T, f_bcc, pen=pg.mkPen("#FF9800", width=2.5), name="BCC_A2 (Ferrite/RHEA)")
                if np.any(f_b2 > 0):
                    self.plot_widget.plot(T, f_b2, pen=pg.mkPen("#00BCD4", width=2.5), name="B2 Ordered (CsCl)")
                self.plot_widget.plot(T, f_liq, pen=pg.mkPen("#F44336", width=2.5, style=Qt.PenStyle.DashLine), name="Liquid Phase")

        self.plot_widget.addLine(x=sol_k, pen=pg.mkPen("#2196F3", width=1.2, style=Qt.PenStyle.DashLine))
        self.plot_widget.addLine(x=liq_k, pen=pg.mkPen("#F44336", width=1.2, style=Qt.PenStyle.DashLine))
