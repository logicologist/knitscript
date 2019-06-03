from antlr4 import CommonTokenStream, FileStream

from knitscript.astgen import build_ast
from knitscript.astnodes import Document, PatternDef, PatternExpr
from knitscript.export import export_text
from knitscript.interpreter import alternate_sides, flatten, infer_counts, \
    infer_sides, substitute
from knitscript.parser.KnitScriptLexer import KnitScriptLexer
from knitscript.parser.KnitScriptParser import KnitScriptParser
from knitscript.verifiers import verify_pattern


def process_pattern(filename: str) -> PatternExpr:
    lexer = KnitScriptLexer(
        FileStream(filename)
    )
    parser = KnitScriptParser(CommonTokenStream(lexer))
    document = build_ast(parser.document())

    assert isinstance(document, Document)
    env = {}
    for def_ in document.patterns:
        assert isinstance(def_, PatternDef)
        env[def_.name] = def_.pattern

    pattern = infer_counts(infer_sides(substitute(env["main"], env)))
    pattern = flatten(pattern)
    pattern = alternate_sides(pattern)
    assert isinstance(pattern, PatternExpr)
    return pattern


def check_output(filename: str, expected: str) -> bool:
    pattern = process_pattern(filename)
    actual = export_text(pattern)
    return actual == expected


def verify_error(filename: str) -> bool:
    pattern = process_pattern(filename)
    verification = verify_pattern(pattern)
    errors = []
    for error in verification:
        errors.append(error.message)
    # We can also do more checking of the specific errors... not sure what
    # the right format is, though
    return len(errors) >= 1


def test(callback, desc: str):
    try:
        assert callback()
    except AssertionError:
        print("TEST FAILED: " + desc)
    else:
        print("√")


test(lambda: verify_error("test/too-many-stitches.ks"),
     "Should catch expedted stitches greater than available")
test(lambda: verify_error("test/too-few-stitches.ks"),
     "Should catch expected stitches smaller than available")
test(lambda: check_output("test/just-right.ks",
                          "CO 12.\nK 12.\n*BO; rep from * to end."),
     "Should compile simple pattern")
test(lambda: verify_error("test/double-expanding-repeat-2.ks"),
     "Should catch bad double expanding repeat")
# technically legit even though nobody writes patterns this way
test(lambda: not verify_error("test/double-expanding-repeat.ks"),
     "Should allow okay double expanding repeat")
