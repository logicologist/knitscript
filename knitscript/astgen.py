from functools import singledispatch
from typing import Collection, Union

from knitscript.astnodes import ExpandingStitchRepeatExpr, Expr, \
    FixedStitchRepeatExpr, NaturalLit, PatternExpr, RowExpr, StitchExpr
from knitscript.parser.KnitScriptParser import KnitScriptParser, \
    ParserRuleContext
from knitscript.stitch import Stitch


@singledispatch
def build_ast(ctx: ParserRuleContext) -> Expr:
    """
    Builds an AST from a parse tree generated by ANTLR.

    :param ctx: a parse tree context node
    :return: the AST corresponding to the parse tree
    """
    raise TypeError(f"unsupported parser context {type(ctx).__name__}")


@build_ast.register
def _(pattern: KnitScriptParser.PatternContext) -> Expr:
    return PatternExpr(map(build_ast, pattern.rows))


@build_ast.register
def _(row: KnitScriptParser.RowContext) -> Expr:
    return RowExpr(map(build_ast, row.stitchList().stitches))


@build_ast.register
def _(repeat: KnitScriptParser.StitchRepeatContext) -> Expr:
    return build_ast(repeat.fixedStitchRepeat() or
                     repeat.expandingStitchRepeat() or
                     repeat.stitch())


@build_ast.register
def _(fixed: KnitScriptParser.FixedStitchRepeatContext) -> Expr:
    count = NaturalLit(int(fixed.count.text))
    return FixedStitchRepeatExpr(map(build_ast, _stitches(fixed)), count)


@build_ast.register
def _(expanding: KnitScriptParser.ExpandingStitchRepeatContext) -> Expr:
    to_last = NaturalLit(int(expanding.toLast.text) if expanding.toLast else 0)
    return ExpandingStitchRepeatExpr(map(build_ast, _stitches(expanding)),
                                     to_last)


@build_ast.register
def _(stitch: KnitScriptParser.StitchContext) -> Expr:
    return StitchExpr(Stitch.from_symbol(stitch.ID().getText()))


def _stitches(ctx: Union[KnitScriptParser.FixedStitchRepeatContext,
                         KnitScriptParser.ExpandingStitchRepeatContext]) \
        -> Collection[ParserRuleContext]:
    return [ctx.stitch()] if ctx.stitch() else ctx.stitchList().stitches
