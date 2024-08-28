from functools import partial, cache
from json import dumps
from typing import Optional

import numpy as np
import pyqtgraph as pg
from PyQt6 import QtCore, QtGui, QtWidgets

from src.utils import datatypes
from src.utils import encryption
from src.utils.database import getDataframe
from src.utils.paths import resourcePath
from src.views.trays.calibrationtray import CalibrationTrayWidget

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


class ConditionForm(QtWidgets.QListView):
    def __init__(self, parent=None):
        super(ConditionForm, self).__init__(parent)
        self.setObjectName("condition-form")
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self._df = getDataframe("Conditions")
        self._createComboBox()
        self._createTable()
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(self._selectorComboBox)
        mainLayout.addWidget(self._tableWidget)
        self.setMaximumHeight(360)
        self.setMinimumHeight(150)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Maximum
        )

    def _createComboBox(self):
        self._selectorComboBox = QtWidgets.QComboBox(self)
        self._selectorComboBox.addItems(self._df.query("active == 1")["name"])
        self._selectorComboBox.currentTextChanged.connect(self._showConditionInList)

    def _createTable(self):
        self._tableWidget = QtWidgets.QTableWidget(self)
        self._tableWidget.setColumnCount(1)
        self._tableWidget.setRowCount(len(self._df.columns[1:-1]))
        self._tableWidget.setVerticalHeaderLabels([label.title() for label in self._df.columns[1:-1]])
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
        self._showConditionInList(1)

    def _showConditionInList(self, conditionId: int):
        conditionDf = self._df[self._df["condition_id"] == conditionId].drop(["condition_id", "active"], axis=1)
        for index in range(conditionDf.size):
            value = conditionDf.iat[0, index]
            item = QtWidgets.QTableWidgetItem()
            item.setText(str(value))
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self._tableWidget.setItem(index, 0, item)


class PlotWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(PlotWindow, self).__init__()
        self._indexOfFile = None
        self._analyseFiles = list()
        self._initializeUi()

    def _initializeUi(self) -> None:
        self.resize(1200, 800)
        self.setWindowTitle("XRF Semi Quantitative")
        self._createActions()
        self._createMenuBar()
        self._createToolBar()
        self._createPlotWidget()
        self._createTreeWidget()
        self._createListWidget()
        self._createCoordinateLabel()
        self._setUpView()

    def _createActions(self) -> None:
        self._actionsMap = {}
        actions = (
            "New",
            "Open",
            "Save",
            "Save as",
            "Close",
            "Print",
            "Print Preview",
            "Print Setup",
            "Standards Tray List",
            "Defaults",
            "Calibrate",
            "Methods Tray List"
        )
        self._blockedActionsNames = ["save-as", "save", "new", "print", "print-preview", "print-setup"]
        for label in actions:
            action = QtGui.QAction(label)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"icons/{key}.png")))
            if key in self._blockedActionsNames:
                action.setDisabled(True)
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        if key == "open":
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
        elif key == "save":
            # TODO
            pass
        elif key == "save-as":
            # TODO
            pass
        elif key == "new":
            self.resetWindow()
        elif key == "standards-tray-list":
            self._openCalibrationTrayListWidget()
        elif key == "close":
            self.close()

    def _createMenus(self) -> None:
        self._menusMap = {}
        menuBar = self.menuBar()
        menus = ["&File", "&Edit", "&View", "&Calibration", "&Method", "&Window", "&Help"]
        for label in menus:
            menu = menuBar.addMenu(label)
            key = label.lower()[1:]
            self._menusMap[key] = menu

    def _fillMenusWithActions(self) -> None:
        self._menusMap["file"].addAction(self._actionsMap["new"])
        self._menusMap["file"].addSeparator()
        self._menusMap["file"].addAction(self._actionsMap["open"])
        self._menusMap["file"].addAction(self._actionsMap["save-as"])
        self._menusMap["file"].addSeparator()
        self._menusMap["file"].addAction(self._actionsMap["print"])
        self._menusMap["file"].addAction(self._actionsMap["print-preview"])
        self._menusMap["file"].addAction(self._actionsMap["print-setup"])
        self._menusMap["file"].addSeparator()
        self._menusMap["file"].addAction(self._actionsMap["close"])

        self._menusMap["calibration"].addAction(self._actionsMap["standards-tray-list"])
        self._menusMap["calibration"].addAction(self._actionsMap["defaults"])
        self._menusMap["calibration"].addAction(self._actionsMap["calibrate"])

        self._menusMap["method"].addAction(self._actionsMap["methods-tray-list"])

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
        toolBar.addAction(self._actionsMap["save"])
        toolBar.addAction(self._actionsMap["save-as"])

    def _createPlotWidget(self) -> None:
        self._plotWidget = pg.PlotWidget()
        self._plotWidget.setObjectName("plot-widget")
        self._plotWidget.setBackground("#fff")
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
        self._coordinateLabel.setText(
            f"x = {round(x, 2)} y = {round(y, 2)}"
        )

    def _createTreeWidget(self) -> None:
        self._treeWidget = QtWidgets.QTreeWidget()
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
        self._treeWidget.setFixedWidth(int(self.size().width() / 3))
        self._treeWidget.setColumnWidth(0, int(self._treeWidget.size().width() * 0.7))
        self._fillTreeWidget()
        self._treeWidget.itemChanged.connect(self._drawCanvas)

    def _fillTreeWidget(self) -> None:
        items = ["Text Files", "Antique'X Files", "Packet Files"]
        for label in items:
            item = QtWidgets.QTreeWidgetItem(self._treeWidget)
            item.setText(0, label)
            self._treeWidget.addTopLevelItem(item)

    def _createListWidget(self) -> None:
        self._formWidget = ConditionForm(self)

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
        secondSplitter.addWidget(self._formWidget)
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
        if not self._actionsMap["save-as"].isEnabled():
            for actionName in self._blockedActionsNames:
                self._actionsMap[actionName].setDisabled(False)

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
        mapper = {"txt": 0, "atx": 1}
        self._treeWidget.topLevelItem(mapper[analyse.extension]).addChild(item)

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

    def _openCalibrationTrayListWidget(self):
        calibrationTrayWidget = CalibrationTrayWidget(dataframe=getDataframe("Calibrations"))
        calibrationTrayWidget.show()

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
        mapper = {0: "txt", 1: "atx"}
        analyse = list(
            filter(lambda a: a.extension == mapper[extensionIndex], self._analyseFiles)
        )[analyseIndex]
        return analyse

    def _setPlotLimits(self, maxIntensity: int) -> None:
        xMin = -100
        xMax = 2048 + 100
        yMin = -maxIntensity * 0.1
        yMax = maxIntensity * 1.1
        self._plotWidget.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

    def _plot(self, x: np.ndarray, y: np.ndarray, pen=pg.mkPen("red", width=2)) -> None:
        self._plotWidget.plot(x, y, pen=pen)

    def saveFile(self, filename: str) -> None:
        analyse = self._analyseFiles[self._indexOfFile]
        if filename.endswith(".atx"):
            key = encryption.loadKey()
            with open(filename, "wb") as f:
                jsonText = dumps(analyse.toDict())
                encryptedText = encryption.encryptText(jsonText, key)
                f.write(encryptedText + b"\n")
        elif filename.endswith(".txt"):
            with open(filename, "w") as f:
                for data in analyse.data:
                    f.write("<<Data>>\n")
                    f.write("*****\n")
                    f.write(f"Condition {data.condition}\n")
                    for i in data.y:
                        f.write(str(i) + "\n")

    # def closeEvent(self, event):
    #     # Intercept the close event
    #     # Check if the close is initiated by the close button
    #     if event.spontaneous():
    #         # Hide the window instead of closing
    #         self.hide()
    #         event.ignore()
    #     else:
    #         # Handle the close event normally
    #         event.accept()
