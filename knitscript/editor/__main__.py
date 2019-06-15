from tkinter import Tk

from knitscript.editor.app import Application


def main() -> None:
    """Runs the KnitScript editor."""
    app = Application(Tk())
    app.mainloop()


if __name__ == "__main__":
    main()
