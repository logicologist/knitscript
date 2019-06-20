import os
import platform
from functools import wraps
from idlelib.redirector import WidgetRedirector
from io import StringIO
from tkinter import BOTH, DISABLED, END, Event, FLAT, LEFT, Menu, NORMAL, NS, \
    NSEW, RIGHT, Text, Tk, VERTICAL, Y, YES, Widget, filedialog, \
    messagebox
from tkinter.font import Font, nametofont
from tkinter.ttk import Frame, Scrollbar, Separator
from typing import Callable, TypeVar

from knitscript.editor._document import FileDocument
from knitscript.loader import load_text

_T = TypeVar("_T")

if platform.system() == "Darwin":
    _KEYS = {
        "new": ("Cmd+N", "<Command-n>"),
        "open": ("Cmd+O", "<Command-o>"),
        "save": ("Cmd+S", "<Command-s>"),
        "close": ("Cmd+W", "<Command-w>")
    }
else:
    _KEYS = {
        "new": ("Ctrl+N", "<Control-n>"),
        "open": ("Ctrl+O", "<Control-o>"),
        "save": ("Ctrl+S", "<Control-s>"),
        "close": ("Ctrl+W", "<Control-w>")
    }

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


class Window(Frame):
    """The editor window."""

    def __init__(self, master: Tk) -> None:
        """
        Creates the editor window.

        :param master: the parent widget
        """
        super().__init__(master)
        self._document = FileDocument(master)
        self._document.text = _DEFAULT_DOCUMENT
        self.master.title(self._document.name)
        self.master.configure(menu=self._create_menu())

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self._editor = _Editor(self, self._document, width=500, height=500)
        self._editor.text = _DEFAULT_DOCUMENT
        self._editor.grid(row=0, column=0, sticky=NSEW)

        def update_title():
            self.master.title(self._document.name +
                              (" — Edited" if self._document.modified else ""))

        for name in "<<Opened>>", "<<Modified>>", "<<SavedAs>>":
            self._document.bind(name, lambda event: update_title(), add=True)

        sep = Separator(self, orient=VERTICAL)
        sep.grid(row=0, column=1, sticky=NS)

        preview = _Preview(self, self._document, width=500, height=500)
        preview.grid(row=0, column=2, sticky=NSEW)

        def on_delete():
            if self._can_reset_document():
                self.master.destroy()

        self.pack(expand=YES, fill=BOTH)
        self.master.wm_protocol("WM_DELETE_WINDOW", on_delete)
        self.master.createcommand(
            "tkAboutDialog",
            lambda: self.master.call("::tk::mac::standardAboutPanel")
        )
        self.master.createcommand("::tk::mac::Quit", on_delete)

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

    def close(self) -> None:
        """
        Closes the window after asking the user to save (if there are any
        unsaved changes).
        """
        if self._can_reset_document():
            self.master.destroy()

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

    def _create_menu(self) -> Menu:
        menu = Menu(self.master)
        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="New", command=self.new,
                              underline=0, accelerator=_KEYS["new"][0])
        self.master.bind_all(_KEYS["new"][1], lambda event: self.new())
        file_menu.add_command(label="Open", command=self.open,
                              underline=0, accelerator=_KEYS["open"][0])
        self.master.bind_all(_KEYS["open"][1], lambda event: self.open())
        file_menu.add_command(label="Save", command=self.save,
                              underline=0, accelerator=_KEYS["save"][0])
        self.master.bind_all(_KEYS["save"][1], lambda event: self.save())
        file_menu.entryconfigure(2, state=DISABLED)
        self._document.bind(
            "<<Modified>>",
            lambda event: file_menu.entryconfigure(
                2, state=NORMAL if self._document.modified else DISABLED
            ),
            add=True
        )
        file_menu.add_command(label="Save As", command=self.save_as,
                              underline=5)
        file_menu.add_command(label="Close", command=self.close,
                              underline=0, accelerator=_KEYS["close"][0])
        self.master.bind_all(_KEYS["close"][1], lambda event: self.close())
        menu.add_cascade(label="File", menu=file_menu, underline=0)
        return menu


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
        self._text = Text(self, undo=True, font=_get_fixed_font(),
                          padx=5, pady=5, relief=FLAT, highlightthickness=0)

        scrollbar = Scrollbar(self, command=self._text.yview)
        self._text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self._text.pack(side=LEFT, expand=YES, fill=BOTH)

        # TODO:
        #  This is kind of a hack to stop Ctrl-O from inserting a new line. :/
        if platform.system() != "Darwin":
            def on_open(_event):
                self.master.open()
                return "break"

            self._text.bind("<Control-o>", on_open)

        def on_text_key() -> None:
            document.text = _strip_trailing_newline(self._text.get("1.0", END))
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

    # noinspection PyShadowingNames
    def __init__(self, master: Widget, document: FileDocument, **kwargs) \
            -> None:
        """
        Creates a live preview widget.

        :param master: the parent widget
        :param document: the model for the current KnitScript document
        """
        super().__init__(master, **kwargs)
        self.pack_propagate(False)
        self._text = Text(self,
                          font=_get_default_font(),
                          padx=5, pady=5,
                          relief=FLAT,
                          bg=("systemSheetBackground"
                              if platform.system() == "Darwin"
                              else "systemMenu"),
                          highlightthickness=0)
        redirector = WidgetRedirector(self._text)
        redirector.register("insert", lambda *args, **kwargs: "break")
        redirector.register("delete", lambda *args, **kwargs: "break")

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
        self._text.replace("1.0", END, output.getvalue())


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


def _strip_trailing_newline(string: str) -> str:
    if len(string) >= 2 and string[-2:] == "\r\n":
        return string[:-2]
    elif len(string) >= 1 and string[-1] == "\n":
        return string[:-1]
    else:
        return string
