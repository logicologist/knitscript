from __future__ import annotations

from functools import partial, singledispatch, reduce
from itertools import accumulate, chain, repeat
from operator import attrgetter
from typing import Mapping, Optional
from math import gcd

from knitscript.astnodes import BlockExpr, CallExpr, \
    ExpandingStitchRepeatExpr, Expr, FixedStitchRepeatExpr, GetExpr, \
    KnitExpr, NaturalLit, Node, PatternExpr, RowExpr, RowRepeatExpr, Side, \
    StitchLit, ast_map, pretty_print


class InterpretError(Exception):
    """
    An error in a KnitScript document that prevents it from being interpreted.
    """

    def __init__(self, message: str, node: Node) -> None:
        """
        Creates a new interpretation error.

        :param message: a message describing the error
        :param node: the node the error happened at
        """
        self._message = message
        self._node = node

    @property
    def message(self) -> str:
        """A message describing the error."""
        return self._message

    @property
    def node(self) -> Node:
        """The node the error happened at."""
        return self._node

    def __str__(self) -> str:
        return f"{self.message} at {self.node}"


@singledispatch
def infer_counts(node: Node, available: Optional[int] = None) -> Node:
    """
    Tries to count the number of stitches that each node consumes and produces.
    If not enough information is available for a particular node, its stitch
    counts are not updated.

    :param node: the AST to count stitches in
    :param available:
        the number of stitches remaining in the current row, if known
    :return:
        an AST with as many stitch counts (consumes and produces) as possible
        filled in
    """
    # noinspection PyTypeChecker
    return ast_map(node, partial(infer_counts, available=available))


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
    if available is None:
        raise InterpretError("ambiguous use of expanding stitch repeat",
                             expanding)
    fixed = infer_counts(
        FixedStitchRepeatExpr(expanding.stitches, NaturalLit(1)),
        available - expanding.to_last.value
    )
    assert isinstance(fixed, FixedStitchRepeatExpr)
    n = (available - expanding.to_last.value) // fixed.consumes
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
    if len(block.blocks) == 1:
        counted = [infer_counts(block.blocks[0], available)]
    else:
        counted = list(map(infer_counts, block.blocks))
    return BlockExpr(counted,
                     sum(map(attrgetter("consumes"), counted)),
                     sum(map(attrgetter("produces"), counted)))


@infer_counts.register
def _(pattern: PatternExpr, available: Optional[int] = None) -> Node:
    counted = infer_counts.dispatch(RowRepeatExpr)(pattern, available)
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
    # noinspection PyTypeChecker
    return ast_map(node, partial(substitute, env=env))


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
def flatten(node: Node, unroll: bool = False) -> Node:
    """
    Flattens each block concatenation expression and nested pattern expression
    into a single pattern.

    :param node: the AST to transform
    :param unroll:
        whether to unroll row repeat expressions into a sequence of repeated
        rows
    :return: the flattened AST
    """
    # noinspection PyTypeChecker
    return ast_map(node, partial(flatten, unroll=unroll))


@flatten.register
def _(row_repeat: RowRepeatExpr, unroll: bool = False) -> Node:
    rows = []
    # noinspection PyTypeChecker
    for row in map(partial(flatten, unroll=unroll), row_repeat.rows):
        if isinstance(row, RowRepeatExpr) and (unroll or row.times.value <= 1):
            rows.extend(chain.from_iterable(repeat(row.rows, row.times.value)))
        else:
            rows.append(row)
    return RowRepeatExpr(rows, row_repeat.times,
                         rows[0].consumes if rows else 0,
                         rows[-1].produces if rows else 0)


@flatten.register
def _(pattern: PatternExpr, unroll: bool = False) -> Node:
    flattened = flatten.dispatch(RowRepeatExpr)(pattern, unroll)
    return PatternExpr(flattened.rows, pattern.params,
                       flattened.consumes, flattened.produces)


@flatten.register
def _(concat: BlockExpr, unroll: bool = False) -> Node:
    if len(concat.blocks) > 1:
        # Unroll row repeats if there is more than one pattern in this block.
        # This makes merging across rows much simpler.
        # noinspection PyTypeChecker
        return _merge_across(*map(partial(flatten, unroll=True),
                                  concat.blocks))
    else:
        # noinspection PyTypeChecker
        return _merge_across(*map(partial(flatten, unroll=unroll),
                                  concat.blocks))


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
        map(infer_sides, pattern.rows, Side.Right.alternate()),
        pattern.params
    )


@infer_sides.register
def _(block: BlockExpr, side: Side = Side.Right) -> Node:
    return BlockExpr(map(infer_sides, block.blocks, side.alternate()))


@infer_sides.register
def _(repeat: RowRepeatExpr, side: Side = Side.Right) -> Node:
    return RowRepeatExpr(map(infer_sides, repeat.rows, side.alternate()),
                         repeat.times)


@infer_sides.register
def _(row: RowExpr, side: Side = Side.Right) -> Node:
    return RowExpr(row.stitches, side if row.side is None else row.side)


@singledispatch
def alternate_sides(node: Node, side: Side = Side.Right) -> Node:
    """
    Ensures that every row alternates between right and wrong side, starting
    from the given side.

    :param node: the AST to alternate the sides of
    :param side: the side of the first row
    :return: the AST with every row alternating sides
    """
    # noinspection PyTypeChecker
    return ast_map(node, partial(alternate_sides, side=side))


@alternate_sides.register
def _(row: RowExpr, side: Side = Side.Right) -> Node:
    return row if row.side == side else reverse(row, 0)


@alternate_sides.register
def _(repeat: RowRepeatExpr, side: Side = Side.Right) -> Node:
    return RowRepeatExpr(map(alternate_sides, repeat.rows, side.alternate()),
                         repeat.times, repeat.consumes, repeat.produces)


@alternate_sides.register
def _(pattern: PatternExpr, side: Side = Side.Right) -> Node:
    return PatternExpr(
        alternate_sides.dispatch(RowRepeatExpr)(pattern, side).rows,
        pattern.params, pattern.consumes, pattern.produces
    )


@singledispatch
def _merge_across(*exprs: Expr) -> KnitExpr:
    raise TypeError(f"unsupported expression {type(exprs[0]).__name__}")


@_merge_across.register
def _(*patterns: PatternExpr) -> KnitExpr:
    repeat = _merge_across.dispatch(RowRepeatExpr)(*patterns)
    # TODO should the params from each pattern be combined for the new PatternExpr below, rather than just ()?
    return PatternExpr(repeat.rows, (), repeat.consumes, repeat.produces)


@_merge_across.register
def _(*repeats: RowRepeatExpr) -> KnitExpr:
    print("****")
    list(map(pretty_print, repeats))
    print("****")
    # Check that the number of rows in total for each RowRepeatExpr is the same
    num_rows = map(lambda repeat: sum(1 for _ in repeat.rows) * repeat.times.value, repeats)
    # print(len(set(num_rows)) == 1)
    # assert (len(set(num_rows)) == 1)
    lcm = reduce(lambda x, y: (x*y)//gcd(x,y), map(lambda repeat: sum(1 for _ in repeat.rows), repeats), 1)
    # Merge each row
    rows = []
    for line in zip(*map(lambda repeat: _unroll_repeat_n_times(repeat, lcm//sum(1 for _ in repeat.rows)), repeats)):
        print("-----")
        list(map(pretty_print, line))
        print("-----")
        rows.append(_merge_across(*line))
    return RowRepeatExpr(rows, NaturalLit(next(num_rows)//lcm),
                         rows[0].consumes, rows[-1].produces)


@_merge_across.register
def _(*rows: RowExpr) -> KnitExpr:
    # The side of the combined row is the same as the side of the first row
    # in the list. We reverse the other rows before combining them if they
    # have a different side.
    side = rows[0].side
    rows = list(map(lambda row: row if row.side == side else reverse(row, 0),
                    rows))
    # If we're reading RS rows, we need to read the list right-to-left instead of left-to-right.
    if side == Side.Right:
        rows.reverse()
    return RowExpr(
        chain.from_iterable(map(attrgetter("stitches"), rows)), side,
        sum(map(attrgetter("consumes"), rows)),
        sum(map(attrgetter("produces"), rows))
    )

def _unroll_repeat_n_times(repeat: RowRepeatExpr, n: int):
    for i in range(n):
        for row in repeat.rows:
            yield row
