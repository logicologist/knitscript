from knitscript.astnodes import PatternExpr, RepeatExpr, RowExpr, StitchExpr
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
        [[Stitch.BIND_OFF] * 41]
    )


def basic_scarf_ast(n: int) -> PatternExpr:
    kpk = RowExpr([StitchExpr(Stitch.KNIT),
                   RepeatExpr([StitchExpr(Stitch.PURL)], 39),
                   StitchExpr(Stitch.KNIT)])

    return PatternExpr([
        RowExpr([RepeatExpr([StitchExpr(Stitch.CAST_ON)], 41)]),
        RepeatExpr(
            [RowExpr([StitchExpr(Stitch.KNIT),
                      RepeatExpr([StitchExpr(Stitch.YARN_OVER),
                                  RepeatExpr([StitchExpr(Stitch.KNIT)], 3),
                                  StitchExpr(Stitch.SLIP),
                                  StitchExpr(Stitch.KNIT2TOG),
                                  StitchExpr(Stitch.PSSO),
                                  RepeatExpr([StitchExpr(Stitch.KNIT)], 3),
                                  StitchExpr(Stitch.YARN_OVER),
                                  StitchExpr(Stitch.KNIT)], 4)]),
             kpk,
             RowExpr([StitchExpr(Stitch.KNIT),
                      RepeatExpr([StitchExpr(Stitch.KNIT),
                                  StitchExpr(Stitch.YARN_OVER),
                                  RepeatExpr([StitchExpr(Stitch.KNIT)], 2),
                                  StitchExpr(Stitch.SLIP),
                                  StitchExpr(Stitch.KNIT2TOG),
                                  StitchExpr(Stitch.PSSO),
                                  RepeatExpr([StitchExpr(Stitch.KNIT)], 2),
                                  StitchExpr(Stitch.YARN_OVER),
                                  RepeatExpr([StitchExpr(Stitch.KNIT)], 2)],
                                 4)]),
             kpk,
             RowExpr([StitchExpr(Stitch.KNIT),
                      RepeatExpr([RepeatExpr([StitchExpr(Stitch.KNIT)], 2),
                                  StitchExpr(Stitch.YARN_OVER),
                                  StitchExpr(Stitch.KNIT),
                                  StitchExpr(Stitch.SLIP),
                                  StitchExpr(Stitch.KNIT2TOG),
                                  StitchExpr(Stitch.PSSO),
                                  StitchExpr(Stitch.KNIT),
                                  StitchExpr(Stitch.YARN_OVER),
                                  RepeatExpr([StitchExpr(Stitch.KNIT)], 3)],
                                 4)]),
             kpk,
             RowExpr([StitchExpr(Stitch.KNIT),
                      RepeatExpr([RepeatExpr([StitchExpr(Stitch.KNIT)], 3),
                                  StitchExpr(Stitch.YARN_OVER),
                                  StitchExpr(Stitch.SLIP),
                                  StitchExpr(Stitch.KNIT2TOG),
                                  StitchExpr(Stitch.PSSO),
                                  StitchExpr(Stitch.YARN_OVER),
                                  RepeatExpr([StitchExpr(Stitch.KNIT)], 4)],
                                 4)]),
             kpk],
            n
        ),
        RowExpr([RepeatExpr([StitchExpr(Stitch.BIND_OFF)], 41)])
    ])


print(basic_scarf(5).verify())
print(basic_scarf_ast(5).eval().verify())
