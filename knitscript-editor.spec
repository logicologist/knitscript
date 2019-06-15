a = Analysis(
    ["knitscript/editor/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("knitscript/library/__init__.py", "knitscript/library"),
        ("knitscript/library/builtins.ks", "knitscript/library")
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="knitscript-editor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="knitscript-editor"
)
