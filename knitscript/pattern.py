from __future__ import annotations

from itertools import chain, tee
from typing import Callable, Iterable, Iterator, TypeVar

from knitscript.ast import Visitor, StitchExpr, RowExpr, PatternExpr, \
    RepeatStitchExpr, RepeatRowExpr
from knitscript.stitch import Stitch

_T = TypeVar("_T")
_U = TypeVar("_U")


def to_rows(expr):
    return _RowVisitor().visit(expr)


def validate(rows: Iterable[Iterable[Stitch]]) -> str:
    count = 0
    next_count = 0
    for row in rows:
        for stitch in row:
            if count < stitch.consumes:
                return "not enough stitches"
            count -= stitch.consumes
            next_count += stitch.produces

        if count > 0:
            return "too many stitches"
        count = next_count
        next_count = 0

    if count > 0:
        return "left over stitches"
    return "ok"


class _RowVisitor(Visitor[Iterator[Iterator[Stitch]]]):
    def visit(self, expr) -> Iterator[Iterator[Stitch]]:
        return expr.accept(self)

    def visit_stitch(self, stitch: StitchExpr) -> Iterator[Iterator[Stitch]]:
        def wrap():
            yield stitch.stitch

        yield wrap()

    def visit_row(self, row: RowExpr) -> Iterator[Iterator[Stitch]]:
        yield _flat_map(lambda e: next(e.accept(self)), row.stitches)

    def visit_pattern(self, pattern: PatternExpr) \
            -> Iterator[Iterator[Stitch]]:
        return _flat_map(lambda r: r.accept(self), pattern.rows)

    def visit_repeat_stitch(self, repeat_stitch: RepeatStitchExpr) \
            -> Iterator[Iterator[Stitch]]:
        yield _cycle(
            _flat_map(lambda e: next(e.accept(self)), repeat_stitch.stitches),
            repeat_stitch.count)

    def visit_repeat_row(self, repeat_row: RepeatRowExpr) -> \
            Iterator[Iterator[Stitch]]:
        return _cycle(_flat_map(lambda e: e.accept(self), repeat_row.rows),
                      repeat_row.count)


def _flat_map(func: Callable[[_T], Iterable[_U]], iterable: Iterable[_T]) \
        -> Iterator[_U]:
    return chain.from_iterable(map(func, iterable))


def _cycle(iterable: Iterable[_T], n: int) -> Iterator[_T]:
    return chain.from_iterable(tee(iterable, n))
