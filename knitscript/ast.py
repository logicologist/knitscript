from __future__ import annotations

from abc import ABC
from typing import Collection

from knitscript.stitch import Stitch


class Expr(ABC):
    pass


class StitchExpr(Expr):
    def __init__(self, stitch: Stitch) -> None:
        self._stitch = stitch

    @property
    def stitch(self) -> Stitch:
        return self._stitch


class FixedStitchRepeatExpr(Expr):
    def __init__(self, stitches: Collection[Expr], count: int) -> None:
        self._stitches = tuple(stitches)
        self._count = count

    @property
    def stitches(self) -> Collection[Expr]:
        return self._stitches

    @property
    def count(self) -> int:
        return self._count


class ExpandingStitchRepeatExpr(Expr):
    def __init__(self, stitches: Collection[Expr], to_last: int = 0) -> None:
        self._stitches = tuple(stitches)
        self._to_last = to_last

    @property
    def stitches(self) -> Collection[Expr]:
        return self._stitches

    @property
    def to_last(self) -> int:
        return self._to_last


class RowExpr(FixedStitchRepeatExpr):
    def __init__(self, stitches: Collection[Expr]):
        super().__init__(stitches, 1)


class RowRepeatExpr(Expr):
    def __init__(self, rows: Collection[Expr], count: int) -> None:
        self._rows = tuple(rows)
        self._count = count

    @property
    def rows(self) -> Collection[Expr]:
        return self._rows

    @property
    def count(self) -> int:
        return self._count


class PatternExpr(RowRepeatExpr):
    def __init__(self, rows: Collection[Expr]) -> None:
        super().__init__(rows, 1)
