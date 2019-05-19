from __future__ import annotations

from functools import singledispatch
from itertools import chain, tee
from typing import Callable, Iterable, Iterator, TypeVar

from knitscript.ast import StitchExpr, RowExpr, PatternExpr, \
    RepeatStitchExpr, RepeatRowExpr
from knitscript.stitch import Stitch

_T = TypeVar("_T")
_U = TypeVar("_U")


@singledispatch
def to_rows(_: object) -> Iterator[Iterator[Stitch]]:
    raise NotImplementedError()


@to_rows.register
def _(stitch: StitchExpr) -> Iterator[Iterator[Stitch]]:
    def wrap():
        yield stitch.stitch

    yield wrap()


@to_rows.register
def _(row: RowExpr) -> Iterator[Iterator[Stitch]]:
    yield _flat_map(lambda stitch: next(to_rows(stitch)), row.stitches)


@to_rows.register
def _(pattern: PatternExpr) -> Iterator[Iterator[Stitch]]:
    return _flat_map(to_rows, pattern.rows)


@to_rows.register
def _(repeat_stitch: RepeatStitchExpr) -> Iterator[Iterator[Stitch]]:
    yield _cycle(_flat_map(lambda stitch: next(to_rows(stitch)),
                           repeat_stitch.stitches), repeat_stitch.count)


@to_rows.register
def _(repeat_row: RepeatRowExpr) -> Iterator[Iterator[Stitch]]:
    return _cycle(_flat_map(to_rows, repeat_row.rows), repeat_row.count)


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


def _flat_map(func: Callable[[_T], Iterable[_U]], iterable: Iterable[_T]) \
        -> Iterator[_U]:
    return chain.from_iterable(map(func, iterable))


def _cycle(iterable: Iterable[_T], n: int) -> Iterator[_T]:
    return chain.from_iterable(tee(iterable, n))
