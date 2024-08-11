import pandas as pd

from functools import partial
from json import dumps, loads
from PyQt6 import QtCore, QtGui, QtWidgets

from python.utils.paths import resourcePath
from python.utils.database import getDatabase
from python.utils import encryption

from python.views.methodexplorer.analyte import AnalytesAndConditionsWidget
from python.views.methodexplorer.calibration import CalibrationWidget


class MethodExplorer(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MethodExplorer, self).__init__(parent)
        self._db = getDatabase(resourcePath("fundamentals.db"))
        self._method = {
            "conditions": self._db.dataframe("SELECT * FROM Conditions")
            .query("active == 1")
            .drop(["condition_id", "active"], axis=1),
            "lines": self._db.dataframe("SELECT * FROM Lines"),
            "calibrations": [],
            "report": {},
        }
        self.setObjectName("method-explorer")
        self.setFixedSize(900, 600)
        self.setWindowTitle("Method explorer")
        self._createActions()
        self._createMenuBar()
        self._createToolBar()
        self._createTreeWidget()
        self._setUpView()

    def _createActions(self) -> None:
        self._actionsMap = {}
        actions = ("New", "Open", "Save as", "Close")
        for label in actions:
            action = QtGui.QAction(label)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"icons/{key}.png")))
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))

    def _actionTriggered(self, key: str) -> None:
        if key == "new":
            messageBox = QtWidgets.QMessageBox()
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
            messageBox.setWindowTitle("New method")
            messageBox.setText("Are you sure you want to open a new method?")
            messageBox.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
            )
            result = messageBox.exec()
            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                self._method = {
                    "conditions": self._db.dataframe("SELECT * FROM Conditions")
                    .query("active == 1")
                    .drop(["condition_id", "active"], axis=1),
                    "lines": self._db.dataframe("SELECT * FROM Lines"),
                    "calibrations": [],
                }
                self._reinitializeWidget()
        elif key == "open":
            filename, filters = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Open File",
                "./",
                "Antique'X Method (*.atxm)",
            )
            if filename:
                with open(filename, "r") as f:
                    encryptionKey = encryption.loadKey()
                    encryptedText = f.readline()
                    decryptedText = encryption.decryptText(encryptedText, encryptionKey)
                    method = loads(decryptedText)
                    self._method = {
                        "conditions": pd.DataFrame(method["conditions"]),
                        "lines": pd.DataFrame(method["lines"]),
                        "calibrations": method["calibrations"],
                    }
                    self._reinitializeWidget()
        elif key == "save-as":
            filename, filters = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save Method",
                "./",
                "Antique'X Method (*.atxm)",
            )
            if filename:
                key = encryption.loadKey()
                with open(filename, "wb") as f:
                    hashableDict = self._toHashableDict(self._method)
                    jsonText = dumps(hashableDict)
                    encryptedText = encryption.encryptText(jsonText, key)
                    f.write(encryptedText + b"\n")
        elif key == "close":
            self.close()

    def _reinitializeWidget(self):
        widget = self._mainLayout.itemAt(1).widget()
        # Get the class name of the widget
        className = type(widget).__name__

        # Delete the existing widget
        widget.deleteLater()

        # Dynamically get the class from globals() and create a new instance
        widgetClass = globals()[className]
        newWidget = widgetClass(self, self._method)
        self._mainLayout.addWidget(newWidget)

    @staticmethod
    def _toHashableDict(method: dict):
        hashableDicy = method.copy()
        hashableDicy["conditions"] = method["conditions"].to_dict()
        hashableDicy["lines"] = method["lines"].to_dict()
        return hashableDicy

    def _createMenuBar(self) -> None:
        self._createMenus()
        self._fillMenusWithActions()

    def _createMenus(self) -> None:
        self._menusMap = {}
        menuBar = self.menuBar()
        menus = ("&File", "&Edit", "&View", "&Window", "&Help")
        for label in menus:
            menu = menuBar.addMenu(label)
            key = label.lower()[1:]
            self._menusMap[key] = menu

    def _fillMenusWithActions(self) -> None:
        self._menusMap["file"].addAction(self._actionsMap["new"])
        self._menusMap["file"].addAction(self._actionsMap["open"])
        self._menusMap["file"].addAction(self._actionsMap["save-as"])
        self._menusMap["file"].addAction(self._actionsMap["close"])

    def _createToolBar(self) -> None:
        toolBar = QtWidgets.QToolBar(self)
        toolBar.setIconSize(QtCore.QSize(16, 16))
        toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        toolBar.setMovable(False)
        self._fillToolBarWithActions(toolBar)
        self.addToolBar(toolBar)

    def _fillToolBarWithActions(self, toolBar: QtWidgets.QToolBar) -> None:
        toolBar.addAction(self._actionsMap["new"])
        toolBar.addAction(self._actionsMap["open"])
        toolBar.addAction(self._actionsMap["save-as"])

    def _createTreeWidget(self) -> None:
        self._treeWidget = QtWidgets.QTreeWidget(self)
        self._treeWidget.setFixedWidth(200)
        methodContentsItem = QtWidgets.QTreeWidgetItem()
        methodContentsItem.setText(0, "Method Contents")
        methodContentsItem.setIcon(
            0, QtGui.QIcon(resourcePath("icons/method-contents.png"))
        )
        self._treeWidget.setHeaderItem(methodContentsItem)
        self._fillTreeWithItems()
        self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))
        self._treeWidget.itemSelectionChanged.connect(self._changeWidget)

    def _fillTreeWithItems(self) -> None:
        # 'Elemental Peak Profile', 'Spectrum Processing', 'Unknown Components', 'Sample Lists', 'Spectra', 'Analysis Report'
        labels = ("Analytes And Conditions", "Calibrations")
        for label in labels:
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, label)
            key = "-".join(label.lower().split(" "))
            item.setIcon(0, QtGui.QIcon(resourcePath(f"icons/{key}.png")))
            self._treeWidget.addTopLevelItem(item)

    @QtCore.pyqtSlot()
    def _changeWidget(self) -> None:
        # Clear any existing widgets in the right layout
        if (widget := self._mainLayout.itemAt(1).widget()) is not None:
            widget.deleteLater()
        # Get the selected items (we assume single selection for this example)
        selectedItems = self._treeWidget.selectedItems()
        if selectedItems:
            selectedItem = selectedItems[0]
            label = selectedItem.text(0)
            if label == "Analytes And Conditions":
                self._mainLayout.addWidget(
                    AnalytesAndConditionsWidget(self, self._method)
                )
            elif label == "Calibrations":
                self._mainLayout.addWidget(CalibrationWidget(self, method=self._method))
            else:
                self._mainLayout.addWidget(QtWidgets.QWidget())

    def _setUpView(self) -> None:
        self._mainLayout = QtWidgets.QHBoxLayout()
        self._mainLayout.addWidget(self._treeWidget)
        self._mainLayout.addWidget(AnalytesAndConditionsWidget(self, self._method))
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(self._mainLayout)
        self.setCentralWidget(centralWidget)
