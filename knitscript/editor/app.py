import os
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
_EXTENSION = ".ks"
_FILE_TYPES = [("KnitScript Document", "*" + _EXTENSION),
               ("All Files", "*.*")]


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
        file_menu.add_command(label="Save", command=window.save)
        file_menu.add_command(label="Save As", command=window.save_as)
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
        self._editor.text = _DEFAULT_DOCUMENT
        self._editor.grid(row=0, column=0, sticky=NSEW)
        self._file = None
        self._title = "New Document"

        def on_modified(_event):
            self._modified = self._editor.modified

        self._editor.bind("<<Modified>>", on_modified)

        sep = Separator(self)
        sep.grid(row=0, column=1)

        preview = _Preview(self, self._editor, width=500, height=500)
        preview.grid(row=0, column=2, sticky=NSEW)

    def open(self) -> None:
        """Opens a file using a file dialog."""
        file = filedialog.askopenfile("r+", filetypes=_FILE_TYPES)
        if file is not None:
            if self._file is not None:
                self._file.close()
            self._file = file
            self._editor.text = self._file.read()
            self._title = os.path.basename(self._file.name)
            self._modified = False

    def save(self) -> None:
        """
        Saves the current file if there is one. Otherwise, opens the save as
        dialog.
        """
        if self._file is None:
            self.save_as()
        else:
            self._file.seek(0)
            self._file.write(self._editor.text)
            self._file.truncate()
            self._modified = False

    def save_as(self) -> None:
        """Saves a file using a file dialog."""
        file = filedialog.asksaveasfile(defaultextension=_EXTENSION,
                                        filetypes=_FILE_TYPES)
        if file is not None:
            self._title = os.path.basename(file.name)
            self._file = file
            self.save()

    @property
    def _modified(self) -> bool:
        return self._editor.modified

    @_modified.setter
    def _modified(self, value) -> None:
        if value != self._editor.modified:
            self._editor.modified = value
        self._title = self._title

    @property
    def _title(self) -> str:
        return self.__title

    @_title.setter
    def _title(self, value) -> None:
        self.__title = value
        self.master.title(self.__title + ("*" if self._modified else ""))


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

        def bind_modified():
            self._text.edit_modified(False)
            self._text.bind("<<Modified>>",
                            lambda _event: self.event_generate("<<Modified>>"))

        self.after_idle(bind_modified)

    @property
    def text(self) -> str:
        """The text in the editor."""
        return self._text.get("1.0", END)

    @text.setter
    def text(self, value: str) -> None:
        self._text.replace("1.0", END, value)
        self.event_generate("<<Set>>")

    @property
    def modified(self) -> bool:
        """
        Whether the editor has been modified since the last save.
        """
        return self._text.edit_modified()

    @modified.setter
    def modified(self, value) -> None:
        self._text.edit_modified(value)


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
        self._source.bind("<<Set>>", self._update)
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
