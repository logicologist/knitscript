from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from knitscript.stitch import Stitch

_T = TypeVar("_T")


class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor[_T]) -> _T:
        pass


class StitchExpr(Expr):
    def __init__(self, stitch: Stitch) -> None:
        self._stitch = stitch

    def accept(self, visitor: Visitor[_T]) -> _T:
        return visitor.visit_stitch(self)

    @property
    def stitch(self) -> Stitch:
        return self._stitch


class RowExpr(Expr):
    def __init__(self, stitches: List[Expr]) -> None:
        self._stitches = stitches

    def accept(self, visitor: Visitor[_T]) -> _T:
        return visitor.visit_row(self)

    @property
    def stitches(self) -> List[Expr]:
        return self._stitches.copy()


class PatternExpr(Expr):
    def __init__(self, rows: List[Expr]) -> None:
        self._rows = rows

    def accept(self, visitor):
        return visitor.visit_pattern(self)

    @property
    def rows(self) -> List[Expr]:
        return self._rows.copy()


class RepeatStitchExpr(Expr):
    def __init__(self, stitches: List[Expr], count: int) -> None:
        self._stitches = stitches
        self._count = count

    def accept(self, visitor):
        return visitor.visit_repeat_stitch(self)

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

    def accept(self, visitor):
        return visitor.visit_repeat_row(self)

    @property
    def rows(self) -> List[Expr]:
        return self._rows.copy()

    @property
    def count(self) -> int:
        return self._count


class Visitor(ABC, Generic[_T]):
    @abstractmethod
    def visit(self, expr: Expr) -> _T:
        pass

    @abstractmethod
    def visit_stitch(self, stitch: StitchExpr) -> _T:
        pass

    @abstractmethod
    def visit_row(self, row: RowExpr) -> _T:
        pass

    @abstractmethod
    def visit_pattern(self, pattern: PatternExpr) -> _T:
        pass

    @abstractmethod
    def visit_repeat_stitch(self, repeat_stitch: RepeatStitchExpr) -> _T:
        pass

    @abstractmethod
    def visit_repeat_row(self, repeat_row: RepeatRowExpr) -> _T:
        pass
