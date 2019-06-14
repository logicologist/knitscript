from functools import singledispatch
from operator import attrgetter
from typing import Generator, Sequence

from knitscript.astnodes import ExpandingStitchRepeat, FixedStitchRepeat, \
    Knittable, Node, Pattern, RowRepeat, Row, StitchLit
from knitscript.asttools import to_fixed_repeat
from knitscript.stitch import Stitch


class KnitError:
    """Describes a knitting error in a pattern."""

    def __init__(self, message: str, node: Node) -> None:
        """
        Creates a new description of a knitting error in a pattern.

        :param message: a message describing the error
        :param node: the node the error occurred at
        """
        self._message = message
        self._node = node

    @property
    def message(self) -> str:
        """A message describing the error."""
        return self._message

    @property
    def node(self) -> Node:
        """The node the error occurred at."""
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


def verify_pattern(pattern: Pattern) -> Generator[KnitError, None, None]:
    """
    Checks the correctness of stitch counts in the pattern.

    :param pattern: the pattern to verify
    :return: a generator producing all of the errors in the pattern, if any
    """
    yield from verify_counts(pattern, 0)
    assert isinstance(pattern, Knittable)
    if pattern.consumes != 0:
        yield KnitError(
            f"expected {pattern.consumes} stitches to be cast on", pattern
        )
    if pattern.produces != 0:
        yield KnitError(
            f"expected {pattern.produces} stitches to be bound off", pattern
        )
    yield from _verify_psso(pattern)
    yield from _verify_make(pattern)


# noinspection PyUnusedLocal
@singledispatch
def verify_counts(node: Node, available: int) \
        -> Generator[KnitError, None, None]:
    """
    Checks stitch counts for consistency, and verifies that every row has
    enough stitches available and doesn't leave any stitches left over.

    :param node: the AST to verify the stitch counts of
    :param available: the number of stitches remaining in the current row
    :return: a generator producing all of the errors in the pattern, if any
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


@verify_counts.register
def _(stitch: StitchLit, available: int) -> Generator[KnitError, None, None]:
    yield from _at_least(stitch.consumes, available, stitch)


@verify_counts.register
def _(fixed: FixedStitchRepeat, available: int) \
        -> Generator[KnitError, None, None]:
    consumes = 0
    produces = 0
    for stitch in fixed.stitches:
        yield from verify_counts(stitch, available - consumes)
        assert isinstance(stitch, Knittable)
        consumes += stitch.consumes
        produces += stitch.produces
    if fixed.times.value > 1:
        yield from _at_least(fixed.times.value * consumes, available, fixed)


@verify_counts.register
def _(expanding: ExpandingStitchRepeat, available: int) \
        -> Generator[KnitError, None, None]:
    yield from verify_counts(to_fixed_repeat(expanding),
                             available - expanding.to_last.value)
    n = (available - expanding.to_last.value) // expanding.consumes
    yield from _exactly(n * expanding.consumes,
                        available - expanding.to_last.value,
                        expanding)


@verify_counts.register
def _(row: Row, available: int) -> Generator[KnitError, None, None]:
    yield from verify_counts(to_fixed_repeat(row), available)


@verify_counts.register
def _(repeat: RowRepeat, available: int) -> Generator[KnitError, None, None]:
    start = available
    for row in repeat.rows:
        yield from verify_counts(row, available)
        assert isinstance(row, Knittable)
        yield from _exactly(row.consumes, available, row)
        available = row.produces
    if repeat.times.value > 1:
        yield from _exactly(start, available, repeat)


@verify_counts.register
def _(pattern: Pattern, available: int) -> Generator[KnitError, None, None]:
    yield from verify_counts(to_fixed_repeat(pattern), available)


def _at_least(expected: int, actual: int, node: Node) \
        -> Generator[KnitError, None, None]:
    if expected > actual:
        yield KnitError(
            f"expected {expected} stitches, but only {actual} are available"
            if actual > 0
            else f"expected {expected} stitches, but none are available",
            node
        )


def _exactly(expected: int, actual: int, node: Node) \
        -> Generator[KnitError, None, None]:
    yield from _at_least(expected, actual, node)
    if expected < actual:
        yield KnitError(f"{actual - expected} stitches left over", node)


@singledispatch
def _unroll_row(node: Node) -> Sequence:
    """
    Turns a row into a list of stitches.

    :param node: the node to unroll.
    :return: a list of stitches.
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


@_unroll_row.register
def _(row: Row) -> Sequence:
    return [item for st in row.stitches for item in _unroll_row(st)]


@_unroll_row.register
def _(fixed: FixedStitchRepeat) -> Sequence:
    acc = []
    for _ in range(fixed.times.value):
        acc += [item for st in fixed.stitches for item in _unroll_row(st)]
    return acc


@_unroll_row.register
def _(expanding: ExpandingStitchRepeat) -> Sequence:
    times = expanding.consumes // \
            sum(map(attrgetter("consumes"), expanding.stitches))
    acc = []
    for _ in range(times):
        acc += [item for st in expanding.stitches for item in _unroll_row(st)]
    return acc


@_unroll_row.register
def _(stitch: StitchLit) -> Sequence:
    return [stitch.value]


def _unroll_slip(stitch: Stitch) -> Sequence[Stitch]:
    if stitch == Stitch.SLIP:
        return [Stitch.SLIP]
    elif stitch == Stitch.SLIP_PURLWISE:
        return [Stitch.SLIP]
    elif stitch == Stitch.SLIP_2_KNITWISE:
        return [Stitch.SLIP, Stitch.SLIP]
    elif stitch == Stitch.SLIP_2_PURLWISE:
        return [Stitch.SLIP, Stitch.SLIP]
    else:
        return [stitch]


@singledispatch
def _verify_psso(node: Node) -> Generator[KnitError, None, None]:
    """
    Verifies that every psso is preceded by a slipped stitch.

    :param node: the expression to verify.
    :return: a generator producing all errors of this kind, if any.
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


@_verify_psso.register
def _(pattern: Pattern) -> Generator[KnitError, None, None]:
    return _verify_psso(to_fixed_repeat(pattern))


@_verify_psso.register
def _(rep: RowRepeat) -> Generator[KnitError, None, None]:
    for row in rep.rows:
        yield from _verify_psso(row)


@_verify_psso.register
def _(row: Row) -> Generator[KnitError, None, None]:
    stitches = list(_unroll_row(row))
    stitches = [item for st in stitches for item in _unroll_slip(st)]
    num_stitches = len(stitches)
    i = 0
    for _ in range(num_stitches):
        if stitches[i] == Stitch.PSSO:
            # attempt to remove the last slip
            if stitches[i-1] == Stitch.SLIP:
                yield KnitError("PSSO without stitch to pass over", row)
            try:
                st_before = stitches[:i]
                st_before.reverse()
                st_before.remove(Stitch.SLIP)
                i -= 1
                st_before.reverse()
                stitches = st_before + stitches[i+1:]
            except ValueError:
                yield KnitError("PSSO without SLIP", row)
        i += 1


@singledispatch
def _verify_make(node: Node) -> Generator[KnitError, None, None]:
    """
    Verifies that no make-1 appears at the beginning of a row.

    :param node: the expression to verify.
    :return: a generator procuding all errors of this kind, if any.
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


@_verify_make.register
def _(pattern: Pattern) -> Generator[KnitError, None, None]:
    return _verify_make(to_fixed_repeat(pattern))


@_verify_make.register
def _(rep: RowRepeat) -> Generator[KnitError, None, None]:
    for row in rep.rows:
        yield from _verify_make(row)


@_verify_make.register
def _(row: Row) -> Generator[KnitError, None, None]:
    stitches = list(_unroll_row(row))
    if stitches[0] == Stitch.MAKE_1_LEFT or stitches[0] == Stitch.MAKE_1_RIGHT:
        yield KnitError("Make 1 on first stitch of row", row)

