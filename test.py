from knitscript.astnodes import PatternExpr
from knitscript.export import export_text
from knitscript.interpreter import prepare_pattern
from knitscript.loader import load
from knitscript.verifiers import verify_pattern


def process_pattern(filename: str) -> PatternExpr:
    env = load(filename)
    pattern = env["main"]
    assert isinstance(pattern, PatternExpr)
    return prepare_pattern(pattern)


def check_output(filename: str, expected: str) -> bool:
    pattern = process_pattern(filename)
    actual = export_text(pattern)
    return actual == expected


def expect_except(filename: str, exceptionType: Exception) -> bool:
    try:
        pattern = process_pattern(filename)
    except exceptionType as e:
        return True


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
test(lambda: expect_except("test/patterns-lexical-scoping.ks", KeyError),
     "Patterns shouldn't be able to reference variables outside their environment")
test(lambda: check_output(
    "test/tile.ks",
    "CO 6.\n**\n[K, P] 3.\n[P, K] 3.\nrep from ** 3 times.\nBO 6."
), "Should allow n-by-m tiling of patterns")

