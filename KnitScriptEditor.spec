analysis = Analysis(
    ["knitscript/editor/__main__.py"],
    datas=[("knitscript/library/builtins.ks", "knitscript/library")]
)
pyz = PYZ(
    analysis.pure,
    analysis.zipped_data
)
exe = EXE(
    pyz,
    analysis.scripts,
    name="KnitScriptEditor",
    console=False,
    exclude_binaries=True
)
COLLECT(
    exe,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    name="KnitScriptEditor"
)