from __future__ import annotations

from dataclasses import replace
from functools import partial, singledispatch, reduce
from itertools import accumulate, chain, starmap, zip_longest
from math import ceil, gcd
from operator import attrgetter
from typing import Callable, Iterable, Iterator, Generator, Mapping, \
    Optional, Sequence, Tuple, TypeVar

from knitscript.astnodes import Block, Call, ExpandingStitchRepeat, \
    FixedBlockRepeat, FixedStitchRepeat, Get, Knittable, NativeFunction, \
    NaturalLit, Node, Pattern, Row, RowRepeat, Side, StitchLit
from knitscript.asttools import Error, ast_map, ast_reduce, to_fixed_repeat
from knitscript.stitch import Stitch

_T = TypeVar("_T")


class InterpretError(Error):
    """
    An error in a KnitScript document that prevents it from being interpreted.
    """


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
    pattern = infer_counts(pattern)
    pattern = _alternate_sides(
        pattern, Side.Wrong if _starts_with_cast_ons(pattern) else Side.Right
    )
    pattern = _combine_stitches(pattern)
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
    return replace(pattern, env=env)


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
def _(get: Get, env: Mapping[str, Node]) -> Node:
    return env[get.name]


@substitute.register
def _(call: Call, env: Mapping[str, Node]) -> Node:
    try:
        result = do_call(call, env)
    except InterpretError as e:
        # Re-raise the error with this node added to the call stack.
        raise InterpretError(e.message, [*e.nodes, call])
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
    return replace(row, stitches=list(map(reflect, reversed(row.stitches))))


@reflect.register
def _(rep: FixedStitchRepeat) -> Node:
    return replace(rep, stitches=list(map(reflect, reversed(rep.stitches))))


@reflect.register
def _(rep: ExpandingStitchRepeat) -> Node:
    return replace(rep, stitches=list(map(reflect, reversed(rep.stitches))))


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
    assert isinstance(target, Pattern) or isinstance(target, NativeFunction)
    if isinstance(target, Pattern):
        if len(target.params) != len(call.args):
            raise InterpretError(
                f"called pattern with {len(call.args)} arguments, but " +
                f"expected {len(target.params)}",
                call
            )
        return substitute(replace(target, params=[]),
                          {**target.env, **dict(zip(target.params, args))})
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
    return replace(
        pattern,
        rows=[RowRepeat(
            rows=[FixedBlockRepeat(
                block=Block(patterns=[pattern],
                            consumes=pattern.consumes,
                            produces=pattern.produces,
                            sources=pattern.sources),
                times=NaturalLit.of(n),
                consumes=pattern.consumes * n, produces=pattern.produces * n,
                sources=pattern.sources
            )],
            times=NaturalLit.of(m),
            consumes=pattern.consumes * n, produces=pattern.produces * n,
            sources=pattern.sources
        )],
        consumes=pattern.consumes * n, produces=pattern.produces * n
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
def _(pattern: Pattern) -> int:
    return count_rows(to_fixed_repeat(pattern))


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
def _(rep: FixedStitchRepeat, available: Optional[int] = None) -> Node:
    counted = []
    consumes = 0
    produces = 0
    for stitch in rep.stitches:
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
        return replace(rep,
                       stitches=counted,
                       consumes=consumes * rep.times.value,
                       produces=produces * rep.times.value)
    except TypeError:
        return replace(rep, stitches=counted)


@infer_counts.register
def _(rep: ExpandingStitchRepeat, available: Optional[int] = None) -> Node:
    if available is None:
        raise InterpretError("ambiguous use of expanding stitch repeat", rep)
    fixed = infer_counts(to_fixed_repeat(rep), available - rep.to_last.value)
    assert isinstance(fixed, FixedStitchRepeat)
    n = (available - rep.to_last.value) // fixed.consumes
    return replace(rep,
                   stitches=fixed.stitches,
                   consumes=fixed.consumes * n,
                   produces=fixed.produces * n)


@infer_counts.register
def _(row: Row, available: Optional[int] = None) -> Node:
    counted = infer_counts(to_fixed_repeat(row), available)
    assert isinstance(counted, FixedStitchRepeat)
    return replace(row,
                   stitches=counted.stitches,
                   consumes=counted.consumes,
                   produces=counted.produces)


@infer_counts.register
def _(rep: RowRepeat, available: Optional[int] = None) -> Node:
    counted = []
    for _ in range(max(1, rep.times.value)):
        for row in rep.rows:
            row = infer_counts(row, available)
            assert isinstance(row, Knittable)
            available = row.produces
            if len(counted) < len(rep.rows):
                counted.append(row)
    return replace(rep,
                   rows=counted,
                   consumes=counted[0].consumes,
                   produces=available)


@infer_counts.register
def _(block: Block, available: Optional[int] = None) -> Node:
    if len(block.patterns) == 1:
        counted = [infer_counts(block.patterns[0], available)]
    else:
        counted = list(map(infer_counts, block.patterns))
    return replace(block,
                   patterns=counted,
                   consumes=sum(map(attrgetter("consumes"), counted)),
                   produces=sum(map(attrgetter("produces"), counted)))


@infer_counts.register
def _(pattern: Pattern, available: Optional[int] = None) -> Node:
    counted = infer_counts(to_fixed_repeat(pattern), available)
    assert isinstance(counted, RowRepeat)
    return replace(pattern,
                   rows=counted.rows,
                   consumes=counted.consumes,
                   produces=counted.produces)


@infer_counts.register
def _(rep: FixedBlockRepeat, available: Optional[int] = None) -> Node:
    counted = infer_counts(rep.block, available)
    assert isinstance(counted, Block)
    return replace(rep,
                   block=counted,
                   consumes=counted.consumes * rep.times.value,
                   produces=counted.produces * rep.times.value)


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
def _(rep: FixedStitchRepeat, unroll: bool = False) -> Node:
    # Cases where the only node a fixed stitch repeat contains is another fixed
    # stitch repeat should be flattened by multiplying the repeat times
    # together, because the unflattened output is confusing.
    if (rep.times.value != 1
            and len(rep.stitches) == 1
            and isinstance(rep.stitches[0], FixedStitchRepeat)):
        first = rep.stitches[0]
        assert isinstance(first, FixedStitchRepeat)
        # noinspection PyTypeChecker
        return ast_map(
            replace(rep,
                    stitches=first.stitches,
                    times=NaturalLit.of(first.times.value * rep.times.value),
                    consumes=first.consumes * rep.times.value,
                    produces=first.produces * rep.times.value),
            partial(_flatten, unroll=unroll)
        )
    else:
        stitches = []
        # noinspection PyTypeChecker
        for stitch in map(partial(_flatten, unroll=unroll), rep.stitches):
            if (isinstance(stitch, FixedStitchRepeat) and
                    stitch.times.value == 1):
                # Un-nest fixed stitch repeats that only repeat once.
                stitches.extend(stitch.stitches)
            else:
                stitches.append(stitch)
        return replace(rep, stitches=stitches)


@_flatten.register
def _(row: Row, unroll: bool = False) -> Node:
    flattened = _flatten(to_fixed_repeat(row), unroll)
    assert isinstance(flattened, FixedStitchRepeat)
    assert flattened.consumes == row.consumes
    assert flattened.produces == row.produces
    return replace(row, stitches=flattened.stitches)


@_flatten.register
def _(rep: RowRepeat, unroll: bool = False) -> Node:
    flattened_rows = []
    # noinspection PyTypeChecker
    for row in map(partial(_flatten, unroll=unroll), rep.rows):
        if isinstance(row, RowRepeat) and (unroll or row.times.value <= 1):
            flattened_rows.extend(_repeat_rows(row.rows, row.times.value))
        elif isinstance(row, Pattern):
            flattened_rows.extend(row.rows)
        else:
            flattened_rows.append(row)
    return replace(rep, rows=flattened_rows)


@_flatten.register
def _(pattern: Pattern, unroll: bool = False) -> Node:
    flattened = _flatten(to_fixed_repeat(pattern), unroll)
    assert isinstance(flattened, RowRepeat)
    assert flattened.consumes == pattern.consumes
    assert flattened.produces == pattern.produces
    return replace(pattern, rows=flattened.rows)


@_flatten.register
def _(block: Block, unroll: bool = False) -> Node:
    # noinspection PyTypeChecker
    return _merge_across(*map(partial(_flatten, unroll=unroll),
                              block.patterns))


@_flatten.register
def _(rep: FixedBlockRepeat, unroll: bool = False) -> Node:
    # TODO: Can we avoid calling _flatten twice here?
    pattern = _flatten(_repeat_across(_flatten(rep.block, unroll),
                                      rep.times.value), unroll)
    assert isinstance(pattern, Pattern)
    return replace(pattern,
                   # TODO: Why is this necessary?
                   consumes=pattern.consumes * rep.times.value,
                   produces=pattern.produces * rep.times.value)


@singledispatch
def _repeat_across(node: Node, times: int) -> Node:
    # noinspection PyTypeChecker
    return ast_map(node, partial(_repeat_across, times=times))


@_repeat_across.register
def _(row: Row, times: int) -> Node:
    return replace(row,
                   stitches=[FixedStitchRepeat(stitches=row.stitches,
                                               times=NaturalLit.of(times),
                                               consumes=row.consumes * times,
                                               produces=row.produces * times,
                                               sources=row.sources)],
                   consumes=row.consumes * times,
                   produces=row.produces * times)


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
def _(rep: FixedStitchRepeat, before: int) -> Node:
    before_acc = accumulate(
        chain([before], map(attrgetter("consumes"), rep.stitches[:-1]))
    )
    return replace(rep, stitches=list(map(_reverse,
                                          reversed(rep.stitches),
                                          reversed(list(before_acc)))))


# noinspection PyUnusedLocal
@_reverse.register
def _(stitch: StitchLit, before: int) -> Node:
    if stitch.value.reverse is not None:
        return replace(stitch, value=stitch.value.reverse)
    else:
        raise InterpretError(f"Cannot reverse stitch {stitch.value}", stitch)


@_reverse.register
def _(rep: ExpandingStitchRepeat, before: int) -> Node:
    fixed = _reverse(to_fixed_repeat(rep), before)
    assert isinstance(fixed, FixedStitchRepeat)
    return replace(rep, stitches=fixed.stitches, to_last=NaturalLit.of(before))


@_reverse.register
def _(row: Row, before: int) -> Node:
    fixed = _reverse(to_fixed_repeat(row), before)
    assert isinstance(fixed, FixedStitchRepeat)
    assert fixed.consumes == row.consumes
    assert fixed.produces == row.produces
    return replace(row,
                   stitches=fixed.stitches,
                   side=row.side.flip() if row.side else None)


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
    return replace(
        pattern,
        rows=list(map(_infer_sides, pattern.rows, side.alternate()))
    )


@_infer_sides.register
def _(block: Block, side: Side = Side.Right) -> Node:
    return replace(
        block,
        patterns=list(map(_infer_sides, block.patterns, side.alternate()))
    )


@_infer_sides.register
def _(rep: FixedBlockRepeat, side: Side = Side.Right) -> Node:
    return replace(rep, block=_infer_sides(rep.block, side))


@_infer_sides.register
def _(rep: RowRepeat, side: Side = Side.Right) -> Node:
    return replace(rep,
                   rows=list(map(_infer_sides, rep.rows, side.alternate())))


@_infer_sides.register
def _(row: Row, side: Side = Side.Right) -> Node:
    if row.side is None or row.inferred:
        return replace(row, side=side, inferred=True)
    else:
        return row


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
    rows = []
    for row in rep.rows:
        # TODO: This is somewhat inefficient.
        num_rows = count_rows(row)
        rows.append(_alternate_sides(row, side))
        if num_rows % 2 != 0:
            side = side.flip()
    return replace(rep, rows=rows)


@_alternate_sides.register
def _(pattern: Pattern, side: Side = Side.Right) -> Node:
    rep = _alternate_sides(to_fixed_repeat(pattern), side)
    assert isinstance(rep, RowRepeat)
    assert rep.consumes == pattern.consumes
    assert rep.produces == pattern.produces
    return replace(pattern, rows=rep.rows)


@singledispatch
def _merge_across(*nodes: Node) -> Knittable:
    raise TypeError(f"unsupported node {type(nodes[0]).__name__}")


@_merge_across.register
def _(*patterns: Pattern) -> Knittable:
    rep = _merge_across(*map(to_fixed_repeat, patterns))
    assert isinstance(rep, RowRepeat)
    # Pattern calls have already been substituted by this point so the
    # parameters of the combined pattern can be empty.
    return Pattern(rows=rep.rows, params=[], env=None,
                   consumes=rep.consumes, produces=rep.produces,
                   sources=list(_flat_map(attrgetter("sources"), patterns)))


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
        return RowRepeat(rows=rows,
                         times=NaturalLit.of(1),
                         consumes=rows[0].consumes, produces=rows[-1].produces,
                         sources=list(_flat_map(attrgetter("sources"), reps)))

    # Find the smallest number of rows that all row repeats can be expanded to.
    num_rows = _lcm(*map(lambda rep: sum(map(count_rows, rep.rows)), reps))

    def expand(rep: RowRepeat) -> Iterator[Node]:
        times = min(rep.times.value,
                    num_rows // sum(map(count_rows, rep.rows)))
        return _repeat_rows(rep.rows, times)

    rows = list(starmap(_merge_across, _padded_zip(*map(expand, reps))))
    return RowRepeat(
        rows=rows,
        times=NaturalLit.of(ceil(max(map(count_rows, reps)) / num_rows)),
        consumes=rows[0].consumes, produces=rows[-1].produces,
        sources=list(_flat_map(attrgetter("sources"), reps))
    )


@_merge_across.register
def _(*rows: Row) -> Knittable:
    # The side of the combined row is the same as the side of the first row
    # in the list. We reverse the other rows before combining them if they
    # have a different side.
    #
    # If we're reading RS rows, we need to read the list right-to-left
    # instead of left-to-right.
    side = rows[0].side
    rows = list(map(lambda row: row if row.side == side else _reverse(row, 0),
                    reversed(rows) if side == Side.Right else rows))

    # Update the "to last" value of any expanding stitch repeat in the rows by
    # adding the number of stitches that come after it.
    after = map(lambda i: sum(map(attrgetter("consumes"), rows[i + 1:])),
                range(len(rows)))
    rows = list(map(_increase_expanding_repeats, rows, after))

    # noinspection PyUnresolvedReferences
    return Row(
        stitches=list(chain.from_iterable(map(attrgetter("stitches"), rows))),
        side=side, inferred=rows[0].inferred,
        consumes=sum(map(attrgetter("consumes"), rows)),
        produces=sum(map(attrgetter("produces"), rows)),
        sources=list(_flat_map(attrgetter("sources"), rows))
    )


@singledispatch
def _increase_expanding_repeats(node: Node, n: int) -> Node:
    # noinspection PyTypeChecker
    return ast_map(node, partial(_increase_expanding_repeats, n=n))


@_increase_expanding_repeats.register
def _(expanding: ExpandingStitchRepeat, n: int) -> Node:
    # noinspection PyTypeChecker
    return replace(
        expanding,
        stitches=list(map(partial(_increase_expanding_repeats, n=n),
                          expanding.stitches)),
        to_last=NaturalLit.of(expanding.to_last.value + n),
    )


@singledispatch
def _starts_with_cast_ons(node: Node, acc: bool = True) -> bool:
    return ast_reduce(node, _starts_with_cast_ons, acc)


@_starts_with_cast_ons.register
def _(pattern: Pattern, acc: bool = True) -> bool:
    return _starts_with_cast_ons(pattern.rows[0], acc)


@_starts_with_cast_ons.register
def _(rep: RowRepeat, acc: bool = True) -> bool:
    return _starts_with_cast_ons(rep.rows[0], acc)


@_starts_with_cast_ons.register
def _(stitch: StitchLit, acc: bool = True) -> bool:
    return acc and stitch.value == Stitch.CAST_ON


def _padded_zip(*rows: Node) -> Iterable[Sequence[Node]]:
    return zip_longest(*rows,
                       fillvalue=Row(stitches=[],
                                     side=Side.Right, inferred=False,
                                     consumes=0, produces=0,
                                     sources=[]))


def _lcm(*nums: int) -> int:
    return reduce(lambda x, y: x * y // gcd(x, y), nums, 1)


@singledispatch
def _combine_stitches(node: Node) -> Node:
    return ast_map(node, _combine_stitches)


@_combine_stitches.register
def _(rep: FixedStitchRepeat) -> Node:
    # noinspection PyUnusedLocal
    @singledispatch
    def get_stitch(node: Node) -> Tuple[Stitch, int]:
        raise TypeError()

    @get_stitch.register
    def _(stitch: StitchLit) -> Tuple[Stitch, int]:
        return stitch.value, 1

    @get_stitch.register
    def _(rep: FixedStitchRepeat) -> Tuple[Stitch, int]:
        if len(rep.stitches) != 1:
            raise ValueError()
        return rep.stitches[0].value, rep.times.value

    def combine(acc, node):
        try:
            current_stitch, current_times = get_stitch(node)
            last_stitch, last_times = get_stitch(acc[-1])
        except (IndexError, TypeError, ValueError):
            return acc + [node]
        if current_stitch != last_stitch:
            return acc + [node]

        times = current_times + last_times
        return acc[:-1] + [
            FixedStitchRepeat(
                stitches=[StitchLit(value=current_stitch,
                                    consumes=current_stitch.consumes,
                                    produces=current_stitch.produces,
                                    sources=acc[-1].sources + node.sources)],
                times=NaturalLit.of(times),
                consumes=current_stitch.consumes * times,
                produces=current_stitch.produces * times,
                sources=acc[-1].sources + node.sources
            )
        ]

    # noinspection PyTypeChecker
    return replace(
        rep,
        stitches=reduce(combine, map(_combine_stitches, rep.stitches), [])
    )


@_combine_stitches.register
def _(rep: ExpandingStitchRepeat) -> Node:
    fixed = _combine_stitches(to_fixed_repeat(rep))
    assert isinstance(fixed, FixedStitchRepeat)
    return replace(rep, stitches=fixed.stitches)


@_combine_stitches.register
def _(row: Row) -> Node:
    fixed = _combine_stitches(to_fixed_repeat(row))
    assert isinstance(fixed, FixedStitchRepeat)
    assert fixed.consumes == row.consumes
    assert fixed.produces == row.produces
    return replace(row, stitches=fixed.stitches)


def _flat_map(function: Callable[..., Iterable[_T]], *iterables) \
        -> Iterator[_T]:
    return chain.from_iterable(map(function, *iterables))


def _repeat_rows(rows: Sequence[Node], times: int) \
        -> Generator[Node, None, None]:
    side = _starting_side(rows[0])
    for _ in range(times):
        for row in rows:
            yield row
        if len(rows) % 2 != 0:
            # If there are an odd number of rows in a row repeat, the rows
            # should not be reversed every other iteration. To prevent this,
            # infer the side of every row again after flipping the starting
            # side.
            side = side.flip()
            rows = list(map(_infer_sides, rows, side.alternate()))


@singledispatch
def _starting_side(node: Node) -> Side:
    raise TypeError(f"unsupported node {type(node).__name__}")


@_starting_side.register
def _(rep: RowRepeat) -> Side:
    return _starting_side(rep.rows[0])


@_starting_side.register
def _(row: Row) -> Side:
    return row.side
