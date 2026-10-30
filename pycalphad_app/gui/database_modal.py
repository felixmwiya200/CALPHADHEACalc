# -*- coding: utf-8 -*-
"""
database_modal.py - Materials Database Selector & Thermodynamics Catalog
Presents the 14-database CALPHAD registry with real-time filtering, domain categorization,
interactive alloy archetype preview, element chemistry tags, and full thermodynamic scope.
Adheres to publication-grade scientific CAE standards (OriginLab, Thermo-Calc, and JMatPro).

Lead Materials Suite Developers: Felix Mwiya and Prof. (Dr.) Sheela Singh, SRM University-AP.
"""

from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QComboBox, QLineEdit, QSplitter, QWidget, QFrame,
    QScrollArea, QGridLayout
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

from pycalphad_app.database.material_selector import MaterialDatabaseSelector
from pycalphad_app.core.elements_data import get_element


class DatabaseModalDialog(QDialog):
    """
    Standard scientific CAE Materials Database Selector dialog.
    Enables rapid domain filtering, alloy archetype preview, nominal chemistry
    breakdown, phase equilibrium summary, and seamless calculation triggering.
    """
    def __init__(self, current_db: str = "Thermal Spray Coatings", parent=None, theme: str = "light"):
        super().__init__(parent)
        self.current_theme = theme
        self.selected_database = current_db
        self.selected_preset_name = ""

        self.setWindowTitle("CALPHAD Materials Database Selector")
        self.resize(1000, 680)
        self.setMinimumSize(850, 560)

        self.setup_ui()
        self.apply_theme(self.current_theme)

        # Pre-select active database
        self.select_database(current_db)

    def setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(12)

        # -------------------------------------------------------------------
        # 1. Header Banner
        # -------------------------------------------------------------------
        header_bar = QHBoxLayout()
        header_titles = QVBoxLayout()
        header_titles.setSpacing(2)

        self.lbl_header_title = QLabel("Materials Database Catalog & Thermodynamic Selector")
        self.lbl_header_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        header_titles.addWidget(self.lbl_header_title)

        self.lbl_header_sub = QLabel(
            "Select an authoritative multi-component thermodynamic and physical database to configure the CALPHAD calculation engine."
        )
        self.lbl_header_sub.setFont(QFont("Segoe UI", 9))
        header_titles.addWidget(self.lbl_header_sub)
        header_bar.addLayout(header_titles, stretch=1)

        # Academic Attribution Badge
        self.lbl_badge_org = QLabel("SRM University-AP | CALPHAD Suite")
        self.lbl_badge_org.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        header_bar.addWidget(self.lbl_badge_org)
        root_layout.addLayout(header_bar)

        # Divider line
        div_line = QFrame()
        div_line.setFrameShape(QFrame.Shape.HLine)
        div_line.setFrameShadow(QFrame.Shadow.Plain)
        div_line.setObjectName("hairlineDivider")
        root_layout.addWidget(div_line)

        # -------------------------------------------------------------------
        # 2. Main 2-Column Splitter: Left Browser & Right Dossier
        # -------------------------------------------------------------------
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("mainSplitter")
        root_layout.addWidget(splitter, stretch=1)

        # Left Column: Search, Filter, and Database List
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(8)

        # Search Bar
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search databases, alloys, or elements (e.g. Ni, Cr, Steel)...")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setFont(QFont("Segoe UI", 9))
        self.search_box.textChanged.connect(self.filter_databases)
        left_layout.addWidget(self.search_box)

        # Domain Category Filter
        domain_row = QHBoxLayout()
        domain_lbl = QLabel("Domain:")
        domain_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        domain_row.addWidget(domain_lbl)

        self.combo_domain = QComboBox()
        self.combo_domain.setFont(QFont("Segoe UI", 9))
        self.combo_domain.addItems([
            "All Domains (14 Databases)",
            "High-Entropy & Multi-Principal",
            "Ferrous & Structural Steels",
            "Lightweight Aerospace Alloys",
            "High-Temperature Superalloys",
            "Specialty & Nuclear Alloys"
        ])
        self.combo_domain.currentTextChanged.connect(self.filter_databases)
        domain_row.addWidget(self.combo_domain, stretch=1)
        left_layout.addLayout(domain_row)

        # Database List Widget
        self.db_list = QListWidget()
        self.db_list.setObjectName("dbListWidget")
        self.db_list.setFont(QFont("Segoe UI", 9))
        self.db_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.db_list.currentItemChanged.connect(self.on_db_item_changed)
        left_layout.addWidget(self.db_list, stretch=1)

        # List Footer Counter
        self.lbl_list_count = QLabel("14 Databases Available")
        self.lbl_list_count.setFont(QFont("Segoe UI", 8))
        self.lbl_list_count.setObjectName("lblMuted")
        left_layout.addWidget(self.lbl_list_count)

        splitter.addWidget(left_widget)

        # Right Column: Comprehensive Materials Engineering Dossier Card
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(8)

        # Scroll area enclosing the rich dossier card
        dossier_scroll = QScrollArea()
        dossier_scroll.setWidgetResizable(True)
        dossier_scroll.setFrameShape(QFrame.Shape.NoFrame)
        dossier_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.dossier_card = QWidget()
        self.dossier_card.setObjectName("dossierCard")
        dossier_card_layout = QVBoxLayout(self.dossier_card)
        dossier_card_layout.setContentsMargins(14, 14, 14, 14)
        dossier_card_layout.setSpacing(10)

        # Identity Row: Title and Badges
        self.lbl_db_name = QLabel("Database Name")
        self.lbl_db_name.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        dossier_card_layout.addWidget(self.lbl_db_name)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(6)
        self.lbl_badge_category = QLabel("Category")
        self.lbl_badge_category.setObjectName("pillCategory")
        badge_row.addWidget(self.lbl_badge_category)

        self.lbl_badge_framework = QLabel("CALPHAD Sublattice Solution Model")
        self.lbl_badge_framework.setObjectName("pillFramework")
        badge_row.addWidget(self.lbl_badge_framework)

        self.lbl_badge_basis = QLabel("Basis: wt%")
        self.lbl_badge_basis.setObjectName("pillBasis")
        badge_row.addWidget(self.lbl_badge_basis)
        badge_row.addStretch()
        dossier_card_layout.addLayout(badge_row)

        # Executive Description
        self.lbl_desc_title = QLabel("Thermodynamic Scope and Metallurgical Description:")
        self.lbl_desc_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        dossier_card_layout.addWidget(self.lbl_desc_title)

        self.lbl_description = QLabel("")
        self.lbl_description.setObjectName("lblDescription")
        self.lbl_description.setFont(QFont("Segoe UI", 9))
        self.lbl_description.setWordWrap(True)
        dossier_card_layout.addWidget(self.lbl_description)

        # Archetype Selector Row
        preset_box = QHBoxLayout()
        preset_box.setSpacing(8)
        lbl_pre = QLabel("Alloy Archetype Preset:")
        lbl_pre.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        preset_box.addWidget(lbl_pre)

        self.combo_preset = QComboBox()
        self.combo_preset.setFont(QFont("Segoe UI", 9))
        self.combo_preset.currentTextChanged.connect(self.on_preset_changed)
        preset_box.addWidget(self.combo_preset, stretch=1)
        dossier_card_layout.addLayout(preset_box)

        # Nominal Chemistry Chips Container
        lbl_chem = QLabel("Nominal Chemical Composition:")
        lbl_chem.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        dossier_card_layout.addWidget(lbl_chem)

        self.chem_chips_widget = QWidget()
        self.chem_chips_layout = QHBoxLayout(self.chem_chips_widget)
        self.chem_chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chem_chips_layout.setSpacing(6)
        dossier_card_layout.addWidget(self.chem_chips_widget)

        # Primary Equilibrium Phases
        lbl_phases = QLabel("Primary Equilibrium and Precipitate Phases:")
        lbl_phases.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        dossier_card_layout.addWidget(lbl_phases)

        self.phases_widget = QWidget()
        self.phases_layout = QHBoxLayout(self.phases_widget)
        self.phases_layout.setContentsMargins(0, 0, 0, 0)
        self.phases_layout.setSpacing(6)
        dossier_card_layout.addWidget(self.phases_widget)

        # Specifications Grid (2x2 Stats Card)
        grid_container = QWidget()
        grid_container.setObjectName("statsGrid")
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        grid_layout.setHorizontalSpacing(16)
        grid_layout.setVerticalSpacing(8)

        lbl_t_title = QLabel("Temperature Window:")
        lbl_t_title.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.lbl_temp_range = QLabel("300 - 1800 K")
        self.lbl_temp_range.setFont(QFont("Segoe UI", 9))
        grid_layout.addWidget(lbl_t_title, 0, 0)
        grid_layout.addWidget(self.lbl_temp_range, 0, 1)

        lbl_proc_title = QLabel("Processing Routes:")
        lbl_proc_title.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.lbl_processes = QLabel("Cast, Wrought, Powder Metallurgy")
        self.lbl_processes.setFont(QFont("Segoe UI", 9))
        grid_layout.addWidget(lbl_proc_title, 1, 0)
        grid_layout.addWidget(self.lbl_processes, 1, 1)

        lbl_app_title = QLabel("Key Applications:")
        lbl_app_title.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.lbl_apps = QLabel("Aerospace, Turbomachinery, Surface Hardfacing")
        self.lbl_apps.setFont(QFont("Segoe UI", 9))
        grid_layout.addWidget(lbl_app_title, 2, 0)
        grid_layout.addWidget(self.lbl_apps, 2, 1)

        lbl_bench_title = QLabel("Validation Status:")
        lbl_bench_title.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.lbl_benchmarks = QLabel("Calibrated with 20+ Peer-Reviewed Benchmarks")
        self.lbl_benchmarks.setFont(QFont("Segoe UI", 9))
        grid_layout.addWidget(lbl_bench_title, 3, 0)
        grid_layout.addWidget(self.lbl_benchmarks, 3, 1)

        dossier_card_layout.addWidget(grid_container)
        dossier_card_layout.addStretch()

        dossier_scroll.setWidget(self.dossier_card)
        right_layout.addWidget(dossier_scroll, stretch=1)
        splitter.addWidget(right_container)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([340, 620])

        # -------------------------------------------------------------------
        # 3. Footer Action Bar
        # -------------------------------------------------------------------
        footer_div = QFrame()
        footer_div.setFrameShape(QFrame.Shape.HLine)
        footer_div.setFrameShadow(QFrame.Shadow.Plain)
        footer_div.setObjectName("hairlineDivider")
        root_layout.addWidget(footer_div)

        footer_bar = QHBoxLayout()
        self.lbl_selection_status = QLabel("Active Selection: Thermal Spray Coatings")
        self.lbl_selection_status.setFont(QFont("Segoe UI", 9))
        footer_bar.addWidget(self.lbl_selection_status, stretch=1)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFont(QFont("Segoe UI", 9))
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        footer_bar.addWidget(self.btn_cancel)

        self.btn_confirm = QPushButton("Load Database and Configure Engine")
        self.btn_confirm.setObjectName("primaryBtn")
        self.btn_confirm.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.clicked.connect(self.on_confirm_clicked)
        footer_bar.addWidget(self.btn_confirm)

        root_layout.addLayout(footer_bar)

        # Populate initial databases
        self.populate_database_list()

    def populate_database_list(self):
        self.db_list.clear()
        databases = MaterialDatabaseSelector.get_database_list()
        for db in databases:
            item = QListWidgetItem(db)
            self.db_list.addItem(item)
        self.lbl_list_count.setText(f"{len(databases)} Databases Available")

    def filter_databases(self):
        query = self.search_box.text().strip().lower()
        selected_domain = self.combo_domain.currentText()

        visible_count = 0
        for i in range(self.db_list.count()):
            item = self.db_list.item(i)
            db_name = item.text()
            spec = MaterialDatabaseSelector.get_spec(db_name)

            # Check domain
            domain = spec.get("domain_group", "")
            domain_match = (
                selected_domain.startswith("All Domains") or
                selected_domain.lower() in domain.lower() or
                domain.lower() in selected_domain.lower()
            )

            # Check search query across name, category, and elements
            comp_keys = [k.lower() for k in spec.get("raw_composition", {}).keys()]
            text_corpus = f"{db_name} {spec.get('category', '')} {' '.join(comp_keys)}".lower()
            query_match = (not query) or (query in text_corpus)

            is_visible = domain_match and query_match
            item.setHidden(not is_visible)
            if is_visible:
                visible_count += 1

        self.lbl_list_count.setText(f"{visible_count} of 14 Databases Shown")

    def select_database(self, db_name: str):
        for i in range(self.db_list.count()):
            item = self.db_list.item(i)
            if item.text().lower() == db_name.lower():
                self.db_list.setCurrentItem(item)
                return
        if self.db_list.count() > 0:
            self.db_list.setCurrentRow(0)

    def on_db_item_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if not current:
            return
        db_name = current.text()
        self.selected_database = db_name
        spec = MaterialDatabaseSelector.get_spec(db_name)

        # Update Identity
        self.lbl_db_name.setText(spec.get("name", db_name))
        self.lbl_badge_category.setText(spec.get("category", "Materials Database"))
        basis = spec.get("basis", "wt%")
        self.lbl_badge_basis.setText(f"Basis: {basis}")

        # Update Description
        desc = spec.get("description", "")
        self.lbl_description.setText(desc)

        # Update Archetype Presets Combo
        presets = MaterialDatabaseSelector.get_presets_for_database(db_name)
        self.combo_preset.blockSignals(True)
        self.combo_preset.clear()
        if presets:
            self.combo_preset.addItems(list(presets.keys()))
            first_key = list(presets.keys())[0]
            self.selected_preset_name = first_key
            self.render_chemistry_chips(presets[first_key], basis)
        else:
            default_alloy = spec.get("default_alloy", db_name)
            self.combo_preset.addItem(default_alloy)
            self.selected_preset_name = default_alloy
            self.render_chemistry_chips(spec.get("raw_composition", {}), basis)
        self.combo_preset.blockSignals(False)

        # Update Primary Phases Badges
        self.render_phase_badges(spec.get("primary_phases", ["Solid", "Liquid"]))

        # Update Stats Grid
        self.lbl_temp_range.setText(spec.get("temperature_range", "300 - 1800 K"))
        apps = spec.get("key_applications", ["Aerospace", "Energy", "Manufacturing"])
        self.lbl_apps.setText(", ".join(apps) if isinstance(apps, list) else str(apps))

        # Update Footer Status
        self.lbl_selection_status.setText(
            f"Active Selection: {db_name} (Archetype: {self.combo_preset.currentText()})"
        )

    def on_preset_changed(self, preset_name: str):
        if not preset_name:
            return
        self.selected_preset_name = preset_name
        presets = MaterialDatabaseSelector.get_presets_for_database(self.selected_database)
        spec = MaterialDatabaseSelector.get_spec(self.selected_database)
        basis = spec.get("basis", "wt%")

        if preset_name in presets:
            self.render_chemistry_chips(presets[preset_name], basis)
        else:
            self.render_chemistry_chips(spec.get("raw_composition", {}), basis)

        self.lbl_selection_status.setText(
            f"Active Selection: {self.selected_database} (Archetype: {preset_name})"
        )

    def render_chemistry_chips(self, comp: Dict[str, float], basis: str):
        # Clear existing chips
        while self.chem_chips_layout.count():
            item = self.chem_chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total = sum(comp.values())
        is_fraction = (total <= 1.5)

        for el, val in comp.items():
            pct = val * 100.0 if (is_fraction and basis != "mol") else val
            edata = get_element(el)
            color_dot = getattr(edata, "color_hex", "#3B82F6")

            chip = QLabel(f"<span style='color:{color_dot}; font-weight:bold;'>&#9679;</span> <b>{el}</b>: {pct:.2f} {basis}")
            chip.setObjectName("elementChip")
            chip.setFont(QFont("Segoe UI", 9))
            self.chem_chips_layout.addWidget(chip)

        self.chem_chips_layout.addStretch()

    def render_phase_badges(self, phases: List[str]):
        while self.phases_layout.count():
            item = self.phases_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for ph in phases:
            lbl = QLabel(ph)
            lbl.setObjectName("phasePill")
            lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            self.phases_layout.addWidget(lbl)

        self.phases_layout.addStretch()

    def on_confirm_clicked(self):
        curr_item = self.db_list.currentItem()
        if curr_item:
            self.selected_database = curr_item.text()
        self.selected_preset_name = self.combo_preset.currentText()
        self.accept()

    def get_selected_database(self) -> str:
        return self.selected_database or "High Entropy Alloys"

    def get_selected_preset(self) -> str:
        return self.selected_preset_name or ""

    def apply_theme(self, theme: str = "light"):
        self.current_theme = theme
        if theme == "light":
            self.setStyleSheet("""
                QDialog {
                    background-color: #F8FAFC;
                    color: #0F172A;
                }
                #hairlineDivider {
                    color: #E2E8F0;
                    background-color: #E2E8F0;
                    height: 1px;
                }
                #lblMuted {
                    color: #64748B;
                }
                QLineEdit, QComboBox {
                    background-color: #FFFFFF;
                    color: #0F172A;
                    border: 1px solid #CBD5E1;
                    border-radius: 4px;
                    padding: 5px 8px;
                }
                QLineEdit:focus, QComboBox:focus {
                    border-color: #2563EB;
                }
                #dbListWidget {
                    background-color: #FFFFFF;
                    color: #1E293B;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 4px;
                }
                #dbListWidget::item {
                    padding: 9px 12px;
                    border-radius: 4px;
                    margin-bottom: 2px;
                }
                #dbListWidget::item:hover {
                    background-color: #F1F5F9;
                    color: #0F172A;
                }
                #dbListWidget::item:selected {
                    background-color: #EFF6FF;
                    color: #1D4ED8;
                    font-weight: bold;
                    border-left: 3px solid #1D4ED8;
                }
                #dossierCard {
                    background-color: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                }
                #lblDescription {
                    color: #334155;
                    line-height: 1.4;
                    background-color: #F8FAFC;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 8px 12px;
                }
                #pillCategory {
                    background-color: #DBEAFE;
                    color: #1E40AF;
                    padding: 3px 10px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 8.5pt;
                }
                #pillFramework {
                    background-color: #FEF3C7;
                    color: #92400E;
                    padding: 3px 10px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 8.5pt;
                }
                #pillBasis {
                    background-color: #F1F5F9;
                    color: #475569;
                    padding: 3px 10px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 8.5pt;
                }
                #elementChip {
                    background-color: #F1F5F9;
                    color: #1E293B;
                    border: 1px solid #CBD5E1;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                #phasePill {
                    background-color: #DCFCE7;
                    color: #15803D;
                    border: 1px solid #86EFAC;
                    padding: 3px 8px;
                    border-radius: 4px;
                }
                #statsGrid {
                    background-color: #F8FAFC;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                }
                QPushButton {
                    background-color: #FFFFFF;
                    color: #334155;
                    border: 1px solid #CBD5E1;
                    border-radius: 4px;
                    padding: 6px 14px;
                }
                QPushButton:hover {
                    background-color: #F1F5F9;
                    color: #0F172A;
                }
                QPushButton#primaryBtn {
                    background-color: #1D4ED8;
                    color: #FFFFFF;
                    border: 1px solid #1E40AF;
                    padding: 7px 18px;
                }
                QPushButton#primaryBtn:hover {
                    background-color: #2563EB;
                }
                QPushButton#primaryBtn:pressed {
                    background-color: #1E40AF;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #0F172A;
                    color: #F8FAFC;
                }
                #hairlineDivider {
                    color: #334155;
                    background-color: #334155;
                    height: 1px;
                }
                #lblMuted {
                    color: #94A3B8;
                }
                QLineEdit, QComboBox {
                    background-color: #1E293B;
                    color: #F8FAFC;
                    border: 1px solid #475569;
                    border-radius: 4px;
                    padding: 5px 8px;
                }
                QLineEdit:focus, QComboBox:focus {
                    border-color: #3B82F6;
                }
                #dbListWidget {
                    background-color: #1E293B;
                    color: #E2E8F0;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    padding: 4px;
                }
                #dbListWidget::item {
                    padding: 9px 12px;
                    border-radius: 4px;
                    margin-bottom: 2px;
                }
                #dbListWidget::item:hover {
                    background-color: #334155;
                    color: #FFFFFF;
                }
                #dbListWidget::item:selected {
                    background-color: #1E3A8A;
                    color: #93C5FD;
                    font-weight: bold;
                    border-left: 3px solid #3B82F6;
                }
                #dossierCard {
                    background-color: #1E293B;
                    border: 1px solid #334155;
                    border-radius: 8px;
                }
                #lblDescription {
                    color: #CBD5E1;
                    line-height: 1.4;
                    background-color: #0F172A;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    padding: 8px 12px;
                }
                #pillCategory {
                    background-color: #1E3A8A;
                    color: #93C5FD;
                    padding: 3px 10px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 8.5pt;
                }
                #pillFramework {
                    background-color: #78350F;
                    color: #FDE68A;
                    padding: 3px 10px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 8.5pt;
                }
                #pillBasis {
                    background-color: #334155;
                    color: #E2E8F0;
                    padding: 3px 10px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 8.5pt;
                }
                #elementChip {
                    background-color: #0F172A;
                    color: #F8FAFC;
                    border: 1px solid #475569;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                #phasePill {
                    background-color: #064E3B;
                    color: #6EE7B7;
                    border: 1px solid #059669;
                    padding: 3px 8px;
                    border-radius: 4px;
                }
                #statsGrid {
                    background-color: #0F172A;
                    border: 1px solid #334155;
                    border-radius: 6px;
                }
                QPushButton {
                    background-color: #1E293B;
                    color: #CBD5E1;
                    border: 1px solid #475569;
                    border-radius: 4px;
                    padding: 6px 14px;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: #FFFFFF;
                }
                QPushButton#primaryBtn {
                    background-color: #2563EB;
                    color: #FFFFFF;
                    border: 1px solid #1D4ED8;
                    padding: 7px 18px;
                }
                QPushButton#primaryBtn:hover {
                    background-color: #3B82F6;
                }
                QPushButton#primaryBtn:pressed {
                    background-color: #1D4ED8;
                }
            """)
