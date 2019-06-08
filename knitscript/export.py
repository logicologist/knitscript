from functools import singledispatch

from knitscript.astnodes import ExpandingStitchRepeat, FixedStitchRepeat, \
    NaturalLit, Node, RowRepeat, StitchLit


@singledispatch
def export_text(expr: Node) -> str:
    """
    Exports the AST to human-readable knitting instructions in plain text.

    :param expr: the AST to export
    :return: the instructions for the expression
    """
    raise TypeError(f"unsupported node {type(expr).__name__}")


@export_text.register
def _(stitch: StitchLit) -> str:
    return stitch.value.symbol


@export_text.register
def _(repeat: FixedStitchRepeat) -> str:
    stitches = ", ".join(map(export_text, repeat.stitches))
    if repeat.times == NaturalLit(1):
        return stitches
    elif len(repeat.stitches) == 1:
        return f"{stitches} {repeat.times}"
    else:
        return f"[{stitches}] {repeat.times}"


@export_text.register
def _(repeat: ExpandingStitchRepeat) -> str:
    stitches = export_text(FixedStitchRepeat(repeat.stitches,
                                             NaturalLit(1)))
    if repeat.to_last == NaturalLit(0):
        return f"*{stitches}; rep from * to end"
    else:
        return f"*{stitches}; rep from * to last {repeat.to_last}"


@export_text.register
def _(repeat: RowRepeat) -> str:
    rows = ".\n".join(map(export_text, repeat.rows)) + "."
    if repeat.times == NaturalLit(1):
        return rows
    else:
        return f"**\n{rows}\nrep from ** {repeat.times} times"
