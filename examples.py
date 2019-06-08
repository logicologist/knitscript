from knitscript.astnodes import Block, Call, \
    ExpandingStitchRepeat, FixedStitchRepeat, Get, NaturalLit, \
    Pattern, Row, RowRepeat, Side, StitchLit, \
    pretty_print
from knitscript.interpreter import compile_text, infer_counts, \
    reverse
from knitscript.stitch import Stitch
from knitscript.verifiers import verify_pattern

row_to_reverse = \
    Row([FixedStitchRepeat([StitchLit(Stitch.KNIT)],
                           NaturalLit(4)),
         FixedStitchRepeat(
                 [StitchLit(Stitch.KNIT), StitchLit(Stitch.PURL)],
                 NaturalLit(3))])
row_to_reverse = infer_counts(row_to_reverse, 10)

reversed_pattern = Pattern([
    Row([FixedStitchRepeat([StitchLit(Stitch.CAST_ON)],
                           NaturalLit(10))]),
    Row([FixedStitchRepeat([StitchLit(Stitch.KNIT)],
                           NaturalLit(4)),
         FixedStitchRepeat(
                 [StitchLit(Stitch.KNIT), StitchLit(Stitch.PURL)],
                 NaturalLit(3))]),
    reverse(row_to_reverse, 0),
    Row([ExpandingStitchRepeat([StitchLit(Stitch.BIND_OFF)])])
], [])

print(*verify_pattern(reversed_pattern), sep="\n")
print(compile_text(reversed_pattern))

row_to_reverse_2 = \
    Row([ExpandingStitchRepeat([StitchLit(Stitch.KNIT),
                                StitchLit(Stitch.KNIT),
                                StitchLit(Stitch.PURL),
                                StitchLit(Stitch.KNIT),
                                StitchLit(Stitch.PURL)],
                               NaturalLit(2)),
         FixedStitchRepeat([StitchLit(Stitch.KNIT)],
                           NaturalLit(2))],
        Side.Right)
row_to_reverse_2 = infer_counts(row_to_reverse_2, 17)

reversed_pattern_2 = Pattern([
    Row([FixedStitchRepeat([StitchLit(Stitch.CAST_ON)],
                           NaturalLit(17))]),
    Row([ExpandingStitchRepeat([StitchLit(Stitch.KNIT),
                                StitchLit(Stitch.KNIT),
                                StitchLit(Stitch.PURL),
                                StitchLit(Stitch.KNIT),
                                StitchLit(Stitch.PURL)],
                               NaturalLit(2)),
         FixedStitchRepeat([StitchLit(Stitch.KNIT)],
                           NaturalLit(2))]),
    reverse(row_to_reverse_2, 0),
    Row([ExpandingStitchRepeat([StitchLit(Stitch.BIND_OFF)])])
], [])

print(*verify_pattern(reversed_pattern_2), sep="\n")
print(compile_text(reversed_pattern_2))




fixed_row = Row([
    StitchLit(Stitch.KNIT),
    FixedStitchRepeat([StitchLit(Stitch.KNIT), StitchLit(Stitch.PURL)], NaturalLit(4)),
    StitchLit(Stitch.KNIT)
  ])

pretty_print(infer_counts(fixed_row), 0)




# # This example should eventually fail

# bad_block_concat = PatternExpr([
#     BlockExpr([
#       PatternExpr([
#           RowExpr([StitchLit(Stitch.KNIT), StitchLit(Stitch.PURL), StitchLit(Stitch.KNIT), StitchLit(Stitch.KNIT)])
#         ], []),
#       PatternExpr([
#           RowExpr([StitchLit(Stitch.KNIT), StitchLit(Stitch.PURL)]),
#           RowExpr([StitchLit(Stitch.KNIT), StitchLit(Stitch.PURL)])
#         ], [])])
#   ], [])

# print(is_valid_pattern(bad_block_concat))

