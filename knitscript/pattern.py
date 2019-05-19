from __future__ import annotations
from typing import List

from knitscript.stitch import Stitch


def validate(rows: List[List[Stitch]]) -> str:
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
