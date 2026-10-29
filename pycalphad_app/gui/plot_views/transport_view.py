"""
transport_view.py - Thermophysical & Transport Properties View
Renders Density, CTE, and Thermal Conductivity vs. Temperature
with OriginLab-style navigation tools.
"""

from typing import Dict, Any
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGridLayout
from PyQt6.QtGui import QFont

from pycalphad_app.gui.graph_toolbar import GraphNavigationToolbar


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

        # OriginLab Navigation Toolbar attached to density plot
        self.nav_toolbar = GraphNavigationToolbar(self.plot_density, title="Transport Properties", parent=self)
        layout.insertWidget(1, self.nav_toolbar)

    def update_data(self, results: Dict[str, Any]):
        self.plot_density.clear()
        self.plot_cte.clear()
        self.plot_k.clear()

        thermo = results.get("thermo", {})
        rho_0 = float(thermo.get("Density_g_cm3", thermo.get("density", 8.0)))
        sol_k = float(thermo.get("Solidus_K", 1400.0))
        transport = thermo.get("Transport", {})

        if isinstance(transport, dict) and "T_K" in transport:
            T = transport["T_K"]
            # density_kg_m3 to g/cm3
            rho_T = transport.get("density_kg_m3", np.ones_like(T) * rho_0 * 1000.0) / 1000.0
            k_T = transport.get("thermal_conductivity_W_mK", np.ones_like(T) * 15.0)
            cte_val = float(transport.get("cte_1e6_K", 13.5))
            cte_T = cte_val + 0.005 * (T - 300.0)
        else:
            T = np.linspace(300.0, 1800.0, 200)
            alpha = 1.35e-5
            rho_T = rho_0 / (1.0 + 3.0 * alpha * (T - 300.0))
            rho_T = np.where(T > sol_k, rho_T * 0.94, rho_T)
            cte_T = 12.5 + 0.005 * (T - 300.0)
            k_0 = 16.4 if results.get("is_coating", False) else 12.0
            k_T = k_0 + 0.0085 * (T - 300.0)

        self.plot_density.plot(T, rho_T, pen=pg.mkPen("#4CAF50", width=2.5))
        self.plot_density.addLine(x=sol_k, pen=pg.mkPen("#F44336", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine))

        self.plot_cte.plot(T, cte_T, pen=pg.mkPen("#FF9800", width=2.5))

        self.plot_k.plot(T, k_T, pen=pg.mkPen("#00BCD4", width=2.5))
        self.plot_k.addLine(x=sol_k, pen=pg.mkPen("#F44336", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine))
