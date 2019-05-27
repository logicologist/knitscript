from setuptools import find_packages, setup
from setuptools.command.build_py import build_py
import subprocess


class KnitScriptBuildPy(build_py):
    def run(self) -> None:
        subprocess.run(["antlr4",
                        "-o", "knitscript/parser",
                        "-Dlanguage=Python3",
                        "KnitScript.g4"])
        super().run()


setup(
    name="knitscript",
    version="0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["knitscript=knitscript.__main__:main"]
    },
    install_requires=["antlr4-python3-runtime"],
    cmdclass={"build_py": KnitScriptBuildPy}
)
