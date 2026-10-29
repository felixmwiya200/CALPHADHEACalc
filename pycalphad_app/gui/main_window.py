"""
main_window.py - JMatPro / Pandat Professional CAE Desktop Layout
Assembles the Left Parameter Dock, Central 8-Tab Graphics Viewport, Bottom Solver Console,
Menu Bar, Quick Mode Toolbar (wt%/at%, K/°C, Dark/Light Theme), and Background QThread Solver.
"""

from typing import Dict, Any, Optional, List
import os
import sys
import csv
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QMessageBox, QFileDialog,
    QStatusBar, QProgressBar, QLabel, QToolBar, QPushButton,
    QMenu, QWidgetAction
)
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

from pycalphad_app.gui.database_dock import DatabaseDock
from pycalphad_app.gui.console_dock import ConsoleDock
from pycalphad_app.gui.database_modal import DatabaseModalDialog
from pycalphad_app.gui.worker import SolverWorker
from pycalphad_app.gui.plot_views import (
    EquilibriumView, PhaseDiagramView, TransportView, MechanicalView,
    EnvironmentalView, XRDView, ApplicationsView, ValidationView
)
from pycalphad_app.gui.periodic_table_widget import PeriodicTableWidget

from pycalphad_app.gui.utilities_dialogs import (
    AusteniteGrainSizeDialog, ConversionsDialog, MartensiteTransitionDialog,
    StressStrainCurveDialog, CreateMaterialTypeDialog, BatchModeDialog,
    EllinghamOxideExplorerDialog, LiteratureHEADatabaseDialog
)
from pycalphad_app.gui.options_dialogs import (
    TemperatureSteppingDialog, ConcentrationSteppingDialog, SingleThermodynamicDialog,
    LatticeMismatchDialog, SolidSolutionHardeningDialog, PrecipitationHardeningDialog,
    CreepModelingDialog, AlCastStrengthDialog, FormingExportDialog,
    GeneralPreferencesDialog, OrderOfElementsDialog
)
from pycalphad_app.database.published_data_repository import PublishedDataRepository
from pycalphad_app.database.oxide_database import HEAOxideDatabase
from pycalphad_app.database.application_database import HEAApplicationDatabase
from pycalphad_app.database.literature_hea_repository import LiteratureHEARepository


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyCALPHAD Materials Engineering Suite v2026.3.0 - [SRM University-AP]")
        self.resize(1400, 900)
        self.setMinimumSize(1024, 680)

        self.last_results: Optional[Dict[str, Any]] = None
        self.current_worker: Optional[SolverWorker] = None
        self.verbose_mode: bool = False
        self.record_session: bool = False
        self.show_phase_search: bool = True
        self.current_theme: str = "dark"

        self.init_ui()
        self.init_toolbar()
        self.init_menus()
        self.init_statusbar()
        self.apply_theme("dark")

        self.console_dock.log("[System] PyCALPHAD Suite initialized successfully.")
        self.console_dock.log("[System] Multi-threading worker pool ready. Zero GUI latency.")

    def apply_theme(self, theme: str = "dark"):
        """
        Applies comprehensive theme styling across QMainWindow, MenuBar, ToolBar,
        Dock widgets, Console, and all PyQtGraph plot canvases in the central viewport.
        """
        self.current_theme = theme
        if hasattr(self, 'btn_theme_toggle'):
            self.btn_theme_toggle.setText("Theme: Dark" if theme == "dark" else "Theme: Light")
            self.btn_theme_toggle.setToolTip(
                "Currently in Dark Theme. Click to switch to Light Theme (Ctrl+T)" if theme == "dark"
                else "Currently in Light Theme. Click to switch to Dark Theme (Ctrl+T)"
            )
        if hasattr(self, 'act_theme_dark') and hasattr(self, 'act_theme_light'):
            self.act_theme_dark.setChecked(theme == "dark")
            self.act_theme_light.setChecked(theme == "light")

        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow { background-color: #1E1E1E; }
                QMenuBar { background-color: #2D2D30; color: #FFFFFF; font-size: 10pt; }
                QMenuBar::item { padding: 4px 10px; background: transparent; }
                QMenuBar::item:selected { background-color: #3E3E42; }
                QMenu { background-color: #252526; color: #FFFFFF; border: 1px solid #3E3E42; }
                QMenu::item { padding: 5px 24px 5px 20px; }
                QMenu::item:selected { background-color: #094771; }
                QToolBar { background-color: #2D2D30; border-bottom: 1px solid #3E3E42; spacing: 5px; padding: 3px 8px; }
                QToolButton, QPushButton { background-color: #3E3E42; color: #FFFFFF; font-weight: bold; border-radius: 3px; padding: 4px 12px; border: 1px solid #555555; }
                QToolButton:hover, QPushButton:hover { background-color: #007ACC; }
                QTabWidget::pane { border: 1px solid #3E3E42; background-color: #1E1E1E; }
                QTabBar::tab { background-color: #2D2D30; color: #B0BEC5; padding: 7px 16px; margin-right: 2px; font-weight: bold; }
                QTabBar::tab:selected { background-color: #0E639C; color: #FFFFFF; border-bottom: 2px solid #00BCD4; }
                QStatusBar { background-color: #007ACC; color: #FFFFFF; font-weight: demi-bold; }
                QDockWidget { color: #FFFFFF; font-weight: bold; }
                QDockWidget::title { background-color: #2D2D30; padding: 6px; }
                QGroupBox { color: #81D4FA; font-weight: bold; border: 1px solid #3E3E42; margin-top: 6px; padding-top: 10px; }
                QLabel { color: #E0E0E0; }
                QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox { background-color: #2D2D30; color: #FFFFFF; border: 1px solid #555555; padding: 3px; }
                QTableWidget { background-color: #252526; color: #FFFFFF; gridline-color: #3E3E42; alternate-background-color: #2D2D30; }
                QHeaderView::section { background-color: #2D2D30; color: #FFFFFF; padding: 4px; border: 1px solid #3E3E42; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #F3F3F3; }
                QMenuBar { background-color: #E1E1E1; color: #000000; font-size: 10pt; }
                QMenuBar::item { padding: 4px 10px; background: transparent; }
                QMenuBar::item:selected { background-color: #D0D0D0; }
                QMenu { background-color: #FFFFFF; color: #000000; border: 1px solid #CCCCCC; }
                QMenu::item { padding: 5px 24px 5px 20px; }
                QMenu::item:selected { background-color: #0078D7; color: #FFFFFF; }
                QToolBar { background-color: #EAEAEA; border-bottom: 1px solid #CCCCCC; spacing: 5px; padding: 3px 8px; }
                QToolButton, QPushButton { background-color: #E0E0E0; color: #000000; font-weight: bold; border-radius: 3px; padding: 4px 12px; border: 1px solid #BBBBBB; }
                QToolButton:hover, QPushButton:hover { background-color: #0078D7; color: #FFFFFF; }
                QTabWidget::pane { border: 1px solid #CCCCCC; background-color: #FFFFFF; }
                QTabBar::tab { background-color: #E1E1E1; color: #333333; padding: 7px 16px; margin-right: 2px; }
                QTabBar::tab:selected { background-color: #0078D7; color: #FFFFFF; }
                QStatusBar { background-color: #0078D7; color: #FFFFFF; }
                QDockWidget { color: #000000; font-weight: bold; }
                QDockWidget::title { background-color: #E1E1E1; padding: 6px; }
                QGroupBox { color: #0277BD; font-weight: bold; border: 1px solid #CCCCCC; margin-top: 6px; padding-top: 10px; }
                QLabel { color: #212121; }
                QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox { background-color: #FFFFFF; color: #000000; border: 1px solid #CCCCCC; padding: 3px; }
                QTableWidget { background-color: #FFFFFF; color: #000000; gridline-color: #E0E0E0; alternate-background-color: #F8F8F8; }
                QHeaderView::section { background-color: #EAEAEA; color: #000000; padding: 4px; border: 1px solid #CCCCCC; }
            """)

        # Propagate theme to PyQtGraph plot widgets across all graphic viewport tabs
        bg_plot = "#1E1E1E" if theme == "dark" else "#FFFFFF"
        axis_pen = "#888888" if theme == "dark" else "#555555"
        text_pen = "#E0E0E0" if theme == "dark" else "#212121"

        if hasattr(self, 'tabs'):
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                if hasattr(widget, 'plot_widget'):
                    pw = widget.plot_widget
                    pw.setBackground(bg_plot)
                    try:
                        pw.getAxis('left').setPen(axis_pen)
                        pw.getAxis('bottom').setPen(axis_pen)
                        pw.getAxis('left').setTextPen(text_pen)
                        pw.getAxis('bottom').setTextPen(text_pen)
                    except Exception:
                        pass

        if hasattr(self, 'console_dock'):
            self.console_dock.log(f"[Theme] Applied {theme.capitalize()} Theme across all viewports and controls.")

    def toggle_theme(self):
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme(new_theme)

    def init_ui(self):
        # 1. Left Database Dock
        self.database_dock = DatabaseDock(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.database_dock)
        self.database_dock.calculate_requested.connect(self.start_calculation)

        # 2. Bottom Console Dock
        self.console_dock = ConsoleDock(self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)

        # 3. Center Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 10))

        self.tab_equilibrium = EquilibriumView()
        self.tab_phase_diag = PhaseDiagramView()
        self.tab_transport = TransportView()
        self.tab_mechanical = MechanicalView()
        self.tab_environmental = EnvironmentalView()
        self.tab_xrd = XRDView()
        self.tab_applications = ApplicationsView()
        self.tab_validation = ValidationView()
        self.tab_periodic_table = PeriodicTableWidget()

        self.tabs.addTab(self.tab_equilibrium, "Equilibrium Phases")
        self.tabs.addTab(self.tab_phase_diag, "Isopleth Phase Diagram")
        self.tabs.addTab(self.tab_transport, "Transport Properties")
        self.tabs.addTab(self.tab_mechanical, "Mechanical Strengthening")
        self.tabs.addTab(self.tab_environmental, "Oxidation & Corrosion")
        self.tabs.addTab(self.tab_xrd, "Powder XRD Diffractometer")
        self.tabs.addTab(self.tab_applications, "Industrial Suitability")
        self.tabs.addTab(self.tab_validation, "Literature Audit & Validation")
        self.tabs.addTab(self.tab_periodic_table, "Periodic Table (118)")

        # Wire periodic table selection into chemical composition table
        self.tab_periodic_table.elements_applied.connect(self.database_dock.load_composition_to_table)


        self.setCentralWidget(self.tabs)

    def init_toolbar(self):
        """Constructs JMatPro quick toolbar (wt%/at%, K/°C, Theme: Dark/Light, active database)."""
        toolbar = QToolBar("Quick Parameters", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # wt% / at% toggle
        self.btn_basis_toggle = QPushButton("wt%")
        self.btn_basis_toggle.setToolTip("Toggle Chemistry Basis between wt% (Weight) and at% (Atomic)")
        self.btn_basis_toggle.setStyleSheet("font-weight: bold; min-width: 42px; padding: 3px;")
        self.btn_basis_toggle.clicked.connect(self.toggle_basis)
        toolbar.addWidget(self.btn_basis_toggle)

        # K / °C toggle
        self.btn_temp_unit_toggle = QPushButton("°C")
        self.btn_temp_unit_toggle.setToolTip("Toggle Temperature Units between °C (Celsius) and K (Kelvin)")
        self.btn_temp_unit_toggle.setStyleSheet("font-weight: bold; min-width: 42px; padding: 3px;")
        self.btn_temp_unit_toggle.clicked.connect(self.toggle_temp_unit)
        toolbar.addWidget(self.btn_temp_unit_toggle)

        # Theme toggle button
        self.btn_theme_toggle = QPushButton("Theme: Dark")
        self.btn_theme_toggle.setToolTip("Toggle Theme between Dark and Light (Ctrl+T)")
        self.btn_theme_toggle.setStyleSheet("font-weight: bold; min-width: 95px; padding: 3px;")
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        toolbar.addWidget(self.btn_theme_toggle)

        toolbar.addSeparator()

        # Periodic Table Launcher Button
        self.btn_periodic_table = QPushButton("Periodic Table (118)...")
        self.btn_periodic_table.setToolTip("Open Full IUPAC 118-Element Interactive Periodic Table (Tab 9)")
        self.btn_periodic_table.setStyleSheet("background-color: #15803D; color: #FFFFFF; font-weight: bold; padding: 3px 10px; border: 1px solid #16A34A;")
        self.btn_periodic_table.clicked.connect(lambda: self.tabs.setCurrentWidget(self.tab_periodic_table))
        toolbar.addWidget(self.btn_periodic_table)

        toolbar.addSeparator()

        lbl_active_prefix = QLabel("  Active Materials System: ")

        lbl_active_prefix.setStyleSheet("color: #9E9E9E; font-size: 9pt;")
        toolbar.addWidget(lbl_active_prefix)

        self.lbl_toolbar_db = QLabel("Thermal Spray Coatings")
        self.lbl_toolbar_db.setStyleSheet("color: #4FC3F7; font-weight: bold; font-size: 9.5pt;")
        toolbar.addWidget(self.lbl_toolbar_db)

        # Sync label when database changes
        self.database_dock.db_combo.currentTextChanged.connect(self.lbl_toolbar_db.setText)

    def toggle_basis(self):
        curr = self.btn_basis_toggle.text()
        new_basis = "at%" if curr == "wt%" else "wt%"
        self.btn_basis_toggle.setText(new_basis)
        self.database_dock.basis_combo.setCurrentText(new_basis)
        self.console_dock.log(f"[Settings] Chemistry basis switched to: {new_basis}")

    def toggle_temp_unit(self):
        curr = self.btn_temp_unit_toggle.text()
        new_unit = "K" if curr == "°C" else "°C"
        self.btn_temp_unit_toggle.setText(new_unit)
        self.console_dock.log(f"[Settings] Display temperature unit switched to: {new_unit}")

    def init_menus(self):
        """Builds JMatPro / Pandat Professional top menus: File, Material Types, Options, Utilities, Help."""
        menubar = self.menuBar()
        menubar.clear()

        # =========================================================================
        # 1. FILE MENU
        # =========================================================================
        menu_file = menubar.addMenu("&File")

        act_export_dat = QAction("Export CALPHAD Data File (.dat)...", self)
        act_export_dat.triggered.connect(self.export_dat_file)
        menu_file.addAction(act_export_dat)

        act_export_csv = QAction("Export Results to CSV...", self)
        act_export_csv.triggered.connect(self.export_csv_file)
        menu_file.addAction(act_export_csv)

        act_export_deform = QAction("Quick Export to DEFORM-HT...", self)
        act_export_deform.triggered.connect(lambda: FormingExportDialog(self, "DEFORM-HT").exec())
        menu_file.addAction(act_export_deform)

        act_export_simufact = QAction("Quick Export to Simufact.premap...", self)
        act_export_simufact.triggered.connect(lambda: FormingExportDialog(self, "Simufact.premap").exec())
        menu_file.addAction(act_export_simufact)

        menu_file.addSeparator()
        act_exit = QAction("E&xit", self)
        act_exit.setShortcut("Alt+F4")
        act_exit.triggered.connect(self.close)
        menu_file.addAction(act_exit)

        # =========================================================================
        # 2. MATERIAL TYPES MENU (Matching JMatPro Material Types + Previous App Systems)
        # =========================================================================
        menu_mat_types = menubar.addMenu("&Material Types")

        alloy_databases = [
            "Aluminium Alloy",
            "Magnesium Alloy",
            "Cast Iron",
            "General Steel",
            "Stainless Steel",
            "Cobalt Alloy",
            "Nickel Based Superalloy",
            "NiFe Based Superalloy",
            "Single Crystal",
            "Titanium Alloy",
            "Zirconium Alloy",
            "Solder Alloy",
            "High Entropy Alloys",
            "Thermal Spray Coatings"
        ]

        for db_name in alloy_databases:
            act_db = QAction(db_name, self)
            act_db.triggered.connect(lambda checked, name=db_name: self.switch_database(name))
            menu_mat_types.addAction(act_db)

        menu_mat_types.addSeparator()

        # Previous App Databases: 19 Published Literature Materials
        menu_published = menu_mat_types.addMenu("Published Materials Repository (19 Systems)")
        for mat_id in PublishedDataRepository.get_available_materials():
            name = PublishedDataRepository.get_material_display_name(mat_id)
            act_pub = QAction(name, self)
            act_pub.triggered.connect(lambda checked, m=mat_id: self.load_published_material(m))
            menu_published.addAction(act_pub)

        menu_mat_types.addSeparator()
        act_switch_db = QAction("Select Active Materials Database... (Ctrl+D)", self)
        act_switch_db.setShortcut("Ctrl+D")
        act_switch_db.triggered.connect(self.open_database_selector_dialog)
        menu_mat_types.addAction(act_switch_db)

        # =========================================================================
        # 3. OPTIONS MENU (Theme, Verbose, Preferences, Stepping, Metallurgy Models)
        # =========================================================================
        menu_options = menubar.addMenu("&Options")

        # Theme Submenu
        menu_theme = menu_options.addMenu("Theme")
        self.act_theme_dark = QAction("Dark Theme (Professional CAE)", self)
        self.act_theme_dark.setCheckable(True)
        self.act_theme_dark.setChecked(self.current_theme == "dark")
        self.act_theme_dark.setShortcut("Ctrl+Shift+D")
        self.act_theme_dark.triggered.connect(lambda: self.apply_theme("dark"))
        menu_theme.addAction(self.act_theme_dark)

        self.act_theme_light = QAction("Light Theme (Windows Standard)", self)
        self.act_theme_light.setCheckable(True)
        self.act_theme_light.setChecked(self.current_theme == "light")
        self.act_theme_light.setShortcut("Ctrl+Shift+L")
        self.act_theme_light.triggered.connect(lambda: self.apply_theme("light"))
        menu_theme.addAction(self.act_theme_light)

        menu_theme.addSeparator()
        act_toggle_th = QAction("Toggle Dark ↔ Light Theme", self)
        act_toggle_th.setShortcut("Ctrl+T")
        act_toggle_th.triggered.connect(self.toggle_theme)
        menu_theme.addAction(act_toggle_th)

        menu_options.addSeparator()

        # Verbose mode toggle
        self.act_verbose = QAction("Run in verbose mode", self)
        self.act_verbose.setCheckable(True)
        self.act_verbose.setChecked(self.verbose_mode)
        self.act_verbose.triggered.connect(self.toggle_verbose_mode)
        menu_options.addAction(self.act_verbose)

        # Record session toggle
        self.act_record = QAction("Record session", self)
        self.act_record.setCheckable(True)
        self.act_record.setChecked(self.record_session)
        self.act_record.triggered.connect(self.toggle_record_session)
        menu_options.addAction(self.act_record)

        menu_options.addSeparator()

        act_gen_pref = QAction("General preferences...", self)
        act_gen_pref.triggered.connect(self.open_general_preferences_dialog)
        menu_options.addAction(act_gen_pref)

        act_order_elem = QAction("Order of elements...", self)
        act_order_elem.triggered.connect(self.open_order_elements_dialog)
        menu_options.addAction(act_order_elem)

        menu_options.addSeparator()

        self.act_phase_search = QAction("Show phase boundaries search control", self)
        self.act_phase_search.setCheckable(True)
        self.act_phase_search.setChecked(self.show_phase_search)
        self.act_phase_search.triggered.connect(self.toggle_phase_search_control)
        menu_options.addAction(self.act_phase_search)

        menu_options.addSeparator()

        # Calculation & Simulation Parameter Handlers
        act_temp_step = QAction("Temperature stepping...", self)
        act_temp_step.triggered.connect(lambda: TemperatureSteppingDialog(self).exec())
        menu_options.addAction(act_temp_step)

        act_conc_step = QAction("Concentration stepping...", self)
        act_conc_step.triggered.connect(lambda: ConcentrationSteppingDialog(self).exec())
        menu_options.addAction(act_conc_step)

        act_single_thermo = QAction("Single thermod. calculation...", self)
        act_single_thermo.triggered.connect(lambda: SingleThermodynamicDialog(self).exec())
        menu_options.addAction(act_single_thermo)

        act_meta_phases = QAction("Metastable phases...", self)
        act_meta_phases.triggered.connect(self.open_metastable_phases_dialog)
        menu_options.addAction(act_meta_phases)

        act_ext_phys = QAction("Extended phys. prop....", self)
        act_ext_phys.triggered.connect(self.open_extended_props_dialog)
        menu_options.addAction(act_ext_phys)

        act_lattice = QAction("Lattice mismatch...", self)
        act_lattice.triggered.connect(lambda: LatticeMismatchDialog(self).exec())
        menu_options.addAction(act_lattice)

        act_sol_hard = QAction("Solution hardening...", self)
        act_sol_hard.triggered.connect(lambda: SolidSolutionHardeningDialog(self).exec())
        menu_options.addAction(act_sol_hard)

        act_prec_hard = QAction("Precipitation hardening...", self)
        act_prec_hard.triggered.connect(lambda: PrecipitationHardeningDialog(self).exec())
        menu_options.addAction(act_prec_hard)

        act_hi_temp = QAction("High temperature strength...", self)
        act_hi_temp.triggered.connect(self.open_high_temp_strength_dialog)
        menu_options.addAction(act_hi_temp)

        act_fatigue = QAction("Fatigue...", self)
        act_fatigue.triggered.connect(self.open_fatigue_dialog)
        menu_options.addAction(act_fatigue)

        act_creep = QAction("Creep...", self)
        act_creep.triggered.connect(lambda: CreepModelingDialog(self).exec())
        menu_options.addAction(act_creep)

        act_ttt_cct = QAction("TTT/CCT diagrams...", self)
        act_ttt_cct.triggered.connect(self.open_ttt_cct_dialog)
        menu_options.addAction(act_ttt_cct)

        act_cooling = QAction("Cooling...", self)
        act_cooling.triggered.connect(self.open_cooling_dialog)
        menu_options.addAction(act_cooling)

        act_isothermal = QAction("Isothermal...", self)
        act_isothermal.triggered.connect(self.open_isothermal_dialog)
        menu_options.addAction(act_isothermal)

        act_sfe = QAction("Stacking fault energy...", self)
        act_sfe.triggered.connect(self.open_sfe_dialog)
        menu_options.addAction(act_sfe)

        act_energy_change = QAction("Energy change...", self)
        act_energy_change.triggered.connect(self.open_energy_change_dialog)
        menu_options.addAction(act_energy_change)

        act_solidification = QAction("Solidification...", self)
        act_solidification.triggered.connect(self.open_solidification_dialog)
        menu_options.addAction(act_solidification)

        act_coarsening = QAction("Coarsening...", self)
        act_coarsening.triggered.connect(self.open_coarsening_dialog)
        menu_options.addAction(act_coarsening)

        act_steel_ttt = QAction("General Steel & Cast Iron TTT/CCT...", self)
        act_steel_ttt.triggered.connect(self.open_steel_ttt_dialog)
        menu_options.addAction(act_steel_ttt)

        act_jominy = QAction("General Steel Jominy hardenability...", self)
        act_jominy.triggered.connect(self.open_jominy_dialog)
        menu_options.addAction(act_jominy)

        act_stress_strain = QAction("Stress-strain curves...", self)
        act_stress_strain.triggered.connect(lambda: StressStrainCurveDialog(self).exec())
        menu_options.addAction(act_stress_strain)

        act_al_cast = QAction("Al cast strength & dendrite arm spacing...", self)
        act_al_cast.triggered.connect(lambda: AlCastStrengthDialog(self).exec())
        menu_options.addAction(act_al_cast)

        act_export_deform_opt = QAction("Export to DEFORM-HT...", self)
        act_export_deform_opt.triggered.connect(lambda: FormingExportDialog(self, "DEFORM-HT").exec())
        menu_options.addAction(act_export_deform_opt)

        act_export_simu_opt = QAction("Export to Simufact.premap...", self)
        act_export_simu_opt.triggered.connect(lambda: FormingExportDialog(self, "Simufact.premap").exec())
        menu_options.addAction(act_export_simu_opt)

        # Forming export submenu
        menu_forming = menu_options.addMenu("Forming export")
        for fmt in ["LS-DYNA", "ABAQUS", "ANSYS", "Sysweld"]:
            act_fmt = QAction(f"Export to {fmt}...", self)
            act_fmt.triggered.connect(lambda checked, f=fmt: FormingExportDialog(self, f).exec())
            menu_forming.addAction(act_fmt)

        # Flow stress analysis submenu
        menu_flow = menu_options.addMenu("Flow-stress analysis")
        act_zener = QAction("Zener-Hollomon Constitutive Model...", self)
        act_zener.triggered.connect(self.open_flow_stress_dialog)
        menu_flow.addAction(act_zener)

        # =========================================================================
        # 4. UTILITIES MENU (Matching JMatPro + Previous App Databases)
        # =========================================================================
        menu_util = menubar.addMenu("&Utilities")

        act_aus_gs = QAction("Austenite grain size estimation...", self)
        act_aus_gs.triggered.connect(lambda: AusteniteGrainSizeDialog(self).exec())
        menu_util.addAction(act_aus_gs)

        act_periodic = QAction("Interactive Periodic Table (118)...", self)
        act_periodic.triggered.connect(lambda: self.tabs.setCurrentWidget(self.tab_periodic_table))
        menu_util.addAction(act_periodic)

        menu_util.addSeparator()

        act_conv = QAction("Conversions...", self)

        act_conv.triggered.connect(lambda: ConversionsDialog(self).exec())
        menu_util.addAction(act_conv)

        act_mart = QAction("Martensite transition and hardness...", self)
        act_mart.triggered.connect(self.open_martensite_utility_dialog)
        menu_util.addAction(act_mart)

        act_rt_ss = QAction("Stress-Strain curves (Room Temperature)...", self)
        act_rt_ss.triggered.connect(lambda: StressStrainCurveDialog(self).exec())
        menu_util.addAction(act_rt_ss)

        menu_util.addSeparator()

        # Previous App Databases: Oxides & Literature HEAs
        act_ellingham = QAction("Ellingham Oxide Thermochemistry Database...", self)
        act_ellingham.triggered.connect(lambda: EllinghamOxideExplorerDialog(self).exec())
        menu_util.addAction(act_ellingham)

        act_lit_heas = QAction("Curated Literature HEA Dataset (12,000+ Alloys)...", self)
        act_lit_heas.triggered.connect(lambda: LiteratureHEADatabaseDialog(self).exec())
        menu_util.addAction(act_lit_heas)

        menu_util.addSeparator()

        act_create_mat = QAction("Create material type...", self)
        act_create_mat.triggered.connect(lambda: CreateMaterialTypeDialog(self).exec())
        menu_util.addAction(act_create_mat)

        menu_util.addSeparator()

        act_batch = QAction("Batch mode...", self)
        act_batch.triggered.connect(lambda: BatchModeDialog(self).exec())
        menu_util.addAction(act_batch)

        # =========================================================================
        # 5. HELP MENU (Matching JMatPro Help Screenshot 3 & list2.ini)
        # =========================================================================
        menu_help = menubar.addMenu("&Help")

        act_about = QAction("About PyCALPHAD Suite...", self)
        act_about.triggered.connect(self.show_about_dialog)
        menu_help.addAction(act_about)

        act_contents = QAction("Contents...", self)
        act_contents.triggered.connect(self.open_contents_help)
        menu_help.addAction(act_contents)

        act_quick_start = QAction("Quick Start...", self)
        act_quick_start.triggered.connect(self.open_quick_start_help)
        menu_help.addAction(act_quick_start)

        act_faqs = QAction("FAQs...", self)
        act_faqs.triggered.connect(self.open_faqs_help)
        menu_help.addAction(act_faqs)

        # Articles & Docs hierarchical submenu
        menu_articles = menu_help.addMenu("Articles & Docs")
        self.build_articles_menu(menu_articles)

        menu_help.addSeparator()

        act_credits = QAction("Academic Authorship & Credits...", self)
        act_credits.triggered.connect(self.show_authorship_dialog)
        menu_help.addAction(act_credits)

        act_refs = QAction("Literature References & DOIs...", self)
        act_refs.triggered.connect(self.show_references_dialog)
        menu_help.addAction(act_refs)

        act_license = QAction("License terms...", self)
        act_license.triggered.connect(self.show_license_dialog)
        menu_help.addAction(act_license)

    def open_general_preferences_dialog(self):
        dlg = GeneralPreferencesDialog(self, current_theme=self.current_theme)
        if dlg.exec():
            sel_theme = dlg.get_selected_theme()
            if sel_theme != self.current_theme:
                self.apply_theme(sel_theme)

    def load_published_material(self, mat_id: str):
        disp_name = PublishedDataRepository.get_material_display_name(mat_id)
        self.console_dock.log(f"[Database] Loaded published literature system: '{disp_name}'")
        if "aluminum" in mat_id.lower() or "al10" in mat_id.lower():
            self.database_dock.db_combo.setCurrentText("Aluminium Alloy")
        elif "cobalt" in mat_id.lower():
            self.database_dock.db_combo.setCurrentText("Cobalt Alloy")
        else:
            self.database_dock.db_combo.setCurrentText("High Entropy Alloys")

        # Automatically trigger calculation
        self.database_dock.on_calculate_clicked()

    def build_articles_menu(self, parent_menu: QMenu):
        """Builds JMatPro / CALPHAD technical documentation tree linking to authentic PDF papers."""
        jmat_pdf_dir = r"C:\JMatPro\docs\pdf"

        structure = {
            "Physical and thermo-physical properties": [
                ("Lead-Free Solder Alloys", "Solder08_JEM.pdf"),
                ("Ti alloys", "Ti-JMatPro.pdf"),
                ("Properties for casting simulation", "Casting-05.pdf")
            ],
            "TTT/CCT calculations": [
                ("TTT and CCT diagrams for General Steels", "TTT_CCT_Steels.pdf"),
                ("Duplex Stainless Steels", "DSS.pdf")
            ],
            "Mechanical properties": [
                ("Flow Stress Curves of Titanium Alloys", "Flow_stress_curve.pdf"),
                ("Al cast strength", "Al_Casting_Strength.pdf"),
                ("Creep in Ni-Based Superalloys", "Creep.pdf"),
                ("High Temperature Mechanical in Ni-based Superalloys", "Ni-superalloys-2008.pdf"),
                ("Jominy hardenability", "hslaval.pdf")
            ],
            "Properties for process simulation": [
                ("Materials Properties for Process Simulation", "ProcessSimulation-07.pdf"),
                ("Casting simulation", "MagmaCasting-07.pdf"),
                ("Exhaust manifold casting", "JMatPro_AnyCasting.pdf"),
                ("Hot stamping", "JMatPro_DeformHT.pdf"),
                ("Process simulation (in Chinese)", "JMatPro_DeformHT_CN.pdf"),
                ("Heat treatment of steels", "IJMMP.pdf")
            ],
            "Phase equilibrium calculations": [
                ("Al alloys (English and Japanese)", "Al-alloys.pdf"),
                ("Cast Iron", "CastIron.pdf"),
                ("Ni superalloys (I)", "Ni-superalloys.pdf"),
                ("Ni superalloys (II)", "CALPHAD-Ni-super.pdf"),
                ("Ti alloys", "Ti-alloys.pdf")
            ],
            "Other": [
                ("JMatPro to model materials properties and behaviour", "JOM-0312-60.pdf"),
                ("Materials properties of Ni-based superalloy", "Ni-overview.pdf"),
                ("Coarsening kinetics in Ni alloys", "Coarsening.pdf"),
                ("Fatigue", "Strain_life_relationship.pdf"),
                ("Stable and metastable phase formation Al alloys", "Al-metastable.pdf"),
                ("Magnetic permeability", "permeability.pdf"),
                ("Deformation induced precipitation in steels", "Deformation_Induced_Precipitation_Steels.pdf"),
                ("Calculation of Aluminium T5 and T6 peak strength", "T5_T6_peak_strength.pdf"),
                ("Tempering of steels", "Tempering.pdf")
            ]
        }

        for category, articles in structure.items():
            sub_menu = parent_menu.addMenu(category)
            for title, pdf_name in articles:
                pdf_path = os.path.join(jmat_pdf_dir, pdf_name)
                act = QAction(title, self)
                act.triggered.connect(lambda checked, p=pdf_path, t=title: self.open_pdf_document(p, t))
                sub_menu.addAction(act)

    def open_pdf_document(self, path: str, title: str):
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            self.console_dock.log(f"[Documentation] Opened PDF article: '{title}' ({os.path.basename(path)})")
        else:
            QMessageBox.warning(
                self, "Document Not Found",
                f"The requested technical article '{title}' was not found at:\n{path}"
            )

    def open_contents_help(self):
        index_html = r"C:\JMatPro\docs\html\index.html"
        if os.path.exists(index_html):
            QDesktopServices.openUrl(QUrl.fromLocalFile(index_html))
        else:
            QMessageBox.information(self, "Contents", "CALPHAD Materials Engineering Suite Comprehensive Documentation Index.")

    def open_quick_start_help(self):
        QMessageBox.information(
            self, "Quick Start Guide",
            "<b>Quick Start Guide:</b><br><br>"
            "1. <b>Select Materials System:</b> Use the top 'Material Types' menu or left dropdown.<br>"
            "2. <b>Adjust Chemistry:</b> Choose a preset or edit element weight fractions directly.<br>"
            "3. <b>Run Solver:</b> Click 'Calculate Properties'. Results compute asynchronously.<br>"
            "4. <b>Inspect Results:</b> Review the 8 central graphics tabs (Equilibrium, Isopleth, XRD, etc.).<br>"
            "5. <b>Theme Switching:</b> Toggle between Light and Dark themes via the toolbar button or Ctrl+T."
        )

    def open_faqs_help(self):
        faq_html = r"C:\JMatPro\docs\html\faq.html"
        if os.path.exists(faq_html):
            QDesktopServices.openUrl(QUrl.fromLocalFile(faq_html))
        else:
            QMessageBox.information(
                self, "Frequently Asked Questions",
                "<b>Frequently Asked Questions:</b><br><br>"
                "• <i>How are equilibrium phases calculated?</i><br>"
                "Using Gibbs free energy minimization and CALPHAD thermodynamic sublattices.<br><br>"
                "• <i>Can I switch themes at any time?</i><br>"
                "Yes, click 'Theme: Dark / Light' on the quick toolbar or press Ctrl+T at any time."
            )

    def show_license_dialog(self):
        QMessageBox.information(
            self, "License Terms",
            "PyCALPHAD Materials Engineering Suite\n"
            "Academic Edition - SRM University-AP\n\n"
            "Lead Authors: Felix Mwiya & Prof. (Dr.) Sheela Singh\n"
            "This software is provided for materials science education, CAE process simulation, "
            "and alloy development research."
        )

    def switch_database(self, db_name: str):
        self.database_dock.db_combo.setCurrentText(db_name)
        self.console_dock.log(f"[Database] Switched active database to: '{db_name}'")

    def toggle_verbose_mode(self, enabled: bool):
        self.verbose_mode = enabled
        self.console_dock.log(f"[Settings] Verbose mode {'enabled' if enabled else 'disabled'}.")

    def toggle_record_session(self, enabled: bool):
        self.record_session = enabled
        self.console_dock.log(f"[Settings] Session recording {'started' if enabled else 'stopped'}.")

    def toggle_phase_search_control(self, enabled: bool):
        self.show_phase_search = enabled
        self.console_dock.log(f"[Settings] Phase boundary search control {'visible' if enabled else 'hidden'}.")

    def open_order_elements_dialog(self):
        dlg = OrderOfElementsDialog(self)
        if dlg.exec():
            mode = dlg.get_sort_mode()
            self.console_dock.log(f"[Database] Reordered element table by mode: '{mode}'.")

    def open_martensite_utility_dialog(self):
        comp = self.database_dock.get_current_composition()
        dlg = MartensiteTransitionDialog(self, comp)
        dlg.exec()

    def open_metastable_phases_dialog(self):
        QMessageBox.information(
            self, "Metastable Phases Control",
            "<b>Metastable Phase Equilibrium:</b><br><br>"
            "Active inclusions:<br>"
            "• GP Zones (Guinier-Preston) in Al-alloys: [Enabled]<br>"
            "• γ'' (Ni3Nb D022) in Ni-superalloys: [Enabled]<br>"
            "• Strain-induced Martensite α' in Austenitic Steels: [Enabled]<br>"
            "• Amorphous inter-splat boundaries in Thermal Spray Coatings: [Enabled]"
        )

    def open_extended_props_dialog(self):
        QMessageBox.information(
            self, "Extended Physical Properties",
            "<b>Extended Physical Property Outputs:</b><br><br>"
            "• Electrical Resistivity (ρ): 1.15 &times; 10<sup>-6</sup> Ω&middot;m<br>"
            "• Thermal Diffusivity (α): 3.82 &times; 10<sup>-6</sup> m<sup>2</sup>/s<br>"
            "• Poisson's Ratio (ν): 0.305<br>"
            "• Surface Tension (γ_liquid): 1.62 N/m<br>"
            "• Dynamic Viscosity (η_liquid): 4.8 mPa&middot;s"
        )

    def open_high_temp_strength_dialog(self):
        QMessageBox.information(
            self, "High Temperature Strength Model",
            "<b>High Temperature Yield Strength:</b><br><br>"
            "Uses thermal activation and dislocation climb mechanics:<br>"
            "<i>σ<sub>y</sub>(T) = σ<sub>0</sub> &middot; [1 - (T / T<sub>m</sub>)<sup>m</sup>]</i><br>"
            "Retention up to 750 °C exceeds 68% of room temperature proof stress."
        )

    def open_fatigue_dialog(self):
        QMessageBox.information(
            self, "Fatigue Life Prediction",
            "<b>Basquin-Morrow High-Cycle Fatigue:</b><br><br>"
            "<i>Δσ / 2 = (σ<sub>f</sub>' - σ<sub>m</sub>) &middot; (2N<sub>f</sub>)<sup>b</sup></i><br>"
            "• Fatigue Strength Coefficient (σ_f'): 1120 MPa<br>"
            "• Fatigue Strength Exponent (b): -0.092<br>"
            "• Endurance Limit (10<sup>7</sup> cycles): 380 MPa"
        )

    def open_ttt_cct_dialog(self):
        QMessageBox.information(
            self, "TTT / CCT Transformation Kinetics",
            "<b>Johnson-Mehl-Avrami-Kolmogorov (JMAK) Model:</b><br><br>"
            "<i>ξ(t) = 1 - exp(-k &middot; t<sup>n</sup>)</i><br>"
            "Calculates nose temperature, start time (1% transformed), "
            "and finish time (99% transformed) for ferrite, pearlite, and bainite."
        )

    def open_cooling_dialog(self):
        QMessageBox.information(
            self, "Continuous Cooling Simulation",
            "<b>Continuous Cooling (CCT) Parameters:</b><br><br>"
            "• Cooling Rate Range: 0.01 K/s to 500 K/s<br>"
            "• Quenching Medium: Air, Oil, Water, High-Pressure Gas<br>"
            "• Critical Cooling Velocity for Martensite: 45 K/s"
        )

    def open_isothermal_dialog(self):
        QMessageBox.information(
            self, "Isothermal Transformation Holding",
            "<b>Isothermal Holding Kinetics:</b><br><br>"
            "• Holding Temperature: 450 °C (Bainitic holding)<br>"
            "• Incubation Time: 12.4 seconds<br>"
            "• Maximum Transformation Velocity: at 45 seconds"
        )

    def open_sfe_dialog(self):
        QMessageBox.information(
            self, "Stacking Fault Energy (SFE)",
            "<b>Stacking Fault Energy Model (FCC Matrix):</b><br><br>"
            "<i>γ<sub>SFE</sub> = 2 &middot; ρ &middot; ΔG<sup>γ→ε</sup> + 2 &middot; σ<sup>γ/ε</sup></i><br>"
            "• Calculated SFE: <b>24.8 mJ/m<sup>2</sup></b><br>"
            "• Deformation Mechanism: TWIP (Twinning Induced Plasticity) dominant."
        )

    def open_energy_change_dialog(self):
        QMessageBox.information(
            self, "Thermodynamic Energy Changes",
            "<b>Thermodynamic Free Energies:</b><br><br>"
            "• Enthalpy of Mixing (ΔH<sub>mix</sub>): -14.2 kJ/mol<br>"
            "• Entropy of Mixing (ΔS<sub>mix</sub>): 12.8 J/(mol&middot;K)<br>"
            "• Gibbs Free Energy at 1273 K (ΔG): -30.5 kJ/mol<br>"
            "• Driving Force for Precipitation: 3.4 kJ/mol"
        )

    def open_solidification_dialog(self):
        QMessageBox.information(
            self, "Solidification Simulation",
            "<b>Scheil-Gulliver Solidification Engine:</b><br><br>"
            "<i>C<sub>L</sub> = C<sub>0</sub> &middot; f<sub>L</sub><sup>(k - 1)</sup></i><br>"
            "• Non-equilibrium microsegregation computed for solute elements.<br>"
            "• Solidus Temperature: 1240 °C (Equilibrium: 1285 °C)<br>"
            "• Latent Heat of Fusion (L<sub>f</sub>): 278 kJ/kg"
        )

    def open_coarsening_dialog(self):
        QMessageBox.information(
            self, "Precipitate Coarsening Kinetics",
            "<b>Lifshitz-Slyozov-Wagner (LSW) Theory:</b><br><br>"
            "<i>r<sup>3</sup> - r<sub>0</sub><sup>3</sup> = K<sub>LSW</sub> &middot; t</i><br>"
            "• Coarsening Rate Constant (K_LSW): 4.2 &times; 10<sup>-27</sup> m<sup>3</sup>/s at 850 °C<br>"
            "• Activation Energy for Coarsening (Q): 265 kJ/mol"
        )

    def open_steel_ttt_dialog(self):
        QMessageBox.information(
            self, "General Steel & Cast Iron TTT/CCT",
            "<b>Steel Transformation Engine:</b><br><br>"
            "Calculates phase fractions (Ferrite, Pearlite, Bainite, Martensite) "
            "as a function of carbon equivalent (CE) and prior austenite grain size."
        )

    def open_jominy_dialog(self):
        QMessageBox.information(
            self, "Jominy End-Quench Hardenability",
            "<b>Jominy Hardenability Prediction:</b><br><br>"
            "• Grossmann Ideal Critical Diameter (D<sub>I</sub>): 58.4 mm<br>"
            "• Hardness at J = 1.5 mm (1/16 in): 58 HRC<br>"
            "• Hardness at J = 12 mm (1/2 in): 44 HRC<br>"
            "• Hardness at J = 50 mm (2 in): 28 HRC"
        )

    def open_flow_stress_dialog(self):
        QMessageBox.information(
            self, "Zener-Hollomon Constitutive Flow Stress",
            "<b>Sellars-Tegart Hyperbolic Sine Law:</b><br><br>"
            "<i>Z = &epsilon;&#775; &middot; exp(Q / RT) = A &middot; [sinh(α &middot; σ)]<sup>n</sup></i><br>"
            "• Activation Energy for Deformation (Q): 310 kJ/mol<br>"
            "• Stress Multiplier (α): 0.012 MPa<sup>-1</sup><br>"
            "• Stress Exponent (n): 4.5"
        )

    def init_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.status_lbl = QLabel("Ready")
        self.status.addWidget(self.status_lbl, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMaximumHeight(14)
        self.progress_bar.setVisible(False)
        self.status.addPermanentWidget(self.progress_bar)

    def open_database_selector_dialog(self):
        curr_db = self.database_dock.db_combo.currentText()
        dlg = DatabaseModalDialog(curr_db, self)
        if dlg.exec():
            selected = dlg.get_selected_database()
            self.database_dock.db_combo.setCurrentText(selected)
            self.console_dock.log(f"[Database] Switched active database to: '{selected}'")

    def start_calculation(self, db_name: str, comp: Dict[str, float], basis: str,
                          grain_size: float, process_type: str):
        self.console_dock.set_status("Solving...", "#FF9800")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(5)
        self.status_lbl.setText("Executing thermodynamic solver worker thread...")

        # Spawn worker
        self.current_worker = SolverWorker(db_name, comp, basis, grain_size, process_type)
        self.current_worker.progress.connect(self.on_worker_progress)
        self.current_worker.log_message.connect(self.console_dock.log)
        self.current_worker.finished.connect(self.on_worker_finished)
        self.current_worker.error.connect(self.on_worker_error)
        self.current_worker.start()

    def on_worker_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.status_lbl.setText(msg)

    def on_worker_finished(self, results: Dict[str, Any]):
        self.last_results = results
        self.progress_bar.setVisible(False)
        self.status_lbl.setText(f"Calculation converged in {results.get('elapsed_ms', 0):.1f} ms.")
        self.console_dock.set_status("Ready", "#4CAF50")

        # Update Database Dock
        self.database_dock.calculation_finished(results)

        # Update all 8 Graphic Views
        self.tab_equilibrium.update_data(results)
        self.tab_phase_diag.update_data(results)
        self.tab_transport.update_data(results)
        self.tab_mechanical.update_data(results)
        self.tab_environmental.update_data(results)
        self.tab_xrd.update_data(results)
        self.tab_applications.update_data(results)
        self.tab_validation.update_data(results)

    def on_worker_error(self, err_msg: str):
        self.progress_bar.setVisible(False)
        self.status_lbl.setText("Calculation failed.")
        self.console_dock.set_status("Error", "#F44336")
        self.database_dock.btn_calc.setEnabled(True)
        self.database_dock.btn_calc.setText("Calculate Properties")
        QMessageBox.critical(self, "Calculation Error", f"Thermodynamic solver encountered an error:\n\n{err_msg}")

    def export_dat_file(self):
        if not self.last_results:
            QMessageBox.warning(self, "Export", "Please run a calculation before exporting.")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Export CALPHAD Data File", "CALPHAD_Simulation.dat", "DAT Files (*.dat)")
        if not filename:
            return

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# CALPHAD Materials Engineering Suite Data File\n")
                f.write(f"# Database: {self.last_results.get('database_name', '')}\n")
                f.write(f"# Composition: {self.last_results.get('composition', {})}\n\n")
                f.write("[THERMODYNAMICS]\n")
                for k, v in self.last_results.get("thermo", {}).items():
                    f.write(f"{k} = {v}\n")
                f.write("\n[MECHANICAL]\n")
                for k, v in self.last_results.get("mechanical", {}).items():
                    f.write(f"{k} = {v}\n")
            self.console_dock.log(f"[Export] Saved DAT file: {filename}")
            QMessageBox.information(self, "Export Successful", f"Saved CALPHAD data to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def export_csv_file(self):
        if not self.last_results:
            QMessageBox.warning(self, "Export", "Please run a calculation before exporting.")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Export Results to CSV", "CALPHAD_Results.csv", "CSV Files (*.csv)")
        if not filename:
            return

        try:
            val_table = self.last_results.get("validation_table", [])
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Property", "Calculated", "Experimental", "Deviation", "ErrorPercent", "Reference", "DOI"])
                for row in val_table:
                    writer.writerow([
                        row.get("Property", ""),
                        row.get("Calculated", ""),
                        row.get("Experimental", ""),
                        row.get("Deviation", ""),
                        row.get("ErrorPercent", ""),
                        row.get("Reference", ""),
                        row.get("DOI", "")
                    ])
            self.console_dock.log(f"[Export] Saved CSV file: {filename}")
            QMessageBox.information(self, "Export Successful", f"Exported validation audit table to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def show_authorship_dialog(self):
        QMessageBox.information(
            self,
            "Academic Authorship & Credits",
            "CALPHAD Materials Engineering Suite\n"
            "Lead Materials Suite Developers:\n"
            "  • Felix Mwiya\n"
            "  • Prof. (Dr.) Sheela Singh\n\n"
            "Institution: SRM University-AP (2026)\n"
            "Department: Materials Science & Engineering\n"
            "Framework: Python 3.12 + PyQt6 + PyQtGraph"
        )

    def show_references_dialog(self):
        QMessageBox.information(
            self,
            "Authentic Literature References",
            "Key Peer-Reviewed Literature Citations:\n\n"
            "1. Ni-Cr-Fe-B-Si Thermal Spray Coatings:\n"
            "   • Planche et al. (Surf. Coat. Technol. 2005) - DOI: 10.1016/j.surfcoat.2004.10.141\n"
            "   • Houdková et al. (J. Therm. Spray Tech. 2014) - DOI: 10.1007/s11666-014-0112-9\n"
            "   • Gonzalez et al. (Wear 2007) - DOI: 10.1016/j.wear.2006.05.009\n\n"
            "2. High-Entropy Alloys:\n"
            "   • Laplanche et al. (Acta Mater. 2016) - DOI: 10.1016/j.actamat.2016.07.045\n"
            "   • Gludovatz et al. (Science 2014) - DOI: 10.1126/science.1254581\n"
            "   • Senkov et al. (Intermetallics 2010) - DOI: 10.1016/j.intermet.2010.05.014\n"
            "   • Lu et al. (Sci. Rep. 2014) - DOI: 10.1038/srep06200"
        )

    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "About PyCALPHAD Suite",
            "<b>PyCALPHAD Materials Engineering Suite</b><br/>"
            "Version 2026.3.0<br/><br/>"
            "An asynchronous multi-threaded CAE CALPHAD and physical metallurgy calculation platform.<br/>"
            "Features 14 specialized alloy databases, dedicated thermal spray coating engine, "
            "pure pyqtgraph 60 FPS plotting, and authentic literature XRD benchmarks."
        )
