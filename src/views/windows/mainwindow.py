from functools import partial
from typing import Optional

import pandas
import pyqtgraph as pg
from PyQt6 import QtCore, QtGui, QtWidgets

from src.utils import datatypes
from src.utils.database import getDataframe
from src.utils.paths import resourcePath
from src.views.base.tablewidget import TableWidget
from src.views.calibration.traywidget import CalibrationTrayWidget
from src.views.method.traywidget import MethodTrayWidget
from src.views.background.traywidget import BackgroundTrayWidget

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


class AnalyseGeneralDataGroupBox(QtWidgets.QGroupBox):
    backgroundChanged = QtCore.pyqtSignal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        analyse: datatypes.Analyse | None = None,
    ):
        super().__init__(parent)
        self.setTitle("General Data")
        self._analyse = None
        self._generalDataWidgetsMap = {}
        self._initializeUi()
        if analyse is not None:
            self.supply(analyse)
        self.hide()

    def _initializeUi(self) -> None:
        self._createWidgets()
        self._fillGeneralDataGroupBox()

    def _createWidgets(self) -> None:
        keys = [
            "Type",
            "Area",
            "Mass",
            "Rho",
            "Background Profile",
            "Rest",
            "Diluent",
        ]
        for key in keys:
            if key == "Background Profile":
                widget = QtWidgets.QComboBox(self)
                items = getDataframe("BackgroundProfiles")["filename"].to_list()
                items.insert(0, "")
                widget.addItems(items)
                widget.currentTextChanged.connect(
                    partial(self._generalDataChanged, key, widget)
                )
            else:
                widget = QtWidgets.QLineEdit(self)
                widget.textEdited.connect(
                    partial(self._generalDataChanged, key, widget)
                )
            self._generalDataWidgetsMap[key] = widget

    def _fillGeneralDataGroupBox(self) -> None:
        self._generalDataLayout = QtWidgets.QVBoxLayout()
        self._generalDataLayout.setSpacing(25)
        for label, widget in self._generalDataWidgetsMap.items():
            self._addWidgetToLayout(label, widget)
        self.setLayout(self._generalDataLayout)

    def _addWidgetToLayout(self, key: str, widget: QtWidgets.QWidget) -> None:
        widget.setFixedSize(100, 25)
        widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        hLayout = QtWidgets.QHBoxLayout()
        hLayout.addWidget(QtWidgets.QLabel(f"{key}:"))
        hLayout.addWidget(widget)
        self._generalDataLayout.addLayout(hLayout)

    def _generalDataChanged(self, key, widget) -> None:
        if key == "Background Profile":
            if filename := widget.currentText():
                profile = datatypes.BackgroundProfile.fromATXBFile(
                    resourcePath(f"backgrounds/{filename}.atxb")
                )
                self._analyse.backgroundProfile = profile
            else:
                self._analyse.backgroundProfile = None
            self.backgroundChanged.emit()

    def _fillWidgetsFromAnalyse(self) -> None:
        for key, widget in self._generalDataWidgetsMap.items():
            value = self._analyse.generalData.get(key)
            if isinstance(widget, (QtWidgets.QLineEdit, QtWidgets.QLabel)):
                widget.setText(value)
            else:
                widget.setCurrentText(value)

    def setDisabled(self, a0):
        for widget in self._generalDataWidgetsMap.values():
            widget.setDisabled(a0)

    def supply(self, analyse: datatypes.Analyse) -> None:
        self.blockSignals(True)
        if analyse == self._analyse:
            return
        self._analyse = analyse
        self._fillWidgetsFromAnalyse()
        self.blockSignals(False)


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
        self._createGeneralDataGroupBox()
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
        self._plotWidget.setMinimumSize(500, 500)
        self._plotWidget.setXRange(0, 2048)
        self._plotWidget.setLimits(xMin=-100, xMax=2148, yMax=1)
        self._backgroundRegion = pg.LinearRegionItem(
            pen=pg.mkPen(color="#330311", width=2),
            brush=pg.mkBrush(192, 192, 192, 100),
            hoverBrush=pg.mkBrush(169, 169, 169, 100),
            bounds=(0, 2048),
        )
        self._backgroundRegion.setZValue(10)
        self._plotWidget.scene().sigMouseMoved.connect(self._mouseMoved)
        self._backgroundRegion.sigRegionChanged.connect(self._backgroundRegionChanged)

    def _mouseMoved(self, pos: QtCore.QPointF) -> None:
        if self._plotWidget.sceneBoundingRect().contains(pos):
            mousePoint = self._plotWidget.getPlotItem().vb.mapSceneToView(pos)
            self._setCoordinate(mousePoint.x(), mousePoint.y())

    def _setCoordinate(self, x: float, y: float) -> None:
        self._coordinateLabel.setText(f"x = {round(x, 2)} y = {round(y, 2)}")

    def _backgroundRegionChanged(self) -> None:
        self._analyse.backgroundRegion = self._backgroundRegion.getRegion()
        item = self._treeWidget.currentItem()
        for i in range(item.childCount()):
            item.child(i).plotDataItem.setData(
                self._analyse.data[i].x, self._analyse.data[i].optimalY
            )

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
        self._treeWidget.itemSelectionChanged.connect(self._itemSelectionChanged)
        self._treeWidget.itemChanged.connect(self._itemChanged)

    @QtCore.pyqtSlot()
    def _itemSelectionChanged(self) -> None:
        item = self._treeWidget.currentItem()
        if getattr(item, "analyse", None) is None:
            self._conditionFormWidget.hide()
            self._generalDataGroupBox.hide()
            return
        self._analyse = item.analyse
        self._conditionFormWidget.show()
        self._generalDataGroupBox.show()
        self._conditionFormWidget.supply(self._analyse.conditions)
        self._generalDataGroupBox.supply(self._analyse)
        self._actionsMap["save-as"].setDisabled(False)
        self._actionsMap["results"].setDisabled(False)
        if self._analyse.generalData["Background Profile"]:
            if self._backgroundRegion not in self._plotWidget.plotItem.items:
                self._backgroundRegion.setRegion(self._analyse.backgroundRegion)
                self._plotWidget.addItem(self._backgroundRegion)
        elif self._backgroundRegion in self._plotWidget.plotItem.items:
            self._plotWidget.removeItem(self._backgroundRegion)

    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem, int)
    def _itemChanged(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        if getattr(item, "plotDataItem", None) is None:
            return
        if item.checkState(column) == QtCore.Qt.CheckState.Checked:
            if item.plotDataItem not in self._plotWidget.plotItem.items:
                self._plotWidget.addItem(item.plotDataItem)
                if (
                    yMax := max(item.plotDataItem.getData()[1])
                ) * 1.1 > self._plotWidget.getViewBox().state["limits"]["yLimits"][1]:
                    self._plotWidget.setLimits(yMin=-0.1 * yMax, yMax=yMax * 1.1)
        else:
            self._plotWidget.removeItem(item.plotDataItem)

    def _fillTreeWidget(self) -> None:
        items = ["Text Files", "Antique'X Files", "Packet Files"]
        for label in items:
            item = QtWidgets.QTreeWidgetItem(self._treeWidget)
            item.setText(0, label)
            self._treeWidget.addTopLevelItem(item)

    def _createGeneralDataGroupBox(self) -> None:
        self._generalDataGroupBox = AnalyseGeneralDataGroupBox(self)
        self._generalDataGroupBox.setFixedWidth(300)
        self._generalDataGroupBox.backgroundChanged.connect(self._backgroundChanged)

    def _backgroundChanged(self) -> None:
        if self._analyse:
            if self._analyse.generalData["Background Profile"]:
                if self._backgroundRegion not in self._plotWidget.plotItem.items:
                    self._backgroundRegion.setRegion(self._analyse.backgroundRegion)
                    self._plotWidget.addItem(self._backgroundRegion)
                    if (item := self._treeWidget.currentItem()).checkState(
                        0
                    ) == QtCore.Qt.CheckState.Unchecked:
                        item.setCheckState(0, QtCore.Qt.CheckState.Checked)
            else:
                if self._backgroundRegion in self._plotWidget.plotItem.items:
                    self._plotWidget.removeItem(self._backgroundRegion)

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
        splitter.addWidget(self._generalDataGroupBox)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(splitter)
        self.mainLayout.addWidget(self._coordinateLabel)
        mainWidget = QtWidgets.QWidget(self)
        mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(mainWidget)

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
        item = QtWidgets.QTreeWidgetItem()
        item.analyse = analyse
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
            child.plotDataItem = pg.PlotDataItem(
                x=data.x, y=data.optimalY, pen=pg.mkPen(color=COLORS[index], width=2)
            )
            item.addChild(child)
            colorButton = pg.ColorButton()
            colorButton.setColor(COLORS[index])
            colorButton.sigColorChanged.connect(
                partial(self._colorChanged, child, colorButton)
            )
            self._treeWidget.setItemWidget(child, 1, colorButton)
        mapper = {"txt": 0, "atx": 1, None: 2}
        self._treeWidget.topLevelItem(mapper[analyse.extension]).addChild(item)

    def _colorChanged(
        self, item: QtWidgets.QTreeWidgetItem, colorButton: pg.ColorButton
    ) -> None:
        self._plotWidget.removeItem(item.plotDataItem)
        item.plotDataItem.setPen(pg.mkPen(color=colorButton.color(), width=2))
        self._plotWidget.addItem(item.plotDataItem)

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
        self._resultDialog = ResultDialog(
            self,
            self._analyse.calculateConcentrations(
                datatypes.Method.fromATXMFile(resourcePath("methods/Fundamental.atxm"))
            ),
        )
        self._resultDialog.exec()

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
