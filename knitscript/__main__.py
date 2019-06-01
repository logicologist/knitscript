from antlr4 import CommonTokenStream, StdinStream

from knitscript.astgen import build_ast
from knitscript.astnodes import Document, PatternDef, pretty_print
from knitscript.interpreter import compile_text, flatten, substitute, \
    infer_sides
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
    global_env = {}
    for def_ in document.patterns:
        assert isinstance(def_, PatternDef)
        global_env[def_.name] = def_.pattern

    processed = flatten(infer_sides(substitute(global_env["main"],
                                               global_env)))
    pretty_print(processed)
    print()
    print(compile_text(processed))


if __name__ == "__main__":
    main()
