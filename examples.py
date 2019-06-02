from knitscript.astnodes import BlockExpr, CallExpr, \
    ExpandingStitchRepeatExpr, FixedStitchRepeatExpr, GetExpr, NaturalLit, \
    PatternExpr, RowExpr, Side, StitchLit

from knitscript.interpreter import compile_text, flatten, infer_counts, \
    substitute, reverse, infer_sides
from knitscript.verifiers import verify_pattern
from knitscript.stitch import Stitch

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

processed = flatten(infer_counts(
    infer_sides(substitute(CallExpr(first_class_patterns_omg, [seed]), {}))
))
assert isinstance(processed, PatternExpr)

print(*verify_pattern(processed), sep="\n")
print(compile_text(processed))

row_to_reverse = \
    RowExpr([FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                   NaturalLit(4)),
             FixedStitchRepeatExpr(
                 [StitchLit(Stitch.KNIT), StitchLit(Stitch.PURL)],
                 NaturalLit(3))])
row_to_reverse = infer_counts(row_to_reverse, 10)

reversed_pattern = PatternExpr([
    RowExpr([FixedStitchRepeatExpr([StitchLit(Stitch.CAST_ON)],
                                   NaturalLit(10))]),
    RowExpr([FixedStitchRepeatExpr([StitchLit(Stitch.KNIT)],
                                   NaturalLit(4)),
             FixedStitchRepeatExpr(
                 [StitchLit(Stitch.KNIT), StitchLit(Stitch.PURL)],
                 NaturalLit(3))]),
    reverse(row_to_reverse, 0),
    RowExpr([ExpandingStitchRepeatExpr([StitchLit(Stitch.BIND_OFF)])])
], [])

print(*verify_pattern(reversed_pattern), sep="\n")
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
row_to_reverse_2 = infer_counts(row_to_reverse_2, 17)

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

print(*verify_pattern(reversed_pattern_2), sep="\n")
print(compile_text(reversed_pattern_2))
