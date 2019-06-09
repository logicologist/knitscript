from typing import Type

from knitscript.astnodes import Pattern
from knitscript.exporter import export_text
from knitscript.interpreter import InterpretError, prepare_pattern
from knitscript.loader import load_file
from knitscript.verifier import verify_pattern


def process_pattern(filename: str) -> Pattern:
    env = load_file(filename)
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
                          "CO 12. (12 sts)\n" +
                          "K 12. (12 sts)\n" +
                          "*BO; rep from * to end. (0 sts)"),
     "Should compile simple pattern")
test(lambda: verify_error("test/double-expanding-repeat-2.ks"),
     "Should catch bad double expanding repeat")
# technically legit even though nobody writes patterns this way
test(lambda: not verify_error("test/double-expanding-repeat.ks"),
     "Should allow okay double expanding repeat")
test(lambda: expect_except("test/patterns-lexical-scoping.ks", KeyError),
     "Patterns shouldn't be able to reference variables outside their " +
     "environment")
test(lambda: check_output("test/tile.ks",
                          "CO 6. (6 sts)\n" +
                          "**\n" +
                          "[K, P] 3. (6 sts)\n" +
                          "[P, K] 3. (6 sts)\n" +
                          "rep from ** 3 times\n" +
                          "BO 6. (0 sts)"),
     "Should allow n-by-m tiling of patterns")
test(lambda: check_output("test/pass-called-pattern.ks",
                          "CO 3. (3 sts)\n" +
                          "**\n" +
                          "K, P, K. (3 sts)\n" +
                          "rep from ** 5 times\n" +
                          "**\n" +
                          "P, K, P. (3 sts)\n" +
                          "rep from ** 3 times\n" +
                          "BO 3. (0 sts)"),
     "Patterns can be passed with or without being called with arguments")
test(lambda: expect_except("test/too-few-arguments.ks", InterpretError),
     "Should catch patterns called with too few arguments")
test(lambda: expect_except("test/too-many-arguments.ks", InterpretError),
     "Should catch patterns called with too many arguments")
test(lambda: expect_except("test/called-twice.ks", InterpretError),
     "Should catch patterns that are called twice")
test(lambda: check_output("test/nested-stitch-repeats.ks",
                          "CO 6. (6 sts)\n" +
                          "K 6. (6 sts)\n" +
                          "BO 6. (0 sts)"),
     "Should flatten redundant nested fixed stitch repeats")
test(lambda: check_output("test/nested-stitch-repeats-with-block.ks",
                          "CO 6. (6 sts)\n" +
                          "K 6. (6 sts)\n" +
                          "BO 6. (0 sts)"),
     "Should flatten nested fixed stitch repeats that result from block " +
     "substitution")
test(lambda: check_output("test/reflection.ks",
                          "CO 9. (9 sts)\n" +
                          "K, [K, K, P] 2, K, K. (9 sts)\n" +
                          "BO 9. (0 sts)"),
     "Should be able to reflect patterns horizontally")
test(lambda: verify_error("test/bad-block.ks"),
     "Should catch invalid block combinations")
