"""
applications_view.py - Industrial Domain Suitability & Multi-Criteria Ranking View
Evaluates the alloy against 12 critical industrial sectors with ranked bars and table.
"""

from typing import Dict, Any
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSplitter)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt


class ApplicationsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("Industrial Domain Suitability & Multi-Criteria Evaluation")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left: Bar chart of scores
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#1E1E1E")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel("left", "Industrial Sector")
        self.plot_widget.setLabel("bottom", "Suitability Index Score", units="[%]")
        splitter.addWidget(self.plot_widget)

        # Right: Ranked Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Sector / Application", "Score (%)", "Match Tier", "Bottleneck / Advice"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(
            "QTableWidget { background-color: #252526; color: #FFFFFF; gridline-color: #3E3E42; }"
            "QHeaderView::section { background-color: #2D2D30; color: #FFFFFF; padding: 4px; font-weight: bold; }"
        )
        splitter.addWidget(self.table)
        splitter.setSizes([450, 550])

    def update_data(self, results: Dict[str, Any]):
        self.plot_widget.clear()

        app_scores = results.get("application_scores", [])
        if not app_scores:
            return

        # Sort descending
        sorted_scores = sorted(app_scores, key=lambda x: x.get("score", 0.0), reverse=True)

        # Populate Table
        self.table.setRowCount(len(sorted_scores))
        for row, item in enumerate(sorted_scores):
            name = item.get("name", item.get("sector", ""))
            score = float(item.get("score", 0.0))
            tier = item.get("tier", item.get("status", "Suitable"))
            bottle = item.get("bottleneck", "")
            adv = item.get("advice", "")
            info_text = f"{bottle} | {adv}" if adv and bottle != "Balanced" else bottle

            it_name = QTableWidgetItem(name)
            it_score = QTableWidgetItem(f"{score:.1f}%")
            it_score.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_tier = QTableWidgetItem(tier)
            it_info = QTableWidgetItem(info_text)

            # Color coding
            if score >= 75.0:
                it_score.setForeground(QColor("#4CAF50"))
            elif score >= 50.0:
                it_score.setForeground(QColor("#FF9800"))
            else:
                it_score.setForeground(QColor("#F44336"))

            self.table.setItem(row, 0, it_name)
            self.table.setItem(row, 1, it_score)
            self.table.setItem(row, 2, it_tier)
            self.table.setItem(row, 3, it_info)

        # Horizontal Bar Chart
        y_pos = np.arange(len(sorted_scores))
        scores_arr = [float(s.get("score", 0.0)) for s in reversed(sorted_scores)]
        names = [s.get("name", s.get("sector", ""))[:28] for s in reversed(sorted_scores)]

        # Custom string axis for y
        y_axis = self.plot_widget.getPlotItem().getAxis("left")
        y_axis.setTicks([[(i, name) for i, name in enumerate(names)]])

        bar_item = pg.BarGraphItem(x0=0, y=y_pos, height=0.6, width=scores_arr,
                                   brush=pg.mkBrush("#2196F3"), pen=pg.mkPen("#64B5F6", width=1.0))
        self.plot_widget.addItem(bar_item)
        self.plot_widget.setXRange(0, 100)
