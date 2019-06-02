from abc import ABC
from functools import singledispatch, wraps
from typing import Any, Callable, Iterable

from knitscript.astnodes import ExpandingStitchRepeatExpr, \
    FixedStitchRepeatExpr, KnitExpr, NaturalLit, Node, PatternExpr, \
    RowRepeatExpr, StitchLit
from knitscript.interpreter import infer_counts


class Knitability(ABC):
    """Represents the knitability of a pattern after verification."""
    pass


class Good(Knitability):
    """Describes a pattern that doesn't contain any known errors."""

    def __str__(self) -> str:
        return "<Good Knitability>"


class Bad(Knitability):
    """Describes an error in a pattern.."""

    def __init__(self, problem: str, node: Node) -> None:
        """
        Creates a new description of an error in a pattern.

        :param problem: a message describing the error
        :param node: the node the error occurred at
        """
        self._problem = problem
        self._node = node

    @property
    def problem(self) -> str:
        """A message describing the error."""
        return self._problem

    @property
    def node(self) -> Node:
        """The node the error occurred at."""
        return self._node

    def __str__(self) -> str:
        return f"<Bad Knitability: {self.problem} at {self.node}>"


def _verifier(function: Callable[..., Iterable[Knitability]]) \
        -> Callable[..., Iterable[Knitability]]:
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Knitability:
        for knitability in function(*args, **kwargs):
            if not isinstance(knitability, Knitability):
                raise TypeError(
                    "expected knitability from verification function"
                )
            if isinstance(knitability, Bad):
                return knitability
        return Good()

    # noinspection PyTypeChecker
    return wrapper


@_verifier
def verify_pattern(pattern: PatternExpr) -> Knitability:
    """
    Checks the knitability of a pattern.

    :param pattern: the pattern to verify
    :return: the knitability of the pattern (good or bad)
    """
    pattern = infer_counts(pattern, 0)
    yield verify_counts(pattern, 0)
    assert isinstance(pattern, KnitExpr)
    if pattern.consumes != 0 or pattern.produces != 0:
        yield Bad("patterns should not consume or produce any stitches",
                  pattern)


# noinspection PyUnusedLocal
@singledispatch
def verify_counts(node: Node, available: int) -> Knitability:
    """
    Checks stitch counts for consistency, and verifies that every row has
    enough stitches available and doesn't leave any stitches left over.

    :param node: the AST to verify the stitch counts of
    :param available: the number of stitches remaining in the current row
    :return: the knitability of the AST
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


@verify_counts.register
@_verifier
def _(stitch: StitchLit, available: int) -> Knitability:
    yield _at_least(stitch.value.consumes, available, stitch)


@verify_counts.register
@_verifier
def _(fixed: FixedStitchRepeatExpr, available: int) -> Knitability:
    consumes = 0
    produces = 0
    for stitch in fixed.stitches:
        yield verify_counts(stitch, available - consumes)
        assert isinstance(stitch, KnitExpr)
        yield _at_least(stitch.consumes, available - consumes, stitch)
        consumes += stitch.consumes
        produces += stitch.produces
    yield _at_least(fixed.times.value * consumes, available, fixed)


@verify_counts.register
@_verifier
def _(expanding: ExpandingStitchRepeatExpr, available: int) -> Knitability:
    yield verify_counts(
        FixedStitchRepeatExpr(expanding.stitches, NaturalLit(1)),
        available - expanding.to_last.value
    )
    n = (available - expanding.to_last.value) // expanding.consumes
    yield _exactly(n * expanding.consumes,
                   available - expanding.to_last.value,
                   expanding)


@verify_counts.register
@_verifier
def _(repeat: RowRepeatExpr, available: int) -> Knitability:
    start = available
    for row in repeat.rows:
        yield verify_counts(row, available)
        assert isinstance(row, KnitExpr)
        yield _exactly(row.consumes, available, row)
        available = row.produces
    yield _exactly(start, available, repeat)


@_verifier
def _at_least(expected: int, actual: int, node: Node) -> Knitability:
    if expected > actual:
        yield Bad(
            f"expected {expected} stitches, but only {actual} are available",
            node
        )


@_verifier
def _exactly(expected: int, actual: int, node: Node) -> Knitability:
    yield _at_least(expected, actual, node)
    if expected < actual:
        yield Bad(f"{actual - expected} stitches left over", node)
