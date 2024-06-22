from functools import partial
from json import dumps
from typing import Optional, Union

import numpy as np
import pyqtgraph as pg
from PyQt6 import QtCore, QtGui, QtWidgets

from python.utils import datatypes
from python.utils import encryption
from python.utils.database import getDatabase
from python.utils.paths import resource_path
from python.views.elementswindow import ElementsWindow
from python.views.peaksearchwindow import PeakSearchWindow

COLORS = [
    "#FF0000",
    "#FFD700",
    "#00FF00",
    "#00FFFF",
    "#000080",
    "#0000FF",
    "#8B00FF",
    "#FF1493",
    "#FFC0CB",
    "#FF4500",
    "#FFFF00",
    "#FF00FF",
    "#00FF7F",
    "#FF7F00",
]


class SaveDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SaveDialog, self).__init__(parent)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(self)
        label.setText("Select the file you like to save:")
        verticalLayout.addWidget(label)
        self.listWidget = QtWidgets.QListWidget(self)
        self.listWidget.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.listWidget.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.listWidget.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.listWidget.setProperty("showDropIndicator", False)
        self.listWidget.setDefaultDropAction(QtCore.Qt.DropAction.IgnoreAction)
        verticalLayout.addWidget(self.listWidget)
        buttonBox = QtWidgets.QDialogButtonBox(self)
        buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        buttonBox.setCenterButtons(True)
        verticalLayout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def fillList(self, items: list):
        self.listWidget.addItems(items)


class CalibrationDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(CalibrationDialog, self).__init__(parent)
        self._db = getDatabase(resource_path("fundamentals.db"))
        self._df = self._db.dataframe("SELECT * FROM Elements")
        self.element = None
        self.concentration = None
        self.path = None
        self.setWindowTitle("Set Calibration Parameters")
        self.setFixedSize(500, 200)
        self._setUpView()

    def _setUpView(self) -> None:
        horizontalLayout = QtWidgets.QHBoxLayout(self)
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.setContentsMargins(7, 7, 7, 7)
        self._filePathLineEdit = self._createLineEdit()
        gridLayout.addWidget(self._filePathLineEdit, 3, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        gridLayout.addItem(spacerItem, 2, 0, 1, 1)
        self._openButton = self._createButton()
        gridLayout.addWidget(self._openButton, 3, 2, 1, 1)
        label = self._createLabel("Concentration")
        gridLayout.addWidget(label, 1, 0, 1, 1)
        self._elementComboBox = self._createComboBox()
        gridLayout.addWidget(self._elementComboBox, 0, 1, 1, 1)
        label = self._createLabel("Element")
        gridLayout.addWidget(label, 0, 0, 1, 1)
        label = self._createLabel("File Path")
        gridLayout.addWidget(label, 3, 0, 1, 1)
        self._concentrationSpinBox = self._createSpinBox()
        gridLayout.addWidget(self._concentrationSpinBox, 1, 1, 1, 1)
        gridLayout.setColumnStretch(1, 1)
        horizontalLayout.addLayout(gridLayout)
        buttonBox = self._createButtonBox()
        horizontalLayout.addWidget(buttonBox)

    def _createLabel(self, text: str) -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(self)
        label.setText(text)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
        label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        return label

    def _createLineEdit(self) -> QtWidgets.QLineEdit:
        lineEdit = QtWidgets.QLineEdit(self)
        lineEdit.setStyleSheet("""
            QLineEdit {
                border-radius: 5px;
                border: 1px solid gray;
                padding: 2px;
            }
            QLineEdit:hover {
                border: 1px solid darkblue;
            }
            QLineEdit:focus {
                border: 1px solid black;
            }
        """)
        return lineEdit

    def _createButton(self) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton(self)
        button.setIcon(QtGui.QIcon(resource_path("icons/open.png")))
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                padding: 2px;
                border-radius: 3px;
                border: 1px solid gray;
            }
            QPushButton:hover {
                background-color: lightgray;
            }
        """)
        button.clicked.connect(self._setPath)
        return button

    @QtCore.pyqtSlot()
    def _setPath(self) -> None:
        self.path = self.parent().showFileDialog(QtWidgets.QFileDialog.AcceptMode.AcceptOpen)
        if self.path is not None:
            self._filePathLineEdit.setText(self.path)

    def _createComboBox(self) -> QtWidgets.QComboBox:
        comboBox = QtWidgets.QComboBox(self)
        comboBox.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        comboBox.setStyleSheet("""
            QComboBox {
                border: 1px solid gray;
                border-radius: 3px;
                padding: 1px 34px 1px 3px;
            }
            QComboBox:hover {
                border: 1px solid darkblue;
            }
            QComboBox:focus {
                border: 1px solid black;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow {
                image: url(icons/down-arrow-resized.png)
            }
            QComboBox QAbstractItemView {
                border-radius: 3px;
                border: 1px solid gray;
                selection-background-color: gray;
                background-color: lightgray; /* Custom background color for the drop-down menu */
            }
        """)
        comboBox.addItems(self._df['symbol'].tolist())
        comboBox.setCurrentIndex(0)
        self.element = comboBox.itemText(0)
        comboBox.currentTextChanged.connect(self._setElement)
        return comboBox

    @QtCore.pyqtSlot(str)
    def _setElement(self, text: str) -> None:
        self.element = text

    def _createSpinBox(self) -> QtWidgets.QDoubleSpinBox:
        spinBox = QtWidgets.QDoubleSpinBox(self)
        spinBox.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        spinBox.setStyleSheet("""
            QDoubleSpinBox {
                border-radius: 3px;
                border: 1px solid gray;
                padding: 1px 20px 1px 3px;
            }
            QDoubleSpinBox:hover {
                border: 1px solid darkblue;
            }
            QDoubleSpinBox:focus {
                border: 1px solid black;
            }
        """)
        spinBox.setValue(100)
        spinBox.setDecimals(1)
        self.concentration = spinBox.value()
        spinBox.valueChanged.connect(self._setConcentration)
        return spinBox

    @QtCore.pyqtSlot(float)
    def _setConcentration(self, value: float) -> None:
        self.concentration = value

    def _createButtonBox(self) -> QtWidgets.QDialogButtonBox:
        buttonBox = QtWidgets.QDialogButtonBox(self)
        buttonBox.setOrientation(QtCore.Qt.Orientation.Vertical)
        buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        return buttonBox

class ConditionForm(QtWidgets.QListView):
    def __init__(self, parent=None):
        super(ConditionForm, self).__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        db = getDatabase(resource_path("fundamentals.db"))
        self._df = db.dataframe('SELECT * FROM Conditions')
        self._createComboBox()
        self._createTable()
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(self._selectorComboBox)
        mainLayout.addWidget(self._tableWidget)
        self.setMaximumHeight(350)
        self.setMinimumHeight(150)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum
        )

    def _createComboBox(self):
        self._selectorComboBox = QtWidgets.QComboBox(self)
        self._selectorComboBox.addItems(self._df.query("active == 1")["name"])
        self._selectorComboBox.currentTextChanged.connect(self._showConditionInList)

    def _createTable(self):
        self._tableWidget = QtWidgets.QTableWidget(self)
        self._tableWidget.setColumnCount(1)
        self._tableWidget.setRowCount(len(self._df.columns))
        self._tableWidget.setVerticalHeaderLabels(self._df.columns)
        self._tableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self._tableWidget.horizontalHeader().setVisible(False)
        self._tableWidget.setAlternatingRowColors(True)
        self._tableWidget.setEditTriggers(QtWidgets.QTreeWidget.EditTrigger.NoEditTriggers)
        self._showConditionInList("Condition 1")

    def _showConditionInList(self, conditionName: str):
        conditionDf = self._df[self._df["name"] == conditionName]
        for index in range(conditionDf.size):
            item = QtWidgets.QTableWidgetItem()
            value = conditionDf.iat[0, index]
            if index == conditionDf.size - 1:
                value = bool(value)
                if value is True:
                    item.setForeground(QtGui.QColor(0, 255, 0))
                else:
                    item.setForeground(QtGui.QColor(255, 0, 0))
            item.setText(str(value))
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self._tableWidget.setItem(index, 0, item)


class PlotWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(PlotWindow, self).__init__()
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

        self._indexOfFile = None
        self._analyseFiles = list()
        self._elementsWindow: Optional[ElementsWindow] = None
        self._calibrationDialog: Optional[CalibrationDialog] = None
        self._peakSearchWindow: Optional[PeakSearchWindow] = None
        # TODO interferenceWindow

    def _createActions(self) -> None:
        self._actionsMap = {}
        actions = ["New", "Open", "Save as", "Close", "Peak Search", "Elements", "Add Calibration"]
        for label in actions:
            action = QtGui.QAction(label)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resource_path(f"icons/{key}.png")))
            if key in ["save-as", "peak-search", "new"]:
                action.setDisabled(True)
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str):
        if key == "open":
            self._getFileNameFromDialog(QtWidgets.QFileDialog.AcceptMode.AcceptOpen)
        elif key == "save-as":
            self._getFileNameFromDialog(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        elif key == "new":
            self.resetWindow()
        elif key == "close":
            self.close()
        elif key == "elements":
            self._elementsWindow = ElementsWindow()
            self._elementsWindow.show()
        elif key == "peak-search":
            self._showPeakSearchWindow()
        elif key == "add-calibration":
            self._openCalibrationDialog()

    def _createMenus(self) -> None:
        self._menusMap = {}
        menuBar = self.menuBar()
        menus = ["&File", "&Edit", "&Help"]
        for label in menus:
            menu = menuBar.addMenu(label)
            key = label.lower()[1:]
            self._menusMap[key] = menu

    def _fillMenusWithActions(self) -> None:
        self._menusMap["file"].addAction(self._actionsMap["new"])
        self._menusMap["file"].addSeparator()
        self._menusMap["file"].addAction(self._actionsMap["open"])
        self._menusMap["file"].addAction(self._actionsMap["add-calibration"])
        self._menusMap["file"].addAction(self._actionsMap["save-as"])
        self._menusMap["file"].addSeparator()
        self._menusMap["file"].addAction(self._actionsMap["close"])

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
        toolBar.addAction(self._actionsMap["add-calibration"])
        toolBar.addAction(self._actionsMap["save-as"])
        toolBar.addAction(self._actionsMap["elements"])
        toolBar.addAction(self._actionsMap["peak-search"])

    def _createPlotWidget(self) -> None:
        self._plotWidget = pg.PlotWidget()
        self._plotWidget.setBackground("#fff")
        self._plotWidget.setLabel(
            "bottom", """<span style=\"font-size:1.5rem\">px</span>"""
        )
        self._plotWidget.setLabel(
            "left",
            """<span style=\"font-size:1.5rem\">Intensity</span>""",
        )
        self._plotWidget.showGrid(x=True, y=True)
        self._plotWidget.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self._plotWidget.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self._plotWidget.setMinimumWidth(500)
        self._plotWidget.setMinimumHeight(500)
        self._plotWidget.scene().sigMouseMoved.connect(self._mouseMoved)

    def _mouseMoved(self, pos: QtCore.QPointF) -> None:
        if self._plotWidget.sceneBoundingRect().contains(pos):
            mousePoint = self._plotWidget.getPlotItem().vb.mapSceneToView(pos)
            self._setCoordinate(mousePoint.x(), mousePoint.y())

    def _setCoordinate(self, x: int, y: int) -> None:
        self._coordinateLabel.setText(
            "<span style='font-size: 2rem'>x=%0.1f,y=%0.1f</span>" % (x, y)
        )

    def _createTreeWidget(self) -> None:
        self._treeWidget = QtWidgets.QTreeWidget()
        self._treeWidget.setColumnCount(3)
        self._treeWidget.setHeaderLabels(["File", "Condition", "Color"])
        self._treeWidget.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self._treeWidget.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self._treeWidget.header().setHighlightSections(True)
        self._treeWidget.setAnimated(True)
        self._treeWidget.setExpandsOnDoubleClick(False)
        header = self._treeWidget.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setHighlightSections(True)
        self._treeWidget.setEditTriggers(
            QtWidgets.QTreeWidget.EditTrigger.NoEditTriggers
        )
        self._treeWidget.setTabKeyNavigation(True)
        self._treeWidget.setAlternatingRowColors(True)
        self._treeWidget.setMaximumWidth(int(self.size().width() / 3))
        self._treeWidget.setMinimumWidth(int(self.size().width() / 5))
        self._fillTreeWidget()
        self._treeWidget.itemChanged.connect(self._checkStateChanged)
        self._treeWidget.itemClicked.connect(self._togglePeakSearchAction)

    def _fillTreeWidget(self) -> None:
        items = ["Text Files", "Antique'X Files", "Packet Files"]
        for label in items:
            item = QtWidgets.QTreeWidgetItem(self._treeWidget)
            item.setText(0, label)
            self._treeWidget.addTopLevelItem(item)

    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem, int)
    def _checkStateChanged(self, item: QtWidgets.QTreeWidgetItem) -> None:
        self._treeWidget.blockSignals(True)
        if self._treeWidget.indexOfTopLevelItem(item.parent()) != -1:
            if item.checkState(0) == QtCore.Qt.CheckState.Unchecked:
                for dataIndex in range(item.childCount()):
                    item.child(dataIndex).setCheckState(
                        1, QtCore.Qt.CheckState.Unchecked
                    )
            elif item.checkState(0) == QtCore.Qt.CheckState.Checked:
                for dataIndex in range(item.childCount()):
                    item.child(dataIndex).setCheckState(1, QtCore.Qt.CheckState.Checked)
        else:
            analyseItem = item.parent()
            states = [
                analyseItem.child(childIndex).checkState(1)
                for childIndex in range(analyseItem.childCount())
            ]
            mapper = map(lambda state: state == QtCore.Qt.CheckState.Checked, states)
            if all(mapper):
                analyseItem.setCheckState(0, QtCore.Qt.CheckState.Checked)
            else:
                analyseItem.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
        self._treeWidget.blockSignals(False)
        self._drawCanvas()

    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem)
    def _togglePeakSearchAction(self, item: QtWidgets.QTreeWidgetItem):
        if "condition" in item.text(1).lower():
            self._actionsMap['peak-search'].setDisabled(False)
        else:
            self._actionsMap['peak-search'].setDisabled(True)

    def _createListWidget(self):
        self._formWidget = ConditionForm(self)

    def _createCoordinateLabel(self) -> None:
        self._coordinateLabel = QtWidgets.QLabel(self)
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
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(splitter)
        vlayout.addWidget(self._coordinateLabel)
        mainWidget = QtWidgets.QWidget(self)
        mainWidget.setLayout(vlayout)
        self.setCentralWidget(mainWidget)

    def _getFileNameFromDialog(self, mode: QtWidgets.QFileDialog.AcceptMode) -> None:
        if mode == QtWidgets.QFileDialog.AcceptMode.AcceptSave:
            saveDialog = SaveDialog(self)
            saveDialog.fillList(list(map(lambda x: x.name, self._analyseFiles)))
            saveDialog.listWidget.setCurrentRow(0)
            result = saveDialog.exec()
            if result:
                self._indexOfFile = saveDialog.listWidget.currentRow()
                path = self.showFileDialog(mode)
                self._configureSaveOrOpen(mode, path)
        elif mode == QtWidgets.QFileDialog.AcceptMode.AcceptOpen:
            path = self.showFileDialog(mode)
            self._configureSaveOrOpen(mode, path)

    def showFileDialog(self, mode: QtWidgets.QFileDialog.AcceptMode) -> Optional[str]:
        fileDialog = QtWidgets.QFileDialog(self)
        fileDialog.setFileMode(QtWidgets.QFileDialog.FileMode.AnyFile)
        fileDialog.setNameFilters(
            ["Antique'X Spectrum (*.atx)", "Text Spectrum (*.txt)"]
        )
        fileDialog.setAcceptMode(mode)
        result = fileDialog.exec()
        if result == 1:
            return fileDialog.selectedFiles()[0] if fileDialog.selectedFiles() else None
        return None

    @QtCore.pyqtSlot(str)
    def _configureSaveOrOpen(
            self, mode: QtWidgets.QFileDialog.AcceptMode, filename: str
    ) -> None:
        if mode == QtWidgets.QFileDialog.AcceptMode.AcceptOpen:
            self.addAnalyseFile(filename)
        elif mode == QtWidgets.QFileDialog.AcceptMode.AcceptSave:
            self.saveFile(filename)

    def addAnalyseFile(self, filename: str) -> None:
        analyse = None
        extension = filename[-4:]
        if extension == ".txt":
            analyse = datatypes.Analyse.fromTextFile(filename)
        elif extension == ".atx":
            analyse = datatypes.Analyse.fromATXFile(filename)
        if analyse is not None and analyse.data:
            self.addAnalyse(analyse)
            # TODO show dialog for asking for edit privileges
            # TODO auto save
            # TODO get raw intensities file if profile == cal and calculate interference coefficient and fill the table
        else:
            messageBox = QtWidgets.QMessageBox(self)
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            messageBox.setWindowTitle("Invalid File Selected!")
            messageBox.setText("Make Sure You Are Opening The Right File")
            messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            messageBox.show()

    def addAnalyse(self, analyse: Union[datatypes.Analyse, datatypes.CalibrationAnalyse]) -> None:
        self._analyseFiles.append(analyse)
        self._addAnalyseToTree(analyse)
        if not self._actionsMap["save-as"].isEnabled():
            self._actionsMap["save-as"].setDisabled(False)
            self._actionsMap["new"].setDisabled(False)

    def _addAnalyseToTree(self, analyse: Union[datatypes.Analyse, datatypes.CalibrationAnalyse]) -> None:
        item = QtWidgets.QTreeWidgetItem()
        item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
        if isinstance(analyse, datatypes.CalibrationAnalyse):
            item.setText(0, f"{analyse.name} - CAL")
        else:
            item.setText(0, analyse.name)
        for index, data in enumerate(analyse.data):
            child = QtWidgets.QTreeWidgetItem()
            child.setText(1, f"Condition {data.condition}")
            child.setCheckState(1, QtCore.Qt.CheckState.Unchecked)
            item.addChild(child)
            colorButton = pg.ColorButton()
            colorButton.setColor(COLORS[index])
            colorButton.sigColorChanged.connect(self._drawCanvas)
            self._treeWidget.setItemWidget(child, 2, colorButton)
        mapper = {".txt": 0, ".atx": 1}
        self._treeWidget.topLevelItem(mapper[analyse.extension]).addChild(item)

    def resetWindow(self):
        messageBox = QtWidgets.QMessageBox(self)
        messageBox.setWindowTitle("Reset Window?")
        messageBox.setText(
            "This Will Clear All Added Files. " "Do You Want To Continue?"
        )
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

    def _findActivePlotAttrs(self) -> list:
        activePlotAttrs = []
        for extensionIndex in range(self._treeWidget.topLevelItemCount()):
            extensionItem = self._treeWidget.topLevelItem(extensionIndex)
            for analyseIndex in range(extensionItem.childCount()):
                analyseItem = extensionItem.child(analyseIndex)
                for dataIndex in range(analyseItem.childCount()):
                    analyseDataItem = analyseItem.child(dataIndex)
                    if analyseDataItem.checkState(1) == QtCore.Qt.CheckState.Checked:
                        color = self._treeWidget.itemWidget(analyseDataItem, 2).color()
                        activePlotAttrs.append(
                            (extensionIndex, analyseIndex, dataIndex, color)
                        )
        return activePlotAttrs

    def _drawCanvas(self) -> None:
        self._plotWidget.clear()
        attrs = self._findActivePlotAttrs()
        maxIntensity = 0
        for index, attr in enumerate(attrs):
            extensionIndex, analyseIndex, dataIndex, color = attr
            data = self._getDataFromIndex(extensionIndex, analyseIndex, dataIndex)
            x, y = data.x, data.y
            temp = max(y)
            if temp > maxIntensity:
                maxIntensity = temp
                self._setPlotLimits(maxIntensity)
            self._plot(x, y, pg.mkPen(color=color, width=2))

    def _getDataFromIndex(self, extensionIndex: int, analyseIndex: int, dataIndex: int) -> datatypes.AnalyseData:
        return self._getAnalyseFromIndex(extensionIndex, analyseIndex).data[dataIndex]

    def _getAnalyseFromIndex(self, extensionIndex: int, analyseIndex: int) -> datatypes.Analyse:
        mapper = {0: ".txt", 1: ".atx"}
        analyse = list(
            filter(
                lambda a: a.extension == mapper[extensionIndex], self._analyseFiles
            )
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
                for d in analyse.data:
                    jsonText = dumps(d.toDict())
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

    def _showPeakSearchWindow(self):
        self._peakSearchWindow = PeakSearchWindow()
        dataItem = self._treeWidget.currentItem()
        analyseItem = dataItem.parent()
        extensionItem = analyseItem.parent()
        extensionIndex = self._treeWidget.indexOfTopLevelItem(extensionItem)
        analyseIndex = extensionItem.indexOfChild(analyseItem)
        dataIndex = analyseItem.indexOfChild(dataItem)
        analyse = self._getAnalyseFromIndex(extensionIndex, analyseIndex)
        self._peakSearchWindow.addAnalyse(analyse)
        self._peakSearchWindow.show()
        self._peakSearchWindow.displayAnalyseData(dataIndex)

    def _openCalibrationDialog(self) -> None:
        self._calibrationDialog = CalibrationDialog(self)
        self._calibrationDialog.show()
        self._calibrationDialog.accepted.connect(self.addCalibration)

    def addCalibration(self) -> None:
        path = self._calibrationDialog.path
        if path:
            if path.endswith(".txt"):
                analyse = datatypes.CalibrationAnalyse.fromTextFile(path)
            else:
                analyse = datatypes.CalibrationAnalyse.fromATXFile(path)
            analyse.concentration = self._calibrationDialog.concentration
            analyse.element = self._calibrationDialog.element
            self.addAnalyse(analyse)

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
