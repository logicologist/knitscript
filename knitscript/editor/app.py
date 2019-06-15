from functools import wraps
from io import StringIO
from tkinter import BOTH, END, Text, Tk, YES
from tkinter.font import Font
from tkinter.ttk import Frame
from typing import Callable, TypeVar

from knitscript.loader import load_text

_T = TypeVar("_T")


class Application(Frame):
    """The KnitScript editor main window."""

    def __init__(self, master: Tk = None):
        """
        Creates the main window.

        :param master: the parent widget
        """
        super().__init__(master)
        self.pack()

        preview_frame = Frame(self, width=600, height=500)
        preview_frame.pack(side="right")
        preview_frame.pack_propagate(False)
        preview = Text(preview_frame)
        preview.configure(font=Font(family="Segoe UI"))
        preview.pack(expand=YES, fill=BOTH)

        editor_frame = Frame(self, width=700, height=500)
        editor_frame.pack(side="left")
        editor_frame.pack_propagate(False)
        editor = Text(editor_frame)

        @_debounce(master, 500)
        def update(_event=None) -> None:
            text = editor.get(1.0, END)
            output = StringIO()
            try:
                load_text(text, output)
            except Exception as e:
                # TODO: Catching all exceptions is too broad.
                output.write(f"error: {e}\n")
            preview.replace(1.0, END, output.getvalue())

        editor.bind("<Key>", update)
        editor.configure(font=Font(family="Consolas"))
        editor.insert(1.0,
                      "pattern hello\n" +
                      "  row: CO 12.\n" +
                      "  row: K to end.\n" +
                      "  row: BO to end.\n" +
                      "end\n" +
                      "\n" +
                      "show (hello)")
        update()
        editor.pack(expand=YES, fill=BOTH)


def _debounce(widget, delay: int) \
        -> Callable[[Callable[..., _T]], Callable[..., None]]:
    """
    A decorator that debounces a function.

    After the function is called, it is not evaluated until the delay time has
    elapsed. If the function is called again before the delay is over, the
    delay is reset.

    :param widget: the Tk widget to use as a delay timer
    :param delay: the delay in milliseconds
    :return:
        a decorator for debouncing a function using the given widget and delay
    """
    timer_id = None

    def decorator(function: Callable[..., _T]) -> Callable[..., None]:
        @wraps(function)
        def wrapper(*args, **kwargs) -> None:
            nonlocal timer_id
            if timer_id is not None:
                widget.after_cancel(timer_id)
            timer_id = widget.after(delay, lambda: function(*args, **kwargs))

        return wrapper

    return decorator
