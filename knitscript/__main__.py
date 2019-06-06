import sys
from typing import Optional

from antlr4 import CommonTokenStream, FileStream, StdinStream

from knitscript.astgen import build_ast
from knitscript.astnodes import Document, PatternDef, PatternExpr, UsingStmt, \
    pretty_print
from knitscript.export import export_text
from knitscript.interpreter import alternate_sides, flatten, infer_counts, \
    infer_sides, substitute, InterpretError
from knitscript.verifiers import verify_pattern, KnitError
from knitscript.parser.KnitScriptLexer import KnitScriptLexer
from knitscript.parser.KnitScriptParser import KnitScriptParser


def _env_from_filename(filename: str):
    try:
        lexer = KnitScriptLexer(
            FileStream(filename) if filename is not None else StdinStream()
        )
    except FileNotFoundError:
        raise InterpretError(filename + " not found")
    parser = KnitScriptParser(CommonTokenStream(lexer))
    document = build_ast(parser.document())

    assert isinstance(document, Document)
    env = {}
    for def_ in document.patterns:
        assert isinstance(def_, PatternDef)
        env[def_.name] = def_.pattern
    for using_ in document.usings:
        assert isinstance(using_, UsingStmt)
        for patternName in using_.patternNames:
            # Check if there's a name conflict with something already in the environment
            if patternName.value in env:
                raise InterpretError("Name conflict: pattern " + patternName.value + " already defined")
        using_env = _env_from_filename(using)
        # TODO Get env from patternName and add to this env


def main(filename: Optional[str] = None) -> None:
    """
    Prints the knitting instructions for a KnitScript pattern which is read
    from the filename or stdin if no filename is provided.

    :param filename: the filename of the KnitScript pattern to run
    """
    lexer = KnitScriptLexer(
        FileStream(filename) if filename is not None else StdinStream()
    )
    parser = KnitScriptParser(CommonTokenStream(lexer))
    document = build_ast(parser.document())

    assert isinstance(document, Document)
    env = {}
    for def_ in document.patterns:
        assert isinstance(def_, PatternDef)
        env[def_.name] = def_.pattern
    for using_ in document.usings:
        assert isinstance(using_, UsingStmt)
        for patternName in using_.patternNames:
            # Check if there's a name conflict with something already in the environment
            if patternName in env:
                raise KnitError("Name conflict: pattern " + patternName.value + "already defined")
            # TODO get pattern and add to env

    list(map(pretty_print, document.usings))
    pattern = infer_counts(infer_sides(substitute(env["main"], env)))
    pretty_print(pattern)
    print()
    pattern = flatten(pattern)
    # pretty_print(pattern)
    # print()
    pattern = alternate_sides(pattern)
    pretty_print(pattern)
    print()
    print(export_text(pattern))
    print()
    assert isinstance(pattern, PatternExpr)
    print(*verify_pattern(pattern), sep="\n")


if __name__ == "__main__":
    main(*sys.argv[1:])
