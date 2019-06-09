from __future__ import annotations

from functools import partial, singledispatch
from itertools import accumulate, chain, repeat, starmap, zip_longest
from operator import attrgetter
from typing import Mapping, Optional

from knitscript.astnodes import Block, Call, ExpandingStitchRepeat, \
    FixedBlockRepeat, FixedStitchRepeat, Get, Knittable, NativeFunction, \
    NaturalLit, Node, Pattern, Row, RowRepeat, Side, StitchLit
from knitscript.asttools import ast_map, ast_reduce
from knitscript.stitch import Stitch


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


def prepare_pattern(pattern: Pattern) -> Pattern:
    """
    Interprets and prepares the pattern for exporting.

    :param pattern: the pattern to prepare
    :return: the pattern prepared for exporting
    """
    pattern = _substitute(pattern, pattern.env)
    pattern = _infer_sides(pattern)
    pattern = _infer_counts(pattern)
    pattern = _flatten(pattern)
    pattern = _alternate_sides(
        pattern, Side.Wrong if _starts_with_cast_ons(pattern) else Side.Right
    )
    assert isinstance(pattern, Pattern)
    return pattern


@singledispatch
def enclose(node: Node, env: Mapping[str, Node]) -> Node:
    """
    Encloses patterns in environment, in order to achieve lexical scoping.

    :param node: the AST node to enclose
    :param env: the environment that the pattern should form a closure with
    :return: an AST with environments baked into the patterns
    """
    # noinspection PyTypeChecker
    return ast_map(node, partial(enclose, env=env))


@enclose.register
def _(pattern: Pattern, env: Mapping[str, Node]) -> Node:
    return Pattern(pattern.rows, pattern.params, env,
                   pattern.consumes, pattern.produces)


@singledispatch
def reflect(node: Node) -> Node:
    """
    Reflects the AST horizontally.

    :param node: the AST to reflect
    :return: the reflected AST
    """
    return ast_map(node, reflect)


@reflect.register
def _(row: Row) -> Node:
    return Row(map(reflect, reversed(row.stitches)), row.side,
               row.consumes, row.produces)


@reflect.register
def _(fixed: FixedStitchRepeat) -> Node:
    return FixedStitchRepeat(map(reflect, reversed(fixed.stitches)),
                             fixed.times, fixed.consumes, fixed.produces)


@reflect.register
def _(expanding: ExpandingStitchRepeat) -> Node:
    return ExpandingStitchRepeat(map(reflect, reversed(expanding.stitches)),
                                 expanding.to_last,
                                 expanding.consumes, expanding.produces)


@singledispatch
def _infer_counts(node: Node, available: Optional[int] = None) -> Node:
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
    return ast_map(node, partial(_infer_counts, available=available))


@_infer_counts.register
def _(fixed: FixedStitchRepeat, available: Optional[int] = None) -> Node:
    counted = []
    consumes = 0
    produces = 0
    for stitch in fixed.stitches:
        stitch = _infer_counts(
            stitch,
            available - consumes if available is not None else None
        )
        counted.append(stitch)
        try:
            assert isinstance(stitch, Knittable)
            consumes += stitch.consumes
            produces += stitch.produces
        except TypeError:
            consumes = produces = None

    try:
        return FixedStitchRepeat(counted, fixed.times,
                                 fixed.times.value * consumes,
                                 fixed.times.value * produces)
    except TypeError:
        return FixedStitchRepeat(counted, fixed.times)


@_infer_counts.register
def _(expanding: ExpandingStitchRepeat, available: Optional[int] = None) \
        -> Node:
    if available is None:
        raise InterpretError("ambiguous use of expanding stitch repeat",
                             expanding)
    fixed = _infer_counts(
        FixedStitchRepeat(expanding.stitches, NaturalLit(1)),
        available - expanding.to_last.value
    )
    assert isinstance(fixed, FixedStitchRepeat)
    n = (available - expanding.to_last.value) // fixed.consumes
    return ExpandingStitchRepeat(fixed.stitches, expanding.to_last,
                                 n * fixed.consumes, n * fixed.produces)


@_infer_counts.register
def _(row: Row, available: Optional[int] = None) -> Node:
    counted = _infer_counts.dispatch(FixedStitchRepeat)(row, available)
    return Row(counted.stitches, row.side,
               counted.consumes, counted.produces)


@_infer_counts.register
def _(rep: RowRepeat, available: Optional[int] = None) -> Node:
    counted = []
    for row in rep.rows:
        row = _infer_counts(row, available)
        assert isinstance(row, Knittable)
        counted.append(row)
        available = row.produces
    return RowRepeat(counted, rep.times, counted[0].consumes, available)


# noinspection PyUnusedLocal
@_infer_counts.register
def _(block: Block, available: Optional[int] = None) -> Node:
    if len(block.patterns) == 1:
        counted = [_infer_counts(block.patterns[0], available)]
    else:
        counted = list(map(_infer_counts, block.patterns))
    return Block(counted,
                 sum(map(attrgetter("consumes"), counted)),
                 sum(map(attrgetter("produces"), counted)))


@_infer_counts.register
def _(pattern: Pattern, available: Optional[int] = None) -> Node:
    counted = _infer_counts.dispatch(RowRepeat)(pattern, available)
    return Pattern(counted.rows, pattern.params, pattern.env,
                   counted.consumes, counted.produces)


@_infer_counts.register
def _(rep: FixedBlockRepeat, available: Optional[int] = None) -> Node:
    counted = _infer_counts(rep.block, available)
    assert isinstance(counted, Knittable)
    return FixedBlockRepeat(counted, rep.times,
                            rep.times.value * counted.consumes,
                            rep.times.value * counted.produces)


@singledispatch
def _substitute(node: Node, env: Mapping[str, Node]) -> Node:
    """
    Substitutes all variables and calls in the AST with their equivalent
    expressions.

    :param node: the AST to transform
    :param env: the environment
    :return:
        the transformed expression with all variables and calls substituted out
    """
    # noinspection PyTypeChecker
    return ast_map(node, partial(_substitute, env=env))


@_substitute.register
def _(pattern: Pattern, env: Mapping[str, Node]) -> Node:
    # noinspection PyTypeChecker
    return Pattern(map(partial(_substitute, env=env), pattern.rows),
                   (), pattern.env, pattern.consumes, pattern.produces)


@_substitute.register
def _(get: Get, env: Mapping[str, Node]) -> Node:
    return env[get.name]


@_substitute.register
def _(call: Call, env: Mapping[str, Node]) -> Node:
    target = call.target
    if isinstance(target, Get):
        target = _substitute(target, env)
    # noinspection PyTypeChecker
    args = map(partial(_substitute, env=env), call.args)
    assert isinstance(target, Pattern) or isinstance(target, NativeFunction)
    if isinstance(target, Pattern):
        if len(target.params) != len(call.args):
            raise InterpretError(
                f"called pattern with {len(call.args)} arguments, but " +
                f"expected {len(target.params)}",
                call
            )
        return _substitute(target,
                           {**target.env, **dict(zip(target.params, args))})
    elif isinstance(target, NativeFunction):
        return target.function(*args)


@singledispatch
def _flatten(node: Node, unroll: bool = False) -> Node:
    """
    Flattens blocks, nested patterns, and nested fixed stitch repeats.

    :param node: the AST to transform
    :param unroll:
        whether to unroll row repeat expressions into a sequence of repeated
        rows
    :return: the flattened AST
    """
    # noinspection PyTypeChecker
    return ast_map(node, partial(_flatten, unroll=unroll))


@_flatten.register
def _(fixed: FixedStitchRepeat, unroll: bool = False) -> Node:
    # Cases where the only node a fixed stitch repeat contains is another fixed
    # stitch repeat should be flattened by multiplying the repeat times
    # together, because the unflattened output is confusing.
    first = fixed.stitches[0]
    if (fixed.times.value != 1
            and len(fixed.stitches) == 1
            and isinstance(first, FixedStitchRepeat)):
        # noinspection PyTypeChecker
        return ast_map(
            FixedStitchRepeat(
                first.stitches,
                NaturalLit(first.times.value * fixed.times.value),
                first.consumes * fixed.times.value,
                first.produces * fixed.times.value
            ),
            partial(_flatten, unroll=unroll)
        )
    else:
        # noinspection PyTypeChecker
        return ast_map(fixed, partial(_flatten, unroll=unroll))


@_flatten.register
def _(row_repeat: RowRepeat, unroll: bool = False) -> Node:
    rows = []
    # noinspection PyTypeChecker
    for row in map(partial(_flatten, unroll=unroll), row_repeat.rows):
        if isinstance(row, RowRepeat) and (unroll or row.times.value <= 1):
            rows.extend(chain.from_iterable(repeat(row.rows, row.times.value)))
        else:
            rows.append(row)
    return RowRepeat(rows, row_repeat.times,
                     rows[0].consumes if rows else 0,
                     rows[-1].produces if rows else 0)


@_flatten.register
def _(pattern: Pattern, unroll: bool = False) -> Node:
    flattened = _flatten.dispatch(RowRepeat)(pattern, unroll)
    return Pattern(flattened.rows, pattern.params, pattern.env,
                   flattened.consumes, flattened.produces)


@_flatten.register
def _(block: Block, unroll: bool = False) -> Node:
    if len(block.patterns) > 1:
        # Unroll row repeats if there is more than one pattern in this block.
        # This makes merging across rows much simpler.
        # noinspection PyTypeChecker
        return _merge_across(*map(partial(_flatten, unroll=True),
                                  block.patterns))
    else:
        # noinspection PyTypeChecker
        return _flatten(block.patterns[0], unroll)


@_flatten.register
def _(rep: FixedBlockRepeat, unroll: bool = False) -> Node:
    pattern = _flatten(rep.block, unroll)
    assert isinstance(pattern, Pattern)
    rows = map(
        lambda row: Row(
            [FixedStitchRepeat(row.stitches, rep.times,
                               row.consumes * rep.times.value,
                               row.produces * rep.times.value)],
            row.side,
            row.consumes * rep.times.value, row.produces * rep.times.value
        ),
        pattern.rows
    )
    # noinspection PyTypeChecker
    return Pattern(map(partial(_flatten, unroll=unroll), rows),
                   pattern.params, pattern.env,
                   pattern.consumes, pattern.produces)


# noinspection PyUnusedLocal
@singledispatch
def _reverse(node: Node, before: int) -> Node:
    """
    Reverses the yarn direction of an expression. Assumes the AST has had
    stitches counted.

    :param node: the expression to reverse
    :param before:
        the number of stitches made so far, before this expression, in the
        current row
    :return: the reversed expression
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


# noinspection PyUnusedLocal
@_reverse.register
def _(fixed: FixedStitchRepeat, before: int) -> Node:
    before_acc = accumulate(
        chain([before], map(attrgetter("consumes"), fixed.stitches[:-1]))
    )
    return FixedStitchRepeat(map(_reverse,
                                 reversed(fixed.stitches),
                                 reversed(list(before_acc))),
                             fixed.times, fixed.consumes, fixed.produces)


# noinspection PyUnusedLocal
@_reverse.register
def _(stitch: StitchLit, before: int) -> Node:
    return StitchLit(stitch.value.reverse)


@_reverse.register
def _(expanding: ExpandingStitchRepeat, before: int) -> Node:
    fixed = _reverse(FixedStitchRepeat(expanding.stitches, NaturalLit(1)),
                     before)
    assert isinstance(fixed, FixedStitchRepeat)
    return ExpandingStitchRepeat(fixed.stitches, NaturalLit(before),
                                 expanding.consumes, expanding.produces)


@_reverse.register
def _(row: Row, before: int) -> Node:
    fixed = _reverse(FixedStitchRepeat(row.stitches, row.times,
                                       row.consumes, row.produces),
                     before)
    assert isinstance(fixed, FixedStitchRepeat)
    return Row(fixed.stitches, row.side.flip() if row.side else None,
               fixed.consumes, fixed.produces)


# noinspection PyUnusedLocal
@singledispatch
def _infer_sides(node: Node, side: Side = Side.Right) -> Node:
    """
    Infers the side of each row, assuming that:
     1. Patterns that cast on in the first row start on WS; other patterns
        start on RS.
     2. Rows alternate between RS and WS.

    Rows that have an explicit side already are unchanged.

    :param node: the AST to infer sides in
    :param side: the starting side for the next row
    :return: an AST with row sides filled in
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


# noinspection PyUnusedLocal
@_infer_sides.register
def _(pattern: Pattern, side: Side = Side.Right) -> Node:
    side = Side.Wrong if _starts_with_cast_ons(pattern) else Side.Right
    return Pattern(
        map(_infer_sides, pattern.rows, side.alternate()),
        pattern.params,
        pattern.env
    )


@_infer_sides.register
def _(block: Block, side: Side = Side.Right) -> Node:
    return Block(map(_infer_sides, block.patterns, side.alternate()))


@_infer_sides.register
def _(rep: FixedBlockRepeat, side: Side = Side.Right) -> Node:
    return FixedBlockRepeat(_infer_sides(rep.block, side), rep.times)


@_infer_sides.register
def _(rep: RowRepeat, side: Side = Side.Right) -> Node:
    return RowRepeat(map(_infer_sides, rep.rows, side.alternate()),
                     rep.times)


@_infer_sides.register
def _(row: Row, side: Side = Side.Right) -> Node:
    return Row(row.stitches, side if row.side is None else row.side)


@singledispatch
def _alternate_sides(node: Node, side: Side = Side.Right) -> Node:
    """
    Ensures that every row alternates between right and wrong side, starting
    from the given side.

    :param node: the AST to alternate the sides of
    :param side: the side of the first row
    :return: the AST with every row alternating sides
    """
    # noinspection PyTypeChecker
    return ast_map(node, partial(_alternate_sides, side=side))


@_alternate_sides.register
def _(row: Row, side: Side = Side.Right) -> Node:
    return row if row.side == side else _reverse(row, 0)


@_alternate_sides.register
def _(rep: RowRepeat, side: Side = Side.Right) -> Node:
    return RowRepeat(map(_alternate_sides, rep.rows, side.alternate()),
                     rep.times, rep.consumes, rep.produces)


@_alternate_sides.register
def _(pattern: Pattern, side: Side = Side.Right) -> Node:
    return Pattern(
        _alternate_sides.dispatch(RowRepeat)(pattern, side).rows,
        pattern.params, pattern.env, pattern.consumes, pattern.produces
    )


@singledispatch
def _merge_across(*nodes: Node) -> Knittable:
    raise TypeError(f"unsupported node {type(nodes[0]).__name__}")


@_merge_across.register
def _(*patterns: Pattern) -> Knittable:
    rows = tuple(starmap(_merge_across,
                         zip_longest(*map(attrgetter("rows"), patterns),
                                     fillvalue=Row([], Side.Right, 0, 0))))
    # Pattern calls have already been substituted by this point so the
    # parameters of the combined pattern can be empty.
    return Pattern(rows, (), None, rows[0].consumes, rows[-1].produces)


@_merge_across.register
def _(*rows: Row) -> Knittable:
    # The side of the combined row is the same as the side of the first row
    # in the list. We reverse the other rows before combining them if they
    # have a different side.
    #
    # If we're reading RS rows, we need to read the list right-to-left
    # instead of left-to-right.
    side = rows[0].side
    rows = tuple(map(lambda row: row if row.side == side else _reverse(row, 0),
                     reversed(rows) if side == Side.Right else rows))

    # Update the "to last" value of any expanding stitch repeat in the rows by
    # adding the number of stitches that come after it.
    after = map(lambda i: sum(map(attrgetter("consumes"), rows[i + 1:])),
                range(len(rows)))
    rows = tuple(map(_increase_expanding_repeats, rows, after))

    return Row(
        chain.from_iterable(map(attrgetter("stitches"), rows)), side,
        sum(map(attrgetter("consumes"), rows)),
        sum(map(attrgetter("produces"), rows))
    )


@singledispatch
def _increase_expanding_repeats(node: Node, n: int) -> Node:
    # noinspection PyTypeChecker
    return ast_map(node, partial(_increase_expanding_repeats, n=n))


@_increase_expanding_repeats.register
def _(expanding: ExpandingStitchRepeat, n: int) -> Node:
    return ExpandingStitchRepeat(expanding.stitches,
                                 NaturalLit(expanding.to_last.value + n),
                                 expanding.consumes, expanding.produces)


@singledispatch
def _starts_with_cast_ons(node: Node, acc: bool = True) -> bool:
    return ast_reduce(node, _starts_with_cast_ons, acc)


@_starts_with_cast_ons.register
def _(rep: RowRepeat, acc: bool = True) -> bool:
    return _starts_with_cast_ons(rep.rows[0], acc)


@_starts_with_cast_ons.register
def _(stitch: StitchLit, acc: bool = True) -> bool:
    return acc and stitch.value == Stitch.CAST_ON
