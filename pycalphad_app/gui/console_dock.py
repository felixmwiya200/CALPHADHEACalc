"""
console_dock.py - CAE Solver Console & Live Terminal Dock
Displays thermodynamic solver residuals, convergence steps, and process execution logs.
"""

from PyQt6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QPlainTextEdit, QPushButton, QLineEdit, QLabel)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QDateTime


class ConsoleDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("CAE Solver Terminal & Execution Log", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(4)

        # Toolbar
        tb_layout = QHBoxLayout()
        self.status_lbl = QLabel("Ready")
        self.status_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self.status_lbl.setStyleSheet("color: #4CAF50;")
        tb_layout.addWidget(self.status_lbl)
        tb_layout.addStretch()

        self.btn_clear = QPushButton("Clear Console")
        self.btn_clear.setFont(QFont("Segoe UI", 9))
        self.btn_clear.clicked.connect(self.clear_log)
        tb_layout.addWidget(self.btn_clear)
        layout.addLayout(tb_layout)

        # Log Output Box
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(2000)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet(
            "background-color: #181818; color: #D4D4D4; border: 1px solid #333333; "
            "padding: 4px; selection-background-color: #264F78;"
        )
        layout.addWidget(self.log_text)

        # Command input line
        cmd_layout = QHBoxLayout()
        cmd_prompt = QLabel("CALPHAD>")
        cmd_prompt.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        cmd_prompt.setStyleSheet("color: #569CD6;")
        cmd_layout.addWidget(cmd_prompt)

        self.cmd_input = QLineEdit()
        self.cmd_input.setFont(QFont("Consolas", 10))

        self.cmd_input.setPlaceholderText("Enter interactive command (e.g. 'status', 'clear', 'version')...")
        self.cmd_input.setStyleSheet(
            "background-color: #252526; color: #FFFFFF; border: 1px solid #3E3E42; padding: 3px;"
        )
        self.cmd_input.returnPressed.connect(self.execute_command)
        cmd_layout.addWidget(self.cmd_input)
        layout.addLayout(cmd_layout)

        self.setWidget(container)

    def log(self, message: str):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss.zzz")
        self.log_text.appendPlainText(f"[{timestamp}] {message}")

    def clear_log(self):
        self.log_text.clear()
        self.log("Console cleared.")

    def set_status(self, text: str, color: str = "#4CAF50"):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(f"color: {color};")

    def execute_command(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        self.cmd_input.clear()
        self.log(f"> {cmd}")
        cmd_lower = cmd.lower()
        if cmd_lower == "clear":
            self.clear_log()
        elif cmd_lower == "status":
            self.log("[Status] Engine initialized. Multi-threaded solver idle.")
        elif cmd_lower == "version":
            self.log("[Version] PyCALPHAD Suite v2026.3.0 | SRM University-AP")
        elif cmd_lower == "help":
            self.log("[Help] Available commands: status, clear, version, help")
        else:
            self.log(f"[Command] Unknown command: '{cmd}'. Type 'help' for available commands.")
