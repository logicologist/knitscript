import platform
from distutils.spawn import find_executable, spawn
from setuptools import find_packages, setup
from setuptools.command.build_py import build_py


class KnitScriptBuildPy(build_py):
    def run(self) -> None:
        antlr = find_executable("antlr4") or find_executable("antlr")
        spawn([antlr,
               "-o", "knitscript/parser",
               "-no-listener",
               "-Dlanguage=Python3",
               "KnitScript.g4"])
        super().run()


setup(
    name="knitscript",
    version="0.1",
    packages=find_packages(),
    cmdclass={"build_py": KnitScriptBuildPy},
    entry_points={
        "console_scripts": ["knitscript=knitscript.__main__:main"],
        "gui_scripts": ["knitscript-editor=knitscript.editor.__main__:main"]
    },
    install_requires=["antlr4-python3-runtime"],
    setup_requires=(["py2app"]
                    if platform.system() == "Darwin"
                    else ["pyinstaller"]),
    app=["knitscript/editor/__main__.py"],
    options={
        "py2app": {
            "plist": {"CFBundleName": "KnitScript Editor"},
            "extra_scripts": ["scripts/knitscript.py"]
        }
    },
    package_data={"knitscript.library": ["*.ks"]},
    include_package_data=True
)
