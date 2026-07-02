# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Woodsoft Extend
Build:  pyinstaller --clean app.spec
"""

import os
import sys
from PyInstaller.utils.hooks import collect_all

PROJECT_ROOT = os.path.abspath(SPECPATH)
APP_NAME = 'Woodsoft_Extend'

datas = []
binaries = []
hiddenimports = []

# Collect dependencies
for pkg in ['webview', 'ttkbootstrap', 'keyring', 'requests', 'PIL']:
    try:
        _datas, _bins, _hidden = collect_all(pkg)
        datas += _datas
        binaries += _bins
        hiddenimports += _hidden
    except Exception as e:
        print(f"[WARN] Could not collect_all('{pkg}'): {e}")

# Project data files
icon_files = [
    'light.ico', 'logo.png', 'search.png',
    'icon1.png', 'icon2.png', 'icon3.png', 'icon4.png', 'icon6.png',
    'english.png', 'vietnamese.png', 'russian.png',
]
for icon_file in icon_files:
    icon_path = os.path.join(PROJECT_ROOT, icon_file)
    if os.path.exists(icon_path):
        datas.append((icon_path, '.'))

# i18n folder
i18n_dir = os.path.join(PROJECT_ROOT, 'i18n')
if os.path.isdir(i18n_dir):
    datas.append((i18n_dir, 'i18n'))

# Mode directories
for mode_num in [1]:
    mode_name = f'mode{mode_num}'
    mode_dir = os.path.join(PROJECT_ROOT, mode_name)
    if os.path.isdir(mode_dir):
        datas.append((mode_dir, mode_name))

# Common folder
common_dir = os.path.join(PROJECT_ROOT, 'common')
if os.path.isdir(common_dir):
    datas.append((common_dir, 'common'))

hiddenimports += [
    'i18n',
    'i18n.runtime_i18n',
    'common',
    'common.auth_manager',
    'keyring.backends.Windows',
    'mode1',
    'mode1.gui_mode1',
    'mode1.run_webview',
    'tkinter',
    'tkinter.ttk',
    'tkinter.font',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'webview',
    'requests'
]

hiddenimports = list(dict.fromkeys(hiddenimports))

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[PROJECT_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest_cov',
        'sphinx',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT_ROOT, 'light.ico'),
)
