import os
from typing import Mapping, MutableMapping

from antlr4 import CommonTokenStream, FileStream, InputStream

from knitscript.astgen import build_ast
from knitscript.astnodes import Document, NativeFunction, Node, PatternDef, \
    Using
from knitscript.interpreter import enclose, reflect
from knitscript.parser.KnitScriptLexer import KnitScriptLexer
from knitscript.parser.KnitScriptParser import KnitScriptParser


def load_file(filename: str) -> Mapping[str, Node]:
    """
    Loads the environment from a KnitScript document.

    :param filename: the filename of the KnitScript document
    :return: the environment from that document
    """
    return _load(FileStream(filename),
                 _get_default_env(),
                 os.path.basename(filename))


def _load(stream: InputStream, env: Mapping[str, Node], base_dir: str) \
        -> Mapping[str, Node]:
    lexer = KnitScriptLexer(stream)
    parser = KnitScriptParser(CommonTokenStream(lexer))
    document = build_ast(parser.document())
    assert isinstance(document, Document)
    env = dict(env)

    for using in document.usings:
        assert isinstance(using, Using)
        used_env = load_file(os.path.join(base_dir, using.filename + ".ks"))
        for name in using.pattern_names:
            env[name] = used_env[name]

    for pattern in document.patterns:
        assert isinstance(pattern, PatternDef)
        env[pattern.name] = enclose(pattern.pattern, env)

    return env


def _get_default_env() -> MutableMapping[str, Node]:
    return {
        "reflect": NativeFunction(reflect),
        **_load(FileStream(os.path.join(os.path.dirname(__file__),
                                        "library",
                                        "builtins.ks")),
                {},
                os.path.join(os.path.dirname(__file__), "library"))
    }
