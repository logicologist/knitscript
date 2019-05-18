from __future__ import annotations
from enum import Enum
from typing import Callable

class Stitch(Enum):
    CAST_ON = ("CO", 0, 1, lambda: None)
    BIND_OFF = ("BO", 1, 0, lambda: None)
    KNIT = ("K", 1, 1, lambda: Stitch.PURL)
    PURL = ("P", 1, 1, lambda: Stitch.KNIT)
    YARN_OVER = ("YO", 1, 1, lambda: Stitch.YARN_OVER)
    KNIT2TOG = ("K2T", 2, 1, lambda: Stitch.SLIP_SLIP_PURL)
    PURL2TOG = ("P2T", 2, 1, lambda: Stitch.SLIP_SLIP_KNIT)
    SLIP_SLIP_KNIT = ("SSK", 2, 1, lambda: Stitch.PURL2TOG)
    SLIP_SLIP_PURL = ("SSP", 2, 1, lambda: Stitch.KNIT2TOG)

    def __init__(self,
                 symbol: str,
                 consumes: int,
                 produces: int,
                 reverse: Callable[[], Stitch]) -> None:
        self._symbol = symbol
        self._consumes = consumes
        self._produces = produces
        self._reverse = reverse

    @property
    def consumes(self) -> int:
        return self._consumes

    @property
    def produces(self) -> int:
        return self._produces

    @property
    def reverse(self) -> Stitch:
        return self._reverse()