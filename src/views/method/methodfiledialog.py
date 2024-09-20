import os

from PyQt6 import QtWidgets

from src.utils.paths import isValidFilename, resourcePath

from src.views.base.formdialog import FormDialog


class MethodFormDialog(FormDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        inputs: list | tuple | None = None,
        values: list | tuple | None = None,
    ) -> None:
        super().__init__(parent, inputs, values)

    def _check(self) -> None:
        self._fill()
        self._errorLabel.clear()
        if not self._isFilenameValid():
            QtWidgets.QApplication.beep()
            return
        return super()._check()

    def _isFilenameValid(self) -> bool:
        filenameLineEdit = self._fields["filename"][-1]
        filename = filenameLineEdit.text()
        filenameLineEdit.setStyleSheet("color: red;")
        if not isValidFilename(filename):
            self._addError("This filename is not allowed!\n")
            return False
        if os.path.exists(resourcePath(f"methods/{filename}.atxm")):
            self._addError("This filename already exists!\n")
            return False
        if filename == "":
            self._addError("Please enter a filename!\n")
            return False
        filenameLineEdit.setStyleSheet("color: black;")
        return True
