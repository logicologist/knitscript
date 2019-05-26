from __future__ import annotations
from enum import Enum
from typing import Callable


class Stitch(Enum):
    """
    A single stitch.
    """

    CAST_ON = ("CO", 0, 1, lambda: Stitch.CAST_ON)
    BIND_OFF = ("BO", 1, 0, lambda: Stitch.BIND_OFF)
    KNIT = ("K", 1, 1, lambda: Stitch.PURL)
    PURL = ("P", 1, 1, lambda: Stitch.KNIT)
    SLIP = ("SL", 1, 1, lambda: Stitch.SLIP)
    PSSO = ("PSSO", 0, -1, lambda: Stitch.PSSO)
    YARN_OVER = ("YO", 0, 1, lambda: Stitch.YARN_OVER)
    KNIT2TOG = ("K2TOG", 2, 1, lambda: Stitch.SLIP_SLIP_PURL)
    PURL2TOG = ("P2TOG", 2, 1, lambda: Stitch.SLIP_SLIP_KNIT)
    SLIP_SLIP_KNIT = ("SSK", 2, 1, lambda: Stitch.PURL2TOG)
    SLIP_SLIP_PURL = ("SSP", 2, 1, lambda: Stitch.KNIT2TOG)

    def __init__(self,
                 symbol: str,
                 consumes: int,
                 produces: int,
                 reverse: Callable[[], Stitch]) -> None:
        """
        Creates a new stitch type.

        :param symbol:
            an abbreviation that represents the stitch in knitting instructions
        :param consumes:
            the number of stitches this stitch consumes from the current row
        :param produces:
            the number of stitches this stitch produces for the next row
        :param reverse:
            a thunk that returns this stitch's side-reversed stitch type
        """
        self._symbol = symbol
        self._consumes = consumes
        self._produces = produces
        self._reverse = reverse

    @property
    def symbol(self) -> str:
        """
        An abbreviation that represents the stitch in knitting instructions.
        """
        return self._symbol

    @property
    def consumes(self) -> int:
        """The number of stitches this stitch consumes from the current row."""
        return self._consumes

    @property
    def produces(self) -> int:
        """The number of stitches this stitch produces for the next row."""
        return self._produces

    @property
    def reverse(self) -> Stitch:
        """This stitch's side-reversed stitch type."""
        return self._reverse()
