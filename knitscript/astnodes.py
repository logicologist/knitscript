from abc import ABC, abstractmethod
from itertools import chain
from typing import Any, List

from knitscript.stitch import Stitch


class Expr(ABC):
    @abstractmethod
    def eval(self) -> Any:
        pass


class StitchExpr(Expr):
    def __init__(self, stitch: Stitch) -> None:
        self._stitch = stitch

    def eval(self) -> List[Stitch]:
        return [self._stitch]


class RowExpr(Expr):
    def __init__(self, exprs: List[Expr]) -> None:
        self._exprs = exprs

    def eval(self) -> List[List[Stitch]]:
        return [flat_eval(self._exprs)]


class RepeatExpr(Expr):
    def __init__(self, exprs: List[Expr], count: int) -> None:
        self._exprs = exprs
        self._count = count

    def eval(self) -> List[Any]:
        return flat_eval(self._exprs) * self._count


class PatternExpr(Expr):
    def __init__(self, rows: List[Expr]) -> None:
        self._rows = rows

    def eval(self) -> List[List[Stitch]]:
        return flat_eval(self._rows)


def flat_eval(exprs: List[Expr]) -> List[Any]:
    return list(chain.from_iterable(map(lambda e: e.eval(), exprs)))
