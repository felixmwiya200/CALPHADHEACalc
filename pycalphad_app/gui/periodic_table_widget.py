# -*- coding: utf-8 -*-
"""
periodic_table_widget.py - Complete IUPAC 118-Element Interactive Periodic Table
Provides a full 18-group x 7-period + Lanthanide/Actinide grid with:
- Todd Helmenstine card style (Z, Symbol, Name, Mass)
- Category color-coding (Alkali, Alkaline, Transition, Refractory, Cantor, Post-Transition, etc.)
- Multi-element selection and live status readout
- Quick alloy presets (Cantor, AlCoCrFeNi, Senkov RHEA, Inconel 718, Stainless 316L, Ti-6Al-4V)
- Category filter buttons and instant search
- Standalone widget and modal QDialog wrapper
"""

from typing import Dict, List, Set, Optional
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QScrollArea, QFrame, QSizePolicy, QMessageBox
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal

from pycalphad_app.core.elements_data import ElementsData, ElementData


CATEGORY_COLORS = {
    'transition': {'bg': '#F5F3FF', 'border': '#C4B5FD', 'fg': '#4C1D95'},
    'post-transition': {'bg': '#ECFDF5', 'border': '#A7F3D0', 'fg': '#065F46'},
    'metalloid': {'bg': '#FEF3C7', 'border': '#FDE68A', 'fg': '#92400E'},
    'nonmetal': {'bg': '#EFF6FF', 'border': '#BFDBFE', 'fg': '#1E40AF'},
    'alkali': {'bg': '#FEE2E2', 'border': '#FECACA', 'fg': '#991B1B'},
    'alkaline-earth': {'bg': '#FFEDD5', 'border': '#FED7AA', 'fg': '#9A3412'},
    'noble': {'bg': '#F3F4F6', 'border': '#E5E7EB', 'fg': '#374151'},
    'lanthanide': {'bg': '#FDF2F8', 'border': '#FBCFE8', 'fg': '#831843'},
    'actinide': {'bg': '#FAF5FF', 'border': '#E9D5FF', 'fg': '#581C87'},
}

PRESETS = {
    'Cantor (Co-Cr-Fe-Mn-Ni)': ['Co', 'Cr', 'Fe', 'Mn', 'Ni'],
    'AlCoCrFeNi': ['Al', 'Co', 'Cr', 'Fe', 'Ni'],
    'Senkov RHEA (Nb-Mo-Ta-W)': ['Nb', 'Mo', 'Ta', 'W'],
    'Ti-Zr-Hf-Nb-Ta': ['Ti', 'Zr', 'Hf', 'Nb', 'Ta'],
    'Ti-Zr-Nb-Ta': ['Ti', 'Zr', 'Nb', 'Ta'],
    'Inconel 718': ['Ni', 'Cr', 'Fe', 'Nb', 'Mo', 'Ti', 'Al'],
    'Stainless 316L': ['Fe', 'Cr', 'Ni', 'Mo', 'Mn', 'Si'],
    'Ti-6Al-4V': ['Ti', 'Al', 'V'],
    'AA 7075-T6': ['Al', 'Zn', 'Mg', 'Cu', 'Cr'],
}


class ElementTile(QPushButton):
    toggled_element = pyqtSignal(str, bool)

    def __init__(self, elem: ElementData, parent=None):
        super().__init__(parent)
        self.elem = elem
        self.is_selected = False
        self.setCheckable(True)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(46, 52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setText(f"{elem.z}\n{elem.symbol}\n{elem.name[:7]}\n{elem.atomic_mass:.1f}")
        self.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))

        self.setToolTip(
            f"<b>{elem.name} ({elem.symbol})</b><br>"
            f"Atomic Number: {elem.z}<br>"
            f"Atomic Mass: {elem.atomic_mass:.3f} g/mol<br>"
            f"Category: {elem.category.capitalize()}<br>"
            f"Crystal Structure: {elem.crystal_structure}<br>"
            f"Melting Point: {elem.tm_k:.1f} K<br>"
            f"Electronegativity: {elem.electronegativity:.2f}<br>"
            f"Density: {elem.density_g_cm3:.3f} g/cm³<br>"
            f"Valence Electrons (VEC): {elem.vec}"
        )

        self.update_style()
        self.clicked.connect(self.on_clicked)

    def on_clicked(self):
        self.is_selected = self.isChecked()
        self.update_style()
        self.toggled_element.emit(self.elem.symbol, self.is_selected)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.setChecked(selected)
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet(
                "QPushButton {"
                "  background-color: #15803D;"
                "  color: #FFFFFF;"
                "  border: 2px solid #22C55E;"
                "  border-radius: 4px;"
                "  padding: 1px;"
                "  font-family: 'Segoe UI';"
                "  font-size: 7.5pt;"
                "  font-weight: bold;"
                "}"
                "QPushButton:hover {"
                "  background-color: #16A34A;"
                "}"
            )
        else:
            cat_info = CATEGORY_COLORS.get(self.elem.category, {'bg': '#FFFFFF', 'border': '#CBD5E1', 'fg': '#0F172A'})
            bg = cat_info['bg']
            border = cat_info['border']
            fg = cat_info['fg']
            self.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: {bg};"
                f"  color: {fg};"
                f"  border: 1px solid {border};"
                f"  border-radius: 3px;"
                f"  padding: 1px;"
                f"  font-family: 'Segoe UI';"
                f"  font-size: 7pt;"
                f"  font-weight: 600;"
                f"}}"
                f"QPushButton:hover {{"
                f"  border: 2px solid #2563EB;"
                f"  background-color: #FFFFFF;"
                f"}}"
            )


class PeriodicTableWidget(QWidget):
    elements_applied = pyqtSignal(dict)  # emits dict of {elem: pct}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tiles: Dict[str, ElementTile] = {}
        self.selected_elements: Set[str] = set()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # 1. Top Controls Bar: Search & Category Filters
        top_bar = QHBoxLayout()
        top_bar.setSpacing(6)

        search_lbl = QLabel("Search:")
        search_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        top_bar.addWidget(search_lbl)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter by element symbol or name (e.g. Fe, Titanium)...")
        self.search_edit.setFont(QFont("Segoe UI", 9))
        self.search_edit.textChanged.connect(self.on_search_changed)
        self.search_edit.setMaximumWidth(260)
        top_bar.addWidget(self.search_edit)

        # Category Filter Buttons
        top_bar.addWidget(QLabel("Categories:"))
        cat_pills = [
            ("All", "all"),
            ("Transition", "transition"),
            ("Post-Transition", "post-transition"),
            ("Metalloids", "metalloid"),
            ("Nonmetals", "nonmetal"),
            ("Alkali", "alkali"),
            ("Alkaline Earth", "alkaline-earth"),
            ("Lanthanides", "lanthanide"),
            ("Actinides", "actinide"),
            ("Noble", "noble"),
        ]
        self.cat_btn_group = []
        for label, cat_key in cat_pills:
            btn = QPushButton(label)
            btn.setFont(QFont("Segoe UI", 8))
            btn.setCheckable(True)
            if cat_key == "all":
                btn.setChecked(True)
            btn.setStyleSheet(
                "QPushButton { padding: 3px 8px; border-radius: 3px; border: 1px solid #CBD5E1; background: #F8FAFC; }"
                "QPushButton:checked { background: #1D4ED8; color: #FFFFFF; font-weight: bold; border-color: #1E40AF; }"
            )
            btn.clicked.connect(lambda checked, k=cat_key: self.filter_category(k))
            self.cat_btn_group.append((btn, cat_key))
            top_bar.addWidget(btn)

        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        # 2. Preset Shortcuts Bar
        preset_bar = QHBoxLayout()
        preset_bar.setSpacing(4)
        preset_lbl = QLabel("Presets:")
        preset_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        preset_bar.addWidget(preset_lbl)

        for name, elems in PRESETS.items():
            btn = QPushButton(name)
            btn.setFont(QFont("Segoe UI", 8))
            btn.setStyleSheet(
                "QPushButton { padding: 3px 7px; border: 1px solid #CBD5E1; border-radius: 3px; background: #FFFFFF; }"
                "QPushButton:hover { background: #E0E7FF; border-color: #4338CA; }"
            )
            btn.clicked.connect(lambda checked, el=elems: self.apply_preset(el))
            preset_bar.addWidget(btn)

        btn_clear = QPushButton("Clear All")
        btn_clear.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        btn_clear.setStyleSheet(
            "QPushButton { padding: 3px 10px; border: 1px solid #FCA5A5; border-radius: 3px; background: #FEE2E2; color: #991B1B; }"
            "QPushButton:hover { background: #F87171; color: #FFFFFF; }"
        )
        btn_clear.clicked.connect(self.clear_selection)
        preset_bar.addWidget(btn_clear)

        preset_bar.addStretch()
        main_layout.addLayout(preset_bar)

        # 3. Main Periodic Table Grid Container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        grid_container = QWidget()
        self.grid = QGridLayout(grid_container)
        self.grid.setSpacing(3)
        self.grid.setContentsMargins(4, 4, 4, 4)

        self.build_periodic_grid()

        scroll.setWidget(grid_container)
        main_layout.addWidget(scroll, 1)

        # 4. Bottom Action & Selection Status Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(8)

        self.status_lbl = QLabel("Currently Selected Elements: 0 (None)")
        self.status_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.status_lbl.setStyleSheet("color: #0F172A; padding: 4px 8px; background: #E2E8F0; border-radius: 4px;")
        bottom_bar.addWidget(self.status_lbl, 1)

        self.btn_apply = QPushButton("Apply to Chemical Composition")
        self.btn_apply.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_apply.setStyleSheet(
            "QPushButton { background-color: #1D4ED8; color: #FFFFFF; padding: 6px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #2563EB; }"
            "QPushButton:pressed { background-color: #1E40AF; }"
        )
        self.btn_apply.clicked.connect(self.apply_to_composition)
        bottom_bar.addWidget(self.btn_apply)

        main_layout.addLayout(bottom_bar)

    def build_periodic_grid(self):
        # Column headers (Groups 1 to 18)
        grp_labels = [
            '1 IA', '2 IIA', '3 IIIB', '4 IVB', '5 VB', '6 VIB', '7 VIIB',
            '8 VIIIB', '9 VIIIB', '10 VIIIB', '11 IB', '12 IIB',
            '13 IIIA', '14 IVA', '15 VA', '16 VIA', '17 VIIA', '18 VIIIA'
        ]
        lbl_gr = QLabel("Gr.")
        lbl_gr.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lbl_gr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid.addWidget(lbl_gr, 0, 0)

        for col_idx, g_lbl in enumerate(grp_labels):
            lbl = QLabel(g_lbl)
            lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #475569; padding: 2px;")
            self.grid.addWidget(lbl, 0, col_idx + 1)

        # Row headers (Periods 1 to 7)
        for p in range(1, 8):
            lbl = QLabel(str(p))
            lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #475569; padding: 2px;")
            self.grid.addWidget(lbl, p, 0)

        # Center Title Banner in Open Space (Periods 1-2, Groups 3-12)
        banner = QLabel("IUPAC PERIODIC TABLE OF THE ELEMENTS\n18 Groups  |  7 Periods  |  Complete 118 Elements Registry")
        banner.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner.setStyleSheet("color: #1E293B; background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 4px; padding: 8px;")
        self.grid.addWidget(banner, 1, 3, 2, 10)

        # Lanthanide / Actinide placeholder indicators in main body
        lan_marker = QLabel("57-71 *\nLa-Lu\nLanthanides")
        lan_marker.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        lan_marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lan_marker.setStyleSheet("background: #FDF2F8; color: #831843; border: 1px dashed #FBCFE8; border-radius: 3px;")
        self.grid.addWidget(lan_marker, 6, 3)

        act_marker = QLabel("89-103 **\nAc-Lr\nActinides")
        act_marker.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        act_marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
        act_marker.setStyleSheet("background: #FAF5FF; color: #581C87; border: 1px dashed #E9D5FF; border-radius: 3px;")
        self.grid.addWidget(act_marker, 7, 3)

        # Separator row between period 7 and Lanthanides
        sep_lbl = QLabel("")
        sep_lbl.setFixedHeight(8)
        self.grid.addWidget(sep_lbl, 8, 0, 1, 19)

        # Lanthanides and Actinides Row labels
        lan_row_lbl = QLabel("* Lanthanides")
        lan_row_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lan_row_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lan_row_lbl.setStyleSheet("color: #831843;")
        self.grid.addWidget(lan_row_lbl, 9, 0, 1, 3)

        act_row_lbl = QLabel("** Actinides")
        act_row_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        act_row_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        act_row_lbl.setStyleSheet("color: #581C87;")
        self.grid.addWidget(act_row_lbl, 10, 0, 1, 3)

        # Populate all 118 element tiles
        all_elements = ElementsData.get_118_list()
        for elem in all_elements:
            tile = ElementTile(elem)
            tile.toggled_element.connect(self.on_element_toggled)
            self.tiles[elem.symbol] = tile
            self.grid.addWidget(tile, elem.grid_row, elem.grid_col)

    def on_element_toggled(self, symbol: str, is_selected: bool):
        if is_selected:
            self.selected_elements.add(symbol)
        else:
            self.selected_elements.discard(symbol)
        self.update_status()

    def update_status(self):
        n = len(self.selected_elements)
        if n == 0:
            self.status_lbl.setText("Currently Selected Elements: 0 (None)")
            self.status_lbl.setStyleSheet("color: #0F172A; padding: 4px 8px; background: #E2E8F0; border-radius: 4px;")
        else:
            sorted_elems = sorted(list(self.selected_elements))
            elems_str = ", ".join(sorted_elems)
            self.status_lbl.setText(f"Currently Selected Elements: {n} ({elems_str})")
            self.status_lbl.setStyleSheet("color: #065F46; padding: 4px 8px; background: #DCFCE7; border: 1px solid #86EFAC; border-radius: 4px;")

    def apply_preset(self, elems: List[str]):
        self.clear_selection()
        for sym in elems:
            if sym in self.tiles:
                self.tiles[sym].set_selected(True)
                self.selected_elements.add(sym)
        self.update_status()

    def clear_selection(self):
        for tile in self.tiles.values():
            tile.set_selected(False)
        self.selected_elements.clear()
        self.update_status()

    def filter_category(self, category: str):
        for btn, cat_key in self.cat_btn_group:
            btn.setChecked(cat_key == category)

        for tile in self.tiles.values():
            if category == "all" or tile.elem.category == category:
                tile.setVisible(True)
            else:
                tile.setVisible(False)

    def on_search_changed(self, text: str):
        query = text.strip().lower()
        if not query:
            for tile in self.tiles.values():
                tile.setVisible(True)
            return

        for tile in self.tiles.values():
            matches = (query in tile.elem.symbol.lower() or query in tile.elem.name.lower())
            tile.setVisible(matches)

    def set_active_elements(self, elements: List[str]):
        self.clear_selection()
        for sym in elements:
            if sym in self.tiles:
                self.tiles[sym].set_selected(True)
                self.selected_elements.add(sym)
        self.update_status()

    def apply_to_composition(self):
        if len(self.selected_elements) < 1:
            QMessageBox.warning(self, "Selection Notice", "Please select at least one chemical element.")
            return

        # Balance equiatomically to 100%
        n = len(self.selected_elements)
        val = round(100.0 / n, 2)
        comp = {}
        elems = sorted(list(self.selected_elements))
        for el in elems[:-1]:
            comp[el] = val
        comp[elems[-1]] = round(100.0 - sum(comp.values()), 2)

        self.elements_applied.emit(comp)


class PeriodicTableDialog(QDialog):
    def __init__(self, parent=None, initial_elements: Optional[List[str]] = None):
        super().__init__(parent)
        self.setWindowTitle("IUPAC Periodic Table of the Elements - 118 Elements Registry")
        self.resize(1180, 720)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self.pt_widget = PeriodicTableWidget(self)
        if initial_elements:
            self.pt_widget.set_active_elements(initial_elements)
        self.pt_widget.elements_applied.connect(self.on_applied)

        layout.addWidget(self.pt_widget)
        self.result_comp = None

    def on_applied(self, comp: dict):
        self.result_comp = comp
        self.accept()
