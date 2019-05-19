from abc import ABC, abstractmethod
from itertools import chain
from typing import Generic, List, TypeVar

from knitscript.stitch import Stitch

T = TypeVar("T")
Stitches = List[Stitch]
Rows = List[Stitches]


class Expr(ABC, Generic[T]):
    @abstractmethod
    def eval(self) -> T:
        pass


class StitchExpr(Expr[Stitches]):
    def __init__(self, stitch: Stitch) -> None:
        self._stitch = stitch

    def eval(self) -> Stitches:
        return [self._stitch]


class RowExpr(Expr[Rows]):
    def __init__(self, exprs: List[Expr[Stitches]]) -> None:
        self._exprs = exprs

    def eval(self) -> Rows:
        return [flat_eval(self._exprs)]


class PatternExpr(Expr[Rows]):
    def __init__(self, rows: List[Expr[Rows]]) -> None:
        self._rows = rows

    def eval(self) -> Rows:
        return flat_eval(self._rows)


class RepeatExpr(Expr[List[T]]):
    def __init__(self, exprs: List[Expr[List[T]]], count: int) -> None:
        self._exprs = exprs
        self._count = count

    def eval(self) -> List[T]:
        return flat_eval(self._exprs) * self._count


def flat_eval(exprs: List[Expr[List[T]]]) -> List[T]:
    return list(chain.from_iterable(map(lambda e: e.eval(), exprs)))
