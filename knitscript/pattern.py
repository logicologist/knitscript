from __future__ import annotations

from functools import singledispatch
from typing import Tuple

from knitscript.ast import ExpandingStitchRepeatExpr, Expr, \
    FixedStitchRepeatExpr, PatternExpr, RowRepeatExpr, StitchExpr


def is_valid_pattern(pattern: PatternExpr) -> bool:
    return count_stitches(pattern, 0) == (0, 0)


@singledispatch
def count_stitches(_expr: Expr, _available: int) -> Tuple[int, int]:
    """
    Returns the number of stitches consumed from the current row and the number
    of stitches produced for the next row after evaluating all the stitches in
    the tree.
    """
    raise NotImplementedError()


@count_stitches.register
def _(stitch: StitchExpr, available: int) -> Tuple[int, int]:
    _at_least(stitch.stitch.consumes, available)
    return stitch.stitch.consumes, stitch.stitch.produces


@count_stitches.register
def _(repeat: FixedStitchRepeatExpr, available: int) -> Tuple[int, int]:
    this_side = available
    next_side = 0
    for _ in range(repeat.count):
        for stitch in repeat.stitches:
            consumed, produced = count_stitches(stitch, this_side)
            _at_least(consumed, this_side)
            this_side -= consumed
            next_side += produced
    return available - this_side, next_side


@count_stitches.register
def _(repeat: ExpandingStitchRepeatExpr, available: int) -> Tuple[int, int]:
    consumed, produced = count_stitches(
        FixedStitchRepeatExpr(repeat.stitches, 1), available - repeat.to_last
    )
    n = (available - repeat.to_last) // consumed
    _exactly(n * consumed, available - repeat.to_last)
    return n * consumed, n * produced


@count_stitches.register
def _(repeat: RowRepeatExpr, available: int) -> Tuple[int, int]:
    count = available
    for _ in range(repeat.count):
        for row in repeat.rows:
            consumed, produced = count_stitches(row, count)
            _exactly(consumed, count)
            count = produced
    return available, count


@singledispatch
def compile_text(_expr: Expr) -> str:
    raise NotImplementedError()


@compile_text.register
def _(stitch: StitchExpr) -> str:
    return stitch.stitch.symbol


@compile_text.register
def _(repeat: FixedStitchRepeatExpr) -> str:
    stitches = ", ".join(map(compile_text, repeat.stitches))
    if repeat.count == 1:
        return stitches
    elif len(repeat.stitches) == 1:
        return f"{stitches} {repeat.count}"
    else:
        return f"[{stitches}] {repeat.count}"


@compile_text.register
def _(repeat: ExpandingStitchRepeatExpr) -> str:
    stitches = compile_text(FixedStitchRepeatExpr(repeat.stitches, 1))
    if repeat.to_last == 0:
        return f"*{stitches}; rep from * to end"
    else:
        return f"*{stitches}; rep from * to last {repeat.to_last}"


@compile_text.register
def _(repeat: RowRepeatExpr) -> str:
    rows = ".\n".join(map(compile_text, repeat.rows)) + "."
    if repeat.count == 1:
        return rows
    else:
        return f"**\n{rows}\nrep from ** {repeat.count} times"


def _at_least(expected: int, actual: int) -> None:
    if expected > actual:
        raise Exception(
            f"expected {expected} stitches, but only {actual} are available"
        )


def _exactly(expected: int, actual: int) -> None:
    _at_least(expected, actual)
    if expected < actual:
        raise Exception(f"{actual - expected} stitches left over")
