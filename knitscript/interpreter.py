from __future__ import annotations

from functools import partial, singledispatch, reduce
from itertools import accumulate, chain, repeat, starmap, zip_longest
from math import ceil, gcd
from operator import attrgetter
from typing import Iterable, Iterator, Mapping, Optional, Sequence

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
        if self.node.line is not None:
            position = (f"{type(self.node).__name__} at " +
                        f"line {self.node.line}, " +
                        f"column {self.node.column} " +
                        f"in {self.node.file}")
        else:
            position = f"merged {type(self.node).__name__}"
        return f"{self.message} ({position})"


def prepare_pattern(pattern: Pattern) -> Pattern:
    """
    Interprets and prepares the pattern for exporting.

    :param pattern: the pattern to prepare
    :return: the pattern prepared for exporting
    """
    pattern = substitute(pattern, pattern.env)
    pattern = _infer_sides(pattern)
    pattern = infer_counts(pattern)
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
                   pattern.consumes, pattern.produces,
                   pattern.line, pattern.column, pattern.file)


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
def _(pattern: Pattern, env: Mapping[str, Node]) -> Node:
    # noinspection PyTypeChecker
    return Pattern(map(partial(substitute, env=env), pattern.rows),
                   (), pattern.env, pattern.consumes, pattern.produces,
                   pattern.line, pattern.column, pattern.file)


@substitute.register
def _(get: Get, env: Mapping[str, Node]) -> Node:
    return env[get.name]


@substitute.register
def _(call: Call, env: Mapping[str, Node]) -> Node:
    result = do_call(call, env)
    assert result is not None
    return result


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
               row.consumes, row.produces, row.line, row.column, row.file)


@reflect.register
def _(fixed: FixedStitchRepeat) -> Node:
    return FixedStitchRepeat(map(reflect, reversed(fixed.stitches)),
                             fixed.times, fixed.consumes, fixed.produces,
                             fixed.line, fixed.column, fixed.file)


@reflect.register
def _(expanding: ExpandingStitchRepeat) -> Node:
    return ExpandingStitchRepeat(map(reflect, reversed(expanding.stitches)),
                                 expanding.to_last,
                                 expanding.consumes, expanding.produces,
                                 expanding.line, expanding.column,
                                 expanding.file)


def do_call(call: Call, env: Mapping[str, Node]) -> Optional[Node]:
    """
    Evaluates a call node and returns the result.

    :param call: the call node to evaluate
    :param env: the environment to use
    :return: the result of the call
    """
    target = call.target
    if isinstance(target, Get):
        target = substitute(target, env)
    # noinspection PyTypeChecker
    args = map(partial(substitute, env=env), call.args)
    assert isinstance(target, Pattern) or isinstance(target,
                                                     NativeFunction)
    if isinstance(target, Pattern):
        if len(target.params) != len(call.args):
            raise InterpretError(
                f"called pattern with {len(call.args)} arguments, but " +
                f"expected {len(target.params)}",
                call
            )
        return substitute(target,
                          {**target.env,
                           **dict(zip(target.params, args))})
    elif isinstance(target, NativeFunction):
        return target.function(*args)


def fill(pattern: Pattern, width: int, height: int) -> Node:
    """
    Repeats a pattern horizontally and vertically to fill a box.

    :param pattern: the pattern to repeat
    :param width: the width of the box (number of stitches)
    :param height: the height of the box (number of rows)
    :return: the repeated pattern
    """
    pattern = infer_counts(pattern)
    assert isinstance(pattern, Pattern)
    stitches = max(map(attrgetter("consumes"), pattern.rows))
    rows = count_rows(pattern)
    if (width % stitches != 0 or width < stitches or
            height % rows != 0 or height < rows):
        raise InterpretError(
            f"{stitches}×{rows} pattern does not fit evenly into " +
            f"{width}×{height} fill box",
            pattern
        )
    n = width // stitches
    m = height // rows
    return Pattern(
        [RowRepeat([FixedBlockRepeat(Block([pattern],
                                           pattern.consumes,
                                           pattern.produces),
                                     NaturalLit(n),
                                     pattern.consumes * n,
                                     pattern.produces * n)],
                   NaturalLit(m), pattern.consumes * n, pattern.produces * n)],
        pattern.params, pattern.env, pattern.consumes * n, pattern.produces * n
    )


@singledispatch
def count_rows(node: Node) -> int:
    """
    Recursively counts rows in the subexpression.

    :param node: the expression to count rows of.
    :return: the number of rows in the expression.
    """
    return ast_map(node, count_rows)


@count_rows.register
def _(row: Row) -> int:
    return 1


@count_rows.register
def _(rep: RowRepeat) -> int:
    return sum(map(count_rows, rep.rows)) * rep.times.value


@count_rows.register
def _(block: Block) -> int:
    return max(map(count_rows, block.patterns))


@count_rows.register
def _(rep: FixedBlockRepeat) -> int:
    return count_rows(rep.block)


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
def _(fixed: FixedStitchRepeat, available: Optional[int] = None) -> Node:
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
            assert isinstance(stitch, Knittable)
            consumes += stitch.consumes
            produces += stitch.produces
        except TypeError:
            consumes = produces = None

    try:
        return FixedStitchRepeat(counted, fixed.times,
                                 fixed.times.value * consumes,
                                 fixed.times.value * produces,
                                 fixed.line, fixed.column, fixed.file)
    except TypeError:
        return FixedStitchRepeat(counted, fixed.times,
                                 line=fixed.line, column=fixed.column,
                                 file=fixed.file)


@infer_counts.register
def _(expanding: ExpandingStitchRepeat, available: Optional[int] = None) \
        -> Node:
    if available is None:
        raise InterpretError("ambiguous use of expanding stitch repeat",
                             expanding)
    fixed = infer_counts(
        FixedStitchRepeat(expanding.stitches, NaturalLit(1)),
        available - expanding.to_last.value
    )
    assert isinstance(fixed, FixedStitchRepeat)
    n = (available - expanding.to_last.value) // fixed.consumes
    return ExpandingStitchRepeat(fixed.stitches, expanding.to_last,
                                 n * fixed.consumes, n * fixed.produces,
                                 expanding.line, expanding.column,
                                 expanding.file)


@infer_counts.register
def _(row: Row, available: Optional[int] = None) -> Node:
    counted = infer_counts.dispatch(FixedStitchRepeat)(row, available)
    return Row(counted.stitches, row.side,
               counted.consumes, counted.produces,
               row.line, row.column, row.file)


@infer_counts.register
def _(rep: RowRepeat, available: Optional[int] = None) -> Node:
    counted = []
    for row in rep.rows:
        row = infer_counts(row, available)
        assert isinstance(row, Knittable)
        counted.append(row)
        available = row.produces
    return RowRepeat(counted, rep.times, counted[0].consumes, available,
                     rep.line, rep.column, rep.file)


# noinspection PyUnusedLocal
@infer_counts.register
def _(block: Block, available: Optional[int] = None) -> Node:
    if len(block.patterns) == 1:
        counted = [infer_counts(block.patterns[0], available)]
    else:
        counted = list(map(infer_counts, block.patterns))
    return Block(counted,
                 sum(map(attrgetter("consumes"), counted)),
                 sum(map(attrgetter("produces"), counted)),
                 block.line, block.column, block.file)


@infer_counts.register
def _(pattern: Pattern, available: Optional[int] = None) -> Node:
    counted = infer_counts.dispatch(RowRepeat)(pattern, available)
    return Pattern(counted.rows, pattern.params, pattern.env,
                   counted.consumes, counted.produces,
                   pattern.line, pattern.column, pattern.file)


@infer_counts.register
def _(rep: FixedBlockRepeat, available: Optional[int] = None) -> Node:
    counted = infer_counts(rep.block, available)
    assert isinstance(counted, Knittable)
    return FixedBlockRepeat(counted, rep.times,
                            rep.times.value * counted.consumes,
                            rep.times.value * counted.produces,
                            rep.line, rep.column, rep.file)


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
    if (fixed.times.value != 1
            and len(fixed.stitches) == 1
            and isinstance(fixed.stitches[0], FixedStitchRepeat)):
        first = fixed.stitches[0]
        assert isinstance(first, FixedStitchRepeat)
        # noinspection PyTypeChecker
        return ast_map(
            FixedStitchRepeat(
                first.stitches,
                NaturalLit(first.times.value * fixed.times.value),
                first.consumes * fixed.times.value,
                first.produces * fixed.times.value,
                fixed.line, fixed.column, fixed.file
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
                     rows[-1].produces if rows else 0,
                     row_repeat.line, row_repeat.column, row_repeat.file)


@_flatten.register
def _(pattern: Pattern, unroll: bool = False) -> Node:
    flattened = _flatten.dispatch(RowRepeat)(pattern, unroll)
    return Pattern(flattened.rows, pattern.params, pattern.env,
                   flattened.consumes, flattened.produces,
                   pattern.line, pattern.column, pattern.file)


@_flatten.register
def _(block: Block, unroll: bool = False) -> Node:
    # noinspection PyTypeChecker
    return _merge_across(*map(partial(_flatten, unroll=unroll),
                              block.patterns))


@_flatten.register
def _(rep: FixedBlockRepeat, unroll: bool = False) -> Node:
    pattern = _flatten(rep.block, unroll)
    assert isinstance(pattern, Pattern)
    rows = map(
        lambda row: Row(
            [FixedStitchRepeat(row.stitches, rep.times,
                               row.consumes * rep.times.value,
                               row.produces * rep.times.value,
                               row.line, row.column, row.file)],
            row.side,
            row.consumes * rep.times.value, row.produces * rep.times.value
        ),
        pattern.rows
    )
    # noinspection PyTypeChecker
    return Pattern(map(partial(_flatten, unroll=unroll), rows),
                   pattern.params, pattern.env,
                   pattern.consumes, pattern.produces,
                   pattern.line, pattern.column, pattern.file)


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
                             fixed.times, fixed.consumes, fixed.produces,
                             fixed.line, fixed.column, fixed.file)


# noinspection PyUnusedLocal
@_reverse.register
def _(stitch: StitchLit, before: int) -> Node:
    new_stitch = stitch.value.reverse
    if new_stitch is not None:
        return StitchLit(new_stitch, stitch.line, stitch.column, stitch.file)
    else:
        raise InterpretError(stitch,
                             "Cannot reverse stitch " + str(stitch.value))


@_reverse.register
def _(expanding: ExpandingStitchRepeat, before: int) -> Node:
    fixed = _reverse(FixedStitchRepeat(expanding.stitches, NaturalLit(1)),
                     before)
    assert isinstance(fixed, FixedStitchRepeat)
    return ExpandingStitchRepeat(fixed.stitches, NaturalLit(before),
                                 expanding.consumes, expanding.produces,
                                 expanding.line, expanding.column,
                                 expanding.file)


@_reverse.register
def _(row: Row, before: int) -> Node:
    fixed = _reverse(FixedStitchRepeat(row.stitches, row.times,
                                       row.consumes, row.produces),
                     before)
    assert isinstance(fixed, FixedStitchRepeat)
    return Row(fixed.stitches, row.side.flip() if row.side else None,
               fixed.consumes, fixed.produces, row.line, row.column, row.file)


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
        pattern.params, pattern.env,
        pattern.consumes, pattern.produces,
        pattern.line, pattern.column, pattern.file
    )


@_infer_sides.register
def _(block: Block, side: Side = Side.Right) -> Node:
    return Block(map(_infer_sides, block.patterns, side.alternate()),
                 block.consumes, block.produces,
                 block.line, block.column, block.file)


@_infer_sides.register
def _(rep: FixedBlockRepeat, side: Side = Side.Right) -> Node:
    return FixedBlockRepeat(_infer_sides(rep.block, side), rep.times,
                            rep.consumes, rep.produces,
                            rep.line, rep.column, rep.file)


@_infer_sides.register
def _(rep: RowRepeat, side: Side = Side.Right) -> Node:
    return RowRepeat(map(_infer_sides, rep.rows, side.alternate()), rep.times,
                     rep.consumes, rep.produces,
                     rep.line, rep.column, rep.file)


@_infer_sides.register
def _(row: Row, side: Side = Side.Right) -> Node:
    return Row(row.stitches, side if row.side is None else row.side,
               row.consumes, row.produces,
               row.line, row.column, row.file)


@singledispatch
def _alternate_sides(node: Node, side: Side = Side.Right) -> Node:
    """
    Ensures that every row alternates between right and wrong side, starting
    from the given side.

    :param node: the AST to alternate the sides of
    :param side: the side of the first row
    :return: (1) the AST with every row alternating sides, and
    (2) the side that the next row should be on
    """
    # noinspection PyTypeChecker
    return ast_map(node, partial(_alternate_sides, side=side))


@_alternate_sides.register
def _(row: Row, side: Side = Side.Right) -> Node:
    return row if row.side == side else _reverse(row, 0)


@_alternate_sides.register
def _(rep: RowRepeat, side: Side = Side.Right) -> Node:
    new_rows = []
    for row in rep.rows:
        num_rows = count_rows(row) # TODO this is somewhat inefficient
        new_rows.append(_alternate_sides(row, side))
        if num_rows % 2: # num_rows is odd
            side = side.flip()
    return RowRepeat(new_rows, rep.times, rep.consumes, rep.produces,
                     rep.line, rep.column, rep.file)


@_alternate_sides.register
def _(pattern: Pattern, side: Side = Side.Right) -> Node:
    new_patt = _alternate_sides.dispatch(RowRepeat)(pattern, side)
    return Pattern(
        new_patt.rows, pattern.params, pattern.env, 
        pattern.consumes, pattern.produces,
        pattern.line, pattern.column, pattern.file
    )


@singledispatch
def _merge_across(*nodes: Node) -> Knittable:
    raise TypeError(f"unsupported node {type(nodes[0]).__name__}")


@_merge_across.register
def _(*patterns: Pattern) -> Knittable:
    rep = _merge_across.dispatch(RowRepeat)(*patterns)
    # Pattern calls have already been substituted by this point so the
    # parameters of the combined pattern can be empty.
    return Pattern(rep.rows, (), None, rep.consumes, rep.produces)


@_merge_across.register
def _(*reps: RowRepeat) -> Knittable:
    if not all(map(lambda item: len(set(map(type, item))) == 1,
                   _padded_zip(*map(attrgetter("rows"), reps)))):
        # Unroll all row repeats if we see a row and a row repeat side-by-side.
        # There may be a smarter way to do it where we only unroll the
        # misplaced row repeat instead of all of them, but that's more
        # complicated. :(
        #
        # noinspection PyTypeChecker
        rows = list(
            starmap(_merge_across,
                    _padded_zip(*map(attrgetter("rows"),
                                     map(partial(_flatten, unroll=True),
                                         reps))))
        )
        return RowRepeat(rows, NaturalLit(1),
                         rows[0].consumes, rows[-1].produces)

    # Find the smallest number of rows that all row repeats can be expanded to.
    num_rows = _lcm(*map(lambda rep: sum(map(count_rows, rep.rows)), reps))

    def expand(rep: RowRepeat) -> Iterator[Node]:
        times = min(rep.times.value,
                    num_rows // sum(map(count_rows, rep.rows)))
        return chain.from_iterable(repeat(rep.rows, times))

    rows = list(starmap(_merge_across, _padded_zip(*map(expand, reps))))
    return RowRepeat(rows,
                     NaturalLit(ceil(max(map(count_rows, reps)) / num_rows)),
                     rows[0].consumes, rows[-1].produces)


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
                                 expanding.consumes, expanding.produces,
                                 expanding.line, expanding.column,
                                 expanding.file)


@singledispatch
def _starts_with_cast_ons(node: Node, acc: bool = True) -> bool:
    return ast_reduce(node, _starts_with_cast_ons, acc)


@_starts_with_cast_ons.register
def _(rep: RowRepeat, acc: bool = True) -> bool:
    return _starts_with_cast_ons(rep.rows[0], acc)


@_starts_with_cast_ons.register
def _(stitch: StitchLit, acc: bool = True) -> bool:
    return acc and stitch.value == Stitch.CAST_ON


def _padded_zip(*rows: Node) -> Iterable[Sequence[Node]]:
    return zip_longest(*rows, fillvalue=Row([], Side.Right, 0, 0))


def _lcm(*nums: int) -> int:
    return reduce(lambda x, y: (x * y) // gcd(x, y), nums, 1)
