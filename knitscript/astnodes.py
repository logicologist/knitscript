from __future__ import annotations

from abc import ABC
from enum import Enum
from typing import Callable, Generator, Iterable, Mapping, Optional, Sequence

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


class Node(ABC):
    """An AST node."""

    def __init__(self,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new AST node.

        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        self._line = line
        self._column = column
        self._file = file

    @property
    def line(self) -> Optional[int]:
        """This node's line in the source file, if any."""
        return self._line

    @property
    def column(self) -> Optional[int]:
        """This node's column in the source file, if any."""
        return self._column

    @property
    def file(self) -> Optional[str]:
        """This node's source file name, if any."""
        return self._file


class Document(Node):
    """An AST node describing a complete KnitScript document."""

    def __init__(self,
                 stmts: Iterable[Node],
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new document node.

        :param stmts: the statements in the document
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(line, column, file)
        self._stmts = tuple(stmts)

    @property
    def stmts(self) -> Sequence[Node]:
        """The statements in the document."""
        return self._stmts


class Using(Node):
    """An AST node representing a using statement."""

    def __init__(self,
                 names: Iterable[str],
                 module: str,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new using statement node.

        :param names: the names to import
        :param module: the name of the module to import them from
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(line, column, file)
        self._names = tuple(names)
        self._module = module

    @property
    def names(self):
        """The names to import."""
        return self._names

    @property
    def module(self) -> str:
        """The name of the module to import the names from."""
        return self._module


class PatternDef(Node):
    """An AST node that defines a named pattern."""

    def __init__(self,
                 name: str,
                 pattern: Node,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new pattern definition node.

        :param name: the name of the pattern
        :param pattern: the pattern expression
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(line, column, file)
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


class NaturalLit(Node):
    """An AST node for a natural number (non-negative integer) literal."""

    def __init__(self,
                 value: int,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new natural number literal.

        :param value: the value of this literal
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        :raise ValueError: if the value is negative
        """
        super().__init__(line, column, file)
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


class StringLit(Node):
    """An AST node for a string literal."""

    def __init__(self,
                 value: str,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new string literal.

        :param value: the value of this literal
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(line, column, file)
        self._value = value

    @property
    def value(self) -> str:
        """The value of this literal."""
        return self._value

    def __str__(self) -> str:
        return str(self._value)


class Knittable(Node):
    """An AST node representing a knitting action."""

    def __init__(self,
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new knitting action expression.

        :param consumes:
            the number of stitches this expression consumes from the current
            row, if known
        :param produces:
            the number of stitches this expression produces for the next row,
            if known
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(line, column, file)
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


class StitchLit(Knittable):
    """An AST node for a stitch literal."""

    def __init__(self,
                 value: Stitch,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new stitch literal.

        :param value: the value of this literal
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(value.consumes, value.produces, line, column, file)
        self._value = value

    @property
    def value(self) -> Stitch:
        """The value of this literal."""
        return self._value

    def __repr__(self) -> str:
        return f"StitchLit({self.value})"


class FixedStitchRepeat(Knittable):
    """
    An AST node for repeating a sequence of stitches a fixed number of times.
    """

    def __init__(self,
                 stitches: Iterable[Node],
                 times: Node,
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new fixed stitch repeat expression.

        :param stitches: the sequence of stitches to repeat
        :param times: the number of times to repeat the stitches
        :param consumes:
            the number of stitches this expression consumes, if known
        :param produces:
            the number of stitches this expression produces, if known
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(consumes, produces, line, column, file)
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


class ExpandingStitchRepeat(Knittable):
    """
    An AST node for repeating a sequence of stitches an undetermined number of
    times.
    """

    def __init__(self,
                 stitches: Iterable[Node],
                 to_last: Node = NaturalLit(0),
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new expanding stitch repeat expression.

        :param stitches: the sequence of stitches to repeat
        :param to_last: the number of stitches to leave at the end of the row
        :param consumes:
            the number of stitches this expression consumes, if known
        :param produces:
            the number of stitches this expression produces, if known
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(consumes, produces, line, column, file)
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


class Row(FixedStitchRepeat):
    """An AST node representing a row."""

    def __init__(self,
                 stitches: Iterable[Node],
                 side: Optional[Side] = None,
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
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
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(stitches, NaturalLit(1),
                         consumes, produces,
                         line, column, file)
        self._side = side

    @property
    def side(self) -> Optional[Side]:
        """
        The side of the fabric (RS or WS) this row is intended to be knitted
        on, if known.
        """
        return self._side


class RowRepeat(Knittable):
    """An AST node for repeating a sequence of rows a fixed number of times."""

    def __init__(self,
                 rows: Iterable[Node],
                 times: Node,
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new row repeat expression.

        :param rows: the sequence of rows to repeat
        :param times: the number of times to repeat the rows
        :param consumes:
            the number of stitches this expression consumes, if known
        :param produces:
            the number of stitches this expression produces, if known
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(consumes, produces, line, column, file)
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


class Block(Knittable):
    """An AST node representing horizontal combination of patterns."""

    def __init__(self,
                 patterns: Iterable[Node],
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new block concatenation expression.

        :param patterns: the patterns to concatenate
        :param consumes:
            the number of stitches this expression consumes, if known
        :param produces:
            the number of stitches this expression produces, if known
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(consumes, produces, line, column, file)
        self._patterns = tuple(patterns)

    @property
    def patterns(self) -> Sequence[Node]:
        """The blocks to concatenate."""
        return self._patterns


class Pattern(RowRepeat):
    """An AST node representing a pattern."""

    def __init__(self,
                 rows: Iterable[Node],
                 params: Iterable[str] = (),
                 env: Optional[Mapping[str, Node]] = None,
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new pattern expression.

        :param rows: the sequence of rows in the pattern
        :param params: the names of the parameters for the pattern
        :param env: the environment enclosing the pattern, if any
        :param consumes:
            the number of stitches this expression consumes, if known
        :param produces:
            the number of stitches this expression produces, if known
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(rows, NaturalLit(1),
                         consumes, produces,
                         line, column, file)
        self._params = tuple(params)
        self._env = env

    @property
    def params(self) -> Sequence[str]:
        """The names of the parameters for the pattern."""
        return self._params

    @property
    def env(self) -> Optional[Mapping[str, Node]]:
        """The environment enclosing the pattern, if any."""
        return self._env


class FixedBlockRepeat(Knittable):
    """
    An AST node for repeating a block horizontally a fixed number of times.
    """

    def __init__(self,
                 block: Node,
                 times: Node,
                 consumes: Optional[int] = None,
                 produces: Optional[int] = None,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new fixed block repeat expression.

        :param block: the block to repeat
        :param times: the number of times to repeat the block
        :param consumes:
            the number of stitches this expression consumes, if known
        :param produces:
            the number of stitches this expression produces, if known
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(consumes, produces, line, column, file)
        self._block = block
        self._times = times

    @property
    def block(self) -> Node:
        """The block to repeat."""
        return self._block

    @property
    def times(self) -> Node:
        """The number of times to repeat the block."""
        return self._times


class Get(Node):
    """An AST node representing a variable lookup."""

    def __init__(self,
                 name: str,
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new get expression.

        :param name: the name of the variable to lookup
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(line, column, file)
        self._name = name

    @property
    def name(self) -> str:
        """The name of the variable to lookup."""
        return self._name

    def __repr__(self) -> str:
        return f"GetExpr({repr(self.name)})"


class Call(Node):
    """An AST node representing a call to a pattern or texture."""

    def __init__(self,
                 target: Node,
                 args: Iterable[Node],
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new call expression.

        :param target: the expression to call
        :param args: the arguments to send to the target expression
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(line, column, file)
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


class NativeFunction(Node):
    """An AST node representing a native Python function."""

    def __init__(self,
                 function: Callable[[Node, ...], Optional[Node]],
                 line: Optional[int] = None,
                 column: Optional[int] = None,
                 file: Optional[str] = None) -> None:
        """
        Creates a new native function node.

        :param function: the native function
        :param line: this node's line in the source file, if any
        :param column: this node's column in the source file, if any
        :param file: this node's source file name, if any
        """
        super().__init__(line, column, file)
        self._function = function

    @property
    def function(self) -> Callable[[Node, ...], Optional[Node]]:
        """The native function."""
        return self._function
