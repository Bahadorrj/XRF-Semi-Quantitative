from functools import partial
from PyQt6 import QtCore, QtGui, QtWidgets

from python.utils.paths import resourcePath


class Explorer(QtWidgets.QMainWindow):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super(Explorer, self).__init__(parent)
        self.setFixedSize(1200, 800)

    def _createActions(self, labels: list[str] | tuple[str]) -> None:
        self._actionsMap = {}
        for label in labels:
            action = QtGui.QAction(label)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"icons/{key}.png")))
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        pass

    def _reinitializeWidget(self):
        pass

    def _createMenus(self, labels: list[str] | tuple[str]) -> None:
        self._menusMap = {}
        menuBar = self.menuBar()
        for label in labels:
            menu = menuBar.addMenu(label)
            key = label.lower()[1:]
            self._menusMap[key] = menu

    def _fillMenusWithActions(self, relations: dict[list]) -> None:
        for key, values in relations.items():
            for value in values:
                self._menusMap[key].addAction(self._actionsMap[value])

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar(self)
        self._toolBar.setIconSize(QtCore.QSize(16, 16))
        self._toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._toolBar.setMovable(False)
        self.addToolBar(self._toolBar)

    def _fillToolBarWithActions(self, labels: list[str] | tuple[str]) -> None:
        for label in labels:
            self._toolBar.addAction(self._actionsMap[label])

    def _createTreeWidget(self) -> None:
        self._treeWidget = QtWidgets.QTreeWidget(self)
        self._treeWidget.setFixedWidth(200)
        self._treeWidget.itemSelectionChanged.connect(self._changeWidget)

    def _fillTreeWithItems(self, header: str, labels: list[str] | tuple[str]) -> None:
        self._treeItemMap = {}
        headerItem = QtWidgets.QTreeWidgetItem()
        headerItem.setText(0, header)
        headerItem.setIcon(0, QtGui.QIcon(resourcePath("icons/contents.png")))
        self._treeItemMap[header] = headerItem
        self._treeWidget.setHeaderItem(headerItem)
        for label in labels:
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, label)
            key = "-".join(label.lower().split(" "))
            item.setIcon(0, QtGui.QIcon(resourcePath(f"icons/{key}.png")))
            self._treeItemMap[key] = item
            self._treeWidget.addTopLevelItem(item)

    @QtCore.pyqtSlot()
    def _changeWidget(self) -> None:
        pass

    def _setUpView(self) -> None:
        self._mainLayout = QtWidgets.QHBoxLayout()
        self._mainLayout.addWidget(self._treeWidget)
        self._mainLayout.addWidget(QtWidgets.QWidget(self))
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(self._mainLayout)
        self.setCentralWidget(centralWidget)
