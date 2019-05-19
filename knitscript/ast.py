from __future__ import annotations

from abc import ABC
from typing import List

from knitscript.stitch import Stitch


class Expr(ABC):
    pass


class StitchExpr(Expr):
    def __init__(self, stitch: Stitch) -> None:
        self._stitch = stitch

    @property
    def stitch(self) -> Stitch:
        return self._stitch


class RowExpr(Expr):
    def __init__(self, stitches: List[Expr]) -> None:
        self._stitches = stitches

    @property
    def stitches(self) -> List[Expr]:
        return self._stitches.copy()


class PatternExpr(Expr):
    def __init__(self, rows: List[Expr]) -> None:
        self._rows = rows

    @property
    def rows(self) -> List[Expr]:
        return self._rows.copy()


class RepeatStitchExpr(Expr):
    def __init__(self, stitches: List[Expr], count: int) -> None:
        self._stitches = stitches
        self._count = count

    @property
    def stitches(self) -> List[Expr]:
        return self._stitches.copy()

    @property
    def count(self) -> int:
        return self._count


class RepeatRowExpr(Expr):
    def __init__(self, rows: List[Expr], count: int) -> None:
        self._rows = rows
        self._count = count

    @property
    def rows(self) -> List[Expr]:
        return self._rows.copy()

    @property
    def count(self) -> int:
        return self._count
