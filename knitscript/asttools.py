import re
from dataclasses import replace
from functools import reduce, singledispatch
from typing import Callable, Iterable, Sequence, TypeVar, Union

from knitscript.astnodes import Block, Call, ExpandingStitchRepeat, \
    FixedBlockRepeat, FixedStitchRepeat, Get, NaturalLit, Node, Pattern, Row, \
    RowRepeat, Source, StitchLit, Using

_T = TypeVar("_T")


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
def _(rep: FixedStitchRepeat, function: Callable[[Node], Node]) -> Node:
    return replace(rep,
                   stitches=list(map(function, rep.stitches)),
                   times=function(rep.times))


@ast_map.register
def _(rep: ExpandingStitchRepeat, function: Callable[[Node], Node]) -> Node:
    return replace(rep,
                   stitches=list(map(function, rep.stitches)),
                   to_last=function(rep.to_last))


@ast_map.register
def _(row: Row, function: Callable[[Node], Node]) -> Node:
    return replace(row, stitches=list(map(function, row.stitches)))


@ast_map.register
def _(rep: RowRepeat, function: Callable[[Node], Node]) -> Node:
    return replace(rep,
                   rows=list(map(function, rep.rows)),
                   times=function(rep.times))


@ast_map.register
def _(block: Block, function: Callable[[Node], Node]) -> Node:
    return replace(block, patterns=list(map(function, block.patterns)))


@ast_map.register
def _(pattern: Pattern, function: Callable[[Node], Node]) -> Node:
    return replace(pattern, rows=list(map(function, pattern.rows)))


@ast_map.register
def _(rep: FixedBlockRepeat, function: Callable[[Node], Node]) -> Node:
    return replace(rep, block=function(rep.block), times=function(rep.times))


@ast_map.register
def _(call: Call, function: Callable[[Node], Node]) -> Node:
    return replace(call,
                   target=function(call.target),
                   args=list(map(function, call.args)))


# noinspection PyUnusedLocal
@singledispatch
def ast_reduce(node: Node,
               function: Callable[[Node, _T], _T],
               initializer: _T) -> _T:
    """
    Reduces the AST to an accumulated value by repeatedly combining nodes.

    :param node: the AST to reduce
    :param function:
        the reducing function that takes the current node and the accumulated
        value and returns a new value
    :param initializer: the initial value for the accumulator
    :return: the final accumulated value
    """
    return initializer


@ast_reduce.register
def _(fixed: FixedStitchRepeat,
      function: Callable[[Node, _T], _T],
      initializer: _T) -> _T:
    return function(fixed.times,
                    reduce(lambda acc, node: function(node, acc),
                           fixed.stitches, initializer))


@ast_reduce.register
def _(expanding: ExpandingStitchRepeat,
      function: Callable[[Node, _T], _T],
      initializer: _T) -> _T:
    return function(expanding.to_last,
                    reduce(lambda acc, node: function(node, acc),
                           expanding.stitches, initializer))


@ast_reduce.register
def _(row: Row, function: Callable[[Node, _T], _T], initializer: _T) -> _T:
    return reduce(lambda acc, node: function(node, acc),
                  row.stitches, initializer)


@ast_reduce.register
def _(repeat: RowRepeat, function: Callable[[Node, _T], _T], initializer: _T) \
        -> _T:
    return function(repeat.times,
                    reduce(lambda acc, node: function(node, acc),
                           repeat.rows, initializer))


@ast_reduce.register
def _(block: Block, function: Callable[[Node, _T], _T], initializer: _T) -> _T:
    return reduce(lambda acc, node: function(node, acc),
                  block.patterns, initializer)


@ast_reduce.register
def _(pattern: Pattern, function: Callable[[Node, _T], _T], initializer: _T) \
        -> _T:
    return reduce(lambda acc, node: function(node, acc),
                  pattern.rows, initializer)


@ast_reduce.register
def _(repeat: FixedBlockRepeat,
      function: Callable[[Node, _T], _T],
      initializer: _T) -> _T:
    return function(repeat.times, function(repeat.block, initializer))


@ast_reduce.register
def _(call: Call, function: Callable[[Node, _T], _T], initializer: _T) -> _T:
    return function(call.target,
                    reduce(lambda acc, node: function(node, acc),
                           call.args, initializer))


# noinspection PyUnusedLocal
@singledispatch
def to_fixed_repeat(node: Node) -> Node:
    """
    Converts this node into an equivalent fixed stitch or row repeat, if
    possible.

    :param node: the node to convert
    :return: a fixed stitch repeat containing the same stitches as this node
    """
    raise TypeError(f"unsupported node {type(node).__name__}")


@to_fixed_repeat.register
def _(row: Row) -> Node:
    return FixedStitchRepeat(stitches=row.stitches, times=NaturalLit.of(1),
                             consumes=row.consumes, produces=row.produces,
                             sources=row.sources)


@to_fixed_repeat.register
def _(rep: ExpandingStitchRepeat) -> Node:
    return FixedStitchRepeat(stitches=rep.stitches, times=NaturalLit.of(1),
                             consumes=None, produces=None,
                             sources=rep.sources)


@to_fixed_repeat.register
def _(pattern: Pattern, times: int = 1) -> Node:
    return RowRepeat(rows=pattern.rows, times=NaturalLit.of(times),
                     consumes=pattern.consumes, produces=pattern.produces,
                     sources=pattern.sources)


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
def _(using: Using, level: int = 0, end: str = "\n") -> None:
    _print_parent(type(using).__name__,
                  [],
                  (list(map(str, using.names)), str(using.module)),
                  level,
                  end)


@pretty_print.register
def _(pattern: Pattern, level: int = 0, end: str = "\n") -> None:
    _print_parent(type(pattern).__name__,
                  pattern.rows,
                  (pattern.params, pattern.env,
                   pattern.consumes, pattern.produces),
                  level,
                  end)


@pretty_print.register
def _(repeat: FixedBlockRepeat, level: int = 0, end: str = "\n") -> None:
    _print_parent(type(repeat).__name__,
                  repeat.block,
                  (repeat.times, repeat.consumes, repeat.produces),
                  level,
                  end)


@pretty_print.register
def _(block: Block, level: int = 0, end: str = "\n") -> None:
    _print_parent(type(block).__name__,
                  block.patterns,
                  (block.consumes, block.produces),
                  level,
                  end)


@pretty_print.register
def _(repeat: RowRepeat, level: int = 0, end: str = "\n") -> None:
    _print_parent(type(repeat).__name__,
                  repeat.rows,
                  (repeat.times, repeat.consumes, repeat.produces),
                  level,
                  end)


@pretty_print.register
def _(row: Row, level: int = 0, end: str = "\n") -> None:
    _print_parent(type(row).__name__,
                  row.stitches,
                  (row.side, row.consumes, row.produces),
                  level,
                  end)


@pretty_print.register
def _(fixed: FixedStitchRepeat, level: int = 0, end: str = "\n") -> None:
    _print_parent(type(fixed).__name__,
                  fixed.stitches,
                  (fixed.times, fixed.consumes, fixed.produces),
                  level,
                  end)


@pretty_print.register
def _(expanding: ExpandingStitchRepeat, level: int = 0, end: str = "\n") \
        -> None:
    _print_parent(type(expanding).__name__,
                  expanding.stitches,
                  (expanding.to_last, expanding.consumes, expanding.produces),
                  level,
                  end)


def _print_parent(name: str,
                  children: Union[Node, Sequence[Node]],
                  args: Iterable[object],
                  level: int,
                  end: str) -> None:
    print("  " * level + name + "(", end="")
    if isinstance(children, Sequence):
        print("[")
        for i, child in enumerate(children):
            pretty_print(child,
                         level + 1,
                         ",\n" if i < len(children) - 1 else "\n")
        print("  " * level + "], ", end="")
    else:
        print()
        pretty_print(children, level + 1, end=",\n" + "  " * level)
    print(", ".join(map(str, args)) + ")", end=end)


class Error(Exception):
    """Base class for any error in a KnitScript document."""

    def __init__(self, message: str, nodes: Union[Node, Sequence[Node]]) \
            -> None:
        """
        Creates a new KnitScript error.

        :param message: a message describing the error
        :param nodes: the node(s) the error occurred at
        """
        self._message = message
        self._nodes = nodes if isinstance(nodes, Sequence) else [nodes]

    @property
    def message(self) -> str:
        """A message describing the error."""
        return self._message

    @property
    def nodes(self) -> Sequence[Node]:
        """The node(s) the error occurred at."""
        return self._nodes

    def __str__(self) -> str:
        trace = map(lambda node: f"in {_friendly_name(node)} " +
                                 f"{_show_sources(node.sources)}",
                    self.nodes)
        return f"{self.message}\n    " + "\n    ".join(trace)


def _show_sources(sources: Union[Source, Sequence[Source]]) -> str:
    if isinstance(sources, Source):
        return (f"at line {sources.line}, column {sources.column}, in " +
                (sources.file if sources.file is not None else "unknown file"))
    elif not sources:
        return "at unknown source"
    elif len(sources) == 1:
        return _show_sources(sources[0])
    else:
        return ("combined from sources:\n    - " +
                "\n    - ".join(map(_show_sources, sources)))


@singledispatch
def _friendly_name(node: Node) -> str:
    return re.sub(r"([A-Z])", r" \1",  type(node).__name__).lower().lstrip()


@_friendly_name.register
def _(stitch: StitchLit) -> str:
    return str(stitch.value)


@_friendly_name.register
def _(get: Get) -> str:
    return f"reference to {get.name}"


@_friendly_name.register
def _(call: Call) -> str:
    if isinstance(call.target, Get):
        return f"call to {call.target.name}"
    else:
        return f"call to {_friendly_name(call.target)}"
