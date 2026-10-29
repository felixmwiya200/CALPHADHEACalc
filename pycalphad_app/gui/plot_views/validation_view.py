"""
validation_view.py - Quantitative Experimental Literature Audit & Error Analysis View
Addresses user feedback: "All the graphs have errors" & "supporting data for experimental".
Renders full quantitative audit table with Calculated, Experimental, Absolute Deviation,
Error %, Reference, and DOI, plus overall Mean Absolute Percentage Error (MAPE) badge.
"""

from typing import Dict, Any, List
import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt


class ValidationView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("Peer-Reviewed Quantitative Literature Audit & Validation")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.mape_badge = QLabel("Overall MAPE: -- %")
        self.mape_badge.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.mape_badge.setStyleSheet(
            "background-color: #2E7D32; color: #FFFFFF; padding: 4px 12px; border-radius: 4px;"
        )
        header_layout.addWidget(self.mape_badge)
        layout.addLayout(header_layout)

        # Audit Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Physical Property", "Calculated", "Experimental", "Deviation", "Error (%)", "Reference & DOI"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(
            "QTableWidget { background-color: #252526; color: #FFFFFF; gridline-color: #3E3E42; }"
            "QHeaderView::section { background-color: #2D2D30; color: #FFFFFF; padding: 5px; font-weight: bold; }"
        )
        layout.addWidget(self.table, stretch=3)

        # Citation Details Panel
        self.citation_panel = QTextEdit()
        self.citation_panel.setReadOnly(True)
        self.citation_panel.setMaximumHeight(110)
        self.citation_panel.setStyleSheet(
            "background-color: #1E1E1E; color: #B0BEC5; border: 1px solid #37474F; "
            "font-family: 'Segoe UI'; font-size: 9.5pt; padding: 6px;"
        )
        layout.addWidget(self.citation_panel, stretch=1)

    def update_data(self, results: Dict[str, Any]):
        val_table = results.get("validation_table", [])
        citations = results.get("validation_citations", [])

        if not val_table:
            self.table.setRowCount(0)
            self.mape_badge.setText("No Direct Benchmark Match")
            self.mape_badge.setStyleSheet("background-color: #546E7A; color: #FFFFFF; padding: 4px 12px; border-radius: 4px;")
            self.citation_panel.setHtml("<i>No direct single-alloy benchmark match found. System evaluated via generalized CALPHAD equations.</i>")
            return

        self.table.setRowCount(len(val_table))
        errors = []

        for row, item in enumerate(val_table):
            prop = item.get("Property", "")
            calc_val = item.get("Calculated", 0.0)
            exp_val = item.get("Experimental", 0.0)
            diff = item.get("Deviation", 0.0)
            err_pct = item.get("ErrorPercent", 0.0)
            ref = item.get("Reference", "")
            doi = item.get("DOI", "")

            errors.append(err_pct)

            it_prop = QTableWidgetItem(prop)
            it_calc = QTableWidgetItem(f"{calc_val:.2f}" if abs(calc_val) < 10000 else f"{calc_val:.2e}")
            it_exp = QTableWidgetItem(f"{exp_val:.2f}" if abs(exp_val) < 10000 else f"{exp_val:.2e}")
            it_diff = QTableWidgetItem(f"{diff:+.2f}" if abs(diff) < 10000 else f"{diff:+.2e}")
            it_err = QTableWidgetItem(f"{err_pct:.1f}%")
            it_ref = QTableWidgetItem(f"{ref} ({doi})" if doi else ref)

            # Alignment
            for it in (it_calc, it_exp, it_diff, it_err):
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Color coding by accuracy
            if err_pct <= 5.0:
                it_err.setForeground(QColor("#4CAF50"))
            elif err_pct <= 15.0:
                it_err.setForeground(QColor("#FFB74D"))
            else:
                it_err.setForeground(QColor("#E57373"))

            self.table.setItem(row, 0, it_prop)
            self.table.setItem(row, 1, it_calc)
            self.table.setItem(row, 2, it_exp)
            self.table.setItem(row, 3, it_diff)
            self.table.setItem(row, 4, it_err)
            self.table.setItem(row, 5, it_ref)

        # Overall MAPE
        mape = float(np.mean(errors)) if errors else 0.0
        self.mape_badge.setText(f"Overall MAPE: {mape:.2f}%")
        if mape <= 5.0:
            badge_color = "#2E7D32"  # Green
        elif mape <= 12.0:
            badge_color = "#F57C00"  # Orange
        else:
            badge_color = "#C62828"  # Red
        self.mape_badge.setStyleSheet(f"background-color: {badge_color}; color: #FFFFFF; padding: 4px 12px; border-radius: 4px;")

        # Render Citations HTML
        c_lines = ["<b>Authoritative Supporting Experimental Literature Citations:</b><br/>"]
        for cit in citations:
            auth = cit.get("authors", "")
            yr = cit.get("year", "")
            jrnl = cit.get("journal", "")
            doi_str = cit.get("doi", "")
            c_lines.append(f"• <b>{auth}</b> ({yr}). <i>{jrnl}</i>. DOI: <a href='https://doi.org/{doi_str}' style='color: #64B5F6;'>{doi_str}</a><br/>")

        self.citation_panel.setHtml("".join(c_lines))
