from knitscript.pattern import Pattern
from knitscript.stitch import Stitch


def basic_scarf(n: int) -> Pattern:
    return Pattern(
        [[Stitch.CAST_ON] * 41] +
        [[Stitch.KNIT] + ([Stitch.YARN_OVER] +
                          [Stitch.KNIT] * 3 +
                          [Stitch.SLIP, Stitch.KNIT2TOG, Stitch.PSSO] +
                          [Stitch.KNIT] * 3 +
                          [Stitch.YARN_OVER, Stitch.KNIT]) * 4] * n +
        [[Stitch.BIND_OFF] * 41]
    )


print(basic_scarf(1).verify())
