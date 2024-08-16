from functools import partial, cache
from typing import Optional

import numpy as np
import pyqtgraph as pg
from PyQt6 import QtCore, QtGui, QtWidgets

from python.utils import datatypes
from python.utils.paths import resourcePath

COLORS = [
    "#FF0000",
    "#FFD700",
    "#00FF7F",
    "#00FFFF",
    "#000080",
    "#0000FF",
    "#8B00FF",
    "#FF1493",
    "#FF7F00",
    "#FF4500",
    "#FFC0CB",
    "#00FF00",
    "#FFFF00",
    "#FF00FF",
]


class PlotWidget(QtWidgets.QWidget):
    def __init__(
        self, parent: QtWidgets.QWidget | None = None, calibration: dict | None = None
    ):
        assert calibration is not None, "Calibration must be provided"
        super(PlotWidget, self).__init__(parent)
        self._calibration = calibration
        self._analyseFiles = [self._calibration["analyse"]]
        
        self._createActions()
        self._createToolBar()
        self._createPlotWidget()
        self._createTreeWidget()
        self._createCoordinateLabel()
        self._setUpView()
        self._addCalibrationToTree()
        self._drawCanvas()

    def _createActions(self) -> None:
        self._actionsMap = {}
        actions = ("New", "Add")
        for label in actions:
            action = QtGui.QAction(label)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"icons/{key}.png")))
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))
        self._actionsMap["new"].setDisabled(True)

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        if key == "add":
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
        elif key == "new":
            self.resetWindow()

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar(self)
        self._toolBar.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self._toolBar.setMovable(False)
        self._fillToolBarWithActions()

    def _fillToolBarWithActions(self) -> None:
        self._toolBar.addAction(self._actionsMap["new"])
        self._toolBar.addAction(self._actionsMap["add"])

    def _createPlotWidget(self) -> None:
        self._plotWidget = pg.PlotWidget()
        self._plotWidget.setObjectName("plot-widget")
        self._plotWidget.setBackground("#FFFFFF")
        self._plotWidget.setLabel("bottom", '<span style="font-size:1.5rem">px</span>')
        self._plotWidget.setLabel(
            "left", '<span style="font-size:1.5rem">Intensity</span>'
        )
        self._plotWidget.showGrid(x=True, y=True)
        self._plotWidget.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self._plotWidget.setFixedWidth(700)
        plotItem = self._plotWidget.getPlotItem()
        plotItem.setContentsMargins(10, 10, 10, 10)
        self._legend = plotItem.addLegend(
            offset=(-25, 25),
            pen=pg.mkPen(color="#E0E0E0", width=1),
            brush=pg.mkBrush(color="#F2F2F2"),
            labelTextColor="#000000"
        )
        self._plotWidget.scene().sigMouseMoved.connect(self._mouseMoved)

    def _mouseMoved(self, pos: QtCore.QPointF) -> None:
        if self._plotWidget.sceneBoundingRect().contains(pos):
            mousePoint = self._plotWidget.getPlotItem().vb.mapSceneToView(pos)
            self._setCoordinate(mousePoint.x(), mousePoint.y())

    def _setCoordinate(self, x: float, y: float) -> None:
        self._coordinateLabel.setText(f"x= {round(x, 2)} y= {round(y, 2)}")

    def _createTreeWidget(self) -> None:
        self._treeWidget = QtWidgets.QTreeWidget()
        self._treeWidget.setObjectName("file-tree-widget")
        self._treeWidget.setColumnCount(2)
        self._treeWidget.header().setVisible(False)
        # self._treeWidget.setHeaderLabels(["File", "Color"])
        self._treeWidget.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self._treeWidget.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self._treeWidget.setAnimated(True)
        self._treeWidget.setExpandsOnDoubleClick(False)
        self._treeWidget.setEditTriggers(
            QtWidgets.QTreeWidget.EditTrigger.NoEditTriggers
        )
        self._treeWidget.setTabKeyNavigation(True)
        self._fillTreeWidget()
        self._treeWidget.itemChanged.connect(self._drawCanvas)

    def _fillTreeWidget(self) -> None:
        items = ["Calibration", "Text Files", "Antique'X Files", "Packet Files"]
        for label in items:
            item = QtWidgets.QTreeWidgetItem(self._treeWidget)
            item.setText(0, label)
            self._treeWidget.addTopLevelItem(item)

    def _createCoordinateLabel(self) -> None:
        self._coordinateLabel = QtWidgets.QLabel(self)
        self._coordinateLabel.setObjectName("coordinate-label")
        self._coordinateLabel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._setCoordinate(0, 0)

    def _setUpView(self) -> None:
        self._mainLayout = QtWidgets.QVBoxLayout()
        self._mainLayout.addWidget(self._toolBar)
        hLayout = QtWidgets.QHBoxLayout()
        hLayout.addWidget(self._plotWidget)
        hLayout.addWidget(self._treeWidget)
        self._mainLayout.addLayout(hLayout)
        self._mainLayout.addWidget(self._coordinateLabel)
        self.setLayout(self._mainLayout)

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

    def _constructAnalyseFromFilename(self, filename: str) -> datatypes.Analyse | None:
        extension = filename[-4:]
        analyse: Optional[datatypes.Analyse] = None
        if extension == ".txt":
            analyse = datatypes.Analyse.fromTextFile(filename)
        elif extension == ".atx":
            analyse = datatypes.Analyse.fromATXFile(filename)
        return analyse

    def addAnalyse(self, analyse: datatypes.Analyse) -> None:
        self._analyseFiles.append(analyse)
        self._addAnalyseToTree(analyse)
        if not self._actionsMap["new"].isEnabled():
            self._actionsMap["new"].setDisabled(False)

    def _addAnalyseToTree(
        self,
        analyse: datatypes.Analyse,
        checkState: QtCore.Qt.CheckState = QtCore.Qt.CheckState.Unchecked,
    ) -> None:
        item = QtWidgets.QTreeWidgetItem()
        item.setCheckState(0, checkState)
        item.setText(0, analyse.name)
        item.setFlags(
            item.flags()
            | QtCore.Qt.ItemFlag.ItemIsAutoTristate
            | QtCore.Qt.ItemFlag.ItemIsUserCheckable
        )
        for index, data in enumerate(analyse.data):
            child = QtWidgets.QTreeWidgetItem()
            child.setText(0, f"Condition {data.condition}")
            child.setFlags(child.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            child.setCheckState(0, checkState)
            item.addChild(child)
            colorButton = pg.ColorButton()
            colorButton.setFixedSize(25, 25)
            colorButton.setStyleSheet("background-color: transparent;")
            colorButton.setColor(COLORS[index])
            colorButton.sigColorChanged.connect(self._drawCanvas)
            self._treeWidget.setItemWidget(child, 1, colorButton)
        mapper = {"txt": 1, "atx": 2}
        self._treeWidget.topLevelItem(mapper[analyse.extension]).addChild(item)
    
    def _addCalibrationToTree(self) -> None:
        item = QtWidgets.QTreeWidgetItem()
        item.setCheckState(0, QtCore.Qt.CheckState.Checked)
        item.setText(0, self._calibration["analyse"].name)
        item.setFlags(
            item.flags()
            | QtCore.Qt.ItemFlag.ItemIsAutoTristate
            | QtCore.Qt.ItemFlag.ItemIsUserCheckable
        )
        for index, data in enumerate(self._calibration["analyse"].data):
            child = QtWidgets.QTreeWidgetItem()
            child.setText(0, f"Condition {data.condition}")
            child.setFlags(child.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            child.setCheckState(0, QtCore.Qt.CheckState.Checked)
            item.addChild(child)
            colorButton = pg.ColorButton()
            colorButton.setFixedSize(25, 25)
            colorButton.setStyleSheet("background-color: transparent;")
            colorButton.setColor(COLORS[index])
            colorButton.sigColorChanged.connect(self._drawCanvas)
            self._treeWidget.setItemWidget(child, 1, colorButton)
        self._treeWidget.topLevelItem(0).addChild(item)
        self._treeWidget.expandAll()

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
            self._analyseFiles = self._analyseFiles[:1]
            for topLevelIndex in range(1, self._treeWidget.topLevelItemCount()):
                item = self._treeWidget.topLevelItem(topLevelIndex)
                while item.childCount() != 0:
                    item.takeChild(0)
                    self._actionsMap['add'].setDisabled(True)
            self._drawCanvas()

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
            if extensionIndex == 0:
                self._plot(x, y, name=f"Condition {data.condition}", pen=pg.mkPen(color=color, width=2))
            else:
                self._plot(x, y, pen=pg.mkPen(color=color, width=2))

    @cache
    def _getDataFromIndex(
        self, extensionIndex: int, analyseIndex: int, dataIndex: int
    ) -> datatypes.AnalyseData:
        return self._getAnalyseFromIndex(extensionIndex, analyseIndex).data[dataIndex]

    @cache
    def _getAnalyseFromIndex(
        self, extensionIndex: int, analyseIndex: int
    ) -> datatypes.Analyse:
        mapper = {0: "calibration", 1: "txt", 2: "atx"}
        if extensionIndex == 0:
            return self._analyseFiles[0]
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

    def _plot(self, x: np.ndarray, y: np.ndarray, *args, **kwargs) -> None:
        self._plotWidget.plot(x, y, *args, **kwargs)
