"""
database_modal.py - Modal Database Selector Dialog
Presents the 14-database registry at app startup or via menu bar, matching the
reference layout from JMatPro / CALPHAD suites with live dossier preview.
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QPushButton, QTextEdit, QGroupBox,
                             QSplitter, QWidget)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

from pycalphad_app.database.material_selector import MaterialDatabaseSelector


class DatabaseModalDialog(QDialog):
    def __init__(self, current_db: str = "High Entropy Alloys", parent=None):
        super().__init__(parent)
        self.setWindowTitle("CALPHAD Suite - Select Active Materials Database")
        self.setMinimumSize(720, 500)
        self.resize(760, 520)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; color: #FFFFFF; }
            QLabel { color: #E0E0E0; }
            QGroupBox { color: #FFFFFF; font-weight: bold; border: 1px solid #3E3E42; margin-top: 6px; padding-top: 10px; }
            QListWidget { background-color: #252526; color: #FFFFFF; border: 1px solid #3E3E42; font-size: 10pt; }
            QListWidget::item:selected { background-color: #094771; color: #FFFFFF; }
            QListWidget::item:hover { background-color: #2A2D2E; }
            QTextEdit { background-color: #252526; color: #CCCCCC; border: 1px solid #3E3E42; font-size: 9.5pt; }
            QPushButton { background-color: #2D2D30; color: #FFFFFF; border: 1px solid #3E3E42; padding: 6px 14px; border-radius: 3px; }
            QPushButton:hover { background-color: #3E3E42; }
            QPushButton#primaryBtn { background-color: #0E639C; font-weight: bold; }
            QPushButton#primaryBtn:hover { background-color: #1177BB; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header Banner
        header = QVBoxLayout()
        title = QLabel("Select Active Materials Database")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        header.addWidget(title)

        subtitle = QLabel("Select the thermodynamic & physical database to calculate properties from:")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet("color: #AAAAAA;")
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Main 2-Column Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, stretch=1)

        # Left: Database List
        list_group = QGroupBox("Available Alloy Databases")
        list_layout = QVBoxLayout(list_group)
        list_layout.setContentsMargins(6, 6, 6, 6)

        self.db_list = QListWidget()
        all_dbs = MaterialDatabaseSelector.get_database_list()
        self.db_list.addItems(all_dbs)
        list_layout.addWidget(self.db_list)
        splitter.addWidget(list_group)

        # Right: Dossier Details Panel
        dossier_group = QGroupBox("Database Scope & Default Alloy Archetype")
        dossier_layout = QVBoxLayout(dossier_group)
        dossier_layout.setContentsMargins(10, 10, 10, 10)
        dossier_layout.setSpacing(6)

        self.lbl_dossier_title = QLabel("Database: --")
        self.lbl_dossier_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        dossier_layout.addWidget(self.lbl_dossier_title)

        self.lbl_dossier_cat = QLabel("Category: --")
        self.lbl_dossier_cat.setFont(QFont("Segoe UI", 10))
        self.lbl_dossier_cat.setStyleSheet("color: #64B5F6;")
        dossier_layout.addWidget(self.lbl_dossier_cat)

        self.lbl_dossier_alloy = QLabel("Default Archetype: --")
        self.lbl_dossier_alloy.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        dossier_layout.addWidget(self.lbl_dossier_alloy)

        self.lbl_dossier_comp = QLabel("Chemistry: --")
        self.lbl_dossier_comp.setFont(QFont("Segoe UI", 10))
        dossier_layout.addWidget(self.lbl_dossier_comp)

        self.txt_dossier_desc = QTextEdit()
        self.txt_dossier_desc.setReadOnly(True)
        dossier_layout.addWidget(self.txt_dossier_desc, stretch=1)

        self.lbl_dossier_phases = QLabel("Primary Phases: --")
        self.lbl_dossier_phases.setFont(QFont("Segoe UI", 9))

        self.lbl_dossier_phases.setStyleSheet("color: #81C784;")
        dossier_layout.addWidget(self.lbl_dossier_phases)

        splitter.addWidget(dossier_group)
        splitter.setSizes([260, 440])

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_confirm = QPushButton("Load Database & Calculate")
        self.btn_confirm.setObjectName("primaryBtn")
        self.btn_confirm.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_confirm)

        layout.addLayout(btn_layout)

        # Connect list selection change
        self.db_list.currentTextChanged.connect(self.update_dossier)

        # Set initial selection
        match_items = self.db_list.findItems(current_db, Qt.MatchFlag.MatchExactly)
        if match_items:
            self.db_list.setCurrentItem(match_items[0])
        else:
            self.db_list.setCurrentRow(0)

    def update_dossier(self, db_name: str):
        spec = MaterialDatabaseSelector.get_spec(db_name)
        self.lbl_dossier_title.setText(f"Database: {spec.get('name', db_name)}")
        self.lbl_dossier_cat.setText(f"Category: {spec.get('category', '')}")
        self.lbl_dossier_alloy.setText(f"Default Archetype: {spec.get('default_alloy', '')}")

        basis = spec.get("basis", "wt%")
        comp = spec.get("composition", {})
        comp_str = ", ".join([f"{k}: {v * 100:.2f} {basis}" for k, v in comp.items()])
        self.lbl_dossier_comp.setText(f"Chemistry: {comp_str}")

        self.txt_dossier_desc.setPlainText(spec.get("description", ""))
        phases = ", ".join(spec.get("primary_phases", []))
        self.lbl_dossier_phases.setText(f"Primary Phases: {phases}")

    def get_selected_database(self) -> str:
        curr = self.db_list.currentItem()
        return curr.text() if curr else "High Entropy Alloys"
