# -*- mode: python ; coding: utf-8 -*-
import os
import sys

workspace_dir = os.path.abspath('.')
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hidden_imports = [
    'numpy',
    'numpy.core',
    'scipy',
    'scipy.spatial',
    'scipy.spatial.transform',
    'scipy.optimize',
    'pyqtgraph',
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'pycalphad_app',
    'pycalphad_app.database',
    'pycalphad_app.physics',
    'pycalphad_app.gui',
]
hidden_imports += collect_submodules('pycalphad_app')
hidden_imports += collect_submodules('pycalphad')
hidden_imports += collect_submodules('pyqtgraph')

datas = [
    ('pycalphad_app', 'pycalphad_app'),
    ('App/AppIcon.ico', 'App'),
    ('App/published_materials_data.json', 'App'),
    ('App/data/database_of_HEAs.csv', 'App/data'),
]
datas += collect_data_files('pycalphad')

a = Analysis(
    ['pycalphad_app/main.py'],
    pathex=[workspace_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'IPython', 'notebook'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PyCALPHAD_Suite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['App/AppIcon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PyCALPHAD_Suite',
)
