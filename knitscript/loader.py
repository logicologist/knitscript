import os
from functools import partial
from typing import Mapping, Optional, TextIO

from antlr4 import CommonTokenStream, FileStream, InputStream

from knitscript.astgen import build_ast
from knitscript.astnodes import Call, Document, NativeFunction, NaturalLit, \
    Node, Pattern, PatternDef, Using
from knitscript.exporter import export_text
from knitscript.interpreter import do_call, enclose, fill, reflect, \
    prepare_pattern
from knitscript.parser.KnitScriptLexer import KnitScriptLexer
from knitscript.parser.KnitScriptParser import KnitScriptParser
from knitscript.verifier import verify_pattern


class LoadError(Exception):
    """An error that occurred while loading a document."""
    pass


def load_file(filename: str, out: Optional[TextIO] = None) \
        -> Mapping[str, Node]:
    """
    Loads the environment from a document.

    :param filename: the filename of the document
    :param out:
        the stream to use for any output the document produces, or None if
        output should be suppressed
    :return: the document's environment
    """
    return _load(FileStream(filename),
                 _get_default_env(out),
                 os.path.dirname(filename))


def _load(in_: InputStream, env: Mapping[str, Node], base_dir: str) \
        -> Mapping[str, Node]:
    lexer = KnitScriptLexer(in_)
    parser = KnitScriptParser(CommonTokenStream(lexer))
    document = build_ast(parser.document())
    assert isinstance(document, Document)
    env = dict(env)
    for stmt in document.stmts:
        if isinstance(stmt, Using):
            used_env = load_file(os.path.join(base_dir, stmt.module + ".ks"))
            for name in stmt.names:
                env[name] = used_env[name]
        elif isinstance(stmt, PatternDef):
            env[stmt.name] = enclose(stmt.pattern, env)
        elif isinstance(stmt, Call):
            result = do_call(stmt, env)
            assert result is None
        else:
            raise LoadError(f"unsupported statement {type(stmt).__name__}")
    return env


def _show(out: Optional[TextIO],
          pattern: Node,
          description: Optional[Node] = None) -> None:
    if out is None:
        return
    assert isinstance(pattern, Pattern)
    pattern = prepare_pattern(pattern)
    if description:
        out.write(f"\n\033[1m{description}\033[0m\n\n")
    out.write(f"{export_text(pattern)}\n\n")
    for error in verify_pattern(pattern):
        out.write(f"error: {error}\n")


def _note(out: Optional[TextIO], message: Node) -> None:
    if out is not None:
        out.write(f"{message}\n")


def _fill(pattern: Node, width: Node, height: Node) -> Node:
    assert isinstance(pattern, Pattern)
    assert isinstance(width, NaturalLit)
    assert isinstance(height, NaturalLit)
    return fill(pattern, width.value, height.value)


def _get_default_env(out: Optional[TextIO]) -> Mapping[str, Node]:
    # noinspection PyTypeChecker
    return {
        "reflect": NativeFunction(reflect),
        "show": NativeFunction(partial(_show, out)),
        "note": NativeFunction(partial(_note, out)),
        "fill": NativeFunction(_fill),
        **_load(FileStream(os.path.join(os.path.dirname(__file__),
                                        "library",
                                        "builtins.ks")),
                {},
                os.path.join(os.path.dirname(__file__), "library"))
    }
