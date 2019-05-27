from antlr4 import CommonTokenStream, StdinStream

from knitscript.astgen import build_ast
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
    pattern = build_ast(parser.pattern())
    print(compile_text(pattern))


if __name__ == "__main__":
    main()
