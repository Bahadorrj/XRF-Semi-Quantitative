import pandas

from functools import partial
from PyQt6 import QtCore, QtGui, QtWidgets

from src.utils.paths import resourcePath
from src.views.base.tablewidget import DataframeTableWidget


class TrayWidget(QtWidgets.QWidget):
    """A widget that serves as a container for various UI components.

    This class provides a structured layout for managing actions, menus, toolbars, and data display within a tray interface. It initializes the user interface and handles interactions with the contained elements.

    Args:
        parent (QtWidgets.QWidget | None): An optional parent widget.

    Attributes:
        actionsMap (dict): A mapping of action keys to their corresponding QAction objects.
        menusMap (dict): A mapping of menu keys to their corresponding QMenu objects.
        widgets (dict): A mapping of widget labels to their corresponding widget instances.
        tableWidget (DataframeTableWidget): The table widget used for displaying data.
        tabWidget (QTabWidget): The tab widget used for displaying data.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(1000, 800)

        self._widgets = {}
        self._menusMap = {}
        self._actionsMap = {}

    def _initializeUi(self) -> None:
        self.setObjectName("tray-list")
        self._createActions(
            {
                "Add": False,
                "Remove": True,
                "Close": False,
                "Print": True,
                "Print Preview": True,
                "Print Setup": True,
                "Edit": True,
                "Import": False,
            }
        )
        self._createMenus(("&File", "&Edit", "&View", "&Window", "&Help"))
        self._fillMenusWithActions()
        self._createToolBar()
        self._fillToolBarWithActions()
        self._createTableWidget()
        self._createTabWidget()
        self._setUpView()

    def _createActions(self, labels: dict) -> None:
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
        self._menuBar = QtWidgets.QMenuBar()
        self._menuBar.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        for label in labels:
            menu = self._menuBar.addMenu(label)
            key = label.lower()[1:]
            self._menusMap[key] = menu

    def _fillMenusWithActions(self) -> None:
        file_actions = [
            self._actionsMap["import"],
            "separator",
            self._actionsMap["print"],
            self._actionsMap["print-preview"],
            self._actionsMap["print-setup"],
            "separator",
            self._actionsMap["close"],
        ]
        edit_actions = [
            self._actionsMap["add"],
            self._actionsMap["edit"],
            self._actionsMap["remove"],
        ]
        for action in file_actions:
            if action == "separator":
                self._menusMap["file"].addSeparator()
            else:
                self._menusMap["file"].addAction(action)
        for action in edit_actions:
            self._menusMap["edit"].addAction(action)

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar()
        self._toolBar.setIconSize(QtCore.QSize(16, 16))
        self._toolBar.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self._toolBar.setMovable(False)
        self._fillToolBarWithActions()

    def _fillToolBarWithActions(self) -> None:
        self._toolBar.addAction(self._actionsMap["import"])
        self._toolBar.addAction(self._actionsMap["add"])
        self._toolBar.addSeparator()
        self._toolBar.addAction(self._actionsMap["edit"])
        self._toolBar.addSeparator()
        self._toolBar.addAction(self._actionsMap["remove"])

    def _createTableWidget(self) -> None:
        self._tableWidget = DataframeTableWidget(autofill=True)
        self._tableWidget.currentCellChanged.connect(self._currentCellChanged)

    @QtCore.pyqtSlot(int, int)
    def _currentCellChanged(
        self, currentRow: int, currentColumn: int, previousRow: int, previousColumn: int
    ) -> None:
        if currentRow not in [previousRow, -1]:
            if self._tabWidget.count() == 0:
                self._addWidgets(self._widgets)
            if editAction := self._actionsMap.get("edit", None):
                editAction.setDisabled(False)
            if removeAction := self._actionsMap.get("remove", None):
                removeAction.setDisabled(False)
        elif currentRow == -1:
            self._tabWidget.clear()
            if editAction := self._actionsMap.get("edit", None):
                editAction.setDisabled(True)
            if removeAction := self._actionsMap.get("remove", None):
                removeAction.setDisabled(True)

    def _createTabWidget(self) -> None:
        self._tabWidget = QtWidgets.QTabWidget()

    def _addWidgets(self, widgets: dict):
        self._tabWidget.clear()
        for label, widget in widgets.items():
            if widget.contentsMargins().left() == 0:
                widget.mainLayout.setContentsMargins(10, 10, 10, 10)
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

    def _supplyWidgets(self) -> None:
        pass

    def supply(self, dataframe: pandas.DataFrame) -> None:
        """Supply data to the widget from a given DataFrame.

        This function updates the internal DataFrame and clears the tab widget to prepare for new data. It temporarily blocks signals to prevent unnecessary updates during the data supply process.

        Args:
            self: The instance of the class.
            dataframe (pandas.DataFrame): The DataFrame containing the data to supply.

        Returns:
            None
        """
        self.blockSignals(True)
        self._df = dataframe
        self._tabWidget.clear()
        self.blockSignals(False)

    @property
    def actionsMap(self):
        return self._actionsMap

    @property
    def menusMap(self):
        return self._menusMap

    @property
    def widgets(self):
        return self._widgets

    @property
    def tableWidget(self):
        return self._tableWidget

    @property
    def tabWidget(self):
        return self._tabWidget
