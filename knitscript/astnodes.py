from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Generator, Mapping, Optional, Sequence

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

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Source:
    """
    A location in a source file.

    :cvar line: the line in the source file
    :cvar column: the column in the source file
    :cvar file: the source file name
    """
    line: int
    column: int
    file: Optional[str]


@dataclass(frozen=True)
class Node:
    """
    An AST node.

    :cvar sources: the source file locations this node was created from
    """
    sources: Sequence[Source] = field(compare=False)


@dataclass(frozen=True)
class Document(Node):
    """
    An AST node describing a complete KnitScript document.

    :cvar stmts: the statements in the document
    """
    stmts: Sequence[Node]


@dataclass(frozen=True)
class Using(Node):
    """
    An AST node representing a using statement.

    :cvar names: the names to import
    :cvar module: the name of the module to import them from
    """
    names: Sequence[str]
    module: str


@dataclass(frozen=True)
class PatternDef(Node):
    """
    An AST node that defines a named pattern.

    :cvar name: the name of the pattern
    :cvar pattern: the pattern expression
    """
    name: str
    pattern: Node


@dataclass(frozen=True)
class NaturalLit(Node):
    """
    An AST node for a natural number (non-negative integer) literal.

    :cvar value: the value of this literal
    """
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("value must be non-negative")

    @classmethod
    def of(cls, value: int) -> NaturalLit:
        """
        Creates a natural literal representing this value.

        :param value: the value of this literal
        :return: the literal representing this value
        """
        return NaturalLit(value=value, sources=[])


@dataclass(frozen=True)
class StringLit(Node):
    """
    An AST node for a string literal.

    :cvar value: the value of this literal
    """
    value: str


@dataclass(frozen=True)
class Get(Node):
    """
    An AST node representing a variable lookup.

    :cvar name: the name of the variable to lookup
    """
    name: str


@dataclass(frozen=True)
class Call(Node):
    """
    An AST node representing a call to a pattern or texture.

    :cvar target: the expression to call
    :cvar args: the arguments to send to the target expression
    """
    target: Node
    args: Sequence[Node]


@dataclass(frozen=True)
class NativeFunction(Node):
    """
    An AST node representing a native Python function.

    :cvar function: the native function
    """
    function: Callable[[Node, ...], Optional[Node]]

    @classmethod
    def of(cls, function: Callable[[Node, ...], Optional[Node]]) \
            -> NativeFunction:
        """
        Creates a native function node for the function.

        :param function: the native function
        :return: a native function node for the function
        """
        return NativeFunction(function=function, sources=[])


@dataclass(frozen=True)
class Knittable(Node):
    """
    An AST node representing a knitting action.

    :cvar consumes:
        the number of stitches this expression consumes from the current row
    :cvar produces:
        the number of stitches this expression produces for the next row
    """
    consumes: Optional[int]
    produces: Optional[int]


@dataclass(frozen=True)
class StitchLit(Knittable):
    """
    An AST node for a stitch literal.

    :cvar value: the value of this literal
    """
    value: Stitch


@dataclass(frozen=True)
class FixedStitchRepeat(Knittable):
    """
    An AST node for repeating a sequence of stitches a fixed number of times.

    :cvar stitches: the sequence of stitches to repeat
    :cvar times: the number of times to repeat the stitches
    """
    stitches: Sequence[Node]
    times: Node


@dataclass(frozen=True)
class ExpandingStitchRepeat(Knittable):
    """
    An AST node for repeating a sequence of stitches an undetermined number of
    times.

    :cvar stitches: the sequence of stitches to repeat
    :cvar to_last: the number of stitches to leave at the end of the row
    """
    stitches: Sequence[Node]
    to_last: Node


@dataclass(frozen=True)
class Row(Knittable):
    """
    An AST node representing a row.

    :cvar stitches: the stitches in the row
    :cvar side:
        the side of the fabric (RS or WS) this row is intended to be knitted on
    :cvar inferred: whether the side has been inferred from context
    """
    stitches: Sequence[Node]
    side: Optional[Side]
    inferred: bool


@dataclass(frozen=True)
class RowRepeat(Knittable):
    """
    An AST node for repeating a sequence of rows a fixed number of times.

    :cvar rows: the sequence of rows to repeat
    :cvar times: the number of times to repeat the rows
    """
    rows: Sequence[Node]
    times: Node


@dataclass(frozen=True)
class Pattern(Knittable):
    """
    An AST node representing a pattern.

    :cvar rows: the sequence of rows in the pattern
    :cvar params: the names of the parameters for the pattern
    :cvar env: the environment enclosing the pattern
    """
    rows: Sequence[Node]
    params: Sequence[str]
    env: Optional[Mapping[str, Node]]


@dataclass(frozen=True)
class Block(Knittable):
    """
    An AST node representing horizontal combination of patterns.

    :cvar patterns: the patterns to concatenate
    """
    patterns: Sequence[Node]


@dataclass(frozen=True)
class FixedBlockRepeat(Knittable):
    """
    An AST node for repeating a block horizontally a fixed number of times.

    :cvar block: the block to repeat
    :cvar times: the number of times to repeat the block
    """
    block: Node
    times: Node
