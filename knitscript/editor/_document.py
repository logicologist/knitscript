import os
from tkinter import Misc
from tkinter.ttk import Frame
from typing import Optional, TextIO


class FileDocument(Frame):
    """A model for a document that corresponds to some file."""

    def __init__(self, master: Misc) -> None:
        """
        Creates a file document model.

        :param master: the parent widget
        """
        super().__init__(master)
        self._file = None
        self._text = ""
        self._modified = False

    def new(self) -> None:
        """Resets the current document without saving."""
        if self._file is not None:
            self._file.close()
        self._file = None
        self._text = ""
        self._modified = False
        self.event_generate("<<Opened>>")

    def open(self, file: TextIO) -> None:
        """
        Opens a new file as the current document.

        :param file: the file to open
        """
        if self._file is not None:
            self._file.close()
        self._file = file
        self._text = self._file.read()
        self.modified = False
        self.event_generate("<<Opened>>")

    def save(self) -> None:
        """Saves the current document to its original file."""
        self._file.seek(0)
        self._file.write(self._text)
        self._file.truncate()
        self.modified = False

    def save_as(self, file: TextIO) -> None:
        """
        Saves the current document to a new file.

        :param file: the new file to save to
        """
        self._file = file
        self.save()
        self.event_generate("<<SavedAs>>")

    @property
    def file(self) -> Optional[TextIO]:
        """The file for the current document."""
        return self._file

    @property
    def name(self) -> str:
        """The name of the current document."""
        return (os.path.basename(self._file.name)
                if self._file is not None
                else "Untitled")

    @property
    def text(self) -> str:
        """
        The text of the current document.

        **Note:** Setting the text does not automatically set :ref:`modified`,
        because the model does not check if the text has actually been modified
        or if it was reset to its original state after an undo. You should set
        :ref:`modified` to the right value after setting the text.
        """
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value
        self.event_generate("<<Set>>")

    @property
    def modified(self) -> bool:
        """
        Whether the document has been modified since the last time it was
        saved.
        """
        return self._modified

    @modified.setter
    def modified(self, value: bool) -> None:
        if self._modified != value:
            self._modified = value
            self.event_generate("<<Modified>>")
