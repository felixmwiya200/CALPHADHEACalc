# -*- coding: utf-8 -*-
"""
styles.py - Authentic Academic & Industrial Engineering QSS Theme
Transforms the PyQt6 desktop user interface from a generic 'AI-generated' appearance
into an authentic, human-designed, publication-grade materials engineering workspace.
Adheres to design patterns from OriginLab 2024, Thermo-Calc Graphical Mode, and Qt Fusion.
"""

def get_application_stylesheet() -> str:
    """
    Returns the cohesive light-neutral enterprise stylesheet for the suite.
    """
    return """
    /* Global Application Defaults */
    QWidget {
        background-color: #F8FAFC;
        color: #0F172A;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
        font-size: 9pt;
        selection-background-color: #2563EB;
        selection-color: #FFFFFF;
    }

    QMainWindow {
        background-color: #F1F5F9;
    }

    /* Professional QMenuBar & QMenu */
    QMenuBar {
        background-color: #FFFFFF;
        color: #1E293B;
        border-bottom: 1px solid #E2E8F0;
        padding: 2px 6px;
    }
    QMenuBar::item {
        background: transparent;
        padding: 4px 10px;
        border-radius: 4px;
    }
    QMenuBar::item:selected {
        background-color: #F1F5F9;
        color: #0F172A;
    }
    QMenu {
        background-color: #FFFFFF;
        color: #0F172A;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #EFF6FF;
        color: #1D4ED8;
    }
    QMenu::separator {
        height: 1px;
        background-color: #E2E8F0;
        margin: 4px 6px;
    }

    /* QToolBar */
    QToolBar {
        background-color: #FFFFFF;
        border-bottom: 1px solid #E2E8F0;
        padding: 4px 8px;
        spacing: 6px;
    }

    /* QDockWidget */
    QDockWidget {
        font-weight: 600;
        color: #0F172A;
    }
    QDockWidget::title {
        background-color: #F1F5F9;
        color: #0F172A;
        padding: 6px 10px;
        border-bottom: 1px solid #E2E8F0;
        font-weight: bold;
    }

    /* QScrollArea */
    QScrollArea {
        border: none;
        background-color: transparent;
    }

    /* Custom Modern Slim Scrollbars */
    QScrollBar:vertical {
        background: #F1F5F9;
        width: 10px;
        margin: 0;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical {
        background: #CBD5E1;
        min-height: 25px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical:hover {
        background: #94A3B8;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: transparent;
    }

    QScrollBar:horizontal {
        background: #F1F5F9;
        height: 10px;
        margin: 0;
        border-radius: 5px;
    }
    QScrollBar::handle:horizontal {
        background: #CBD5E1;
        min-width: 25px;
        border-radius: 5px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #94A3B8;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }

    /* Modern Card GroupBoxes */
    QGroupBox {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        margin-top: 14px;
        padding-top: 14px;
        font-weight: 600;
        color: #1E293B;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        top: 2px;
        padding: 0 4px;
        background-color: #FFFFFF;
        color: #1D4ED8;
    }

    /* Buttons */
    QPushButton {
        background-color: #FFFFFF;
        color: #1E293B;
        border: 1px solid #CBD5E1;
        border-radius: 4px;
        padding: 5px 12px;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #F8FAFC;
        border-color: #94A3B8;
        color: #0F172A;
    }
    QPushButton:pressed {
        background-color: #E2E8F0;
    }
    QPushButton:disabled {
        background-color: #F1F5F9;
        color: #94A3B8;
        border-color: #E2E8F0;
    }
    QPushButton#primaryBtn {
        background-color: #1D4ED8;
        color: #FFFFFF;
        border: 1px solid #1E40AF;
        font-weight: 600;
        padding: 6px 16px;
    }
    QPushButton#primaryBtn:hover {
        background-color: #2563EB;
        border-color: #1D4ED8;
    }
    QPushButton#primaryBtn:pressed {
        background-color: #1E40AF;
    }

    /* QDialog & Modals */
    QDialog {
        background-color: #F8FAFC;
        color: #0F172A;
    }

    /* QListWidget */
    QListWidget {
        background-color: #FFFFFF;
        color: #1E293B;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 4px;
        outline: none;
    }
    QListWidget::item {
        padding: 8px 12px;
        border-radius: 4px;
        margin-bottom: 2px;
        font-size: 9.5pt;
    }
    QListWidget::item:hover {
        background-color: #F1F5F9;
        color: #0F172A;
    }
    QListWidget::item:selected {
        background-color: #EFF6FF;
        color: #1D4ED8;
        font-weight: 600;
        border-left: 3px solid #1D4ED8;
    }

    /* QTextEdit & QPlainTextEdit */
    QTextEdit, QPlainTextEdit {
        background-color: #FFFFFF;
        color: #334155;
        border: 1px solid #CBD5E1;
        border-radius: 4px;
        padding: 8px;
        font-size: 9.5pt;
    }

    /* QSplitter */
    QSplitter::handle {
        background-color: #E2E8F0;
        width: 3px;
        height: 3px;
    }
    QSplitter::handle:hover {
        background-color: #94A3B8;
    }

    /* QComboBox & Inputs */
    QComboBox, QLineEdit, QDoubleSpinBox, QSpinBox {
        background-color: #FFFFFF;
        color: #0F172A;
        border: 1px solid #CBD5E1;
        border-radius: 4px;
        padding: 5px 8px;
    }
    QComboBox:hover, QLineEdit:hover, QDoubleSpinBox:hover {
        border-color: #94A3B8;
    }
    QComboBox:focus, QLineEdit:focus, QDoubleSpinBox:focus {
        border-color: #2563EB;
    }
    QComboBox::drop-down {
        border: none;
        width: 20px;
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #0F172A;
        border: 1px solid #CBD5E1;
        selection-background-color: #EFF6FF;
        selection-color: #1D4ED8;
        padding: 4px;
    }

    /* Radio Buttons & CheckBoxes */
    QRadioButton, QCheckBox {
        color: #1E293B;
        font-size: 9pt;
        spacing: 6px;
    }
    QRadioButton::indicator, QCheckBox::indicator {
        width: 15px;
        height: 15px;
    }

    /* QTabWidget & TabBar */
    QTabWidget::pane {
        border: 1px solid #E2E8F0;
        background-color: #FFFFFF;
        border-radius: 4px;
    }
    QTabBar::tab {
        background-color: #F1F5F9;
        color: #475569;
        padding: 7px 16px;
        border: 1px solid #E2E8F0;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
        font-weight: 500;
    }
    QTabBar::tab:selected {
        background-color: #FFFFFF;
        color: #1D4ED8;
        font-weight: bold;
        border-bottom: 2px solid #2563EB;
    }
    QTabBar::tab:hover:!selected {
        background-color: #E2E8F0;
        color: #0F172A;
    }

    /* QTableWidget & QHeaderView */
    QTableWidget {
        background-color: #FFFFFF;
        color: #0F172A;
        gridline-color: #E2E8F0;
        border: 1px solid #CBD5E1;
        border-radius: 4px;
        alternate-background-color: #F8FAFC;
    }
    QHeaderView::section {
        background-color: #F1F5F9;
        color: #1E293B;
        font-weight: bold;
        padding: 6px;
        border: 1px solid #E2E8F0;
    }

    /* QStatusBar */
    QStatusBar {
        background-color: #FFFFFF;
        color: #475569;
        border-top: 1px solid #E2E8F0;
    }
    """
