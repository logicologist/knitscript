from functools import reduce, singledispatch
from typing import Callable, Iterable, Sequence, TypeVar, Union

from knitscript.astnodes import Block, Call, ExpandingStitchRepeat, \
    FixedBlockRepeat, FixedStitchRepeat, Node, Pattern, Row, RowRepeat, Using

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
def _(fixed: FixedStitchRepeat, function: Callable[[Node], Node]) -> Node:
    return FixedStitchRepeat(map(function, fixed.stitches),
                             function(fixed.times),
                             fixed.consumes, fixed.produces)


@ast_map.register
def _(expanding: ExpandingStitchRepeat, function: Callable[[Node], Node]) \
        -> Node:
    return ExpandingStitchRepeat(map(function, expanding.stitches),
                                 function(expanding.to_last),
                                 expanding.consumes, expanding.produces)


@ast_map.register
def _(row: Row, function: Callable[[Node], Node]) -> Node:
    return Row(map(function, row.stitches), row.side,
               row.consumes, row.produces)


@ast_map.register
def _(repeat: RowRepeat, function: Callable[[Node], Node]) -> Node:
    return RowRepeat(map(function, repeat.rows), function(repeat.times),
                     repeat.consumes, repeat.produces)


@ast_map.register
def _(block: Block, function: Callable[[Node], Node]) -> Node:
    return Block(map(function, block.patterns),
                 block.consumes, block.produces)


@ast_map.register
def _(pattern: Pattern, function: Callable[[Node], Node]) -> Node:
    return Pattern(map(function, pattern.rows), pattern.params, pattern.env,
                   pattern.consumes, pattern.produces)


@ast_map.register
def _(repeat: FixedBlockRepeat, function: Callable[[Node], Node]) -> Node:
    return FixedBlockRepeat(function(repeat.block), function(repeat.times),
                            repeat.consumes, repeat.produces)


@ast_map.register
def _(call: Call, function: Callable[[Node], Node]) -> Node:
    return Call(function(call.target), map(function, call.args))


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
                  (list(map(str, using.pattern_names)), str(using.filename)),
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
