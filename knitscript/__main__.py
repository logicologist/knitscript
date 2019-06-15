import sys

from knitscript.interpreter import InterpretError
from knitscript.loader import load_file


def main() -> None:
    """
    Prints the knitting instructions for a KnitScript pattern which is read
    from a file, or stdin if no filename is provided.
    """
    if len(sys.argv) != 2:
        print(f"usage: knitscript <filename>")
    else:
        try:
            load_file(sys.argv[1], sys.stdout)
        except (IOError, InterpretError) as e:
            print(f"error: {e}")


if __name__ == "__main__":
    main()
