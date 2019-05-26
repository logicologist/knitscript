from knitscript.ast import CallExpr, ExpandingStitchRepeatExpr, \
    FixedStitchRepeatExpr, GetExpr, NaturalLit, PatternExpr, RowExpr, \
    RowRepeatExpr, StitchExpr

from knitscript.interpreter import compile_text, is_valid_pattern, substitute
from knitscript.stitch import Stitch

simple = PatternExpr(
    [RowExpr([FixedStitchRepeatExpr([StitchExpr(Stitch.CAST_ON)],
                                    NaturalLit(3))]),
     RowExpr([ExpandingStitchRepeatExpr([StitchExpr(Stitch.KNIT)])]),
     RowExpr([FixedStitchRepeatExpr([StitchExpr(Stitch.BIND_OFF)],
                                    NaturalLit(3))])])
print(is_valid_pattern(simple))


kpk = RowExpr([StitchExpr(Stitch.KNIT),
               ExpandingStitchRepeatExpr([StitchExpr(Stitch.PURL)],
                                         NaturalLit(1)),
               StitchExpr(Stitch.KNIT)])

basic_scarf = PatternExpr([
    RowExpr([FixedStitchRepeatExpr([StitchExpr(Stitch.CAST_ON)],
                                   NaturalLit(41))]),
    RowRepeatExpr(
        [RowExpr([StitchExpr(Stitch.KNIT),
                  ExpandingStitchRepeatExpr([
                      StitchExpr(Stitch.YARN_OVER),
                      FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)],
                                            NaturalLit(3)),
                      StitchExpr(Stitch.SLIP),
                      StitchExpr(Stitch.KNIT2TOG),
                      StitchExpr(Stitch.PSSO),
                      FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)],
                                            NaturalLit(3)),
                      StitchExpr(Stitch.YARN_OVER),
                      StitchExpr(Stitch.KNIT)
                  ])]),
         kpk,
         RowExpr([StitchExpr(Stitch.KNIT),
                  ExpandingStitchRepeatExpr([
                      StitchExpr(Stitch.KNIT),
                      StitchExpr(Stitch.YARN_OVER),
                      FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)],
                                            NaturalLit(2)),
                      StitchExpr(Stitch.SLIP),
                      StitchExpr(Stitch.KNIT2TOG),
                      StitchExpr(Stitch.PSSO),
                      FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)],
                                            NaturalLit(2)),
                      StitchExpr(Stitch.YARN_OVER),
                      FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)],
                                            NaturalLit(2))
                  ])]),
         kpk,
         RowExpr([StitchExpr(Stitch.KNIT),
                  ExpandingStitchRepeatExpr([
                      FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)],
                                            NaturalLit(2)),
                      StitchExpr(Stitch.YARN_OVER),
                      StitchExpr(Stitch.KNIT),
                      StitchExpr(Stitch.SLIP),
                      StitchExpr(Stitch.KNIT2TOG),
                      StitchExpr(Stitch.PSSO),
                      StitchExpr(Stitch.KNIT),
                      StitchExpr(Stitch.YARN_OVER),
                      FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)],
                                            NaturalLit(3))
                  ])]),
         kpk,
         RowExpr([StitchExpr(Stitch.KNIT),
                  ExpandingStitchRepeatExpr([
                      FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)],
                                            NaturalLit(3)),
                      StitchExpr(Stitch.YARN_OVER),
                      StitchExpr(Stitch.SLIP),
                      StitchExpr(Stitch.KNIT2TOG),
                      StitchExpr(Stitch.PSSO),
                      StitchExpr(Stitch.YARN_OVER),
                      FixedStitchRepeatExpr([StitchExpr(Stitch.KNIT)],
                                            NaturalLit(4))
                  ])]),
         kpk],
        GetExpr("n")
    ),
    RowExpr([ExpandingStitchRepeatExpr([StitchExpr(Stitch.BIND_OFF)])])
], ["n"])

basic_scarf5 = substitute(CallExpr(basic_scarf, [NaturalLit(5)]), {})
assert isinstance(basic_scarf5, PatternExpr)

print(is_valid_pattern(basic_scarf5))
print()
print(compile_text(basic_scarf5))

seed = PatternExpr([
    RowExpr([StitchExpr(Stitch.KNIT), StitchExpr(Stitch.PURL)]),
    RowExpr([StitchExpr(Stitch.PURL), StitchExpr(Stitch.KNIT)])
])

first_class_patterns_omg = PatternExpr([
    RowExpr([FixedStitchRepeatExpr([StitchExpr(Stitch.CAST_ON)],
                                   NaturalLit(2))]),
    GetExpr("stitch"),
    RowExpr([ExpandingStitchRepeatExpr([StitchExpr(Stitch.BIND_OFF)])])
], ["stitch"])

print()
print(compile_text(substitute(CallExpr(first_class_patterns_omg, [seed]), {})))
