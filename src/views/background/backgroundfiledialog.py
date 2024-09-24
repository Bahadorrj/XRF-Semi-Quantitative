from PyQt6 import QtWidgets

from src.views.base.formdialog import FormDialog
from src.utils.paths import isValidFilename


class BackgroundFileDialog(FormDialog):
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
        filenameLineEdit = self._fields["filename"][-1]
        filename = filenameLineEdit.text()
        if not isValidFilename(filename):
            QtWidgets.QApplication.beep()
            return
        return super()._check()
