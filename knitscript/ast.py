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


class RowExpr(RepeatStitchExpr):
    def __init__(self, stitches: List[Expr]):
        super().__init__(stitches, 1)


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


class PatternExpr(RepeatRowExpr):
    def __init__(self, rows: List[Expr]) -> None:
        super().__init__(rows, 1)
