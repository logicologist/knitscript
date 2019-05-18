from typing import List

from knitscript.stitch import Stitch


class Pattern:
    def __init__(self, stitches: List[List[Stitch]]):
        self._stitches = stitches

    def verify(self):
        count = 0
        next_count = 0
        for row in self._stitches:
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
