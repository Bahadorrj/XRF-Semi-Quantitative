from functools import partial
from os import name
from PyQt6 import QtWidgets, QtGui, QtCore

from python.utils.paths import resourcePath
from python.utils.datatypes import Analyse


class CalibrationWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None, method: dict | None = ...,):
        assert method is not None, "method must be provided"
        super().__init__(parent)
        self._method = method

        self._createActions()
        self._createToolBar()
        self._createTable()
        self._setUpView()

    def _createActions(self) -> None:
        self._actionsMap = {}
        actions = ("Add",)
        for label in actions:
            action = QtGui.QAction(label)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"icons/{key}.png")))
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        if key == "add":
            self._openFileDialog()

    def _openFileDialog(self) -> None:
        fileName, filters = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open File",
            "./",
            "Antique'X Spectrum (*.atx)",
        )
        if fileName:
            analyse = Analyse.fromATXFile(fileName)
            if analyse.classification == "cal":
                self.addAnalyse(analyse)
            else:
                # TODO show error
                pass

    def addAnalyse(self, analyse: Analyse) -> None:
        self._table.setRowCount(self._table.rowCount() + 1)
        items = (
            QtCore.QTableWidgetItem(text=analyse.name),
            QtWidgets.QTableWidgetItem(text=analyse.concentrations[analyse.name]),
            QtCore.QTableWidgetItem(text=analyse.status),
        )
        for index, item in enumerate(items):
            self._table.setItem(self._table.rowCount() - 1, index, item)

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar()
        self._toolBar.addAction(self._actionsMap["add"])

    def _createTable(self) -> None:
        self._table = QtWidgets.QTableWidget()
        headerLabels = ("Component", "Amount", "Status")
        self._table.setColumnCount(len(headerLabels))
        self._table.setHorizontalHeaderLabels(headerLabels)
        self._table.horizontalHeader().setStretchLastSection(True)

    def _setUpView(self) -> None:
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.addWidget(self._toolBar)
        layout.addWidget(self._table)
        self.setLayout(layout)
