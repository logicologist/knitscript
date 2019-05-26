from __future__ import annotations

from abc import ABC
from typing import Collection

from knitscript.stitch import Stitch


class Expr(ABC):
    """An AST node for any expression."""
    pass


class StitchExpr(Expr):
    """An AST node for a single stitch."""

    def __init__(self, stitch: Stitch) -> None:
        """
        Creates a new stitch expression.

        :param stitch: the stitch in this expression
        """
        self._stitch = stitch

    @property
    def stitch(self) -> Stitch:
        """The stitch in this expression."""
        return self._stitch


class FixedStitchRepeatExpr(Expr):
    """
    An AST node for repeating a sequence of stitches a fixed number of times.
    """

    def __init__(self, stitches: Collection[Expr], count: int) -> None:
        """
        Creates a new fixed stitch repeat expression.

        :param stitches: the sequence of stitches to repeat
        :param count: the number of times to repeat the stitches
        """
        self._stitches = tuple(stitches)
        self._count = count

    @property
    def stitches(self) -> Collection[Expr]:
        """The sequence of stitches to repeat."""
        return self._stitches

    @property
    def count(self) -> int:
        """The number of times to repeat the stitches."""
        return self._count


class ExpandingStitchRepeatExpr(Expr):
    """
    An AST node for repeating a sequence of stitches an undetermined number of
    times.
    """

    def __init__(self, stitches: Collection[Expr], to_last: int = 0) -> None:
        """
        Creates a new expanding stitch repeat expression.

        :param stitches: the sequence of stitches to repeat
        :param to_last: the number of stitches to leave at the end of the row
        """
        self._stitches = tuple(stitches)
        self._to_last = to_last

    @property
    def stitches(self) -> Collection[Expr]:
        """The sequence of stitches to repeat."""
        return self._stitches

    @property
    def to_last(self) -> int:
        """The number of stitches to leave at the end of the row."""
        return self._to_last


class RowExpr(FixedStitchRepeatExpr):
    """An AST node representing a row."""

    def __init__(self, stitches: Collection[Expr]):
        """
        Creates a new row expression.

        :param stitches: the stitches in the row
        """
        super().__init__(stitches, 1)


class RowRepeatExpr(Expr):
    """An AST node for repeating a sequence of rows a fixed number of times."""

    def __init__(self, rows: Collection[Expr], count: int) -> None:
        """
        Creates a new row repeat expression.

        :param rows: the sequence of rows to repeat
        :param count: the number of times to repeat the rows
        """
        self._rows = tuple(rows)
        self._count = count

    @property
    def rows(self) -> Collection[Expr]:
        """The sequence of rows to repeat."""
        return self._rows

    @property
    def count(self) -> int:
        """The number of times to repeat the rows."""
        return self._count


class PatternExpr(RowRepeatExpr):
    """An AST node representing a pattern."""

    def __init__(self, rows: Collection[Expr]) -> None:
        """
        Creates a new pattern expression.

        :param rows: the sequence of rows in the pattern
        """
        super().__init__(rows, 1)
