import os
import platform
from distutils.dir_util import copy_tree, remove_tree
from distutils.spawn import find_executable, spawn
from typing import Optional, Tuple

from setuptools import find_packages, setup, Command
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


class KnitScriptPyInstaller(Command):
    user_options: Tuple[str, Optional[str], str] = []

    def initialize_options(self) -> None:
        pass

    def finalize_options(self) -> None:
        pass

    # noinspection PyMethodMayBeStatic
    def run(self) -> None:
        spawn(["pyinstaller", "KnitScript.spec"])
        spawn(["pyinstaller", "KnitScriptEditor.spec"])
        copy_tree("dist/KnitScriptEditor", "dist/KnitScript")
        remove_tree("dist/KnitScriptEditor")
        os.remove("dist/KnitScript/knitscript.exe.manifest")
        os.remove("dist/KnitScript/KnitScriptEditor.exe.manifest")


setup_requires = []
if platform.system() == "Windows":
    setup_requires.append("pyinstaller")
elif platform.system() == "Darwin":
    setup_requires.append("py2app")

setup(
    name="knitscript",
    version="0.1",
    packages=find_packages(),
    cmdclass={
        "build_py": KnitScriptBuildPy,
        "pyinstaller": KnitScriptPyInstaller
    },
    entry_points={
        "console_scripts": ["knitscript=knitscript.__main__:main"],
        "gui_scripts": ["knitscript-editor=knitscript.editor.__main__:main"]
    },
    install_requires=["antlr4-python3-runtime"],
    setup_requires=setup_requires,
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
