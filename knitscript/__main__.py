from antlr4 import CommonTokenStream, StdinStream

from knitscript.astgen import build_ast
from knitscript.astnodes import Document, PatternDef, PatternExpr
from knitscript.interpreter import compile_text
from knitscript.parser.KnitScriptLexer import KnitScriptLexer
from knitscript.parser.KnitScriptParser import KnitScriptParser


def main() -> None:
    """
    Prints the knitting instructions for a KnitScript pattern which is read
    from stdin.
    """
    lexer = KnitScriptLexer(StdinStream())
    parser = KnitScriptParser(CommonTokenStream(lexer))
    document = build_ast(parser.document())

    assert isinstance(document, Document)
    for pattern in document.patterns:
        assert isinstance(pattern, PatternDef)
        assert isinstance(pattern.pattern, PatternExpr)
        print(pattern.name, pattern.pattern.params)
        print(compile_text(pattern.pattern))
        print()


if __name__ == "__main__":
    main()
