"""
applications_view.py - Industrial Domain Suitability & Multi-Criteria Ranking View
Evaluates the alloy against 10 critical industrial sectors with ranked bars and table.
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
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Sector", "Suitability (%)", "Assessment"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(
            "QTableWidget { background-color: #252526; color: #FFFFFF; gridline-color: #3E3E42; }"
            "QHeaderView::section { background-color: #2D2D30; color: #FFFFFF; padding: 4px; font-weight: bold; }"
        )
        splitter.addWidget(self.table)
        splitter.setSizes([450, 400])

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
            sector = item.get("sector", "")
            score = item.get("score", 0.0)
            status = item.get("status", "Suitable")

            it_sector = QTableWidgetItem(sector)
            it_score = QTableWidgetItem(f"{score:.1f}%")
            it_score.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_status = QTableWidgetItem(status)

            # Color coding
            if score >= 75.0:
                it_score.setForeground(QColor("#4CAF50"))
            elif score >= 50.0:
                it_score.setForeground(QColor("#FF9800"))
            else:
                it_score.setForeground(QColor("#F44336"))

            self.table.setItem(row, 0, it_sector)
            self.table.setItem(row, 1, it_score)
            self.table.setItem(row, 2, it_status)

        # Horizontal Bar Chart
        y_pos = np.arange(len(sorted_scores))
        scores_arr = [s.get("score", 0.0) for s in reversed(sorted_scores)]
        names = [s.get("sector", "") for s in reversed(sorted_scores)]

        # Custom string axis for y
        y_axis = self.plot_widget.getPlotItem().getAxis("left")
        y_axis.setTicks([[(i, name) for i, name in enumerate(names)]])

        bar_item = pg.BarGraphItem(x0=0, y=y_pos, height=0.6, width=scores_arr,
                                   brush=pg.mkBrush("#2196F3"), pen=pg.mkPen("#64B5F6", width=1.0))
        self.plot_widget.addItem(bar_item)
        self.plot_widget.setXRange(0, 100)
