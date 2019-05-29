from knitscript.astnodes import BlockExpr, CallExpr, \
    ExpandingStitchRepeatExpr, FixedStitchRepeatExpr, GetExpr, NaturalLit, \
    PatternExpr, RowExpr, RowRepeatExpr, Side, StitchLit

from knitscript.interpreter import compile_text, flatten, is_valid_pattern, \
    substitute, reverse, count_stitches
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
    BlockExpr([GetExpr("stitch"), GetExpr("stitch")]),
    BlockExpr([GetExpr("stitch"), GetExpr("stitch")]),
    RowExpr([ExpandingStitchRepeatExpr([StitchLit(Stitch.BIND_OFF)])])
], ["stitch"])

processed = flatten(substitute(CallExpr(first_class_patterns_omg, [seed]), {}))
assert isinstance(processed, PatternExpr)

print()
print(is_valid_pattern(processed))
print(compile_text(processed))


row_to_reverse = \
    RowExpr([FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                    NaturalLit(4)),
            FixedStitchRepeatExpr([StitchLit(Stitch.KNIT), StitchLit(Stitch.PURL)],
                                    NaturalLit(3))])
row_to_reverse = count_stitches(row_to_reverse, 10)

reversed_pattern = PatternExpr([
    RowExpr([FixedStitchRepeatExpr([StitchLit(Stitch.CAST_ON)],
                                    NaturalLit(10))]),
    RowExpr([FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                    NaturalLit(4)),
            FixedStitchRepeatExpr([StitchLit(Stitch.KNIT), StitchLit(Stitch.PURL)],
                                    NaturalLit(3))]),
    reverse(row_to_reverse, 0),
    RowExpr([ExpandingStitchRepeatExpr([StitchLit(Stitch.BIND_OFF)])])
  ], [])

print()
print(is_valid_pattern(reversed_pattern))
print(compile_text(reversed_pattern))




row_to_reverse_2 = \
    RowExpr([ExpandingStitchRepeatExpr([StitchLit(Stitch.KNIT),
                                        StitchLit(Stitch.KNIT),
                                        StitchLit(Stitch.PURL),
                                        StitchLit(Stitch.KNIT),
                                        StitchLit(Stitch.PURL)],
                                        NaturalLit(2)),
            FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                  NaturalLit(2))],
            Side.Right)
row_to_reverse_2 = count_stitches(row_to_reverse_2, 17)

reversed_pattern_2 = PatternExpr([
    RowExpr([FixedStitchRepeatExpr([StitchLit(Stitch.CAST_ON)],
                                    NaturalLit(17))]),
    RowExpr([ExpandingStitchRepeatExpr([StitchLit(Stitch.KNIT),
                                        StitchLit(Stitch.KNIT),
                                        StitchLit(Stitch.PURL),
                                        StitchLit(Stitch.KNIT),
                                        StitchLit(Stitch.PURL)],
                                        NaturalLit(2)),
            FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                  NaturalLit(2))]),
    reverse(row_to_reverse_2, 0),
    RowExpr([ExpandingStitchRepeatExpr([StitchLit(Stitch.BIND_OFF)])])
  ], [])

print()
print(is_valid_pattern(reversed_pattern_2))
print(compile_text(reversed_pattern_2))
