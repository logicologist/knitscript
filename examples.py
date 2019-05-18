from knitscript.pattern import Pattern
from knitscript.stitch import Stitch


def basic_scarf(n: int) -> Pattern:
    kpk = [Stitch.KNIT] + [Stitch.PURL] * 39 + [Stitch.KNIT]
    return Pattern(
        [[Stitch.CAST_ON] * 41] +
        ([[Stitch.KNIT] + ([Stitch.YARN_OVER] +
                           [Stitch.KNIT] * 3 +
                           [Stitch.SLIP, Stitch.KNIT2TOG, Stitch.PSSO] +
                           [Stitch.KNIT] * 3 +
                           [Stitch.YARN_OVER, Stitch.KNIT]) * 4] +
         [kpk] +
         [[Stitch.KNIT] + ([Stitch.KNIT, Stitch.YARN_OVER] +
                           [Stitch.KNIT] * 2 +
                           [Stitch.SLIP, Stitch.KNIT2TOG, Stitch.PSSO] +
                           [Stitch.KNIT] * 2 +
                           [Stitch.YARN_OVER] +
                           [Stitch.KNIT] * 2) * 4] +
         [kpk] +
         [[Stitch.KNIT] + ([Stitch.KNIT] * 2 +
                           [Stitch.YARN_OVER, Stitch.KNIT] +
                           [Stitch.SLIP, Stitch.KNIT2TOG, Stitch.PSSO,
                            Stitch.KNIT, Stitch.YARN_OVER] +
                           [Stitch.KNIT] * 3) * 4] +
         [kpk] +
         [[Stitch.KNIT] + ([Stitch.KNIT] * 3 +
                           [Stitch.YARN_OVER, Stitch.SLIP, Stitch.KNIT2TOG,
                            Stitch.PSSO, Stitch.YARN_OVER] +
                           [Stitch.KNIT] * 4) * 4] +
         [kpk]) * n +
        [[Stitch.BIND_OFF] * 41]
    )


print(basic_scarf(5).verify())
