# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for macOS: onedir CLI, same behavior as the Windows exe.
# The .app wrapper around this build is assembled by macos/build_macos.sh.
# PyInstaller resolves spec paths relative to the spec file, so anchor on SPECPATH.
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
a = Analysis(
    [os.path.join(ROOT, 'ncm_converter.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[(os.path.join(ROOT, 'ncm_converter.ico'), '.')],
    hiddenimports=[],
    hookspath=[],
    runtime_tmpdir=None,
    excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='ncm_converter',
    debug=False,
    strip=False,
    upx=False,
    console=True,
    icon=os.path.join(ROOT, 'macos/ncm_converter.icns'),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='ncm_converter',
)
