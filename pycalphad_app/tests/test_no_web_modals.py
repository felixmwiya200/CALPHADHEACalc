"""
test_no_web_modals.py - Verify database selector follows native scientific desktop standards
"""

import sys
import pytest
from PyQt6.QtWidgets import QApplication

from pycalphad_app.gui.database_modal import DatabaseModalDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_database_modal_clean_desktop_structure(qapp):
    dlg = DatabaseModalDialog("General Steel")
    assert dlg.windowTitle() == "Materials Database Selector"
    assert dlg.get_selected_database() == "General Steel"
    assert dlg.db_list.count() == 14
    
    # Switch to another database
    dlg.select_database("High Entropy Alloys")
    assert dlg.get_selected_database() == "High Entropy Alloys"
    assert dlg.comp_table.rowCount() > 0
    assert dlg.combo_presets.count() > 0

    dlg.close()
