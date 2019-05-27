from __future__ import annotations

from abc import ABC
from typing import Collection, Iterable

from knitscript.stitch import Stitch


class Node(ABC):
    """An AST node."""
    pass


class Document(Node):
    """An AST node describing a complete KnitScript document."""

    def __init__(self, patterns: Iterable[Node]) -> None:
        """
        Creates a new document node.

        :param patterns: the patterns in the document
        """
        self._patterns = tuple(patterns)

    @property
    def patterns(self) -> Collection[Node]:
        """The patterns in the document."""
        return self._patterns


class PatternDef(Node):
    """An AST node that defines a named pattern."""

    def __init__(self, name: str, pattern: Node) -> None:
        """
        Creates a new pattern definition node.

        :param name: the name of the pattern
        :param pattern: the pattern expression
        """
        self._name = name
        self._pattern = pattern

    @property
    def name(self) -> str:
        """The name of the pattern."""
        return self._name

    @property
    def pattern(self) -> Node:
        """The pattern expression."""
        return self._pattern


class Expr(Node):
    """An expression AST node."""
    pass


class Lit(Expr):
    """A literal expression node."""
    pass


class NaturalLit(Lit):
    """An AST node for a natural number (non-negative integer) literal."""

    def __init__(self, value: int) -> None:
        """
        Creates a new natural number literal.

        :param value: the value of the literal
        :raise ValueError: if the value is negative
        """
        if value < 0:
            raise ValueError("value must be non-negative")
        self._value = value

    @property
    def value(self) -> int:
        """The value of the literal."""
        return self._value

    def __str__(self) -> str:
        return str(self._value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NaturalLit) and self.value == other.value


class StitchLit(Lit):
    """An AST node for a stitch literal."""

    def __init__(self, stitch: Stitch) -> None:
        """
        Creates a new stitch literal.

        :param stitch: the stitch value of this literal
        """
        self._stitch = stitch

    @property
    def stitch(self) -> Stitch:
        """The stitch value of this literal."""
        return self._stitch


class FixedStitchRepeatExpr(Expr):
    """
    An AST node for repeating a sequence of stitches a fixed number of times.
    """

    def __init__(self, stitches: Iterable[Node], count: Node) -> None:
        """
        Creates a new fixed stitch repeat expression.

        :param stitches: the sequence of stitches to repeat
        :param count: the number of times to repeat the stitches
        """
        self._stitches = tuple(stitches)
        self._count = count

    @property
    def stitches(self) -> Collection[Node]:
        """The sequence of stitches to repeat."""
        return self._stitches

    @property
    def count(self) -> Node:
        """The number of times to repeat the stitches."""
        return self._count


class ExpandingStitchRepeatExpr(Expr):
    """
    An AST node for repeating a sequence of stitches an undetermined number of
    times.
    """

    def __init__(self,
                 stitches: Iterable[Node],
                 to_last: Node = NaturalLit(0)) -> None:
        """
        Creates a new expanding stitch repeat expression.

        :param stitches: the sequence of stitches to repeat
        :param to_last: the number of stitches to leave at the end of the row
        """
        self._stitches = tuple(stitches)
        self._to_last = to_last

    @property
    def stitches(self) -> Collection[Node]:
        """The sequence of stitches to repeat."""
        return self._stitches

    @property
    def to_last(self) -> Node:
        """The number of stitches to leave at the end of the row."""
        return self._to_last


class RowExpr(FixedStitchRepeatExpr):
    """An AST node representing a row."""

    def __init__(self, stitches: Iterable[Node], rs=True):
        """
        Creates a new row expression.

        :param stitches: the stitches in the row
        """
        super().__init__(stitches, NaturalLit(1))
        self._rs = rs

    @property
    def rs(self):
        return self._rs
    


class RowRepeatExpr(Expr):
    """An AST node for repeating a sequence of rows a fixed number of times."""

    def __init__(self, rows: Iterable[Node], count: Node) -> None:
        """
        Creates a new row repeat expression.

        :param rows: the sequence of rows to repeat
        :param count: the number of times to repeat the rows
        """
        self._rows = tuple(rows)
        self._count = count

    @property
    def rows(self) -> Collection[Node]:
        """The sequence of rows to repeat."""
        return self._rows

    @property
    def count(self) -> Node:
        """The number of times to repeat the rows."""
        return self._count


class BlockConcatExpr(Expr):
    """An AST node representing horizontal concatenation of 2D blocks."""

    def __init__(self, blocks: Iterable[Node]) -> None:
        """
        Creates a new block concatenation expression.

        :param blocks: the blocks to concatenate
        """
        self._blocks = tuple(blocks)

    @property
    def blocks(self) -> Collection[Node]:
        """The blocks to concatenate."""
        return self._blocks


class PatternExpr(RowRepeatExpr):
    """An AST node representing a pattern."""

    def __init__(self, rows: Iterable[Node], params: Collection[str] = ()) \
            -> None:
        """
        Creates a new pattern expression.

        :param rows: the sequence of rows in the pattern
        :param params: the names of the parameters for the pattern
        """
        super().__init__(rows, NaturalLit(1))
        self._params = tuple(params)

    @property
    def params(self) -> Collection[str]:
        """The names of the parameters for the pattern."""
        return self._params


class GetExpr(Expr):
    """An AST node representing a variable lookup."""

    def __init__(self, name: str) -> None:
        """
        Creates a new get expression.

        :param name: the name of the variable to lookup
        """
        self._name = name

    @property
    def name(self) -> str:
        """The name of the variable to lookup."""
        return self._name


class CallExpr(Expr):
    """An AST node representing a call to a pattern or texture."""

    def __init__(self, target: Node, args: Iterable[Node]) -> None:
        """
        Creates a new call expression.

        :param target: the expression to call
        :param args: the arguments to send to the target expression
        """
        self._target = target
        self._args = tuple(args)

    @property
    def target(self) -> Node:
        """The expression to call."""
        return self._target

    @property
    def args(self) -> Collection[Node]:
        """The arguments to send to the target expression."""
        return self._args
