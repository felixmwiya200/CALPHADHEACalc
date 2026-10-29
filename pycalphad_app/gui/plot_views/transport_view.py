"""
transport_view.py - Thermophysical & Transport Properties View
Renders Density, CTE, and Thermal Conductivity vs. Temperature.
"""

from typing import Dict, Any
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGridLayout
from PyQt6.QtGui import QFont


class TransportView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("Thermophysical & Transport Properties vs. Temperature")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 3 subplots in a grid
        grid = QGridLayout()
        layout.addLayout(grid)

        # 1. Density
        self.plot_density = pg.PlotWidget()
        self.plot_density.setBackground("#1E1E1E")
        self.plot_density.showGrid(x=True, y=True, alpha=0.3)
        self.plot_density.setLabel("left", "Density", units="g/cm³")
        self.plot_density.setLabel("bottom", "Temperature", units="K")
        grid.addWidget(self.plot_density, 0, 0)

        # 2. Thermal Expansion (CTE)
        self.plot_cte = pg.PlotWidget()
        self.plot_cte.setBackground("#1E1E1E")
        self.plot_cte.showGrid(x=True, y=True, alpha=0.3)
        self.plot_cte.setLabel("left", "CTE", units="10⁻⁶ / K")
        self.plot_cte.setLabel("bottom", "Temperature", units="K")
        grid.addWidget(self.plot_cte, 0, 1)

        # 3. Thermal Conductivity
        self.plot_k = pg.PlotWidget()
        self.plot_k.setBackground("#1E1E1E")
        self.plot_k.showGrid(x=True, y=True, alpha=0.3)
        self.plot_k.setLabel("left", "Thermal Cond.", units="W/(m·K)")
        self.plot_k.setLabel("bottom", "Temperature", units="K")
        grid.addWidget(self.plot_k, 1, 0, 1, 2)

    def update_data(self, results: Dict[str, Any]):
        self.plot_density.clear()
        self.plot_cte.clear()
        self.plot_k.clear()

        thermo = results.get("thermo", {})
        rho_0 = thermo.get("Density_g_cm3", 8.0)
        sol_k = thermo.get("Solidus_K", 1400.0)

        T = np.linspace(300.0, 1800.0, 200)

        # Density thermal contraction
        # rho(T) = rho_0 / (1 + 3*alpha*(T - 300))
        alpha = 1.35e-5
        rho_T = rho_0 / (1.0 + 3.0 * alpha * (T - 300.0))
        # Sudden drop at melting
        rho_T = np.where(T > sol_k, rho_T * 0.94, rho_T)

        self.plot_density.plot(T, rho_T, pen=pg.mkPen("#4CAF50", width=2.5))
        self.plot_density.addLine(x=sol_k, pen=pg.mkPen("#F44336", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine))

        # CTE vs T: alpha(T) = alpha_0 * (1 + 0.0004 * (T - 300))
        cte_T = (12.5 + 0.005 * (T - 300.0))
        self.plot_cte.plot(T, cte_T, pen=pg.mkPen("#FF9800", width=2.5))

        # Thermal Conductivity: Wiedemann-Franz + phonon lattice scattering
        # k(T) = k_0 + 0.009 * (T - 300)
        k_0 = 12.0 if not results.get("is_coating", False) else 16.4
        k_T = k_0 + 0.0085 * (T - 300.0)
        self.plot_k.plot(T, k_T, pen=pg.mkPen("#00BCD4", width=2.5))
        self.plot_k.addLine(x=sol_k, pen=pg.mkPen("#F44336", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine))
