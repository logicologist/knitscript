from knitscript.astnodes import BlockConcatExpr, CallExpr, \
    ExpandingStitchRepeatExpr, FixedStitchRepeatExpr, GetExpr, NaturalLit, \
    PatternExpr, RowExpr, RowRepeatExpr, StitchLit

from knitscript.interpreter import compile_text, flatten, is_valid_pattern, \
    substitute
from knitscript.stitch import Stitch

simple = PatternExpr(
    [RowExpr([FixedStitchRepeatExpr([StitchLit(Stitch.CAST_ON)],
                                    NaturalLit(3))]),
     RowExpr([ExpandingStitchRepeatExpr([StitchLit(Stitch.KNIT)])]),
     RowExpr([FixedStitchRepeatExpr([StitchLit(Stitch.BIND_OFF)],
                                    NaturalLit(3))])])
print(is_valid_pattern(simple))

kpk = RowExpr([StitchLit(Stitch.KNIT),
               ExpandingStitchRepeatExpr([StitchLit(Stitch.PURL)],
                                         NaturalLit(1)),
               StitchLit(Stitch.KNIT)])

basic_scarf = PatternExpr([
    RowExpr([FixedStitchRepeatExpr([StitchLit(Stitch.CAST_ON)],
                                   NaturalLit(41))]),
    RowRepeatExpr(
        [RowExpr([StitchLit(Stitch.KNIT),
                  ExpandingStitchRepeatExpr([
                      StitchLit(Stitch.YARN_OVER),
                      FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                            NaturalLit(3)),
                      StitchLit(Stitch.SLIP),
                      StitchLit(Stitch.KNIT2TOG),
                      StitchLit(Stitch.PSSO),
                      FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                            NaturalLit(3)),
                      StitchLit(Stitch.YARN_OVER),
                      StitchLit(Stitch.KNIT)
                  ])]),
         kpk,
         RowExpr([StitchLit(Stitch.KNIT),
                  ExpandingStitchRepeatExpr([
                      StitchLit(Stitch.KNIT),
                      StitchLit(Stitch.YARN_OVER),
                      FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                            NaturalLit(2)),
                      StitchLit(Stitch.SLIP),
                      StitchLit(Stitch.KNIT2TOG),
                      StitchLit(Stitch.PSSO),
                      FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                            NaturalLit(2)),
                      StitchLit(Stitch.YARN_OVER),
                      FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                            NaturalLit(2))
                  ])]),
         kpk,
         RowExpr([StitchLit(Stitch.KNIT),
                  ExpandingStitchRepeatExpr([
                      FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                            NaturalLit(2)),
                      StitchLit(Stitch.YARN_OVER),
                      StitchLit(Stitch.KNIT),
                      StitchLit(Stitch.SLIP),
                      StitchLit(Stitch.KNIT2TOG),
                      StitchLit(Stitch.PSSO),
                      StitchLit(Stitch.KNIT),
                      StitchLit(Stitch.YARN_OVER),
                      FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                            NaturalLit(3))
                  ])]),
         kpk,
         RowExpr([StitchLit(Stitch.KNIT),
                  ExpandingStitchRepeatExpr([
                      FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                            NaturalLit(3)),
                      StitchLit(Stitch.YARN_OVER),
                      StitchLit(Stitch.SLIP),
                      StitchLit(Stitch.KNIT2TOG),
                      StitchLit(Stitch.PSSO),
                      StitchLit(Stitch.YARN_OVER),
                      FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                            NaturalLit(4))
                  ])]),
         kpk],
        GetExpr("n")
    ),
    RowExpr([ExpandingStitchRepeatExpr([StitchLit(Stitch.BIND_OFF)])])
], ["n"])

basic_scarf5 = substitute(CallExpr(basic_scarf, [NaturalLit(5)]), {})
assert isinstance(basic_scarf5, PatternExpr)

print(is_valid_pattern(basic_scarf5))
print()
print(compile_text(basic_scarf5))

seed = PatternExpr([
    RowExpr([StitchLit(Stitch.KNIT), StitchLit(Stitch.PURL)]),
    RowExpr([StitchLit(Stitch.PURL), StitchLit(Stitch.KNIT)])
])

first_class_patterns_omg = PatternExpr([
    RowExpr([FixedStitchRepeatExpr([StitchLit(Stitch.CAST_ON)],
                                   NaturalLit(4))]),
    BlockConcatExpr([GetExpr("stitch"), GetExpr("stitch")]),
    BlockConcatExpr([GetExpr("stitch"), GetExpr("stitch")]),
    RowExpr([ExpandingStitchRepeatExpr([StitchLit(Stitch.BIND_OFF)])])
], ["stitch"])

processed = flatten(substitute(CallExpr(first_class_patterns_omg, [seed]), {}))
assert isinstance(processed, PatternExpr)

print()
print(is_valid_pattern(processed))
print(compile_text(processed))
