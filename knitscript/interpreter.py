from __future__ import annotations

from functools import partial, singledispatch
from itertools import accumulate, chain
from operator import attrgetter
from typing import Mapping, Union

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
    pattern = count_stitches(pattern, 0)
    assert isinstance(pattern, PatternExpr)
    return pattern.consumes == 0 and pattern.produces == 0


# noinspection PyUnusedLocal
@singledispatch
def count_fixed_stitches(expr: Node) -> Node:
    """
    For a fixed sequence of nodes, counts the number of stitches expected and produced
    by that sequence of stitches.

    :param expr: the AST node for the fixed set of stitches
    :return: an AST node with all stitch counts (consumes and produces) filled in
    """
    raise TypeError(f"unsupported node {type(expr).__name__}")

@count_fixed_stitches.register
def _(stitch: StitchLit) -> Node:
    return StitchLit(stitch.value)

@count_fixed_stitches.register
def _(fixed: FixedStitchRepeatExpr) -> Node:
    consumes = sum(map(lambda stitch: stitch.value.consumes, fixed.stitches)) * fixed.times
    produces = sum(map(lambda stitch: stitch.value.produces, fixed.stitches)) * fixed.times
    return FixedStitchRepeatExpr(fixed.stitches, fixed.times, consumes, produces)

@count_fixed_stitches.register
def _(row: RowExpr) -> Node:
    counted_stitches = map(lambda stitch: count_fixed_stitches(stitch))
    consumes = sum(map(lambda stitch: stitch.consumes, counted_stitches))
    produces = sum(map(lambda stitch: stitch.produces, counted_stitches))
    return RowExpr(counted_stitches, row.side, consumes, produces)


# noinspection PyUnusedLocal
@singledispatch
def count_stitches(expr: Node, available: int) -> Node:
    """
    For each node, counts the number of stitches consumed from the current row
    and produced for the next row.

    :param expr: the AST to count the stitches in
    :param available: the number of stitches remaining in the current row
    :return: an AST with all stitch counts (consumes and produces) filled in
    :raise Exception:
        if the expression uses too many stitches or not enough stitches
    """
    raise TypeError(f"unsupported node {type(expr).__name__}")


@count_stitches.register
def _(stitch: StitchLit, available: int) -> Node:
    _at_least(stitch.value.consumes, available)
    return stitch


@count_stitches.register
def _(fixed: FixedStitchRepeatExpr, available: int) -> Node:
    counted = []
    consumes = 0
    produces = 0
    for stitch in fixed.stitches:
        stitch = count_stitches(stitch, available - consumes)
        counted.append(stitch)
        assert isinstance(stitch, KnitExpr)
        _at_least(stitch.consumes, available - consumes)
        consumes += stitch.consumes
        produces += stitch.produces
    _at_least(fixed.times.value * consumes, available)
    return FixedStitchRepeatExpr(counted,
                                 fixed.times,
                                 fixed.times.value * consumes,
                                 fixed.times.value * produces)


@count_stitches.register
def _(expanding: ExpandingStitchRepeatExpr, available: int) -> Node:
    fixed = count_stitches(
        FixedStitchRepeatExpr(expanding.stitches, NaturalLit(1)),
        available - expanding.to_last.value
    )
    assert isinstance(fixed, FixedStitchRepeatExpr)
    n = (available - expanding.to_last.value) // fixed.consumes
    _exactly(n * fixed.consumes, available - expanding.to_last.value)
    return ExpandingStitchRepeatExpr(fixed.stitches,
                                     expanding.to_last,
                                     n * fixed.consumes,
                                     n * fixed.produces)


@count_stitches.register
def _(row: RowExpr, available: int) -> Node:
    counted = count_stitches.dispatch(FixedStitchRepeatExpr)(row, available)
    return RowExpr(counted.stitches, row.side,
                   counted.consumes, counted.produces)


@count_stitches.register
def _(repeat: RowRepeatExpr, available: int) -> Node:
    start = available
    counted = []
    for row in repeat.rows:
        row = count_stitches(row, available)
        counted.append(row)
        assert isinstance(row, KnitExpr)
        _exactly(row.consumes, available)
        available = row.produces
    _exactly(start, available)
    return RowRepeatExpr(counted, repeat.times, start, available)


@count_stitches.register
def _(pattern: PatternExpr, available: int) -> Node:
    counted = count_stitches.dispatch(RowRepeatExpr)(pattern, available)
    return PatternExpr(counted.rows, pattern.params,
                       counted.consumes, counted.produces)


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
def flatten(node: Node) -> Expr:
    """
    Flattens each block concatenation expression and nested pattern expression
    into a single pattern.

    :param node: the AST to transform
    :return: the flattened AST
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


@flatten.register
def _(stitch: StitchLit) -> Expr:
    return stitch


@flatten.register
def _(repeat: FixedStitchRepeatExpr) -> Expr:
    return FixedStitchRepeatExpr(map(flatten, repeat.stitches), repeat.times)


@flatten.register
def _(repeat: ExpandingStitchRepeatExpr) -> Expr:
    return ExpandingStitchRepeatExpr(map(flatten, repeat.stitches),
                                     repeat.to_last)


@flatten.register
def _(row: RowExpr) -> Expr:
    return RowExpr(map(flatten, row.stitches), row.side)


@flatten.register
def _(repeat: RowRepeatExpr) -> Expr:
    rows = []
    for row in map(flatten, repeat.rows):
        if isinstance(row, PatternExpr):
            rows.extend(row.rows)
        else:
            rows.append(row)
    return RowRepeatExpr(rows, repeat.times)


@flatten.register
def _(pattern: PatternExpr) -> Expr:
    return PatternExpr(flatten.dispatch(RowRepeatExpr)(pattern).rows)


@flatten.register
def _(concat: BlockExpr) -> Expr:
    return _merge_across(*map(flatten, concat.blocks))


@singledispatch
def _merge_across(*exprs: Expr) -> Expr:
    raise TypeError(f"unsupported expression {type(exprs[0]).__name__}")


@_merge_across.register
def _(*patterns: PatternExpr) -> Expr:
    return PatternExpr(_merge_across.dispatch(RowRepeatExpr)(*patterns).rows)


@_merge_across.register
def _(*repeats: RowRepeatExpr) -> Expr:
    rows = []
    for line in zip(*map(attrgetter("rows"), repeats)):
        rows.append(_merge_across(*line))
    # TODO: Check that all row repeats have the same number of repetitions.
    return RowRepeatExpr(rows, repeats[0].times)


@_merge_across.register
def _(*rows: RowExpr) -> Expr:
    # Pick the side from the first row in the line.
    # TODO:
    #  We need to check if the rows have different sides and reverse them if
    #  they do.
    side = rows[0].side
    return RowExpr(chain.from_iterable(map(attrgetter("stitches"), rows)),
                   side)


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
                                 fixed.times)


# noinspection PyUnusedLocal
@reverse.register
def _(stitch: StitchLit, before: int) -> Node:
    return StitchLit(stitch.value.reverse)


@reverse.register
def _(expanding: ExpandingStitchRepeatExpr, before: int) -> Node:
    fixed = reverse(FixedStitchRepeatExpr(expanding.stitches, NaturalLit(1)),
                    before)
    assert isinstance(fixed, FixedStitchRepeatExpr)
    return ExpandingStitchRepeatExpr(fixed.stitches, NaturalLit(before))


@reverse.register
def _(row: RowExpr, before: int) -> Node:
    fixed = reverse(FixedStitchRepeatExpr(row.stitches, row.times), before)
    assert isinstance(fixed, FixedStitchRepeatExpr)
    return RowExpr(fixed.stitches, row.side.flip() if row.side else None)


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
