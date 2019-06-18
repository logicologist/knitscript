import os
import platform
from functools import wraps
from io import StringIO
from tkinter import BOTH, DISABLED, END, Event, FLAT, LEFT, Menu, Misc, \
    NORMAL, NS, NSEW, RIGHT, Text, VERTICAL, Y, YES, Widget, filedialog, \
    messagebox
from tkinter.font import Font, nametofont
from tkinter.ttk import Frame, Scrollbar, Separator
from typing import Callable, TypeVar

from knitscript.editor.document import FileDocument
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

    def __init__(self, master: Misc) -> None:
        """
        Creates the editor application.

        :param master: the parent widget
        """
        super().__init__(master)
        document = FileDocument(master)
        document.text = _DEFAULT_DOCUMENT
        window = _Window(master, document)
        window.pack(expand=YES, fill=BOTH)

        menu = Menu(master)
        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="New", command=window.new,
                              underline=0, accelerator="Ctrl+N")
        self.master.bind_all("<Control-n>", lambda event: window.new())
        file_menu.add_command(label="Open", command=window.open,
                              underline=0, accelerator="Ctrl+O")
        self.master.bind_all("<Control-o>", lambda event: window.open())
        file_menu.add_command(label="Save", command=window.save,
                              underline=0, accelerator="Ctrl+S")
        self.master.bind_all("<Control-s>", lambda event: window.save())
        file_menu.entryconfigure(2, state=DISABLED)
        document.bind(
            "<<Modified>>",
            lambda event: file_menu.entryconfigure(
                2, state=NORMAL if document.modified else DISABLED
            ),
            add=True
        )
        file_menu.add_command(label="Save As", command=window.save_as)
        menu.add_cascade(label="File", menu=file_menu, underline=0)
        master.configure(menu=menu)


class _Window(Frame):
    """The editor window."""

    def __init__(self, master: Misc, document: FileDocument) -> None:
        """
        Creates the editor window.

        :param master: the parent widget
        :param document: the model for the current KnitScript document
        """
        super().__init__(master)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self._document = document
        self.master.title(self._document.name)
        self._editor = _Editor(self, self._document, width=500, height=500)
        self._editor.text = _DEFAULT_DOCUMENT
        self._editor.grid(row=0, column=0, sticky=NSEW)

        def update_title():
            self.master.title(self._document.name +
                              ("*" if self._document.modified else ""))

        for name in "<<Opened>>", "<<Modified>>", "<<SavedAs>>":
            self._document.bind(name, lambda event: update_title(), add=True)

        sep = Separator(self, orient=VERTICAL)
        sep.grid(row=0, column=1, sticky=NS)

        preview = _Preview(self, self._document, width=500, height=500)
        preview.grid(row=0, column=2, sticky=NSEW)

        def on_delete():
            if self._can_reset_document():
                self.master.destroy()

        self.master.protocol("WM_DELETE_WINDOW", on_delete)

    def new(self) -> None:
        """Resets the current document without saving."""
        if self._can_reset_document():
            self._document.new()

    def open(self) -> None:
        """Opens a file using a file dialog."""
        if self._can_reset_document():
            file = filedialog.askopenfile("r+", filetypes=_FILE_TYPES)
            if file is not None:
                self._document.open(file)

    def save(self) -> bool:
        """
        Saves the current file if there is one. Otherwise, opens the save as
        dialog.

        :return: True if the file was saved, or False if the user canceled
        """
        if self._document.file is None:
            return self.save_as()
        else:
            self._document.save()
            return True

    def save_as(self) -> bool:
        """
        Saves a file using a file dialog.

        :return: True if the file was saved, or False if the user canceled
        """
        file = filedialog.asksaveasfile(defaultextension=_EXTENSION,
                                        filetypes=_FILE_TYPES)
        if file is not None:
            self._document.save_as(file)
        return file is not None

    def _can_reset_document(self) -> bool:
        if not self._document.modified:
            return True
        response = messagebox.askyesnocancel(
            "KnitScript",
            f"Do you want to save changes to {self._document.name}?"
        )
        if response:
            return self.save()
        return response is not None


class _Editor(Frame):
    """A text editor widget."""

    def __init__(self, master: Widget, document: FileDocument, **kwargs) \
            -> None:
        """
        Creates a text editor widget.

        :param master: the parent widget
        :param document: the model for the current KnitScript document
        """
        super().__init__(master, **kwargs)
        self.pack_propagate(False)
        self._text = Text(self, font=_get_fixed_font(), undo=True, relief=FLAT)

        scrollbar = Scrollbar(self, command=self._text.yview)
        self._text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self._text.pack(side=LEFT, expand=YES, fill=BOTH)

        # TODO:
        #  This is kind of a hack to stop Ctrl-O from inserting a new line. :/
        def on_open(_event):
            self.master.open()
            return "break"

        self._text.bind("<Control-o>", on_open)

        def on_text_key() -> None:
            document.text = self._text.get("1.0", END)
            document.modified = self._text.edit_modified()

        self._text.bind("<Key>", lambda event: self.after_idle(on_text_key),
                        add=True)

        def bind_text_modified():
            def on_text_modified(_event: Event) -> None:
                document.modified = self._text.edit_modified()

            self._text.edit_modified(False)
            self._text.bind("<<Modified>>", on_text_modified, add=True)

        self._text.insert("1.0", document.text)
        self.after_idle(bind_text_modified)

        def on_document_opened(_event: Event) -> None:
            self._text.replace("1.0", END, document.text)
            self._text.edit_modified(False)

        def on_document_modified(_event: Event):
            if document.modified != self._text.edit_modified():
                self._text.edit_modified(document.modified)

        document.bind("<<Opened>>", on_document_opened, add=True)
        document.bind("<<Modified>>", on_document_modified, add=True)


class _Preview(Frame):
    """
    A live preview widget that displays the output of a KnitScript document.
    """

    def __init__(self, master: Widget, document: FileDocument, **kwargs) \
            -> None:
        """
        Creates a live preview widget.

        :param master: the parent widget
        :param document: the model for the current KnitScript document
        """
        super().__init__(master, **kwargs)
        self.pack_propagate(False)
        self._text = Text(self, font=_get_default_font(), state=DISABLED,
                          relief=FLAT, bg="SystemMenu")

        scrollbar = Scrollbar(self, command=self._text.yview)
        self._text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self._text.pack(side=LEFT, expand=YES, fill=BOTH)

        self._document = document
        self._document.bind("<<Opened>>", self._preview, add=True)
        self._document.bind("<<Set>>", _debounce(master, 500)(self._preview),
                            add=True)
        self._preview()

    def _preview(self, _event: Event = None) -> None:
        output = StringIO()
        try:
            load_text(self._document.text, output,
                      (os.path.dirname(self._document.file.name)
                       if self._document.file is not None
                       else None))
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


def _get_default_font() -> Font:
    font = nametofont("TkDefaultFont").copy()
    font.configure(size=13 if platform.system() == "Darwin" else 11)
    return font


def _get_fixed_font() -> Font:
    font = nametofont("TkFixedFont").copy()
    font.configure(size=13 if platform.system() == "Darwin" else 11)
    if platform.system() == "Windows":
        font.configure(family="Consolas")
    return font
