from __future__ import annotations

from functools import singledispatch
from typing import Tuple

from knitscript.ast import ExpandingStitchRepeatExpr, FixedStitchRepeatExpr, \
    PatternExpr, RowRepeatExpr, StitchExpr


def is_valid_pattern(pattern: PatternExpr) -> bool:
    return count_stitches(pattern, 0) == (0, 0)


@singledispatch
def count_stitches(_object: object, _available: int) -> Tuple[int, int]:
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
            (consumed, produced) = count_stitches(stitch, this_side)
            _at_least(consumed, this_side)
            this_side -= consumed
            next_side += produced
    return available - this_side, next_side


@count_stitches.register
def _(repeat: ExpandingStitchRepeatExpr, available: int) -> Tuple[int, int]:
    # TODO: This is too similar to the FixedStitchRepeatExpr case.
    this_side = available
    next_side = 0
    while this_side > repeat.to_last:
        for stitch in repeat.stitches:
            (consumed, produced) = count_stitches(stitch, this_side)
            _at_least(consumed, this_side)
            this_side -= consumed
            next_side += produced
    _exactly(repeat.to_last, this_side)
    return available - this_side, next_side


@count_stitches.register
def _(repeat: RowRepeatExpr, available: int) -> Tuple[int, int]:
    count = available
    for _ in range(repeat.count):
        for row in repeat.rows:
            (consumed, produced) = count_stitches(row, count)
            _exactly(consumed, count)
            count = produced
    return available, count


def _exactly(expected: int, actual: int) -> None:
    _at_least(expected, actual)
    if expected < actual:
        raise Exception(f"{actual - expected} stitches left over")


def _at_least(expected: int, actual: int) -> None:
    if expected > actual:
        raise Exception(
            f"expected {expected} stitches, but only {actual} are available")
