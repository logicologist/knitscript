import os
import pkgutil
from dataclasses import dataclass
from functools import partial
from typing import Mapping, Optional, Sequence, TextIO, TypeVar, Union, \
    overload

from antlr4 import CommonTokenStream, FileStream, InputStream, \
    RecognitionException, Recognizer, Token
from antlr4.error.ErrorListener import ErrorListener

from knitscript._astgen import build_ast
from knitscript.astnodes import Call, Document, NativeFunction, NaturalLit, \
    Node, Pattern, PatternDef, Source, Using
from knitscript._asttools import Error
from knitscript.exporter import export_text
from knitscript.interpreter import count_rows, do_call, enclose, fill, \
    infer_counts, interpret_pattern, reflect, substitute
# noinspection PyProtectedMember
from knitscript._parser.KnitScriptLexer import KnitScriptLexer
# noinspection PyProtectedMember
from knitscript._parser.KnitScriptParser import KnitScriptParser
from knitscript.verifier import verify_pattern

_T_co = TypeVar("_T_co")


class LoadError(Error):
    """An error that occurred while loading a document."""
    pass


def load_file(filename: str, out: Optional[TextIO] = None) \
        -> Mapping[str, Node]:
    """
    Loads the environment from a document in a file.

    :param filename: the filename of the document
    :param out:
        the stream to use for any output the document produces, or None if
        output should be suppressed
    :return: the document's environment
    """
    return _load(FileStream(os.path.abspath(filename)),
                 out,
                 _get_default_env(out),
                 os.path.dirname(filename))


def load_text(text: str,
              out: Optional[TextIO] = None,
              base_dir: Optional[str] = None) -> Mapping[str, Node]:
    """
    Loads the environment from a document in a string.

    :param text: the contents of the document
    :param out:
        the stream to use for any output the document produces, or None if
        output should be suppressed
    :param base_dir: the base directory to use for importing modules
    :return: the document's environment
    """
    return _load(InputStream(text), out, _get_default_env(out), base_dir)


def _load(in_: InputStream,
          out: Optional[TextIO],
          env: Mapping[str, Node],
          base_dir: Optional[str]) -> Mapping[str, Node]:
    errors = _ErrorCollector()
    lexer = KnitScriptLexer(in_)
    lexer.removeErrorListeners()
    lexer.addErrorListener(errors)
    parser = KnitScriptParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(errors)
    document = build_ast(parser.document())
    for error in errors:
        out.write(f"error: {error.message}\n    " +
                  f"on line {error.source.line}, " +
                  f"column {error.source.column}, " +
                  f"in {error.source.file}\n")

    env = dict(env)
    assert isinstance(document, Document)
    for stmt in document.stmts:
        if isinstance(stmt, Using):
            if base_dir is None:
                raise LoadError("no module base directory", stmt)
            # TODO: We shouldn't pass the output stream to imported modules,
            #  but then syntax errors would be silenced--need a way to show
            #  syntax errors even without an output stream.
            used_env = load_file(os.path.join(base_dir, stmt.module + ".ks"),
                                 out)
            for name in stmt.names:
                env[name] = used_env[name]
        elif isinstance(stmt, PatternDef):
            env[stmt.name] = enclose(stmt.pattern, env)
        elif isinstance(stmt, Call):
            result = do_call(stmt, env)
            assert result is None
        else:
            raise LoadError(f"unsupported statement {type(stmt).__name__}",
                            stmt)
    return env


def _show(out: Optional[TextIO],
          pattern: Node,
          description: Optional[Node] = None) -> None:
    if out is None:
        return
    assert isinstance(pattern, Pattern)
    pattern = interpret_pattern(pattern)
    if description:
        out.write(f"\n\033[1m{description.value}\033[0m\n\n")
    out.write(f"{export_text(pattern)}\n\n")
    for error in verify_pattern(pattern):
        out.write(f"error: {error}\n")


def _note(out: Optional[TextIO], message: Node) -> None:
    if out is not None:
        out.write(f"{message.value}\n")


def _fill(pattern: Node, width: Node, height: Node) -> Node:
    assert isinstance(pattern, Pattern)
    assert isinstance(width, NaturalLit)
    assert isinstance(height, NaturalLit)
    return fill(pattern, width.value, height.value)


def _width(pattern: Node) -> Node:
    assert isinstance(pattern, Pattern)
    pattern = infer_counts(substitute(pattern, pattern.env))
    assert isinstance(pattern, Pattern)
    return NaturalLit.of(pattern.consumes)


def _height(pattern: Node) -> Node:
    assert isinstance(pattern, Pattern)
    pattern = substitute(pattern, pattern.env)
    return NaturalLit.of(count_rows(pattern))


def _get_default_env(out: Optional[TextIO]) -> Mapping[str, Node]:
    # noinspection PyTypeChecker
    env = {
        "reflect": NativeFunction.of(reflect),
        "show": NativeFunction.of(partial(_show, out)),
        "note": NativeFunction.of(partial(_note, out)),
        "fill": NativeFunction.of(_fill),
        "width": NativeFunction.of(_width),
        "height": NativeFunction.of(_height)
    }
    builtins = InputStream(pkgutil
                           .get_data("knitscript.library", "builtins.ks")
                           .decode("UTF-8"))
    builtins.name = "builtins"
    return {**env, **_load(builtins, None, env, None)}


@dataclass(frozen=True)
class _SyntaxError:
    source: Source
    message: str


class _ErrorCollector(ErrorListener, Sequence):
    """Collects errors that occur during parsing."""

    def __init__(self) -> None:
        self._errors = []

    def syntaxError(self,
                    recognizer: Recognizer,
                    token: Token,
                    line: int,
                    column: int,
                    message: str,
                    ex: RecognitionException) -> None:
        stream = (token.source[1]
                  if token is not None
                  else recognizer.inputStream)
        file = (stream.fileName
                if isinstance(stream, FileStream)
                else stream.name)
        self._errors.append(_SyntaxError(Source(line, column, file), message))

    @overload
    def __getitem__(self, i: int) -> _T_co:
        ...

    @overload
    def __getitem__(self, s: slice) -> Sequence[_T_co]:
        ...

    def __getitem__(self, i: Union[int, slice]) -> _T_co:
        if isinstance(i, int):
            return self._errors[i]
        elif isinstance(i, slice):
            return self._errors[i.start:i.stop:i.step]
        else:
            raise TypeError("item is not an int or slice")

    def __len__(self) -> int:
        return len(self._errors)
