from typing import Sequence

from PyQt6 import QtGui, QtWidgets, QtCore


class FormDialog(QtWidgets.QDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        inputs: Sequence | None = None,
        values: Sequence | None = None,
    ) -> None:
        super(FormDialog, self).__init__(parent)
        self.setModal(True)
        self._inputs = inputs
        self._values = values
        self._fields = {}
        self._initializeUi()

    def _initializeUi(self) -> None:
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self._createFields()
        self._createErrorLabel()
        self._createButtonBox()
        self._setUpView()

    def _createFields(self) -> None:
        if self._values is None:
            self._values = ["" for _ in self._inputs]
        for i, v in zip(self._inputs, self._values):
            label = QtWidgets.QLabel(i)
            lineEdit = QtWidgets.QLineEdit(v)
            if i == "concentration":
                lineEdit.setValidator(QtGui.QDoubleValidator())
            lineEdit.setFixedWidth(150)
            self._fields[i] = (label, lineEdit)

    def _createErrorLabel(self) -> None:
        self._errorLabel = QtWidgets.QLabel()
        self._errorLabel.setStyleSheet("color: red;")

    def _addError(self, message: str) -> None:
        self._errorLabel.setText(self._errorLabel.text() + message)

    def _createButtonBox(self) -> None:
        self._buttonBox = QtWidgets.QDialogButtonBox()
        self._buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        self._buttonBox.accepted.connect(self._check)
        self._buttonBox.rejected.connect(self.reject)

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QFormLayout()
        for widgets in self._fields.values():
            qLabel, qLineEdit = widgets
            self.mainLayout.addRow(qLabel, qLineEdit)
        self.mainLayout.addWidget(self._errorLabel)
        self.mainLayout.addWidget(self._buttonBox)
        self.setLayout(self.mainLayout)

    def _fill(self) -> None:
        for index, widgets in enumerate(self._fields.values()):
            _, qLineEdit = widgets
            self._values[index] = qLineEdit.text()

    def _check(self) -> None:
        self._fill()
        if all(value != "" for value in self._values):
            self.accept()
        else:
            QtWidgets.QApplication.beep()
            self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

    def errorMessage(self) -> str:
        return self._errorLabel.text()

    @property
    def fields(self):
        return {k: v for k, v in zip(self._inputs, self._values)}
