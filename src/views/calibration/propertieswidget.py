import os

from PyQt6 import QtCore, QtGui, QtWidgets
from src.utils import datatypes
from src.utils.paths import isValidFilename


class CalibrationPropertiesWidget(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        calibration: None = None,
    ) -> None:
        super().__init__(parent)
        self._initializeUi()
        if calibration is not None:
            self.supply(calibration)
        self.hide()

    def _initializeUi(self) -> None:
        self._createFilenameLayout()
        self._createErrorLabel()
        self._createAnalyseFileLayout()
        self._setUpView()

    def _createFilenameLayout(self):
        self._filenameLayout = QtWidgets.QHBoxLayout()
        self._filenameLayout.addWidget(QtWidgets.QLabel("Filename:"))
        self._filenameLayout.addStretch(1)
        self._filenameLineEdit = QtWidgets.QLineEdit(self)
        self._filenameLineEdit.textEdited.connect(self._updateFilename)
        self._filenameLayout.addWidget(self._filenameLineEdit)
        self._filenameLayout.addStretch(10)

    def _createAnalyseFileLayout(self) -> None:
        self._analyseFileLayout = QtWidgets.QHBoxLayout()
        self._analyseFileLayout.addWidget(QtWidgets.QLabel("Analyse File:", self))
        self._analyseFileLayout.addStretch(1)

        self._analyseFileHyperLink = QtWidgets.QLabel(self)
        self._analyseFileHyperLink.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextBrowserInteraction
        )
        self._analyseFileHyperLink.setOpenExternalLinks(False)

        # Use HTML to make the text look like a hyperlink (blue and underlined)
        self._analyseFileHyperLink.setText('<a href="#">Click to select a file</a>')

        # Connect the hyperlink activation to the file dialog method
        self._analyseFileHyperLink.linkActivated.connect(self._setNewAnalyse)

        self._analyseFileLayout.addWidget(self._analyseFileHyperLink)
        self._analyseFileLayout.addStretch(10)

    def _createErrorLabel(self) -> None:
        self._errorLabel = QtWidgets.QLabel(self)
        self._errorLabel.setStyleSheet("color: red;")

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(self._filenameLayout)
        self.mainLayout.addWidget(self._errorLabel)
        self.mainLayout.addLayout(self._analyseFileLayout)
        self.mainLayout.addStretch()
        self.setLayout(self.mainLayout)

    @QtCore.pyqtSlot()
    def _updateFilename(self) -> None:
        filename = self._filenameLineEdit.text()
        if not isValidFilename(filename):
            self._filenameLineEdit.setText(self._calibration.filename)
            self._errorLabel.setText("This filename is not allowed!")
            return
        if os.path.exists(filename):
            self._filenameLineEdit.setText(self._calibration.filename)
            self._errorLabel.setText("This filename already exists!")
        else:
            self._calibration.filename = filename
            self._errorLabel.setText(None)

    @QtCore.pyqtSlot()
    def _setNewAnalyse(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open File",
            "./",
            "Antique'X Spectrum (*.atx);;Text Spectrum (*.txt)",
        )
        if path:
            analyse = (
                datatypes.Analyse.fromTXTFile(path)
                if path.endswith(".txt")
                else datatypes.Analyse.fromATXFile(path)
            )
            self._calibration.analyse = analyse
            self._analyseFileHyperLink.setText(f'<a href="#">{path}</a>')

    def supply(self, calibration: datatypes.Calibration) -> None:
        if calibration is None:
            return
        if self._calibration and self._calibration == calibration:
            return
        self.blockSignals(True)
        self._calibration = calibration
        self._filenameLineEdit.setText(self._calibration.filename)
        self._analyseFileHyperLink.setText(
            f'<a href="#">{self._calibration.analyse.filePath}</a>'
        )
        self.blockSignals(False)
