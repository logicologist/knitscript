import sys

from knitscript.astnodes import PatternExpr, pretty_print
from knitscript.export import export_text
from knitscript.interpreter import alternate_sides, flatten, infer_counts, \
    infer_sides, substitute
from knitscript.loader import load
from knitscript.verifiers import verify_pattern


def main() -> None:
    """
    Prints the knitting instructions for a KnitScript pattern which is read
    from the filename or stdin if no filename is provided.
    """
    env = load(sys.argv[1] if len(sys.argv) >= 2 else None)
    pattern = infer_counts(infer_sides(substitute(env["main"], env)))
    pretty_print(pattern)
    print()
    pattern = flatten(pattern)
    # pretty_print(pattern)
    # print()
    pattern = alternate_sides(pattern)
    pretty_print(pattern)
    print()
    print(export_text(pattern))
    print()
    assert isinstance(pattern, PatternExpr)
    print(*verify_pattern(pattern), sep="\n")


if __name__ == "__main__":
    main()
