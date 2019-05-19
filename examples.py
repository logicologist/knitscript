from typing import List

from knitscript.ast import ExpandingStitchRepeatExpr, FixedStitchRepeatExpr, \
    PatternExpr, RowExpr, RowRepeatExpr, StitchExpr
from knitscript.pattern import is_valid_pattern
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
                   FixedStitchRepeatExpr([StitchExpr(Stitch.PURL)], 39),
                   StitchExpr(Stitch.KNIT)])

    return PatternExpr([
        RowExpr([FixedStitchRepeatExpr([StitchExpr(Stitch.CAST_ON)], 41)]),
        RowRepeatExpr(
            [RowExpr([StitchExpr(Stitch.KNIT),
                      ExpandingStitchRepeatExpr([
                          StitchExpr(Stitch.YARN_OVER),
                          FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)], 3),
                          StitchExpr(Stitch.SLIP),
                          StitchExpr(Stitch.KNIT2TOG),
                          StitchExpr(Stitch.PSSO),
                          FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)], 3),
                          StitchExpr(Stitch.YARN_OVER),
                          StitchExpr(Stitch.KNIT)])]),
             kpk,
             RowExpr([StitchExpr(Stitch.KNIT),
                      ExpandingStitchRepeatExpr([
                          StitchExpr(Stitch.KNIT),
                          StitchExpr(Stitch.YARN_OVER),
                          FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)], 2),
                          StitchExpr(Stitch.SLIP),
                          StitchExpr(Stitch.KNIT2TOG),
                          StitchExpr(Stitch.PSSO),
                          FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)], 2),
                          StitchExpr(Stitch.YARN_OVER),
                          FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)],
                                                2)])]),
             kpk,
             RowExpr([StitchExpr(Stitch.KNIT),
                      ExpandingStitchRepeatExpr([
                          FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)], 2),
                          StitchExpr(Stitch.YARN_OVER),
                          StitchExpr(Stitch.KNIT),
                          StitchExpr(Stitch.SLIP),
                          StitchExpr(Stitch.KNIT2TOG),
                          StitchExpr(Stitch.PSSO),
                          StitchExpr(Stitch.KNIT),
                          StitchExpr(Stitch.YARN_OVER),
                          FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)],
                                                3)])]),
             kpk,
             RowExpr([StitchExpr(Stitch.KNIT),
                      ExpandingStitchRepeatExpr([
                          FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)], 3),
                          StitchExpr(Stitch.YARN_OVER),
                          StitchExpr(Stitch.SLIP),
                          StitchExpr(Stitch.KNIT2TOG),
                          StitchExpr(Stitch.PSSO),
                          StitchExpr(Stitch.YARN_OVER),
                          FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)],
                                                4)])]),
             kpk],
            n
        ),
        RowExpr([FixedStitchRepeatExpr([StitchExpr(Stitch.BIND_OFF)], 41)])
    ])


simple = PatternExpr(
    [RowExpr([FixedStitchRepeatExpr([StitchExpr(Stitch.CAST_ON)], 3)]),
     RowExpr([ExpandingStitchRepeatExpr([StitchExpr(Stitch.KNIT)])]),
     RowExpr([FixedStitchRepeatExpr([StitchExpr(Stitch.BIND_OFF)], 3)])])
print(is_valid_pattern(simple))
print(is_valid_pattern((basic_scarf_ast(1))))
print(is_valid_pattern((basic_scarf_ast(5))))
