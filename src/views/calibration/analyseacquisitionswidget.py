from PyQt6 import QtCore, QtWidgets


class AnalyseAcquisitionWidget(QtWidgets.QWidget):
    """Widget for acquiring data from various sources.

    This widget provides buttons for users to either open files from local storage or retrieve data from a connected XRF analyzer. It emits a signal when the user chooses to open a file, facilitating interaction with other components of the application.

    Args:
        parent (QtWidgets.QWidget | None): An optional parent widget.

    Attributes:
        getAnalyseFile (QtCore.pyqtSignal): Signal emitted to request an analysis file.
    """

    getAnalyseFile = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._initializeUi()

    def _initializeUi(self) -> None:
        layout = QtWidgets.QVBoxLayout()
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addStretch()
        openFromLocalButton = QtWidgets.QPushButton("Open from local storage", self)
        openFromLocalButton.clicked.connect(lambda: self.getAnalyseFile.emit())
        self.mainLayout.addWidget(openFromLocalButton)
        self.mainLayout.addStretch()
        getFromSocketButton = QtWidgets.QPushButton(
            "Get from connected XRF analyser", self
        )
        self.mainLayout.addWidget(getFromSocketButton)
        self.mainLayout.addStretch()
        layout.addStretch()
        layout.addLayout(self.mainLayout)
        layout.addStretch()
        self.setLayout(layout)
