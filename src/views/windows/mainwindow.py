from functools import partial, cache
from typing import Optional

import numpy as np
import pandas
import pyqtgraph as pg
from PyQt6 import QtCore, QtGui, QtWidgets

from src.utils import datatypes
from src.utils.database import getDataframe
from src.utils.paths import resourcePath
from src.views.base.tablewidget import TableWidget
from src.views.calibration.calibrationtraywidget import CalibrationTrayWidget
from src.views.method.methodtraywidget import MethodTrayWidget
from src.views.background.backgroundtray import BackgroundTrayWidget

pg.setConfigOptions(antialias=False)

COLORS = [
    "#FF0000",
    "#FFD700",
    "#00FF00",
    "#00FFFF",
    "#000080",
    "#0000FF",
    "#8B00FF",
    "#FF1493",
    "#000000",
    "#FF4500",
    "#FFFF00",
    "#FF00FF",
    "#00FF7F",
    "#FF7F00",
]


class ResultDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, result: dict | None = None):
        super().__init__(parent)
        self._result = None
        self._initializeUi()
        if result is not None:
            self.supply(result)

    def _initializeUi(self) -> None:
        self.setWindowTitle("Result")
        self._createLabel()
        self._createButtonBox()
        self._setUpView()

    def _createLabel(self) -> None:
        self._label = QtWidgets.QLabel(self)
        self._label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    def _createButtonBox(self) -> None:
        self._buttonBox = QtWidgets.QDialogButtonBox(self)
        self._buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self._buttonBox.accepted.connect(self.accept)

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(self._label)
        self.mainLayout.addWidget(self._buttonBox)
        self.setLayout(self.mainLayout)

    def supply(self, result: dict):
        self.blockSignals(True)
        self._result = result
        self._label.clear()
        txt = "".join(f"{key}: {value}\n" for key, value in result.items())
        self._label.setText(txt)
        self.blockSignals(False)


class ConditionFormWidget(QtWidgets.QListView):
    def __init__(self, parent=None, conditions: pandas.DataFrame | None = None):
        super().__init__(parent)
        self._conditions = None
        self._df = None
        self._initializeUi()
        if conditions is not None:
            self.supply(conditions)

    def _initializeUi(self) -> None:
        self.setObjectName("condition-form")
        self.setMinimumHeight(150)
        self.setMaximumHeight(300)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum
        )
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self._createComboBox()
        self._createTable()
        self._setUpView()

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.addWidget(self._selectorComboBox)
        self.mainLayout.addWidget(self._tableWidget)

    def _createComboBox(self):
        self._selectorComboBox = QtWidgets.QComboBox(self)
        self._selectorComboBox.currentTextChanged.connect(self._currentTextChanged)

    def _currentTextChanged(self, text: str):
        conditionId = self._df.query(f"name == '{text}'")["condition_id"].values[0]
        self._showConditionInList(conditionId)

    def _createTable(self):
        self._tableWidget = TableWidget(self)
        self._tableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self._tableWidget.horizontalHeader().setVisible(False)
        self._tableWidget.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self._tableWidget.setAlternatingRowColors(True)
        self._tableWidget.setEditTriggers(
            QtWidgets.QTreeWidget.EditTrigger.NoEditTriggers
        )

    def _showConditionInList(self, conditionId: int):
        conditionDf = self._df.query(f"condition_id == {conditionId}").drop(
            ["condition_id", "active"], axis=1
        )
        for index in range(conditionDf.size):
            value = conditionDf.iat[0, index]
            item = QtWidgets.QTableWidgetItem()
            item.setText(str(value))
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self._tableWidget.setItem(index, 0, item)

    def supply(self, conditions: pandas.DataFrame) -> None:
        if conditions is None:
            return
        if self._df is not None and self._df.equals(conditions):
            return
        self.blockSignals(True)
        self._df = conditions
        self._selectorComboBox.blockSignals(True)
        self._selectorComboBox.clear()
        self._selectorComboBox.addItems(self._df.query("active == 1")["name"])
        self._selectorComboBox.blockSignals(False)
        self._tableWidget.resetTable()
        self._tableWidget.setColumnCount(1)
        self._tableWidget.setRowCount(len(self._df.columns[1:-1]))
        self._tableWidget.setVerticalHeaderLabels(
            [label.title() for label in self._df.columns[1:-1]]
        )
        self._showConditionInList(1)
        self.blockSignals(False)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, bundleType: int = 0):
        super().__init__()
        self._bundleType = bundleType
        self._analyse = None
        self._analyseFiles = []
        self._methodTray = None
        self._calibrationTray = None
        self._backgroundTray = None
        self._resultDialog = None
        self._initializeUi()

    def _initializeUi(self) -> None:
        self.setMinimumSize(1600, 900)
        self.setWindowTitle("XRF Semi Quantitative")
        self._createActions()
        self._createMenuBar()
        self._createToolBar()
        self._createPlotWidget()
        self._createTreeWidget()
        self._createConditionFormWidget()
        self._createCoordinateLabel()
        self._setUpView()

    def _createActions(self) -> None:
        self._actionsMap = {}
        actions = {
            "New": False,
            "Open": False,
            "Save as": True,
            "Close": False,
            "Print": True,
            "Print Preview": True,
            "Print Setup": True,
            "Standards Tray List": False,
            "Methods Tray List": False,
            "Background Tray List": False,
            "Results": True,
        }
        for label, disabled in actions.items():
            action = QtGui.QAction(label, self)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"resources/icons/{key}.png")))
            action.setDisabled(disabled)
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        if key == "close":
            self.close()
        elif key == "new":
            self.resetWindow()
        elif key == "open":
            self._openAnalyse()
        elif key == "save-as":
            self.saveFile()
        elif key == "methods-tray-list":
            self._openMethodTrayWidget()
        elif key == "standards-tray-list":
            self._openCalibrationTrayWidget()
        elif key == "background-tray-list":
            self._openBackgroundTrayWidget()
        elif key == "results":
            self._openResultsWidget()

    def _createMenus(self) -> None:
        self._menusMap = {}
        menuBar = self.menuBar()
        menus = [
            "&File",
            "&Edit",
            "&View",
            "&Calibration",
            "&Method",
            "&Background",
            "&Window",
            "&Help",
        ]
        for label in menus:
            menu = menuBar.addMenu(label)
            key = label.lower()[1:]
            self._menusMap[key] = menu

    def _fillMenusWithActions(self) -> None:
        fileActions = [
            "new",
            "open",
            "save-as",
            "print",
            "print-preview",
            "print-setup",
            "close",
        ]
        for action in fileActions:
            self._menusMap["file"].addAction(self._actionsMap[action])
            if action in ["new", "save-as", "print-setup"]:
                self._menusMap["file"].addSeparator()

        self._menusMap["calibration"].addAction(self._actionsMap["standards-tray-list"])

        self._menusMap["method"].addAction(self._actionsMap["methods-tray-list"])

        self._menusMap["background"].addAction(self._actionsMap["background-tray-list"])

    def _createMenuBar(self) -> None:
        self._createMenus()
        self._fillMenusWithActions()

    def _createToolBar(self) -> None:
        toolBar = QtWidgets.QToolBar(self)
        toolBar.setIconSize(QtCore.QSize(16, 16))
        toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolBar.setMovable(False)
        self._fillToolBarWithActions(toolBar)
        self.addToolBar(toolBar)

    def _fillToolBarWithActions(self, toolBar: QtWidgets.QToolBar) -> None:
        toolBar.addAction(self._actionsMap["open"])
        toolBar.addAction(self._actionsMap["save-as"])
        toolBar.addAction(self._actionsMap["results"])

    def _createPlotWidget(self) -> None:
        self._plotWidget = pg.PlotWidget(self)
        self._plotWidget.setObjectName("plot-widget")
        self._plotWidget.setBackground("#FFFFFF")
        plotItem = self._plotWidget.getPlotItem()
        plotItem.setContentsMargins(10, 10, 10, 10)
        self._plotWidget.showGrid(x=True, y=True)
        self._plotWidget.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self._plotWidget.setMinimumWidth(500)
        self._plotWidget.setMinimumHeight(500)
        self._plotWidget.scene().sigMouseMoved.connect(self._mouseMoved)

    def _mouseMoved(self, pos: QtCore.QPointF) -> None:
        if self._plotWidget.sceneBoundingRect().contains(pos):
            mousePoint = self._plotWidget.getPlotItem().vb.mapSceneToView(pos)
            self._setCoordinate(mousePoint.x(), mousePoint.y())

    def _setCoordinate(self, x: float, y: float) -> None:
        self._coordinateLabel.setText(f"x = {round(x, 2)} y = {round(y, 2)}")

    def _createTreeWidget(self) -> None:
        self._treeWidget = QtWidgets.QTreeWidget(self)
        self._treeWidget.setObjectName("file-tree")
        self._treeWidget.setColumnCount(2)
        self._treeWidget.setHeaderLabels(["File", "Color"])
        header = self._treeWidget.header()
        header.setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._treeWidget.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self._treeWidget.setAnimated(True)
        self._treeWidget.setExpandsOnDoubleClick(False)
        self._treeWidget.setEditTriggers(
            QtWidgets.QTreeWidget.EditTrigger.NoEditTriggers
        )
        self._treeWidget.setTabKeyNavigation(True)
        self._treeWidget.setFixedWidth(400)
        self._treeWidget.setColumnWidth(0, int(self._treeWidget.size().width() * 0.7))
        self._fillTreeWidget()
        self._treeWidget.itemClicked.connect(self._itemClicked)
        self._treeWidget.itemChanged.connect(self._drawCanvas)

    def _fillTreeWidget(self) -> None:
        items = ["Text Files", "Antique'X Files", "Packet Files"]
        for label in items:
            item = QtWidgets.QTreeWidgetItem(self._treeWidget)
            item.setText(0, label)
            self._treeWidget.addTopLevelItem(item)

    def _createConditionFormWidget(self) -> None:
        self._conditionFormWidget = ConditionFormWidget(self)
        self._conditionFormWidget.hide()

    def _createCoordinateLabel(self) -> None:
        self._coordinateLabel = QtWidgets.QLabel(self)
        self._coordinateLabel.setObjectName("coordinate-label")
        self._coordinateLabel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._setCoordinate(0, 0)

    def _setUpView(self) -> None:
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.addWidget(self._plotWidget)
        secondSplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        secondSplitter.addWidget(self._treeWidget)
        secondSplitter.addWidget(self._conditionFormWidget)
        secondSplitter.setChildrenCollapsible(False)
        splitter.addWidget(secondSplitter)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(splitter)
        self.mainLayout.addWidget(self._coordinateLabel)
        mainWidget = QtWidgets.QWidget(self)
        mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(mainWidget)

    def _addAnalyseFromFileName(self, filename: str) -> None:
        analyse = self._constructAnalyseFromFilename(filename)
        if analyse is not None and analyse.data:
            self.addAnalyse(analyse)
        else:
            messageBox = QtWidgets.QMessageBox(self)
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            messageBox.setWindowTitle("Invalid File Selected!")
            messageBox.setText("Make Sure You Are Opening The Right File")
            messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            messageBox.show()

    @staticmethod
    def _constructAnalyseFromFilename(filename: str) -> datatypes.Analyse | None:
        extension = filename[-4:]
        analyse: Optional[datatypes.Analyse] = None
        if extension == ".txt":
            analyse = datatypes.Analyse.fromTXTFile(filename)
        elif extension == ".atx":
            analyse = datatypes.Analyse.fromATXFile(filename)
        return analyse

    def addAnalyse(self, analyse: datatypes.Analyse) -> None:
        self._analyseFiles.append(analyse)
        self._addAnalyseToTree(analyse)

    def _addAnalyseToTree(self, analyse: datatypes.Analyse) -> None:
        item = QtWidgets.QTreeWidgetItem()
        item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
        item.setText(0, analyse.filename)
        item.setFlags(
            item.flags()
            | QtCore.Qt.ItemFlag.ItemIsAutoTristate
            | QtCore.Qt.ItemFlag.ItemIsUserCheckable
        )
        for index, data in enumerate(analyse.data):
            child = QtWidgets.QTreeWidgetItem()
            child.setText(0, f"Condition {data.conditionId}")
            child.setFlags(child.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            child.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
            item.addChild(child)
            colorButton = pg.ColorButton()
            colorButton.setColor(COLORS[index])
            colorButton.sigColorChanged.connect(self._drawCanvas)
            self._treeWidget.setItemWidget(child, 1, colorButton)
        mapper = {"txt": 0, "atx": 1, None: 2}
        self._treeWidget.topLevelItem(mapper[analyse.extension]).addChild(item)

    def _openAnalyse(self) -> None:
        fileNames, filters = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Open File",
            "./",
            "Antique'X Spectrum (*.atx);;Text Spectrum (*.txt)",
        )
        if fileNames:
            for fileName in fileNames:
                self._addAnalyseFromFileName(fileName)
            mapper = {"Text Spectrum (*.txt)": 0, "Antique'X Spectrum (*.atx)": 1}
            topLevelItem = self._treeWidget.topLevelItem(mapper[filters])
            if not topLevelItem.isExpanded():
                self._treeWidget.expandItem(topLevelItem)

    def resetWindow(self) -> None:
        messageBox = QtWidgets.QMessageBox(self)
        messageBox.setWindowTitle("Reset window")
        messageBox.setText("This will clear all added files.\nDo you want to continue?")
        messageBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
        result = messageBox.exec()
        if result == QtWidgets.QMessageBox.StandardButton.Yes:
            self._analyseFiles.clear()
            for topLevelIndex in range(self._treeWidget.topLevelItemCount()):
                item = self._treeWidget.topLevelItem(topLevelIndex)
                while item.childCount() != 0:
                    item.takeChild(0)
            self._plotWidget.clear()

    def _openMethodTrayWidget(self) -> None:
        self._methodTray = MethodTrayWidget(
            parent=self, dataframe=getDataframe("Methods")
        )
        self._methodTray.showMaximized()

    def _openCalibrationTrayWidget(self) -> None:
        self._calibrationTray = CalibrationTrayWidget(
            parent=self, dataframe=getDataframe("Calibrations")
        )
        self._calibrationTray.showMaximized()

    def _openBackgroundTrayWidget(self) -> None:
        self._backgroundTray = BackgroundTrayWidget(
            parent=self, dataframe=getDataframe("BackgroundProfiles")
        )
        self._backgroundTray.showMaximized()

    def _openResultsWidget(self):
        self._analyse.backgroundProfile = datatypes.BackgroundProfile.fromATXBFile(
            "backgrounds/PROFILE1.atxb"
        )
        self._resultDialog = ResultDialog(
            self,
            self._analyse.calculateConcentrations(
                datatypes.Method.fromATXMFile(resourcePath("methods/Fundamental.atxm"))
            ),
        )
        self._resultDialog.exec()

    def _findActivePlotAttrs(self) -> list:
        activePlotAttrs = []
        for extensionIndex in range(self._treeWidget.topLevelItemCount()):
            extensionItem = self._treeWidget.topLevelItem(extensionIndex)
            for analyseIndex in range(extensionItem.childCount()):
                analyseItem = extensionItem.child(analyseIndex)
                for dataIndex in range(analyseItem.childCount()):
                    analyseDataItem = analyseItem.child(dataIndex)
                    if analyseDataItem.checkState(0) == QtCore.Qt.CheckState.Checked:
                        color = self._treeWidget.itemWidget(analyseDataItem, 1).color()
                        activePlotAttrs.append(
                            (extensionIndex, analyseIndex, dataIndex, color)
                        )
        return activePlotAttrs

    def _itemClicked(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        if self._treeWidget.indexOfTopLevelItem(item.parent()) == -1:
            return
        tmp = self._analyse
        self._analyse = next(
            a for a in self._analyseFiles if a.filename == item.text(0)
        )
        if self._analyse and self._analyse != tmp:
            if self._conditionFormWidget.isVisible() is False:
                self._conditionFormWidget.show()
            self._conditionFormWidget.supply(self._analyse.conditions)
            self._actionsMap["save-as"].setDisabled(False)
            self._actionsMap["results"].setDisabled(False)

    def _drawCanvas(self) -> None:
        self._plotWidget.clear()
        attrs = self._findActivePlotAttrs()
        maxIntensity = 0
        for attr in attrs:
            extensionIndex, analyseIndex, dataIndex, color = attr
            data = self._getDataFromIndex(extensionIndex, analyseIndex, dataIndex)
            x, y = data.x, data.y
            temp = max(y)
            if temp > maxIntensity:
                maxIntensity = temp
                self._setPlotLimits(maxIntensity)
            self._plot(x, y, pg.mkPen(color=color, width=2))

    @cache
    def _getDataFromIndex(
        self, extensionIndex: int, analyseIndex: int, dataIndex: int
    ) -> datatypes.AnalyseData:
        return self._getAnalyseFromIndex(extensionIndex, analyseIndex).data[dataIndex]

    @cache
    def _getAnalyseFromIndex(
        self, extensionIndex: int, analyseIndex: int
    ) -> datatypes.Analyse:
        mapper = {0: "txt", 1: "atx", 2: None}
        return list(
            filter(lambda a: a.extension == mapper[extensionIndex], self._analyseFiles)
        )[analyseIndex]

    def _setPlotLimits(self, maxIntensity: int) -> None:
        xMin = -100
        xMax = 2048 + 100
        yMin = -maxIntensity * 0.1
        yMax = maxIntensity * 1.1
        self._plotWidget.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

    def _plot(self, x: np.ndarray, y: np.ndarray, pen=pg.mkPen("red", width=2)) -> None:
        self._plotWidget.plot(x, y, pen=pen)

    def saveFile(self) -> None:
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save File",
            "./",
            "Antique'X Spectrum (*.atx);;Text Spectrum (*.txt)",
        )
        self._analyse.saveTo(filepath)

    def closeEvent(self, event):
        # Intercept the close event
        # Check if the close is initiated by the close button
        if event.spontaneous() and self._bundleType != 1:
            # Hide the window instead of closing
            self.hide()
            event.ignore()
        else:
            # Handle the close event normally
            event.accept()
