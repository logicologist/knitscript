import sys

from knitscript.loader import load_file


def main() -> None:
    """
    Prints the knitting instructions for a KnitScript pattern which is read
    from a file, or stdin if no filename is provided.
    """
    load_file(sys.argv[1] if len(sys.argv) >= 2 else None, sys.stdout)


if __name__ == "__main__":
    main()
