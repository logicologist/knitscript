from typing import Type

from knitscript.astnodes import Pattern
from knitscript.export import export_text
from knitscript.interpreter import InterpretError, prepare_pattern
from knitscript.loader import load
from knitscript.verifiers import verify_pattern


def process_pattern(filename: str) -> Pattern:
    env = load(filename)
    pattern = env["main"]
    assert isinstance(pattern, Pattern)
    return prepare_pattern(pattern)


def check_output(filename: str, expected: str) -> bool:
    pattern = process_pattern(filename)
    actual = export_text(pattern)
    return actual == expected


def expect_except(filename: str, exception_type: Type[Exception]) -> bool:
    # noinspection PyBroadException
    try:
        process_pattern(filename)
    except exception_type:
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
     "Patterns shouldn't be able to reference variables outside their " +
     "environment")
test(lambda: check_output(
    "test/tile.ks",
    "CO 6.\n**\n[K, P] 3.\n[P, K] 3.\nrep from ** 3 times.\nBO 6."
), "Should allow n-by-m tiling of patterns")
test(lambda: check_output("test/pass-called-pattern.ks",
                          "CO 3.\n" +
                          "**\n" +
                          "K, P, K.\n" +
                          "rep from ** 5 times.\n" +
                          "**\n" +
                          "P, K, P.\n" +
                          "rep from ** 3 times.\n" +
                          "BO 3."),
     "Patterns can be passed with or without being called with arguments")
test(lambda: expect_except("test/too-few-arguments.ks", InterpretError),
     "Should catch patterns called with too few arguments")
test(lambda: expect_except("test/too-many-arguments.ks", InterpretError),
     "Should catch patterns called with too many arguments")
test(lambda: expect_except("test/called-twice.ks", InterpretError),
     "Should catch patterns that are called twice")
