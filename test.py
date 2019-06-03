import sys
from typing import Optional
from enum import Enum

from antlr4 import CommonTokenStream, FileStream, StdinStream

from knitscript.astgen import build_ast
from knitscript.astnodes import Document, PatternDef, PatternExpr, \
    pretty_print
from knitscript.interpreter import alternate_sides, compile_text, flatten, \
    infer_counts, infer_sides, substitute
from knitscript.verifiers import verify_pattern
from knitscript.parser.KnitScriptLexer import KnitScriptLexer
from knitscript.parser.KnitScriptParser import KnitScriptParser

def process_pattern(filename: str) -> PatternExpr:
    """
    Prints the knitting instructions for a KnitScript pattern which is read
    from the filename or stdin if no filename is provided.

    :param filename: the filename of the KnitScript pattern to run
    """
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
    return pattern

    print(compile_text(pattern))
    assert isinstance(pattern, PatternExpr)
    print(*verify_pattern(pattern), sep="\n")

def check_output(filename: str, expected: str) -> bool:
	pattern = process_pattern(filename)
	actual = compile_text(pattern)
	return actual == expected

def verify_error(filename: str) -> bool:
	pattern = process_pattern(filename)
	verification = verify_pattern(pattern)
	errors = []
	for error in verification:
		errors.append(error.message)
	# We can also do more checking of the specific errors... not sure what the right format is, though
	return len(errors) >= 1



assert(verify_error("test/too-many-stitches.ks"))
assert(verify_error("test/too-few-stitches.ks"))
assert(check_output("test/just-right.ks", "CO 12.\nK 12.\n*BO; rep from * to end."))

print("All tests passed")





