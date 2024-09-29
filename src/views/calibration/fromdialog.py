import os

from typing import Sequence
from PyQt6 import QtWidgets

from src.utils.database import getDataframe
from src.utils.paths import isValidFilename, resourcePath
from src.views.base.formdialog import FormDialog


class CalibrationFormDialog(FormDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        inputs: Sequence | None = None,
        values: Sequence | None = None,
    ) -> None:
        super().__init__(parent, inputs, values)

    def _check(self) -> None:
        self._fill()
        self._errorLabel.clear()
        if not all(
            (
                self._isFilenameValid(),
                self._isElementValid(),
                self._isConcentrationValid(),
            )
        ):
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
        if os.path.exists(resourcePath(f"calibrations/{filename}.atxc")):
            self._addError("This filename already exists!\n")
            return False
        if filename == "":
            self._addError("Please enter a filename!\n")
            return False
        filenameLineEdit.setStyleSheet("color: black;")
        return True

    def _isElementValid(self) -> bool:
        elementLineEdit = self._fields["element"][-1]
        element = elementLineEdit.text()
        elementLineEdit.setStyleSheet("color: red;")
        if element not in getDataframe("Elements")["symbol"].values:
            self._addError("This element is not valid!\n")
            return False
        if element == "":
            self._addError("Please enter an element!\n")
            return False
        elementLineEdit.setStyleSheet("color: black;")
        return True

    def _isConcentrationValid(self) -> bool:
        concentrationLineEdit = self._fields["concentration"][-1]
        concentration = concentrationLineEdit.text()
        concentrationLineEdit.setStyleSheet("color: red;")
        if concentration == "":
            self._addError("Please enter a concentration!\n")
            return False
        if not 0 <= float(concentration) <= 100:
            self._addError("This concentration is not valid!\n")
            return False
        concentrationLineEdit.setStyleSheet("color: black;")
        return True
