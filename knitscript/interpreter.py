from __future__ import annotations

from functools import partial, singledispatch
from itertools import accumulate, chain
from operator import attrgetter
from typing import Mapping, Optional, Union

from knitscript.astnodes import BlockExpr, CallExpr, \
    ExpandingStitchRepeatExpr, Expr, FixedStitchRepeatExpr, GetExpr, \
    KnitExpr, NaturalLit, Node, PatternExpr, RowExpr, RowRepeatExpr, Side, \
    StitchLit, alternate_sides


def is_valid_pattern(pattern: PatternExpr) -> bool:
    """
    Checks if the pattern is valid. A valid pattern has the right number of
    stitches in each row.

    :param pattern: the pattern to validate
    :return: True if the pattern is valid and False otherwise
    """
    pattern = infer_counts(pattern, 0)
    verify_counts(pattern, 0)
    assert isinstance(pattern, KnitExpr)
    return pattern.consumes == 0 and pattern.produces == 0


# noinspection PyUnusedLocal
@singledispatch
def infer_counts(expr: Node, available: Optional[int] = None) -> Node:
    """
    Tries to count the number of stitches that each node consumes and produces.
    If not enough information is available for a particular node, its stitch
    counts are not updated.

    :param expr: the AST to count stitches in
    :param available:
        the number of stitches remaining in the current row, if known
    :return:
        an AST with as many stitch counts (consumes and produces) as possible
        filled in
    """
    raise TypeError(f"unsupported node {type(expr).__name__}")


# noinspection PyUnusedLocal
@infer_counts.register
def _(stitch: StitchLit, available: Optional[int] = None) -> Node:
    return stitch


@infer_counts.register
def _(fixed: FixedStitchRepeatExpr, available: Optional[int] = None) -> Node:
    counted = []
    consumes = 0
    produces = 0
    for stitch in fixed.stitches:
        stitch = infer_counts(
            stitch,
            available - consumes if available is not None else None
        )
        counted.append(stitch)
        try:
            assert isinstance(stitch, KnitExpr)
            consumes += stitch.consumes
            produces += stitch.produces
        except TypeError:
            consumes = produces = None

    try:
        return FixedStitchRepeatExpr(counted, fixed.times,
                                     fixed.times.value * consumes,
                                     fixed.times.value * produces)
    except TypeError:
        return FixedStitchRepeatExpr(counted, fixed.times)


@infer_counts.register
def _(expanding: ExpandingStitchRepeatExpr, available: Optional[int] = None) \
        -> Node:
    fixed = infer_counts(
        FixedStitchRepeatExpr(expanding.stitches, NaturalLit(1)),
        available - expanding.to_last.value
    )
    assert isinstance(fixed, FixedStitchRepeatExpr)
    n = (available - expanding.to_last.value) // fixed.consumes
    _exactly(n * fixed.consumes, available - expanding.to_last.value)
    return ExpandingStitchRepeatExpr(fixed.stitches, expanding.to_last,
                                     n * fixed.consumes, n * fixed.produces)


@infer_counts.register
def _(row: RowExpr, available: Optional[int] = None) -> Node:
    counted = infer_counts.dispatch(FixedStitchRepeatExpr)(row, available)
    return RowExpr(counted.stitches, row.side,
                   counted.consumes, counted.produces)


@infer_counts.register
def _(repeat: RowRepeatExpr, available: Optional[int] = None) -> Node:
    counted = []
    for row in repeat.rows:
        row = infer_counts(row, available)
        assert isinstance(row, KnitExpr)
        counted.append(row)
        available = row.produces
    return RowRepeatExpr(counted, repeat.times, counted[0].consumes, available)


# noinspection PyUnusedLocal
@infer_counts.register
def _(block: BlockExpr, available: Optional[int] = None) -> Node:
    counted = list(map(infer_counts, block.blocks))
    return BlockExpr(counted,
                     sum(map(attrgetter("consumes"), counted)),
                     sum(map(attrgetter("produces"), counted)))


@infer_counts.register
def _(pattern: PatternExpr, available: Optional[int] = None) -> Node:
    counted = infer_counts.dispatch(RowRepeatExpr)(pattern, available)
    return PatternExpr(counted.rows, pattern.params,
                       counted.consumes, counted.produces)


# noinspection PyUnusedLocal
@singledispatch
def verify_counts(node: Node, available: int) -> None:
    """
    Checks stitch counts for consistency, and verifies that every row has
    enough stitches available and doesn't leave any stitches left over.

    :param node: the AST to verify the stitch counts of
    :param available: the number of stitches remaining in the current row
    :raise Exception: if the AST has invalid or inconsistent stitch counts
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


@verify_counts.register
def _(stitch: StitchLit, available: int) -> None:
    _at_least(stitch.value.consumes, available)


@verify_counts.register
def _(fixed: FixedStitchRepeatExpr, available: int) -> None:
    consumes = 0
    produces = 0
    for stitch in fixed.stitches:
        verify_counts(stitch, available - consumes)
        assert isinstance(stitch, KnitExpr)
        _at_least(stitch.consumes, available - consumes)
        consumes += stitch.consumes
        produces += stitch.produces
    _at_least(fixed.times.value * consumes, available)


@verify_counts.register
def _(expanding: ExpandingStitchRepeatExpr, available: int) -> None:
    verify_counts(
        FixedStitchRepeatExpr(expanding.stitches, NaturalLit(1)),
        available - expanding.to_last.value
    )
    n = (available - expanding.to_last.value) // expanding.consumes
    _exactly(n * expanding.consumes, available - expanding.to_last.value)


@verify_counts.register
def _(repeat: RowRepeatExpr, available: int) -> None:
    start = available
    for row in repeat.rows:
        verify_counts(row, available)
        assert isinstance(row, KnitExpr)
        _exactly(row.consumes, available)
        available = row.produces
    _exactly(start, available)


@singledispatch
def compile_text(expr: Node) -> str:
    """
    Compiles the expression to human-readable knitting instructions in plain
    text.

    :param expr: the expression to compile
    :return: the instructions for the expression
    """
    raise TypeError(f"unsupported node {type(expr).__name__}")


@compile_text.register
def _(stitch: StitchLit) -> str:
    return stitch.value.symbol


@compile_text.register
def _(repeat: FixedStitchRepeatExpr) -> str:
    stitches = ", ".join(map(compile_text, repeat.stitches))
    if repeat.times == NaturalLit(1):
        return stitches
    elif len(repeat.stitches) == 1:
        return f"{stitches} {repeat.times}"
    else:
        return f"[{stitches}] {repeat.times}"


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
    if repeat.times == NaturalLit(1):
        return rows
    else:
        return f"**\n{rows}\nrep from ** {repeat.times} times"


# noinspection PyUnusedLocal
@singledispatch
def substitute(node: Node, env: Mapping[str, Node]) -> Node:
    """
    Substitutes all variables and calls in the AST with their equivalent
    expressions.

    :param node: the AST to transform
    :param env: the environment
    :return:
        the transformed expression with all variables and calls substituted out
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


# noinspection PyUnusedLocal
@substitute.register(StitchLit)
@substitute.register(NaturalLit)
def _(lit: Union[StitchLit, NaturalLit], env: Mapping[str, Node]) -> Node:
    return lit


@substitute.register
def _(repeat: FixedStitchRepeatExpr, env: Mapping[str, Node]) -> Node:
    # noinspection PyTypeChecker
    return FixedStitchRepeatExpr(
        map(partial(substitute, env=env), repeat.stitches),
        substitute(repeat.times, env)
    )


@substitute.register
def _(repeat: ExpandingStitchRepeatExpr, env: Mapping[str, Node]) -> Node:
    # noinspection PyTypeChecker
    return ExpandingStitchRepeatExpr(
        map(partial(substitute, env=env), repeat.stitches),
        substitute(repeat.to_last, env)
    )


@substitute.register
def _(row: RowExpr, env: Mapping[str, Node]) -> Node:
    substituted = substitute.dispatch(FixedStitchRepeatExpr)(row, env)
    assert isinstance(substituted, FixedStitchRepeatExpr)
    return RowExpr(substituted.stitches, row.side)


@substitute.register
def _(repeat: RowRepeatExpr, env: Mapping[str, Node]) -> Node:
    # noinspection PyTypeChecker
    return RowRepeatExpr(map(partial(substitute, env=env), repeat.rows),
                         substitute(repeat.times, env))


@substitute.register
def _(concat: BlockExpr, env: Mapping[str, Node]) -> Node:
    # noinspection PyTypeChecker
    return BlockExpr(map(partial(substitute, env=env), concat.blocks))


@substitute.register
def _(pattern: PatternExpr, env: Mapping[str, Node]) -> Node:
    # noinspection PyTypeChecker
    return PatternExpr(map(partial(substitute, env=env), pattern.rows),
                       pattern.params)


@substitute.register
def _(get: GetExpr, env: Mapping[str, Node]) -> Node:
    return env[get.name]


@substitute.register
def _(call: CallExpr, env: Mapping[str, Node]) -> Node:
    target = call.target
    if isinstance(target, GetExpr):
        target = substitute(target, env)
    assert isinstance(target, PatternExpr)
    # noinspection PyTypeChecker
    return substitute(
        target,
        {**env, **dict(zip(target.params,
                           map(partial(substitute, env=env), call.args)))}
    )


@singledispatch
def flatten(node: Node) -> KnitExpr:
    """
    Flattens each block concatenation expression and nested pattern expression
    into a single pattern.

    :param node: the AST to transform
    :return: the flattened AST
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


@flatten.register
def _(stitch: StitchLit) -> KnitExpr:
    return stitch


@flatten.register
def _(repeat: FixedStitchRepeatExpr) -> KnitExpr:
    return FixedStitchRepeatExpr(map(flatten, repeat.stitches), repeat.times,
                                 repeat.consumes, repeat.produces)


@flatten.register
def _(repeat: ExpandingStitchRepeatExpr) -> KnitExpr:
    return ExpandingStitchRepeatExpr(
        map(flatten, repeat.stitches), repeat.to_last,
        repeat.consumes, repeat.produces
    )


@flatten.register
def _(row: RowExpr) -> KnitExpr:
    return RowExpr(map(flatten, row.stitches), row.side,
                   row.consumes, row.produces)


@flatten.register
def _(repeat: RowRepeatExpr) -> KnitExpr:
    rows = []
    for row in map(flatten, repeat.rows):
        if isinstance(row, PatternExpr):
            rows.extend(row.rows)
        else:
            rows.append(row)
    return RowRepeatExpr(rows, repeat.times,
                         rows[0].consumes, rows[-1].produces)


@flatten.register
def _(pattern: PatternExpr) -> KnitExpr:
    flattened = flatten.dispatch(RowRepeatExpr)(pattern)
    return PatternExpr(flattened.rows, pattern.params,
                       flattened.consumes, flattened.produces)


@flatten.register
def _(concat: BlockExpr) -> KnitExpr:
    return _merge_across(*map(flatten, concat.blocks))


@singledispatch
def _merge_across(*exprs: Expr) -> KnitExpr:
    raise TypeError(f"unsupported expression {type(exprs[0]).__name__}")


@_merge_across.register
def _(*patterns: PatternExpr) -> KnitExpr:
    repeat = _merge_across.dispatch(RowRepeatExpr)(*patterns)
    return PatternExpr(repeat.rows, (), repeat.consumes, repeat.produces)


@_merge_across.register
def _(*repeats: RowRepeatExpr) -> KnitExpr:
    rows = []
    for line in zip(*map(attrgetter("rows"), repeats)):
        rows.append(_merge_across(*line))
    # TODO: Check that all row repeats have the same number of repetitions.
    return RowRepeatExpr(rows, repeats[0].times,
                         rows[0].consumes, rows[-1].produces)


@_merge_across.register
def _(*rows: RowExpr) -> KnitExpr:
    # The side of the combined row is the same as the side of the first row
    # in the list. We reverse the other rows before combining them if they
    # have a different side.
    side = rows[0].side
    rows = list(map(lambda row: row if row.side == side else reverse(row, 0),
                    rows))
    return RowExpr(
        chain.from_iterable(map(attrgetter("stitches"), rows)), side,
        sum(map(attrgetter("consumes"), rows)),
        sum(map(attrgetter("produces"), rows))
    )


# noinspection PyUnusedLocal
@singledispatch
def reverse(expr: Node, before: int) -> Node:
    """
    Reverses the yarn direction of an expression. Assumes the AST has had
    stitches counted.

    :param expr: the expression to reverse
    :param before:
        the number of stitches made so far, before this expression, in the
        current row
    :return: the reversed expression
    """
    raise TypeError(f"unsupported node {type(expr).__name__}")


# noinspection PyUnusedLocal
@reverse.register
def _(fixed: FixedStitchRepeatExpr, before: int) -> Node:
    before_acc = accumulate(
        chain([before], map(attrgetter("consumes"), fixed.stitches[:-1]))
    )
    return FixedStitchRepeatExpr(map(reverse,
                                     reversed(fixed.stitches),
                                     reversed(list(before_acc))),
                                 fixed.times, fixed.consumes, fixed.produces)


# noinspection PyUnusedLocal
@reverse.register
def _(stitch: StitchLit, before: int) -> Node:
    return StitchLit(stitch.value.reverse)


@reverse.register
def _(expanding: ExpandingStitchRepeatExpr, before: int) -> Node:
    fixed = reverse(FixedStitchRepeatExpr(expanding.stitches, NaturalLit(1)),
                    before)
    assert isinstance(fixed, FixedStitchRepeatExpr)
    return ExpandingStitchRepeatExpr(fixed.stitches, NaturalLit(before),
                                     expanding.consumes, expanding.produces)


@reverse.register
def _(row: RowExpr, before: int) -> Node:
    fixed = reverse(FixedStitchRepeatExpr(row.stitches, row.times,
                                          row.consumes, row.produces),
                    before)
    assert isinstance(fixed, FixedStitchRepeatExpr)
    return RowExpr(fixed.stitches, row.side.flip() if row.side else None,
                   fixed.consumes, fixed.produces)


# noinspection PyUnusedLocal
@singledispatch
def infer_sides(node: Node, side: Side = Side.Right) -> Node:
    """
    Infers the side of each row, assuming that:
     1. Patterns start on RS.
     2. Rows alternate between RS and WS.

    Rows that have an explicit side already are unchanged.

    :param node: the AST to infer sides in
    :param side: the starting side for the next row
    :return: an AST with row sides filled in
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


# noinspection PyUnusedLocal
@infer_sides.register
def _(pattern: PatternExpr, side: Side = Side.Right) -> Node:
    return PatternExpr(
        map(infer_sides, pattern.rows, alternate_sides(Side.Right)),
        pattern.params
    )


@infer_sides.register
def _(block: BlockExpr, side: Side = Side.Right) -> Node:
    return BlockExpr(map(infer_sides, block.blocks, alternate_sides(side)))


@infer_sides.register
def _(repeat: RowRepeatExpr, side: Side = Side.Right) -> Node:
    return RowRepeatExpr(map(infer_sides, repeat.rows, alternate_sides(side)),
                         repeat.times)


@infer_sides.register
def _(row: RowExpr, side: Side = Side.Right) -> Node:
    return RowExpr(row.stitches, side if row.side is None else row.side)


def _at_least(expected: int, actual: int) -> None:
    if expected > actual:
        raise Exception(
            f"expected {expected} stitches, but only {actual} are available"
        )


def _exactly(expected: int, actual: int) -> None:
    _at_least(expected, actual)
    if expected < actual:
        raise Exception(f"{actual - expected} stitches left over")
