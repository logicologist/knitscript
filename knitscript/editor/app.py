from functools import wraps
from io import StringIO
from tkinter import BOTH, DISABLED, END, FLAT, Menu, NORMAL, NSEW, Text, Tk, \
    YES, Widget, filedialog
from tkinter.font import Font
from tkinter.ttk import Frame, Separator
from typing import Callable, TypeVar

from knitscript.loader import load_text

_T = TypeVar("_T")
_DEFAULT_DOCUMENT = ("pattern hello\n" +
                     "  row: CO 12.\n" +
                     "  row: K to end.\n" +
                     "  row: BO to end.\n" +
                     "end\n" +
                     "\n" +
                     "show (hello)")


class Application(Frame):
    """The editor application."""

    def __init__(self, master: Tk) -> None:
        """
        Creates the editor application.

        :param master: the toplevel Tk widget
        """
        super().__init__(master)
        window = _Window(master)
        window.pack()

        menu = Menu(master)
        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="Open", command=window.open)
        menu.add_cascade(label="File", menu=file_menu)
        master.configure(menu=menu)


class _Window(Frame):
    """The editor window."""

    def __init__(self, master: Tk):
        """
        Creates the editor window.

        :param master: the toplevel Tk widget
        """
        super().__init__(master)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self._editor = _Editor(self, width=500, height=500)
        self._editor.grid(row=0, column=0, sticky=NSEW)
        self._editor.text = _DEFAULT_DOCUMENT

        sep = Separator(self)
        sep.grid(row=0, column=1)

        preview = _Preview(self, self._editor, width=500, height=500)
        preview.grid(row=0, column=2, sticky=NSEW)

    def open(self) -> None:
        """Opens a file using a file dialog."""
        file = filedialog.askopenfile()
        if file is not None:
            self._editor.text = file.read()


class _Editor(Frame):
    """A text editor widget."""

    def __init__(self, master: Widget, **kwargs) -> None:
        """
        Creates a text editor widget.

        :param master: the parent widget
        """
        super().__init__(master, **kwargs)
        self.pack_propagate(False)
        self._text = Text(self,
                          font=Font(family="Consolas"), undo=True, relief=FLAT)
        self._text.pack(expand=YES, fill=BOTH)
        self._text.bind("<Key>",
                        lambda _event: self.event_generate("<<Typed>>"))

    @property
    def text(self) -> str:
        """The text in the editor."""
        return self._text.get("1.0", END)

    @text.setter
    def text(self, value: str) -> None:
        self._text.replace("1.0", END, value)
        self.event_generate("<<Changed>>")


class _Preview(Frame):
    """
    A live preview widget that displays the output of a KnitScript document.
    """

    def __init__(self, master: Widget, source: _Editor, **kwargs) -> None:
        """
        Creates a live preview widget.

        :param master: the parent widget
        :param source:
            the text editor widget containing the KnitScript document
        """
        super().__init__(master, **kwargs)
        self.pack_propagate(False)

        self._text = Text(self, state=DISABLED, relief=FLAT, bg="SystemMenu")
        self._text.configure(font=Font(family="Segoe UI"))
        self._text.pack(expand=YES, fill=BOTH)

        self._source = source
        self._source.bind("<<Changed>>", self._update)
        self._source.bind("<<Typed>>", _debounce(master, 500)(self._update))
        self._update()

    def _update(self, _event=None) -> None:
        output = StringIO()
        try:
            load_text(self._source.text, output)
        except Exception as e:
            # TODO: Catching all exceptions is too broad.
            output.write(f"error: {e}\n")
        self._text.configure(state=NORMAL)
        self._text.replace(1.0, END, output.getvalue())
        self._text.configure(state=DISABLED)


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
