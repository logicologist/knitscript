from tkinter import Tk

from knitscript.editor._window import Window


def main() -> None:
    """Runs the KnitScript editor."""
    window = Window(Tk())
    window.mainloop()


if __name__ == "__main__":
    main()
