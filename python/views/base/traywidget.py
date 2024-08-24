from functools import partial

from PyQt6 import QtCore, QtGui, QtWidgets

from python.utils.paths import resourcePath
from python.views.base.tablewidgets import DataframeTableWidget


class TrayWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        self._widgets = {}
        super().__init__(parent)
        self.setFixedSize(800, 800)

    def _connectSignalsAndSlots(self) -> None:
        self._tableWidget.currentCellChanged.connect(self._currentCellChanged)

    def _createActions(self, labels: dict) -> None:
        self._actionsMap = {}
        for label, disabled in labels.items():
            action = QtGui.QAction(label)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"icons/{key}.png")))
            action.setDisabled(disabled)
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))

    @QtCore.pyqtSlot(str)
    def _actionTriggered(self, key: str) -> None:
        pass

    def _createMenus(self, labels: list | tuple) -> None:
        self._menusMap = {}
        self._menuBar = QtWidgets.QMenuBar()
        self._menuBar.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        for label in labels:
            menu = self._menuBar.addMenu(label)
            key = label.lower()[1:]
            self._menusMap[key] = menu

    def _fillMenusWithActions(self) -> None:
        pass

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar()
        self._toolBar.setIconSize(QtCore.QSize(16, 16))
        self._toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self._toolBar.setMovable(False)
        self._fillToolBarWithActions()

    def _fillToolBarWithActions(self) -> None:
        pass

    def _createTableWidget(self) -> None:
        self._tableWidget = DataframeTableWidget(autofill=True)

    @QtCore.pyqtSlot(int, int)
    def _currentCellChanged(self, currentRow: int, currentColumn: int, previousRow: int, previousColumn: int) -> None:
        pass

    def _createTabLayout(self):
        toolBar = QtWidgets.QToolBar()
        toolBar.addAction(self._actionsMap["edit"])
        self._createTabWidget()
        self._viewLayout = QtWidgets.QVBoxLayout()
        self._viewLayout.addWidget(toolBar)
        self._viewLayout.addWidget(self._tabWidget)

    def _createTabWidget(self) -> None:
        self._tabWidget = QtWidgets.QTabWidget()

    def _addWidgets(self, widgets: dict):
        self._widgets = widgets
        self._tabWidget.clear()
        for label, widget in self._widgets.items():
            self._tabWidget.addTab(widget, label)

    def _setUpView(self) -> None:
        vLayout = QtWidgets.QVBoxLayout()
        vLayout.setContentsMargins(0, 0, 0, 0)
        vLayout.addWidget(self._menuBar)
        self._mainLayout = QtWidgets.QVBoxLayout()
        self._mainLayout.setContentsMargins(10, 10, 10, 10)
        self._mainLayout.addWidget(self._toolBar)
        self._mainLayout.addWidget(self._tableWidget)
        self._mainLayout.addLayout(self._viewLayout)
        vLayout.addLayout(self._mainLayout)
        self.setLayout(vLayout)
