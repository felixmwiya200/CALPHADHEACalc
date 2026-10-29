"""
xrd_view.py - Kinematic Powder XRD & Authentic Experimental Diffractogram View
Renders the synthetic diffraction pattern, authentic literature experimental overlay,
prominent (hkl) Miller indices, and peer-reviewed citation banner
with OriginLab-style navigation tools.
"""

from typing import Dict, Any
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTextEdit
from PyQt6.QtGui import QFont

from pycalphad_app.gui.graph_toolbar import GraphNavigationToolbar


class XRDView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("Kinematic Powder XRD Diffractometer (Cu-Kα, λ = 1.5406 Å)")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Plot Widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#1E1E1E")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel("left", "Relative Intensity I / I_max", units="[%]")
        self.plot_widget.setLabel("bottom", "Diffraction Angle 2θ", units="degrees")
        self.plot_widget.addLegend(offset=(10, 10))

        # OriginLab Navigation Toolbar
        self.nav_toolbar = GraphNavigationToolbar(self.plot_widget, title="XRD Diffractogram", parent=self)
        layout.addWidget(self.nav_toolbar)
        layout.addWidget(self.plot_widget, stretch=3)

        # Authentic Citation Banner
        self.citation_box = QTextEdit()
        self.citation_box.setReadOnly(True)
        self.citation_box.setMaximumHeight(85)
        self.citation_box.setStyleSheet(
            "background-color: #252526; color: #CCCCCC; border: 1px solid #3E3E42; "
            "font-family: 'Segoe UI'; font-size: 10pt; padding: 4px;"
        )
        layout.addWidget(self.citation_box, stretch=1)

    def update_data(self, results: Dict[str, Any]):
        self.plot_widget.clear()
        self.plot_widget.addLegend(offset=(10, 10))

        xrd = results.get("xrd", {})
        two_theta = xrd.get("TwoTheta_deg", xrd.get("two_theta_deg", np.linspace(20.0, 100.0, 800)))
        intensity_calc = xrd.get("Intensity_percent", xrd.get("intensity_norm", np.zeros_like(two_theta)))
        if np.max(intensity_calc) <= 1.0 and np.max(intensity_calc) > 0:
            intensity_calc = intensity_calc * 100.0

        peaks = xrd.get("Peaks", xrd.get("peaks", []))
        rad_tube = xrd.get("RadiationTube", "Cu-Ka (λ = 1.5406 Å)")
        self.title_label.setText(f"Kinematic Powder XRD Diffractometer ({rad_tube})")

        # 1. Plot Calculated Diffractogram
        self.plot_widget.plot(two_theta, intensity_calc, pen=pg.mkPen("#2196F3", width=2.0),
                              name="Kinematic Simulation")

        # 2. Plot Authentic Experimental Overlay
        has_bench = xrd.get("HasBenchmark", False)
        bench_tt = xrd.get("BenchmarkTwoTheta")
        bench_int = xrd.get("BenchmarkIntensity")
        bench_title = xrd.get("BenchmarkTitle", "Literature Benchmark")
        bench_cite = xrd.get("BenchmarkCitation", "Peer-Reviewed Experimental Literature")

        if has_bench and bench_tt is not None and len(bench_tt) > 0 and bench_int is not None:
            self.plot_widget.plot(bench_tt, bench_int,
                                  pen=pg.mkPen("#4CAF50", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine),
                                  name=bench_title)
        else:
            int_exp = xrd.get("Intensity_exp", xrd.get("intensity_exp_norm"))
            if int_exp is not None and len(int_exp) == len(two_theta):
                self.plot_widget.plot(two_theta, int_exp,
                                      pen=pg.mkPen("#4CAF50", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine),
                                      name="Literature Experimental Overlay")

        # 3. Annotate Peaks with (hkl) Miller Indices
        for pk in peaks:
            if isinstance(pk, dict):
                pos_2th = float(pk.get("TwoTheta", pk.get("two_theta", 0.0)))
                int_pk = float(pk.get("Intensity", pk.get("intensity", 0.0)))
                if int_pk <= 1.0: int_pk *= 100.0
                hkl = pk.get("HKL", pk.get("hkl", ""))
                phase = pk.get("Phase", pk.get("phase", ""))
            else:
                continue

            if int_pk > 3.0:
                label = f"{phase}\n{hkl}"
                text = pg.TextItem(text=label, color="#FFEB3B", anchor=(0.5, 1.2))
                text.setPos(pos_2th, int_pk)
                self.plot_widget.addItem(text)

                self.plot_widget.plot([pos_2th, pos_2th], [0.0, int_pk],
                                      pen=pg.mkPen("#FFEB3B", width=1.0, style=pg.QtCore.Qt.PenStyle.DotLine))

        self.plot_widget.setXRange(20.0, 100.0)
        self.plot_widget.setYRange(0.0, 120.0)

        # 4. Format Citation Banner
        html = f"""
        <b>Authentic Literature XRD Citation:</b><br/>
        <b>Reference:</b> {bench_cite}<br/>
        <b>Title:</b> {bench_title} | 
        <b>Radiation Source:</b> {rad_tube}, Graphite Monochromator.
        """
        self.citation_box.setHtml(html)
