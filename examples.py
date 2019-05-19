from typing import List

from knitscript.ast import PatternExpr, RepeatRowExpr, RepeatStitchExpr, \
    RowExpr, StitchExpr
from knitscript.pattern import to_rows, validate
from knitscript.stitch import Stitch


def basic_scarf(n: int) -> List[List[Stitch]]:
    kpk = [Stitch.KNIT] + [Stitch.PURL] * 39 + [Stitch.KNIT]
    return ([[Stitch.CAST_ON] * 41] +
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
                               [Stitch.YARN_OVER, Stitch.KNIT, Stitch.SLIP,
                                Stitch.KNIT2TOG, Stitch.PSSO, Stitch.KNIT,
                                Stitch.YARN_OVER] +
                               [Stitch.KNIT] * 3) * 4] +
             [kpk] +
             [[Stitch.KNIT] + ([Stitch.KNIT] * 3 +
                               [Stitch.YARN_OVER, Stitch.SLIP, Stitch.KNIT2TOG,
                                Stitch.PSSO, Stitch.YARN_OVER] +
                               [Stitch.KNIT] * 4) * 4] +
             [kpk]) * n +
            [[Stitch.BIND_OFF] * 41])


def basic_scarf_ast(n: int) -> PatternExpr:
    kpk = RowExpr([StitchExpr(Stitch.KNIT),
                   RepeatStitchExpr([StitchExpr(Stitch.PURL)], 39),
                   StitchExpr(Stitch.KNIT)])

    return PatternExpr([
        RowExpr([RepeatStitchExpr([StitchExpr(Stitch.CAST_ON)], 41)]),
        RepeatRowExpr(
            [RowExpr([StitchExpr(Stitch.KNIT),
                      RepeatStitchExpr([
                          StitchExpr(Stitch.YARN_OVER),
                          RepeatStitchExpr([StitchExpr(Stitch.KNIT)], 3),
                          StitchExpr(Stitch.SLIP),
                          StitchExpr(Stitch.KNIT2TOG),
                          StitchExpr(Stitch.PSSO),
                          RepeatStitchExpr([StitchExpr(Stitch.KNIT)], 3),
                          StitchExpr(Stitch.YARN_OVER),
                          StitchExpr(Stitch.KNIT)], 4)]),
             kpk,
             RowExpr([StitchExpr(Stitch.KNIT),
                      RepeatStitchExpr([
                          StitchExpr(Stitch.KNIT),
                          StitchExpr(Stitch.YARN_OVER),
                          RepeatStitchExpr([StitchExpr(Stitch.KNIT)], 2),
                          StitchExpr(Stitch.SLIP),
                          StitchExpr(Stitch.KNIT2TOG),
                          StitchExpr(Stitch.PSSO),
                          RepeatStitchExpr([StitchExpr(Stitch.KNIT)], 2),
                          StitchExpr(Stitch.YARN_OVER),
                          RepeatStitchExpr([StitchExpr(Stitch.KNIT)], 2)],
                          4)]),
             kpk,
             RowExpr([StitchExpr(Stitch.KNIT),
                      RepeatStitchExpr([
                          RepeatStitchExpr([StitchExpr(Stitch.KNIT)], 2),
                          StitchExpr(Stitch.YARN_OVER),
                          StitchExpr(Stitch.KNIT),
                          StitchExpr(Stitch.SLIP),
                          StitchExpr(Stitch.KNIT2TOG),
                          StitchExpr(Stitch.PSSO),
                          StitchExpr(Stitch.KNIT),
                          StitchExpr(Stitch.YARN_OVER),
                          RepeatStitchExpr([StitchExpr(Stitch.KNIT)], 3)],
                          4)]),
             kpk,
             RowExpr([StitchExpr(Stitch.KNIT),
                      RepeatStitchExpr([
                          RepeatStitchExpr([StitchExpr(Stitch.KNIT)], 3),
                          StitchExpr(Stitch.YARN_OVER),
                          StitchExpr(Stitch.SLIP),
                          StitchExpr(Stitch.KNIT2TOG),
                          StitchExpr(Stitch.PSSO),
                          StitchExpr(Stitch.YARN_OVER),
                          RepeatStitchExpr([StitchExpr(Stitch.KNIT)], 4)],
                          4)]),
             kpk],
            n
        ),
        RowExpr([RepeatStitchExpr([StitchExpr(Stitch.BIND_OFF)], 41)])
    ])


print(validate(basic_scarf(5)))
print(validate(to_rows(
    PatternExpr([RowExpr([RepeatStitchExpr([StitchExpr(Stitch.CAST_ON)], 3)]),
                 RowExpr(
                     [RepeatStitchExpr([StitchExpr(Stitch.BIND_OFF)], 3)])]))))
print(validate(to_rows(basic_scarf_ast(1))))
