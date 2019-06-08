import sys

from knitscript.astnodes import Pattern
from knitscript.asttools import pretty_print
from knitscript.exporter import export_text
from knitscript.interpreter import prepare_pattern
from knitscript.loader import load_file
from knitscript.verifier import verify_pattern


def main() -> None:
    """
    Prints the knitting instructions for a KnitScript pattern which is read
    from a file, or stdin if no filename is provided.
    """
    env = load_file(sys.argv[1] if len(sys.argv) >= 2 else None)
    pattern = env["main"]
    assert isinstance(pattern, Pattern)
    pattern = prepare_pattern(pattern)
    pretty_print(pattern)
    print()
    print(export_text(pattern))
    print()
    assert isinstance(pattern, Pattern)
    print(*verify_pattern(pattern), sep="\n")


if __name__ == "__main__":
    main()
