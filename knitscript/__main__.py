import sys
from typing import Optional

from antlr4 import CommonTokenStream, FileStream, StdinStream

from knitscript.astgen import build_ast
from knitscript.astnodes import Document, PatternDef, PatternExpr, \
    pretty_print
from knitscript.interpreter import alternate_sides, compile_text, flatten, \
    infer_counts, infer_sides, substitute
from knitscript.verifiers import verify_pattern
from knitscript.parser.KnitScriptLexer import KnitScriptLexer
from knitscript.parser.KnitScriptParser import KnitScriptParser


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

    pattern = infer_counts(infer_sides(substitute(env["main"], env)))
    pretty_print(pattern)
    print()
    pattern = alternate_sides(flatten(pattern))
    pretty_print(pattern)
    print()
    print(compile_text(pattern))
    print()
    assert isinstance(pattern, PatternExpr)
    print(*verify_pattern(pattern), sep="\n")


if __name__ == "__main__":
    main(*sys.argv[1:])
