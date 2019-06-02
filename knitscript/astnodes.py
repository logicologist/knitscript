from __future__ import annotations

from abc import ABC
from enum import Enum
from functools import singledispatch
from typing import Callable, Generator, Iterable, Optional, Sequence

from knitscript.stitch import Stitch


class Side(Enum):
    """The side of the fabric, either right side (RS) or wrong side (WS)."""
    Right = "RS"
    Wrong = "WS"

    def flip(self) -> Side:
        """
        Flips to the opposite side.

        :return: the side opposite to this one
        """
        return Side.Wrong if self == Side.Right else Side.Right

    def alternate(self) -> Generator[Side]:
        """
        Creates an infinite generator that alternates back and forth between
        sides, starting from this side.

        :return:
            a generator for the infinite series: self, self.flip(),
            self.flip().flip(), ...
        """
        yield self
        yield from self.flip().alternate()


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
    def patterns(self) -> Sequence[Node]:
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


class NaturalLit(Expr):
    """An AST node for a natural number (non-negative integer) literal."""

    def __init__(self, value: int) -> None:
        """
        Creates a new natural number literal.

        :param value: the value of this literal
        :raise ValueError: if the value is negative
        """
        if value < 0:
            raise ValueError("value must be non-negative")
        self._value = value

    @property
    def value(self) -> int:
        """The value of this literal."""
        return self._value

    def __str__(self) -> str:
        return str(self._value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NaturalLit) and self.value == other.value


class KnitExpr(Expr):
    """An AST node representing a knitting action."""

    def __init__(self,
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None) -> None:
        """
        Creates a new knitting action expression.

        :param consumes:
            the number of stitches this expression consumes from the current
            row, if known
        :param produces:
            the number of stitches this expression produces for the next row,
            if known
        """
        self._consumes = consumes
        self._produces = produces

    @property
    def consumes(self) -> Optional[int]:
        """
        The number of stitches this expression consumes from the current row.
        """
        return self._consumes

    @property
    def produces(self) -> Optional[int]:
        """The number of stitches this expression produces for the next row."""
        return self._produces


class StitchLit(KnitExpr):
    """An AST node for a stitch literal."""

    def __init__(self, value: Stitch) -> None:
        """
        Creates a new stitch literal.

        :param value: the value of this literal
        """
        super().__init__(value.consumes, value.produces)
        self._value = value

    @property
    def value(self) -> Stitch:
        """The value of this literal."""
        return self._value

    def __repr__(self) -> str:
        return f"StitchLit({self.value})"


class FixedStitchRepeatExpr(KnitExpr):
    """
    An AST node for repeating a sequence of stitches a fixed number of times.
    """

    def __init__(self,
                 stitches: Iterable[Node],
                 times: Node,
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None) -> None:
        """
        Creates a new fixed stitch repeat expression.

        :param stitches: the sequence of stitches to repeat
        :param times: the number of times to repeat the stitches
        :param consumes:
            the number of stitches this expression consumes, if known
        :param produces:
            the number of stitches this expression produces, if known
        """
        super().__init__(consumes, produces)
        self._stitches = tuple(stitches)
        self._times = times

    @property
    def stitches(self) -> Sequence[Node]:
        """The sequence of stitches to repeat."""
        return self._stitches

    @property
    def times(self) -> Node:
        """The number of times to repeat the stitches."""
        return self._times


class ExpandingStitchRepeatExpr(KnitExpr):
    """
    An AST node for repeating a sequence of stitches an undetermined number of
    times.
    """

    def __init__(self,
                 stitches: Iterable[Node],
                 to_last: Node = NaturalLit(0),
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None) -> None:
        """
        Creates a new expanding stitch repeat expression.

        :param stitches: the sequence of stitches to repeat
        :param to_last: the number of stitches to leave at the end of the row
        :param consumes:
            the number of stitches this expression consumes, if known
        :param produces:
            the number of stitches this expression produces, if known
        """
        super().__init__(consumes, produces)
        self._stitches = tuple(stitches)
        self._to_last = to_last

    @property
    def stitches(self) -> Sequence[Node]:
        """The sequence of stitches to repeat."""
        return self._stitches

    @property
    def to_last(self) -> Node:
        """The number of stitches to leave at the end of the row."""
        return self._to_last


class RowExpr(FixedStitchRepeatExpr):
    """An AST node representing a row."""

    def __init__(self,
                 stitches: Iterable[Node],
                 side: Optional[Side] = None,
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None) -> None:
        """
        Creates a new row expression.

        :param stitches: the stitches in the row
        :param side:
            the side of the fabric (RS or WS) this row is intended to be
            knitted on, if known
        :param consumes:
            the number of stitches this expression consumes, if known
        :param produces:
            the number of stitches this expression produces, if known
        """
        super().__init__(stitches, NaturalLit(1), consumes, produces)
        self._side = side

    @property
    def side(self) -> Optional[Side]:
        """
        The side of the fabric (RS or WS) this row is intended to be knitted
        on, if known.
        """
        return self._side


class RowRepeatExpr(KnitExpr):
    """An AST node for repeating a sequence of rows a fixed number of times."""

    def __init__(self,
                 rows: Iterable[Node],
                 times: Node,
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None) -> None:
        """
        Creates a new row repeat expression.

        :param rows: the sequence of rows to repeat
        :param times: the number of times to repeat the rows
        :param consumes:
            the number of stitches this expression consumes, if known
        :param produces:
            the number of stitches this expression produces, if known
        """
        super().__init__(consumes, produces)
        self._rows = tuple(rows)
        self._times = times

    @property
    def rows(self) -> Sequence[Node]:
        """The sequence of rows to repeat."""
        return self._rows

    @property
    def times(self) -> Node:
        """The number of times to repeat the rows."""
        return self._times


class BlockExpr(KnitExpr):
    """An AST node representing horizontal concatenation of 2D blocks."""

    def __init__(self,
                 blocks: Iterable[Node],
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None) -> None:
        """
        Creates a new block concatenation expression.

        :param blocks: the blocks to concatenate
        :param consumes:
            the number of stitches this expression consumes, if known
        :param produces:
            the number of stitches this expression produces, if known
        """
        super().__init__(consumes, produces)
        self._blocks = tuple(blocks)

    @property
    def blocks(self) -> Sequence[Node]:
        """The blocks to concatenate."""
        return self._blocks


class PatternExpr(RowRepeatExpr):
    """An AST node representing a pattern."""

    def __init__(self,
                 rows: Iterable[Node],
                 params: Iterable[str] = (),
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None) \
            -> None:
        """
        Creates a new pattern expression.

        :param rows: the sequence of rows in the pattern
        :param params: the names of the parameters for the pattern
        :param consumes:
            the number of stitches this expression consumes, if known
        :param produces:
            the number of stitches this expression produces, if known
        """
        super().__init__(rows, NaturalLit(1), consumes, produces)
        self._params = tuple(params)

    @property
    def params(self) -> Sequence[str]:
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

    def __repr__(self) -> str:
        return f"GetExpr({repr(self.name)})"


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
    def args(self) -> Sequence[Node]:
        """The arguments to send to the target expression."""
        return self._args

    def __repr__(self) -> str:
        return f"CallExpr({repr(self.target)}, {repr(self.args)})"


# noinspection PyUnusedLocal
@singledispatch
def ast_map(node: Node, function: Callable[[Node], Node]) -> Node:
    """
    Calls the mapping function on each of the node's children.

    :param node: the AST to map
    :param function: the mapping function
    :return:
    """
    return node


@ast_map.register
def _(fixed: FixedStitchRepeatExpr, function: Callable[[Node], Node]) -> Node:
    return FixedStitchRepeatExpr(map(function, fixed.stitches),
                                 function(fixed.times),
                                 fixed.consumes, fixed.produces)


@ast_map.register
def _(expanding: ExpandingStitchRepeatExpr, function: Callable[[Node], Node]) \
        -> Node:
    return ExpandingStitchRepeatExpr(map(function, expanding.stitches),
                                     function(expanding.to_last),
                                     expanding.consumes, expanding.produces)


@ast_map.register
def _(row: RowExpr, function: Callable[[Node], Node]) -> Node:
    return RowExpr(map(function, row.stitches), row.side,
                   row.consumes, row.produces)


@ast_map.register
def _(repeat: RowRepeatExpr, function: Callable[[Node], Node]) -> Node:
    return RowRepeatExpr(map(function, repeat.rows), function(repeat.times),
                         repeat.consumes, repeat.produces)


@ast_map.register
def _(block: BlockExpr, function: Callable[[Node], Node]) -> Node:
    return BlockExpr(map(function, block.blocks),
                     block.consumes, block.produces)


@ast_map.register
def _(pattern: PatternExpr, function: Callable[[Node], Node]) -> Node:
    return PatternExpr(map(function, pattern.rows), pattern.params,
                       pattern.consumes, pattern.produces)


@ast_map.register
def _(call: CallExpr, function: Callable[[Node], Node]) -> Node:
    return CallExpr(function(call.target), map(function, call.args))


@singledispatch
def pretty_print(node: Node, level: int = 0, end: str = "\n") -> None:
    """
    Prints the AST with human-readable newlines and indentation.

    :param node: the AST to pretty print
    :param level: the current level of indentation
    :param end: the string to append to the end of the printed AST
    """
    print("  " * level + repr(node), end=end)


@pretty_print.register
def _(pattern: PatternExpr, level: int = 0, end: str = "\n") -> None:
    _print_parent("PatternExpr",
                  pattern.rows,
                  (pattern.params, pattern.consumes, pattern.produces),
                  level,
                  end)


@pretty_print.register
def _(block: BlockExpr, level: int = 0, end: str = "\n") -> None:
    _print_parent("BlockExpr",
                  block.blocks,
                  (block.consumes, block.produces),
                  level,
                  end)


@pretty_print.register
def _(repeat: RowRepeatExpr, level: int = 0, end: str = "\n") -> None:
    _print_parent("RowRepeatExpr",
                  repeat.rows,
                  (repeat.times, repeat.consumes, repeat.produces),
                  level,
                  end)


@pretty_print.register
def _(row: RowExpr, level: int = 0, end: str = "\n") -> None:
    _print_parent("RowExpr",
                  row.stitches,
                  (row.side, row.consumes, row.produces),
                  level,
                  end)


@pretty_print.register
def _(fixed: FixedStitchRepeatExpr, level: int = 0, end: str = "\n") -> None:
    _print_parent("FixedStitchRepeatExpr",
                  fixed.stitches,
                  (fixed.times, fixed.consumes, fixed.produces),
                  level,
                  end)


@pretty_print.register
def _(expanding: ExpandingStitchRepeatExpr, level: int = 0, end: str = "\n") \
        -> None:
    _print_parent("ExpandingStitchRepeatExpr",
                  expanding.stitches,
                  (expanding.to_last, expanding.consumes, expanding.produces),
                  level,
                  end)


def _print_parent(name: str,
                  children: Sequence[Node],
                  args: Iterable[object],
                  level: int,
                  end: str) -> None:
    print("  " * level + name + "([")
    for i, child in enumerate(children):
        pretty_print(child,
                     level + 1,
                     ",\n" if i < len(children) - 1 else "\n")
    print("  " * level + "], " + ", ".join(map(str, args)) + ")", end=end)
