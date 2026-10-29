# -*- coding: utf-8 -*-
"""
applications_view.py - Industrial Domain Suitability & Multi-Criteria Ranking View
Evaluates the alloy against 12 critical industrial sectors with ranked bars and table.
All plots rendered in OriginLab-grade scientific light theme (#FFFFFF canvas).
"""

from typing import Dict, Any
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

from pycalphad_app.gui.plot_theme import apply_scientific_light_theme


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
        apply_scientific_light_theme(
            self.plot_widget,
            title="Multi-Domain Industrial Suitability Index",
            x_label="Suitability Index Score",
            y_label="Industrial Sector",
            x_units="%"
        )
        splitter.addWidget(self.plot_widget)

        # Right: Ranked Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Sector / Application", "Score (%)", "Match Tier", "Bottleneck / Advice"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
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
            notes = item.get("bottleneck", item.get("advice", "Meets target specification criteria."))

            it_name = QTableWidgetItem(name)
            it_score = QTableWidgetItem(f"{score:.1f}%")
            it_tier = QTableWidgetItem(tier)
            it_notes = QTableWidgetItem(notes)

            # Color code tier
            if "Prime" in tier or "Optimal" in tier or score >= 80:
                it_tier.setBackground(QColor("#DCFCE7"))
                it_tier.setForeground(QColor("#15803D"))
            elif "Viable" in tier or "Suitable" in tier or score >= 60:
                it_tier.setBackground(QColor("#EFF6FF"))
                it_tier.setForeground(QColor("#1D4ED8"))
            elif "Conditional" in tier or score >= 40:
                it_tier.setBackground(QColor("#FEF3C7"))
                it_tier.setForeground(QColor("#B45309"))
            else:
                it_tier.setBackground(QColor("#FEE2E2"))
                it_tier.setForeground(QColor("#B91C1C"))

            it_score.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_tier.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, it_name)
            self.table.setItem(row, 1, it_score)
            self.table.setItem(row, 2, it_tier)
            self.table.setItem(row, 3, it_notes)

        # Horizontal Bar Chart
        sectors = [it.get("name", it.get("sector", "")) for it in sorted_scores]
        scores = [float(it.get("score", 0.0)) for it in sorted_scores]
        y_pos = np.arange(len(sectors))

        # Horizontal bars in professional scientific blue
        bg = pg.BarGraphItem(
            x0=0, y=y_pos, height=0.6, width=scores,
            brush=pg.mkBrush("#2563EB"),
            pen=pg.mkPen("#1D4ED8", width=1.0)
        )
        self.plot_widget.addItem(bg)

        # Set category tick labels
        ay = self.plot_widget.getAxis('left')
        ay.setTicks([[(y_val, sec) for y_val, sec in zip(y_pos, sectors)]])
        self.plot_widget.setXRange(0, 105)
