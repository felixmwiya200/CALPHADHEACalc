"""
database_dock.py - Left Parameter & Database Dock Widget
Provides database selection from the 14-alloy catalog, archetype presets,
dynamic composition table, grain size slider, process dropdown, and calculation trigger.
"""

from typing import Dict, Any
from PyQt6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QRadioButton, QButtonGroup,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QSlider, QGroupBox, QDoubleSpinBox,
                             QFrame, QMessageBox, QScrollArea)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal

from pycalphad_app.database.material_selector import MaterialDatabaseSelector
from pycalphad_app.database.unified_hea_database import UnifiedHEADatabase
from pycalphad_app.core.elements_data import ElementsData


class DatabaseDock(QDockWidget):
    calculate_requested = pyqtSignal(str, dict, str, float, str)

    def __init__(self, parent=None):
        super().__init__("Materials Database & Chemistry", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 1. Database Selector
        db_group = QGroupBox("Active Materials Database")
        db_group.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        db_layout = QVBoxLayout(db_group)
        db_layout.setContentsMargins(6, 6, 6, 6)

        self.db_combo = QComboBox()
        self.db_combo.addItems(MaterialDatabaseSelector.get_database_list())
        self.db_combo.currentTextChanged.connect(self.on_database_changed)
        db_layout.addWidget(self.db_combo)

        # Archetype Preset
        self.preset_lbl = QLabel("Alloy Archetype Preset:")
        self.preset_lbl.setFont(QFont("Segoe UI", 9))
        db_layout.addWidget(self.preset_lbl)

        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        db_layout.addWidget(self.preset_combo)

        # Basis Radio Buttons (wt%, at%, Molar ratio)
        basis_layout = QHBoxLayout()
        basis_lbl = QLabel("Basis:")
        basis_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        basis_layout.addWidget(basis_lbl)

        self.current_basis = "wt%"
        self.rb_wt = QRadioButton("wt%")
        self.rb_at = QRadioButton("at%")
        self.rb_mol = QRadioButton("Molar ratio")
        self.rb_wt.setChecked(True)
        self.basis_group = QButtonGroup(self)
        self.basis_group.addButton(self.rb_wt)
        self.basis_group.addButton(self.rb_at)
        self.basis_group.addButton(self.rb_mol)
        self.basis_group.buttonClicked.connect(self.on_basis_radio_changed)
        basis_layout.addWidget(self.rb_wt)
        basis_layout.addWidget(self.rb_at)
        basis_layout.addWidget(self.rb_mol)
        basis_layout.addStretch()
        db_layout.addLayout(basis_layout)

        layout.addWidget(db_group)

        # 2. Composition Table
        comp_group = QGroupBox("Chemical Composition")
        comp_group.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        comp_layout = QVBoxLayout(comp_group)
        comp_layout.setContentsMargins(6, 6, 6, 6)
        comp_layout.setSpacing(6)

        # Periodic Table Launcher Button
        self.btn_open_pt = QPushButton("Select Elements from Periodic Table (118)...")
        self.btn_open_pt.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.btn_open_pt.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_pt.setStyleSheet(
            "QPushButton {"
            "  background-color: #1D4ED8;"
            "  color: #FFFFFF;"
            "  padding: 6px 10px;"
            "  border-radius: 4px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover { background-color: #2563EB; }"
            "QPushButton:pressed { background-color: #1E40AF; }"
        )
        self.btn_open_pt.clicked.connect(self.open_periodic_table_dialog)
        comp_layout.addWidget(self.btn_open_pt)

        self.comp_table = QTableWidget()
        self.comp_table.setColumnCount(2)
        self.comp_table.setHorizontalHeaderLabels(["Element", "Fraction (%)"])
        self.comp_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.comp_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.comp_table.setMinimumHeight(220)
        self.comp_table.setAlternatingRowColors(True)
        comp_layout.addWidget(self.comp_table)

        # Table Control Buttons
        btn_tbl_layout = QHBoxLayout()
        self.btn_add_elem = QPushButton("+ Add Element")
        self.btn_add_elem.clicked.connect(self.add_row)
        btn_tbl_layout.addWidget(self.btn_add_elem)

        self.btn_rem_elem = QPushButton("- Del")
        self.btn_rem_elem.clicked.connect(self.remove_selected_row)
        btn_tbl_layout.addWidget(self.btn_rem_elem)

        self.btn_norm = QPushButton("Balance (100%)")
        self.btn_norm.clicked.connect(self.normalize_composition)
        btn_tbl_layout.addWidget(self.btn_norm)
        comp_layout.addLayout(btn_tbl_layout)

        layout.addWidget(comp_group)

        # 3. Processing Parameters
        proc_group = QGroupBox("Processing & Microstructure")
        proc_group.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        proc_layout = QVBoxLayout(proc_group)
        proc_layout.setContentsMargins(6, 6, 6, 6)

        # Process type dropdown
        proc_row = QHBoxLayout()
        proc_row.addWidget(QLabel("Process:"))
        self.combo_process = QComboBox()
        self.combo_process.addItems(["HVOF", "APS", "Flame Spray", "Laser Cladding", "Arc Melt / Cast"])
        proc_row.addWidget(self.combo_process)
        proc_layout.addLayout(proc_row)

        # Grain Size Slider
        gs_row = QHBoxLayout()
        self.lbl_grain = QLabel("Grain Size: 25 μm")
        self.lbl_grain.setFont(QFont("Segoe UI", 9))
        gs_row.addWidget(self.lbl_grain)
        proc_layout.addLayout(gs_row)

        self.slider_grain = QSlider(Qt.Orientation.Horizontal)
        self.slider_grain.setRange(1, 150)
        self.slider_grain.setValue(25)
        self.slider_grain.valueChanged.connect(self.on_grain_size_changed)
        proc_layout.addWidget(self.slider_grain)

        layout.addWidget(proc_group)

        # 4. Calculate Trigger Button
        self.btn_calc = QPushButton("Calculate Properties / Run Simulation")
        self.btn_calc.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_calc.setToolTip("Execute multi-physics CALPHAD equilibrium, thermophysical, mechanical, oxidation, and XRD simulations.")
        self.btn_calc.setStyleSheet(
            "QPushButton { background-color: #0E639C; color: #FFFFFF; padding: 10px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #1177BB; }"
            "QPushButton:pressed { background-color: #094771; }"
            "QPushButton:disabled { background-color: #555555; color: #888888; }"
        )
        self.btn_calc.clicked.connect(self.on_calculate_clicked)
        layout.addWidget(self.btn_calc)

        # 5. Quick Key Properties Card
        summary_group = QGroupBox("Dossier Summary")
        summary_group.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        summary_layout = QVBoxLayout(summary_group)
        summary_layout.setContentsMargins(6, 6, 6, 6)

        self.lbl_summary_db = QLabel("Database: High Entropy Alloys")
        self.lbl_summary_db.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        summary_layout.addWidget(self.lbl_summary_db)

        self.lbl_summary_sol = QLabel("Solidus / Liquidus: -- / -- K")
        self.lbl_summary_sol.setFont(QFont("Segoe UI", 9))
        summary_layout.addWidget(self.lbl_summary_sol)

        self.lbl_summary_hard = QLabel("Hardness / Yield: -- HV / -- MPa")
        self.lbl_summary_hard.setFont(QFont("Segoe UI", 9))
        summary_layout.addWidget(self.lbl_summary_hard)


        layout.addWidget(summary_group)
        layout.addStretch()

        # Wrap in QScrollArea for smooth vertical scrolling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidget(container)

        self.setWidget(self.scroll_area)

        # Initialize with default database
        self.on_database_changed("High Entropy Alloys")

    def open_periodic_table_dialog(self):
        from pycalphad_app.gui.periodic_table_widget import PeriodicTableDialog
        current_comp = self.get_composition()
        initial_elems = list(current_comp.keys()) if current_comp else ["Co", "Cr", "Fe", "Mn", "Ni"]
        dlg = PeriodicTableDialog(self, initial_elements=initial_elems)
        if dlg.exec():
            if dlg.result_comp:
                self.load_composition_to_table(dlg.result_comp)

    def on_basis_radio_changed(self, button):
        if button == self.rb_wt:
            new_basis = "wt%"
        elif button == self.rb_at:
            new_basis = "at%"
        else:
            new_basis = "mol"

        if new_basis == self.current_basis:
            return

        old_basis = self.current_basis
        self.current_basis = new_basis

        header_text = "Ratio" if new_basis == "mol" else "Fraction (%)"
        self.comp_table.setHorizontalHeaderLabels(["Element", header_text])

        comp = self.get_composition()
        if comp:
            converted = self.convert_basis_composition(comp, old_basis, new_basis)
            self.load_composition_to_table(converted)

    def convert_basis_composition(self, comp: Dict[str, float], old_basis: str, new_basis: str) -> Dict[str, float]:
        if not comp or old_basis == new_basis:
            return comp

        masses = {}
        for elem in comp.keys():
            edata = ElementsData.get_element(elem)
            masses[elem] = getattr(edata, "atomic_mass", 55.845)

        total_in = sum(comp.values())
        if total_in <= 0:
            return comp

        # 1. Convert old_basis to normalized mole fractions x_mol
        if old_basis == "wt%":
            moles_raw = {el: (val / total_in) / max(1e-4, masses[el]) for el, val in comp.items()}
            tot_mol = sum(moles_raw.values())
            x_mol = {el: m / tot_mol for el, m in moles_raw.items()}
        else:
            x_mol = {el: val / total_in for el, val in comp.items()}

        # 2. Convert x_mol to new_basis
        if new_basis == "at%":
            return {el: round(frac * 100.0, 2) for el, frac in x_mol.items()}
        elif new_basis == "wt%":
            mass_raw = {el: frac * masses[el] for el, frac in x_mol.items()}
            tot_mass = sum(mass_raw.values())
            return {el: round((m / tot_mass) * 100.0, 2) for el, m in mass_raw.items()}
        elif new_basis == "mol":
            min_val = min(x_mol.values()) if x_mol.values() else 1.0
            scale = min_val if min_val > 0 else 1.0
            return {el: round(frac / scale, 2) for el, frac in x_mol.items()}
        return comp

    def on_database_changed(self, db_name: str):
        spec = MaterialDatabaseSelector.get_spec(db_name)
        self.lbl_summary_db.setText(f"Database: {db_name}")

        # Set basis radio button
        spec_basis = spec.get("basis", "wt%")
        self.basis_group.blockSignals(True)
        if spec_basis == "wt%":
            self.rb_wt.setChecked(True)
            self.current_basis = "wt%"
        elif spec_basis in ("mol", "molar"):
            self.rb_mol.setChecked(True)
            self.current_basis = "mol"
        else:
            self.rb_at.setChecked(True)
            self.current_basis = "at%"
        self.basis_group.blockSignals(False)

        header_text = "Ratio" if self.current_basis == "mol" else "Fraction (%)"
        self.comp_table.setHorizontalHeaderLabels(["Element", header_text])

        # Update presets from individual database
        presets = MaterialDatabaseSelector.get_presets_for_database(db_name)
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        if presets:
            self.preset_combo.addItems(list(presets.keys()))
        else:
            self.preset_combo.addItem(spec.get("default_alloy", db_name))
        self.preset_combo.blockSignals(False)

        if db_name == "Thermal Spray Coatings":
            self.combo_process.setCurrentText("HVOF")

        # Load first preset composition into table
        if presets:
            first_key = list(presets.keys())[0]
            self.load_composition_to_table(presets[first_key])
        else:
            comp = spec.get("composition", {})
            self.load_composition_to_table(comp)

    def on_preset_changed(self, preset_name: str):
        db_name = self.db_combo.currentText()
        presets = MaterialDatabaseSelector.get_presets_for_database(db_name)
        if preset_name in presets:
            self.load_composition_to_table(presets[preset_name])

    def load_composition_to_table(self, comp: Dict[str, float]):
        self.comp_table.setRowCount(0)
        total = sum(comp.values())
        is_fraction = (total <= 1.5)
        for elem, val in comp.items():
            row = self.comp_table.rowCount()
            self.comp_table.insertRow(row)
            if self.current_basis == "mol":
                val_str = f"{val:.2f}"
            else:
                pct = val * 100.0 if is_fraction else val
                val_str = f"{pct:.2f}"
            self.comp_table.setItem(row, 0, QTableWidgetItem(elem))
            self.comp_table.setItem(row, 1, QTableWidgetItem(val_str))


    def add_row(self):
        comp = self.get_composition()
        common = ["Fe", "Ni", "Cr", "Co", "Al", "Ti", "Mo", "Nb", "V", "W", "Mn", "Cu", "Si", "Zr", "Ta", "Hf"]
        cand = "Fe"
        for el in common:
            if el not in comp:
                cand = el
                break
        row = self.comp_table.rowCount()
        self.comp_table.insertRow(row)
        self.comp_table.setItem(row, 0, QTableWidgetItem(cand))
        self.comp_table.setItem(row, 1, QTableWidgetItem("10.00"))

    def remove_selected_row(self):
        cur_row = self.comp_table.currentRow()
        if cur_row >= 0:
            self.comp_table.removeRow(cur_row)

    def normalize_composition(self):
        comp = self.get_composition()
        total = sum(comp.values())
        if total <= 0:
            return
        for row in range(self.comp_table.rowCount()):
            elem_item = self.comp_table.item(row, 0)
            if elem_item:
                elem = elem_item.text().strip()
                norm_val = (comp.get(elem, 0.0) / total) * 100.0
                self.comp_table.setItem(row, 1, QTableWidgetItem(f"{norm_val:.2f}"))

    def get_composition(self) -> Dict[str, float]:
        comp = {}
        for row in range(self.comp_table.rowCount()):
            elem_it = self.comp_table.item(row, 0)
            val_it = self.comp_table.item(row, 1)
            if elem_it and val_it:
                elem = elem_it.text().strip()
                try:
                    val = float(val_it.text().strip())
                    comp[elem] = val
                except ValueError:
                    continue
        return comp

    def on_grain_size_changed(self, val: int):
        self.lbl_grain.setText(f"Grain Size: {val} μm")

    def on_calculate_clicked(self):
        db_name = self.db_combo.currentText()
        comp = self.get_composition()
        if not comp:
            QMessageBox.warning(self, "Composition Error", "Please specify at least one chemical element.")
            return

        if self.rb_wt.isChecked():
            basis = "wt%"
        elif self.rb_mol.isChecked():
            basis = "mol"
        else:
            basis = "at%"
        grain_size = float(self.slider_grain.value())
        process_type = self.combo_process.currentText()

        self.btn_calc.setEnabled(False)
        self.btn_calc.setText("Solving Equations...")
        self.calculate_requested.emit(db_name, comp, basis, grain_size, process_type)

    def calculation_finished(self, results: Dict[str, Any]):
        self.btn_calc.setEnabled(True)
        self.btn_calc.setText("Calculate Properties / Run Simulation")

        thermo = results.get("thermo", {})
        mech = results.get("mechanical", {})

        sol_k = thermo.get("Solidus_K", 0.0)
        liq_k = thermo.get("Liquidus_K", 0.0)
        hv = mech.get("Hardness_HV", 0.0)
        sy = mech.get("YieldStrength_MPa", 0.0)

        self.lbl_summary_sol.setText(f"Solidus / Liquidus: {sol_k:.1f} / {liq_k:.1f} K")
        self.lbl_summary_hard.setText(f"Hardness / Yield: {hv:.1f} HV / {sy:.1f} MPa")
