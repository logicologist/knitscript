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
     "Should catch expected stitches greater than available")
test(lambda: verify_error("test/too-few-stitches.ks"),
     "Should catch expected stitches smaller than available")
test(lambda: check_output("test/just-right.ks",
                          "WS: CO 12. (12 sts)\n" +
                          "RS: K 12. (12 sts)\n" +
                          "WS: *BO; rep from * to end. (0 sts)"),
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
                          "WS: CO 6. (6 sts)\n" +
                          "**\n" +
                          "RS: [K, P] 3. (6 sts)\n" +
                          "WS: [P, K] 3. (6 sts)\n" +
                          "rep from ** 3 times\n" +
                          "RS: BO 6. (0 sts)"),
     "Should allow n-by-m tiling of patterns")
test(lambda: check_output("test/pass-called-pattern.ks",
                          "WS: CO 3. (3 sts)\n" +
                          "**\n" +
                          "RS: K, P, K. (3 sts)\n" +
                          "rep from ** 5 times\n" +
                          "**\n" +
                          "WS: P, K, P. (3 sts)\n" +
                          "rep from ** 3 times\n" +
                          "RS: BO 3. (0 sts)"),
     "Patterns can be passed with or without being called with arguments")
test(lambda: expect_except("test/too-few-arguments.ks", InterpretError),
     "Should catch patterns called with too few arguments")
test(lambda: expect_except("test/too-many-arguments.ks", InterpretError),
     "Should catch patterns called with too many arguments")
test(lambda: expect_except("test/called-twice.ks", InterpretError),
     "Should catch patterns that are called twice")
test(lambda: check_output("test/nested-stitch-repeats.ks",
                          "WS: CO 6. (6 sts)\n" +
                          "RS: K 6. (6 sts)\n" +
                          "WS: BO 6. (0 sts)"),
     "Should flatten redundant nested fixed stitch repeats")
test(lambda: check_output("test/nested-stitch-repeats-with-block.ks",
                          "WS: CO 6. (6 sts)\n" +
                          "RS: K 6. (6 sts)\n" +
                          "WS: BO 6. (0 sts)"),
     "Should flatten nested fixed stitch repeats that result from block " +
     "substitution")
test(lambda: check_output("test/reflection.ks",
                          "WS: CO 9. (9 sts)\n" +
                          "RS: K, [K 2, P] 2, K 2. (9 sts)\n" +
                          "WS: BO 9. (0 sts)"),
     "Should be able to reflect patterns horizontally")
test(lambda: verify_error("test/bad-block.ks"),
     "Should catch invalid block combinations")
test(lambda: check_output("test/spiral-square.ks",
                          "WS: CO 3. (3 sts)\n" +
                          "RS: P 2, K. (3 sts)\n" +
                          "WS: K, SL, K. (3 sts)\n" +
                          "RS: K, P 2. (3 sts)\n" +
                          "WS: BO 3. (0 sts)"),
     "Should support advanced block concatenation using empty rows")
test(lambda: expect_except("test/reversing-psso.ks", InterpretError),
     "Should disallow reversing psso")
test(lambda: verify_error("test/sl-psso-immediately.ks"),
     "Should disallow psso immediately after slip")
test(lambda: verify_error("test/psso-without-slip.ks"),
     "Should disallow psso without slip")
test(lambda: verify_error("test/psso-without-slip-2.ks"),
     "Should disallow psso without slip in case of multiple psso/slip")
test(
    lambda: check_output(
        "test/nested-psso.ks",
        "WS: CO 8. (8 sts)\n" +
        "RS: K, SL, K, SL, K, PSSO, K, PSSO, K 2. (6 sts)\n" +
        "WS: *BO; rep from * to end. (0 sts)"
    ),
    "Should allow nested psso"
)
test(lambda: check_output("test/merge-with-unrolling.ks",
                          "WS: CO 4. (4 sts)\n" +
                          "RS: P 2, K, P. (4 sts)\n" +
                          "WS: P, K, P 2. (4 sts)\n" +
                          "RS: BO 4. (0 sts)"),
     "Blocks with mixed rows and row repeats should be unrolled")
test(lambda: check_output("test/merge-without-unrolling.ks",
                          "WS: CO 12. (12 sts)\n" +
                          "**\n" +
                          "RS: K 12. (12 sts)\n" +
                          "WS: K, P 10, K. (12 sts)\n" +
                          "rep from ** 10 times\n" +
                          "RS: BO 12. (0 sts)"),
     "Merging parallel row repeats should preserve the repeat")
# TODO:
#  The output changed, but it might be more correct. Should the
#  merge-finding-lcm test be updated?
test(lambda: check_output("test/merge-finding-lcm.ks",
                          "WS: CO 8. (8 sts)\n" +
                          "**\n" +
                          "RS: P 4, K 4. (8 sts)\n" +
                          "WS: P 4, K 4. (8 sts)\n" +
                          "RS: K2TOG, YO, K2TOG, YO, K 4. (8 sts)\n" +
                          "WS: P 4, K 4. (8 sts)\n" +
                          "RS: P 4, K 4. (8 sts)\n" +
                          "WS: P 4, YO, SSP, YO, SSP. (8 sts)\n" +
                          "rep from ** 2 times\n" +
                          "RS: BO 8. (0 sts)"),
     "Merging parallel row repeats should find the least common multiple")
test(lambda: check_output("test/fill.ks",
                          "WS: CO 10. (10 sts)\n" +
                          "**\n" +
                          "RS: [K, P] 5. (10 sts)\n"
                          "WS: [P, K] 5. (10 sts)\n" +
                          "rep from ** 4 times\n" +
                          "RS: BO 10. (0 sts)"),
     "Test fill function")
test(lambda: check_output("test/standalone-triangle.ks",
                          "WS: CO 3. (3 sts)\n" +
                          "RS: KFB, K, KFB. (5 sts)\n" +
                          "WS: P 5. (5 sts)\n" +
                          "RS: KFB, K 3, KFB. (7 sts)\n" +
                          "WS: P 7. (7 sts)\n" +
                          "RS: KFB, K 5, KFB. (9 sts)\n" +
                          "WS: P 9. (9 sts)\n" +
                          "RS: *BO; rep from * to end. (0 sts)"),
     "Should be able to make a triangular pattern standalone")
