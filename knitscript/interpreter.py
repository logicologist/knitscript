from __future__ import annotations

from functools import partial, singledispatch
from operator import attrgetter
from typing import Dict, Tuple, Union

from knitscript.ast import BlockConcatExpr, CallExpr, \
    ExpandingStitchRepeatExpr, Expr, FixedStitchRepeatExpr, GetExpr, \
    NaturalLit, PatternExpr, RowRepeatExpr, StitchExpr, RowExpr


def is_valid_pattern(pattern: PatternExpr) -> bool:
    """
    Checks if the pattern is valid. A valid pattern has the right number of
    stitches in each row.

    :param pattern: the pattern to validate
    :return: True if the pattern is valid and False otherwise
    """
    return count_stitches(pattern, 0) == (0, 0)


# noinspection PyUnusedLocal
@singledispatch
def count_stitches(expr: Expr, available: int) -> Tuple[int, int]:
    """
    Counts the number of stitches used at the beginning and end of the
    expression, and makes sure the expression does not use too many stitches or
    not enough stitches at any point.

    :param expr: the expression to count the stitches of
    :param available: the number of stitches remaining in the current row
    :return:
        a pair; the first is the number of stitches consumed from the current
        row and the second is the number of stitches produced at the end of the
        expression
    :raise Exception:
        if the expression uses too many stitches or not enough stitches
    """
    raise TypeError(f"unsupported expression {type(expr).__name__}")


@count_stitches.register
def _(stitch: StitchExpr, available: int) -> Tuple[int, int]:
    _at_least(stitch.stitch.consumes, available)
    return stitch.stitch.consumes, stitch.stitch.produces


@count_stitches.register
def _(repeat: FixedStitchRepeatExpr, available: int) -> Tuple[int, int]:
    this_side = available
    next_side = 0
    assert isinstance(repeat.count, NaturalLit)
    for _ in range(repeat.count.value):
        for stitch in repeat.stitches:
            consumed, produced = count_stitches(stitch, this_side)
            _at_least(consumed, this_side)
            this_side -= consumed
            next_side += produced
    return available - this_side, next_side


@count_stitches.register
def _(repeat: ExpandingStitchRepeatExpr, available: int) -> Tuple[int, int]:
    assert isinstance(repeat.to_last, NaturalLit)
    consumed, produced = count_stitches(
        FixedStitchRepeatExpr(repeat.stitches, NaturalLit(1)),
        available - repeat.to_last.value
    )
    n = (available - repeat.to_last.value) // consumed
    _exactly(n * consumed, available - repeat.to_last.value)
    return n * consumed, n * produced


@count_stitches.register
def _(repeat: RowRepeatExpr, available: int) -> Tuple[int, int]:
    count = available
    assert isinstance(repeat.count, NaturalLit)
    for _ in range(repeat.count.value):
        for row in repeat.rows:
            consumed, produced = count_stitches(row, count)
            _exactly(consumed, count)
            count = produced
    return available, count


@singledispatch
def compile_text(expr: Expr) -> str:
    """
    Compiles the expression to human-readable knitting instructions in plain
    text.

    :param expr: the expression to compile
    :return: the instructions for the expression
    """
    raise TypeError(f"unsupported expression {type(expr).__name__}")


@compile_text.register
def _(stitch: StitchExpr) -> str:
    return stitch.stitch.symbol


@compile_text.register
def _(repeat: FixedStitchRepeatExpr) -> str:
    stitches = ", ".join(map(compile_text, repeat.stitches))
    if repeat.count == NaturalLit(1):
        return stitches
    elif len(repeat.stitches) == 1:
        return f"{stitches} {repeat.count}"
    else:
        return f"[{stitches}] {repeat.count}"


@compile_text.register
def _(repeat: ExpandingStitchRepeatExpr) -> str:
    stitches = compile_text(FixedStitchRepeatExpr(repeat.stitches,
                                                  NaturalLit(1)))
    if repeat.to_last == NaturalLit(0):
        return f"*{stitches}; rep from * to end"
    else:
        return f"*{stitches}; rep from * to last {repeat.to_last}"


@compile_text.register
def _(repeat: RowRepeatExpr) -> str:
    rows = ".\n".join(map(compile_text, repeat.rows)) + "."
    if repeat.count == NaturalLit(1):
        return rows
    else:
        return f"**\n{rows}\nrep from ** {repeat.count} times"


# noinspection PyUnusedLocal
@singledispatch
def substitute(expr: Expr, env: Dict[str, Expr]) -> Expr:
    """
    Substitutes all variables and calls in the expression with their equivalent
    expressions.

    :param expr: the expression to transform
    :param env: the environment
    :return:
        the transformed expression with all variables and calls substituted out
    """
    raise TypeError(f"unsupported expression {type(expr).__name__}")


# noinspection PyUnusedLocal
@substitute.register(StitchExpr)
@substitute.register(NaturalLit)
def _(expr: Union[StitchExpr, NaturalLit], env: Dict[str, Expr]) -> Expr:
    return expr


@substitute.register
def _(repeat: FixedStitchRepeatExpr, env: Dict[str, Expr]) -> Expr:
    # noinspection PyTypeChecker
    return FixedStitchRepeatExpr(
        list(map(partial(substitute, env=env), repeat.stitches)),
        substitute(repeat.count, env)
    )


@substitute.register
def _(repeat: ExpandingStitchRepeatExpr, env: Dict[str, Expr]) -> Expr:
    # noinspection PyTypeChecker
    return ExpandingStitchRepeatExpr(
        list(map(partial(substitute, env=env), repeat.stitches)),
        substitute(repeat.to_last, env)
    )


@substitute.register
def _(repeat: RowRepeatExpr, env: Dict[str, Expr]) -> Expr:
    # noinspection PyTypeChecker
    return RowRepeatExpr(
        list(map(partial(substitute, env=env), repeat.rows)),
        substitute(repeat.count, env)
    )


@substitute.register
def _(concat: BlockConcatExpr, env: Dict[str, Expr]) -> Expr:
    # noinspection PyTypeChecker
    return BlockConcatExpr(
        list(map(partial(substitute, env=env), concat.blocks))
    )


@substitute.register
def _(pattern: PatternExpr, env: Dict[str, Expr]) -> Expr:
    # noinspection PyTypeChecker
    return PatternExpr(
        list(map(partial(substitute, env=env), pattern.rows)),
        pattern.params
    )


@substitute.register
def _(get: GetExpr, env: Dict[str, Expr]) -> Expr:
    return env[get.name]


@substitute.register
def _(call: CallExpr, env: Dict[str, Expr]) -> Expr:
    target = call.target
    if isinstance(target, GetExpr):
        target = substitute(target, env)

    assert isinstance(target, PatternExpr)
    return substitute(call.target,
                      {**env, **dict(zip(target.params, call.args))})


@singledispatch
def flatten(expr: Expr) -> Expr:
    """
    Flattens each block concatenation expression into a single pattern.

    :param expr: the expression to transform
    :return: the transformed expression after flattening block concatenations
    """
    raise TypeError(f"unsupported expression {type(expr).__name__}")


@flatten.register
def _(stitch: StitchExpr) -> Expr:
    return stitch


@flatten.register
def _(repeat: FixedStitchRepeatExpr) -> Expr:
    return FixedStitchRepeatExpr(list(map(flatten, repeat.stitches)),
                                 repeat.count)


@flatten.register
def _(repeat: ExpandingStitchRepeatExpr) -> Expr:
    return ExpandingStitchRepeatExpr(list(map(flatten, repeat.stitches)),
                                     repeat.to_last)


@flatten.register
def _(repeat: RowRepeatExpr) -> Expr:
    return RowRepeatExpr(list(map(flatten, repeat.rows)), repeat.count)


@flatten.register
def _(pattern: PatternExpr) -> Expr:
    return PatternExpr(list(map(flatten, pattern.rows)), pattern.params)


@flatten.register
def _(concat: BlockConcatExpr) -> Expr:
    for block in concat.blocks:
        assert isinstance(block, PatternExpr)
    rows = map(RowExpr, zip(*map(attrgetter("rows"), concat.blocks)))
    return PatternExpr(list(rows))


def _at_least(expected: int, actual: int) -> None:
    if expected > actual:
        raise Exception(
            f"expected {expected} stitches, but only {actual} are available"
        )


def _exactly(expected: int, actual: int) -> None:
    _at_least(expected, actual)
    if expected < actual:
        raise Exception(f"{actual - expected} stitches left over")
