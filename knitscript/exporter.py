from functools import singledispatch

from knitscript.astnodes import ExpandingStitchRepeat, FixedStitchRepeat, \
    Node, Pattern, Row, RowRepeat, StitchLit
from knitscript._asttools import to_fixed_repeat


@singledispatch
def export_text(node: Node) -> str:
    """
    Exports the AST to human-readable knitting instructions in plain text.

    :param node: the AST to export
    :return: the instructions for the expression
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


@export_text.register
def _(stitch: StitchLit) -> str:
    return stitch.value.symbol


@export_text.register
def _(rep: FixedStitchRepeat) -> str:
    stitches = ", ".join(map(export_text, rep.stitches))
    if rep.times.value == 1:
        return stitches
    elif len(rep.stitches) == 1:
        return f"{stitches} {rep.times.value}"
    else:
        return f"[{stitches}] {rep.times.value}"


@export_text.register
def _(rep: ExpandingStitchRepeat) -> str:
    stitches = export_text(to_fixed_repeat(rep))
    if rep.to_last.value == 0:
        return f"*{stitches}; rep from * to end"
    else:
        return f"*{stitches}; rep from * to last {rep.to_last.value}"


@export_text.register
def _(row: Row) -> str:
    return (
        f"{row.side}: {export_text(to_fixed_repeat(row))}. " +
        f"({row.produces} sts)"
    )


@export_text.register
def _(rep: RowRepeat) -> str:
    rows = "\n".join(map(export_text, rep.rows))
    if rep.times.value == 1:
        return rows
    else:
        return f"**\n{rows}\nrep from ** {rep.times.value} times"


@export_text.register
def _(pattern: Pattern) -> str:
    return export_text(to_fixed_repeat(pattern))
