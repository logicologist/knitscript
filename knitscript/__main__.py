from antlr4 import CommonTokenStream, StdinStream

from knitscript.astgen import build_ast
from knitscript.astnodes import Document, PatternDef, pretty_print
from knitscript.interpreter import compile_text, flatten, infer_counts, \
    infer_sides, substitute
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

    document = substitute(global_env["main"], global_env)
    document = infer_sides(document)
    document = infer_counts(document)
    pretty_print(document)
    print()
    document = flatten(document)
    pretty_print(document)
    print()
    print(compile_text(document))


if __name__ == "__main__":
    main()
