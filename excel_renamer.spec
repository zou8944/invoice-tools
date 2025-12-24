# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['excel_renamer.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'openpyxl',
        'openpyxl.xml',
        'openpyxl.styles',
        'openpyxl.chart',
        'openpyxl.drawing',
        'openpyxl.worksheet',
        'openpyxl.workbook',
        'openpyxl.cell',
        'openpyxl.utils',
        'et_xmlfile',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Excel Sheet Renamer',
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
)

# macOS only
app = BUNDLE(
    exe,
    name='Excel Sheet Renamer.app',
    icon=None,
    bundle_identifier='com.excelrenamer.app',
)
