from functools import partial

from PyQt6 import QtGui, QtWidgets


class FormDialog(QtWidgets.QDialog):
    def __init__(self,
                 parent: QtWidgets.QWidget | None = None,
                 inputs: list | tuple | None = None,
                 values: list | tuple | None = None) -> None:
        super(FormDialog, self).__init__(parent)
        self.setFixedSize(250, 200)
        self.setModal(True)
        if inputs is not None:
            self._fields = {key: "" for key in inputs}
            if values is not None:
                for key, value in zip(inputs, values):
                    self._fields[key] = value
            self._initializeUi()

    def _initializeUi(self) -> None:
        self._mainLayout = QtWidgets.QVBoxLayout()
        for key, value in self._fields.items():
            label = QtWidgets.QLabel(f"{key}:")
            lineEdit = QtWidgets.QLineEdit(value)
            if key == "concentration":
                lineEdit.setValidator(QtGui.QDoubleValidator())
            lineEdit.setFixedWidth(100)
            lineEdit.editingFinished.connect(partial(self._fill, lineEdit, key))
            layout = QtWidgets.QHBoxLayout()
            layout.addWidget(label)
            layout.addWidget(lineEdit)
            self._mainLayout.addLayout(layout)
        self._mainLayout.addStretch()
        self._errorLabel = QtWidgets.QLabel()
        self._errorLabel.setStyleSheet("color: red;")
        self._mainLayout.addWidget(self._errorLabel)
        buttonBox = QtWidgets.QDialogButtonBox()
        buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        buttonBox.accepted.connect(self._check)
        buttonBox.rejected.connect(self.reject)
        self._mainLayout.addWidget(buttonBox)
        self.setLayout(self._mainLayout)

    def _fill(self, lineEdit: QtWidgets.QLineEdit, key: str) -> None:
        self._fields[key] = lineEdit.text()

    def _check(self) -> None:
        if all(value != "" for value in self._fields.values()):
            self.accept()
        else:
            QtWidgets.QApplication.beep()

    @property
    def fields(self):
        return self._fields
