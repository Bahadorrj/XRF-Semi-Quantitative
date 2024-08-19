from functools import partial

from PyQt6 import QtWidgets, QtGui, QtCore

from python.utils import datatypes
from python.utils.paths import resourcePath
from python.views.base.tablewidgets import TableWidget


class CalibrationWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None, method: datatypes.Method | None = None):
        assert method is not None, "method must be provided"
        super().__init__(parent)
        self._method = method

        self._createActions()
        self._createToolBar()
        self._createTable()
        self._setUpView()

    def _createActions(self) -> None:
        self._actionsMap = {}
        actions = ("Add", "Remove")
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
        filename, filters = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open File",
            "./",
            "Antique'X calibration (*.atxc)",
        )
        if filename:
            pass

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar()
        self._toolBar.addAction(self._actionsMap["add"])

    def _createTable(self) -> None:
        self._table = TableWidget()
        headerLabels = ("Component", "Amount", "Status")
        self._table.setHeaders(headerLabels)
        self._table.setHorizontalHeaderLabels(headerLabels)
        self._table.horizontalHeader().setStretchLastSection(True)

    def _setUpView(self) -> None:
        self._mainLayout = QtWidgets.QVBoxLayout()
        self._mainLayout.setContentsMargins(30, 30, 30, 30)
        self._mainLayout.addWidget(self._toolBar)
        self._mainLayout.addWidget(self._table)
        self.setLayout(self._mainLayout)
