from knitscript.ast import ExpandingStitchRepeatExpr, FixedStitchRepeatExpr, \
    PatternExpr, RowExpr, RowRepeatExpr, StitchExpr
from knitscript.pattern import is_valid_pattern
from knitscript.stitch import Stitch

simple = PatternExpr(
    [RowExpr([FixedStitchRepeatExpr([StitchExpr(Stitch.CAST_ON)], 3)]),
     RowExpr([ExpandingStitchRepeatExpr([StitchExpr(Stitch.KNIT)])]),
     RowExpr([FixedStitchRepeatExpr([StitchExpr(Stitch.BIND_OFF)], 3)])])
print(is_valid_pattern(simple))


def basic_scarf(n: int) -> PatternExpr:
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


print(is_valid_pattern((basic_scarf(1))))
print(is_valid_pattern((basic_scarf(5))))
