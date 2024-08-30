from functools import partial

from PyQt6 import QtCore, QtGui, QtWidgets

from src.utils.paths import resourcePath
from src.views.base.tablewidget import DataframeTableWidget


class TrayWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(1000, 800)

    def _connectSignalsAndSlots(self) -> None:
        self._tableWidget.currentCellChanged.connect(self._currentCellChanged)

    def _createActions(self, labels: dict) -> None:
        self._actionsMap = {}
        for label, disabled in labels.items():
            action = QtGui.QAction(label)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"resources/icons/{key}.png")))
            action.setDisabled(disabled)
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))

    @QtCore.pyqtSlot(str)
    def _actionTriggered(self, key: str) -> None:
        pass

    def _createMenus(self, labels: list | tuple) -> None:
        self._menusMap = {}
        self._menuBar = QtWidgets.QMenuBar()
        self._menuBar.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        for label in labels:
            menu = self._menuBar.addMenu(label)
            key = label.lower()[1:]
            self._menusMap[key] = menu

    def _fillMenusWithActions(self) -> None:
        pass

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar()
        self._toolBar.setIconSize(QtCore.QSize(16, 16))
        self._toolBar.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self._toolBar.setMovable(False)
        self._fillToolBarWithActions()

    def _fillToolBarWithActions(self) -> None:
        pass

    def _createTableWidget(self) -> None:
        self._tableWidget = DataframeTableWidget(autofill=True)

    @QtCore.pyqtSlot(int, int)
    def _currentCellChanged(
        self, currentRow: int, currentColumn: int, previousRow: int, previousColumn: int
    ) -> None:
        pass

    def _createTabWidget(self) -> None:
        self._tabWidget = QtWidgets.QTabWidget()

    def _addWidgets(self, widgets: dict):
        self._tabWidget.clear()
        for label, widget in widgets.items():
            self._tabWidget.addTab(widget, label)

    def _setUpView(self) -> None:
        vLayout = QtWidgets.QVBoxLayout()
        vLayout.setContentsMargins(0, 0, 0, 0)
        vLayout.addWidget(self._menuBar)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(10)
        self.mainLayout.addWidget(self._toolBar)
        self.mainLayout.addWidget(self._tableWidget)
        self.mainLayout.addWidget(self._tabWidget)
        vLayout.addLayout(self.mainLayout)
        self.setLayout(vLayout)
