from antlr4 import CommonTokenStream, StdinStream

from knitscript.astgen import build_ast
from knitscript.astnodes import Document, PatternDef, PatternExpr, \
    pretty_print
from knitscript.interpreter import alternate_sides, compile_text, flatten, \
    infer_counts, infer_sides, substitute
from knitscript.verifiers import verify_pattern
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

    pattern = substitute(global_env["main"], global_env)
    pattern = infer_sides(pattern)
    pattern = infer_counts(pattern)
    pretty_print(pattern)
    print()
    pattern = flatten(pattern)
    pattern = alternate_sides(pattern)
    pretty_print(pattern)
    print()
    print(compile_text(pattern))
    print()
    assert isinstance(pattern, PatternExpr)
    print(*verify_pattern(pattern), sep="\n")


if __name__ == "__main__":
    main()
