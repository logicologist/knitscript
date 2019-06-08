import os
from typing import Mapping, Optional

from knitscript.astgen import build_ast
from knitscript.astnodes import Document, NativeFunction, Node, PatternDef, \
    Using
from knitscript.interpreter import enclose, reflect
from knitscript.parser.KnitScriptLexer import CommonTokenStream, FileStream, \
    KnitScriptLexer, StdinStream
from knitscript.parser.KnitScriptParser import KnitScriptParser

_DEFAULT_ENV = {"reflect": NativeFunction(reflect)}


def load_file(filename: Optional[str]) -> Mapping[str, Node]:
    """
    Loads the environment from a KnitScript document.

    :param filename: the filename of the KnitScript document
    :return: the environment from that document
    """
    lexer = KnitScriptLexer(
        FileStream(filename) if filename is not None else StdinStream()
    )
    parser = KnitScriptParser(CommonTokenStream(lexer))
    document = build_ast(parser.document())
    assert isinstance(document, Document)
    env = dict(_DEFAULT_ENV)

    for using in document.usings:
        assert isinstance(using, Using)
        used_env = load_file(os.path.join(os.path.dirname(filename),
                                          using.filename + ".ks"))
        for name in using.pattern_names:
            env[name] = used_env[name]

    for pattern in document.patterns:
        assert isinstance(pattern, PatternDef)
        env[pattern.name] = enclose(pattern.pattern, env)

    return env
