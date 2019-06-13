import sys

from knitscript.interpreter import InterpretError
from knitscript.loader import load_file


def main() -> None:
    """
    Prints the knitting instructions for a KnitScript pattern which is read
    from a file, or stdin if no filename is provided.
    """
    try:
        load_file(sys.argv[1] if len(sys.argv) >= 2 else None, sys.stdout)
    except InterpretError as e:
        print(f"error: {e}")


if __name__ == "__main__":
    main()
