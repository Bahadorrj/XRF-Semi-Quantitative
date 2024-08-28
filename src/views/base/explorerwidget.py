from functools import partial

from PyQt6 import QtCore, QtGui, QtWidgets

from python.utils.paths import resourcePath


class Explorer(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super(Explorer, self).__init__(parent)
        self.setFixedSize(1200, 800)

    def _connectSignalsAndSlots(self):
        self._treeWidget.itemSelectionChanged.connect(self._changeWidget)

    def _createActions(self, labels: list | tuple) -> None:
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

    def _createMenus(self, labels: list | tuple) -> None:
        self._menusMap = {}
        self._menuBar = QtWidgets.QMenuBar()
        for label in labels:
            menu = self._menuBar.addMenu(label)
            key = label.lower()[1:]
            self._menusMap[key] = menu

    def _fillMenusWithActions(self) -> None:
        pass

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar()
        self._toolBar.setIconSize(QtCore.QSize(16, 16))
        self._toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._toolBar.setMovable(False)

    def _fillToolBarWithActions(self) -> None:
        pass

    def _createTreeWidget(self) -> None:
        self._treeWidget = QtWidgets.QTreeWidget()
        self._treeWidget.setFixedWidth(200)

    def _fillTreeWithItems(self, header: str, labels: list | tuple) -> None:
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
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.addWidget(self._treeWidget)
        self.mainLayout.addWidget(QtWidgets.QWidget())
        vLayout = QtWidgets.QVBoxLayout()
        vLayout.setContentsMargins(0, 0, 0, 0)
        vLayout.addWidget(self._menuBar)
        vLayout.addWidget(self._toolBar)
        vLayout.addLayout(self.mainLayout)
        self.setLayout(vLayout)
