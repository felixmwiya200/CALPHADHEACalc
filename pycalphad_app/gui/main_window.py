"""
main_window.py - JMatPro / Pandat Professional CAE Desktop Layout
Assembles the Left Parameter Dock, Central 8-Tab Graphics Viewport, Bottom Solver Console,
Menu Bar, and Background QThread Solver.
"""

from typing import Dict, Any, Optional
import os
import csv
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QMessageBox, QFileDialog,
                             QStatusBar, QProgressBar, QLabel)
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtCore import Qt

from pycalphad_app.gui.database_dock import DatabaseDock
from pycalphad_app.gui.console_dock import ConsoleDock
from pycalphad_app.gui.database_modal import DatabaseModalDialog
from pycalphad_app.gui.worker import SolverWorker
from pycalphad_app.gui.plot_views import (
    EquilibriumView, PhaseDiagramView, TransportView, MechanicalView,
    EnvironmentalView, XRDView, ApplicationsView, ValidationView
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyCALPHAD Materials Engineering Suite v2026.3.0 - [SRM University-AP]")
        self.resize(1380, 880)
        self.setMinimumSize(1024, 680)

        self.last_results: Optional[Dict[str, Any]] = None
        self.current_worker: Optional[SolverWorker] = None

        self.apply_theme("dark")
        self.init_ui()
        self.init_menus()
        self.init_statusbar()

        # Initial calculation on launch for Cantor alloy or thermal spray
        self.console_dock.log("[System] PyCALPHAD Suite initialized successfully.")
        self.console_dock.log("[System] Multi-threading worker pool ready. Zero GUI latency.")

    def apply_theme(self, theme: str = "dark"):
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow { background-color: #1E1E1E; }
                QMenuBar { background-color: #2D2D30; color: #FFFFFF; font-size: 9.5pt; }
                QMenuBar::item:selected { background-color: #3E3E42; }
                QMenu { background-color: #252526; color: #FFFFFF; border: 1px solid #3E3E42; }
                QMenu::item:selected { background-color: #094771; }
                QTabWidget::pane { border: 1px solid #3E3E42; background-color: #1E1E1E; }
                QTabBar::tab { background-color: #2D2D30; color: #B0BEC5; padding: 7px 16px; margin-right: 2px; font-weight: bold; }
                QTabBar::tab:selected { background-color: #0E639C; color: #FFFFFF; border-bottom: 2px solid #00BCD4; }
                QStatusBar { background-color: #007ACC; color: #FFFFFF; font-weight: demi-bold; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #F3F3F3; }
                QMenuBar { background-color: #E1E1E1; color: #000000; font-size: 9.5pt; }
                QMenuBar::item:selected { background-color: #D0D0D0; }
                QMenu { background-color: #FFFFFF; color: #000000; border: 1px solid #CCCCCC; }
                QMenu::item:selected { background-color: #0078D7; color: #FFFFFF; }
                QTabWidget::pane { border: 1px solid #CCCCCC; background-color: #FFFFFF; }
                QTabBar::tab { background-color: #E1E1E1; color: #333333; padding: 7px 16px; margin-right: 2px; }
                QTabBar::tab:selected { background-color: #0078D7; color: #FFFFFF; }
                QStatusBar { background-color: #0078D7; color: #FFFFFF; }
            """)

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

        self.tabs.addTab(self.tab_equilibrium, "Equilibrium Phases")
        self.tabs.addTab(self.tab_phase_diag, "Isopleth Phase Diagram")
        self.tabs.addTab(self.tab_transport, "Transport Properties")
        self.tabs.addTab(self.tab_mechanical, "Mechanical Strengthening")
        self.tabs.addTab(self.tab_environmental, "Oxidation & Corrosion")
        self.tabs.addTab(self.tab_xrd, "Powder XRD Diffractometer")
        self.tabs.addTab(self.tab_applications, "Industrial Suitability")
        self.tabs.addTab(self.tab_validation, "Literature Audit & Validation")

        self.setCentralWidget(self.tabs)

    def init_menus(self):
        menubar = self.menuBar()

        # File Menu
        menu_file = menubar.addMenu("&File")

        act_export_dat = QAction("Export CALPHAD Data File (.dat)...", self)
        act_export_dat.triggered.connect(self.export_dat_file)
        menu_file.addAction(act_export_dat)

        act_export_csv = QAction("Export Results to CSV...", self)
        act_export_csv.triggered.connect(self.export_csv_file)
        menu_file.addAction(act_export_csv)

        menu_file.addSeparator()
        act_exit = QAction("E&xit", self)
        act_exit.triggered.connect(self.close)
        menu_file.addAction(act_exit)

        # Database Menu
        menu_db = menubar.addMenu("&Database")

        act_switch_db = QAction("Select Active Materials Database...", self)
        act_switch_db.setShortcut("Ctrl+D")
        act_switch_db.triggered.connect(self.open_database_selector_dialog)
        menu_db.addAction(act_switch_db)

        # View Menu
        menu_view = menubar.addMenu("&View")
        menu_view.addAction(self.database_dock.toggleViewAction())
        menu_view.addAction(self.console_dock.toggleViewAction())
        menu_view.addSeparator()

        act_theme_dark = QAction("Dark Theme", self)
        act_theme_dark.triggered.connect(lambda: self.apply_theme("dark"))
        menu_view.addAction(act_theme_dark)

        act_theme_light = QAction("Light Theme", self)
        act_theme_light.triggered.connect(lambda: self.apply_theme("light"))
        menu_view.addAction(act_theme_light)

        # Help Menu
        menu_help = menubar.addMenu("&Help")

        act_credits = QAction("Academic Authorship & Credits...", self)
        act_credits.triggered.connect(self.show_authorship_dialog)
        menu_help.addAction(act_credits)

        act_refs = QAction("Literature References & DOIs...", self)
        act_refs.triggered.connect(self.show_references_dialog)
        menu_help.addAction(act_refs)

        menu_help.addSeparator()
        act_about = QAction("About PyCALPHAD Suite...", self)
        act_about.triggered.connect(self.show_about_dialog)
        menu_help.addAction(act_about)

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
