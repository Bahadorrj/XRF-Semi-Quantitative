from collections import deque
from functools import partial
from typing import Iterable

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore, QtGui

from python.utils import calculation, datatypes
from python.utils.database import getDatabase
from python.utils.datatypes import Analyse
from python.utils.paths import resourcePath


class StatusButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentText = self.text()
        self.previousText = self.currentText
        self.setStyleSheet(
            """
                    QPushButton {
                        width: 75px;
                        font-weight: 600;
                        font-size: 14px;
                        color: #fff;
                        background-color: #0066CC;
                        padding: 2px 5px;
                        border: 2px solid #0066cc;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #fff;
                        color: #0066cc;
                        border: 2px solid #0066cc;
                    }
                    QPushButton:pressed {
                        background-color: #fff;
                        color: #011B35;
                        border: 2px solid #011B35;
                    }
                    """
        )

    def setText(self, text: str | None) -> None:
        self.previousText = self.currentText
        self.currentText = text
        return super().setText(text)


class HideButton(QtWidgets.QPushButton):
    def __init__(self, parent=None, icon: QtGui.QIcon = None):
        super().__init__(parent)
        super().setIcon(icon)
        self.currentIcon = icon
        self.previousIcon = self.currentIcon
        self.setStyleSheet(
            """
                    QPushButton {
                        background-color: transparent;
                    }
                """
        )

    def setIcon(self, icon):
        self.previousIcon = self.currentIcon
        self.currentIcon = icon
        return super().setIcon(icon)


class ConditionComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCurrentIndex(0)
        self.currentText_ = super().currentText()
        self.previousText = self.currentText_
        self.setStyleSheet(
            """
                    QComboBox {
                        border: 1px solid gray;
                        border-radius: 3px;
                        padding: 1px 18px 1px 3px;
                    }
                    QComboBox:hover {
                        border: 1px solid darkblue;
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
                        selection-background-color: lightgray;
                        background-color: rgba(135, 206, 250, 128); /* Custom background color for the drop-down menu */
                    }
                """
        )
        self.currentTextChanged.connect(self._currentTextChanged)

    @QtCore.pyqtSlot(str)
    def _currentTextChanged(self, text: str) -> None:
        self.previousText = self.currentText_
        self.currentText_ = text

    def setCurrentText(self, text: str | None) -> None:
        self.previousText = self.currentText_
        self.currentText_ = text
        return super().setCurrentText(text)


class TableItem(QtWidgets.QTableWidgetItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentText = self.text()
        self.previousText = self.currentText

    def setText(self, text: str | None) -> None:
        self.previousText = self.currentText
        self.currentText = text
        return super().setText(text)


class ElementsTableWidget(QtWidgets.QTableWidget):
    rowChanged = QtCore.pyqtSignal(int, str)

    def __init__(self, parent=None, df: pd.DataFrame = None):
        super(ElementsTableWidget, self).__init__(parent)
        self.df = df
        self.rowIds = list()
        self.intensities = list()
        self.rows = list()
        self.setModifiedSections()
        self.setStyleSheet(
            """
            QTableWidget::item:selected {
                background-color: rgba(135, 206, 250, 128);  /* LightSkyBlue with 50% opacity */
                color: black;
            }
        """
        )

    def setModifiedSections(self):
        headers = [
            "",
            "Element",
            "Type",
            "Kev",
            "Low Kev",
            "High Kev",
            "Intensity",
            "Condition",
            "Status",
            "",
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

    def setHorizontalHeaderLabels(self, labels: Iterable[str | None]) -> None:
        for column, label in enumerate(labels):
            if label:
                self.horizontalHeader().setSectionResizeMode(
                    column, QtWidgets.QHeaderView.ResizeMode.Stretch
                )
            else:
                self.horizontalHeader().setSectionResizeMode(
                    column, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
                )
            item = QtWidgets.QTableWidgetItem(label)
            self.setHorizontalHeaderItem(column, item)

    def addRow(self, data: datatypes.PlotData, row: pd.Series, intensity: int) -> None:
        self.setRowCount(self.rowCount() + 1)
        rowAsDict = dict()
        self._createWidgets(data, rowAsDict)
        self._createItems(row, intensity, rowAsDict)
        self.rowIds.append(data.rowId)
        self.intensities.append(intensity)
        self.rows.append(rowAsDict)

    def _createWidgets(self, data: datatypes.PlotData, rowDict: dict) -> None:
        rowIndex = self.rowCount() - 1
        mapper = {"hide": 0, "condition": 7, "status": 9}
        for label, column in mapper.items():
            if label == "hide":
                widget = self._createHideWidget(data)
            elif label == "condition":
                widget = self._createConditionComboBox(data)
            elif label == "status":
                widget = self._createStatusButton(data)
            else:
                widget = None
            rowDict[column] = widget
            self.setCellWidget(rowIndex, column, widget)

    def _createHideWidget(self, data: datatypes.PlotData) -> HideButton:
        if data.visible:
            widget = HideButton(icon=QtGui.QIcon(resourcePath(f"icons/show.png")))
        else:
            widget = HideButton(icon=QtGui.QIcon(resourcePath(f"icons/hide.png")))
        widget.clicked.connect(partial(self._emitRowChanged, data.rowId, "hide"))
        return widget

    def _createConditionComboBox(self, data: datatypes.PlotData) -> ConditionComboBox:
        widget = ConditionComboBox()
        values = [
            "",
            "Condition 1",
            "Condition 2",
            "Condition 3",
            "Condition 4",
            "Condition 5",
            "Condition 6",
            "Condition 7",
            "Condition 8",
            "Condition 9",
        ]
        widget.addItems(values)
        if data.active:
            widget.setDisabled(True)
        if data.condition is not None:
            widget.setCurrentText(f"Condition {data.condition}")
        widget.currentTextChanged.connect(
            partial(self._emitRowChanged, data.rowId, "condition")
        )
        return widget

    def _createStatusButton(self, data: datatypes.PlotData) -> StatusButton:
        if not data.active:
            widget = StatusButton("Activate")
        else:
            widget = StatusButton("Deactivate")
        widget.clicked.connect(partial(self._emitRowChanged, data.rowId, "status"))
        return widget

    def _createItems(self, row: pd.Series, intensity: int, rowDict: dict) -> None:
        rowIndex = self.rowCount() - 1
        mapper = {
            1: str(row["symbol"]),
            2: str(row["radiation_type"]),
            3: str(row["kiloelectron_volt"]),
            4: str(row["low_kiloelectron_volt"]),
            5: str(row["high_kiloelectron_volt"]),
            6: str(intensity),
            8: "Activated" if row["active"] == 1 else "Deactivated",
        }
        for column, value in mapper.items():
            item = TableItem(value)
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            if column == 8:
                if value == "Activated":
                    item.setForeground(QtGui.QColor(0, 255, 0))
                else:
                    item.setForeground(QtGui.QColor(255, 0, 0))
            rowDict[column] = item
            self.setItem(rowIndex, column, item)

    def getRow(self, rowId: int) -> dict:
        return self.rows[self.rowIds.index(rowId)]

    def _emitRowChanged(self, rowId: int, label: str) -> None:
        self.rowChanged.emit(rowId, label)

    def resetTable(self) -> None:
        self.setRowCount(0)
        self.rowIds.clear()
        self.intensities.clear()
        self.rows.clear()

    def updateRow(self, rowId: int, values: list) -> None:
        rowIndex = self.rowIds.index(rowId)
        self.blockSignals(True)
        for columnIndex, value in enumerate(values):
            if columnIndex == 0:
                self.cellWidget(rowIndex, columnIndex).setIcon(value)
            elif columnIndex == 7:
                self.cellWidget(rowIndex, columnIndex).setCurrentText(value)
            elif columnIndex == 9:
                self.cellWidget(rowIndex, columnIndex).setText(value)
            else:
                self.item(rowIndex, columnIndex).setText(value)
        self.blockSignals(False)


class PeakSearchWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(PeakSearchWindow, self).__init__(parent)
        self._analyse = None
        self._conditionId = None
        self._kev = None
        self._db = getDatabase(resourcePath("fundamentals.db"))
        self._df = self._db.dataframe("SELECT * FROM Lines")
        self._plotDataList = [
            datatypes.PlotData.fromSeries(rowId, s) for rowId, s in self._df.iterrows()
        ]
        self._undoStack = deque()
        self._redoStack = deque()
        self._flag = False
        self.resize(1200, 800)
        self._mainLayout = QtWidgets.QVBoxLayout()
        self._createToolBar()
        self._createSearchBar()
        self._createTableWidget()
        self._createPlotViewBox()
        # self._createMenuBar()
        self._setupView()

    def _createToolBar(self) -> None:
        toolBar = QtWidgets.QToolBar(self)
        toolBar.setIconSize(QtCore.QSize(16, 16))
        toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        toolBar.setMovable(False)
        self._fillToolBarWithActions(toolBar)
        self.addToolBar(toolBar)

    def _fillToolBarWithActions(self, toolBar: QtWidgets.QToolBar) -> None:
        self._undoAction = QtGui.QAction(
            icon=QtGui.QIcon(resourcePath("icons/undo.png"))
        )
        # self._redoAction = QtGui.QAction(icon=QtGui.QIcon(resource_path("icons/redo.png")))
        self._undoAction.setDisabled(True)
        # self._redoAction.setDisabled(True)
        self._undoAction.setShortcut(QtGui.QKeySequence("Ctrl+z"))
        # self._redoAction.setShortcut(QtGui.QKeySequence("Ctrl+r"))
        toolBar.addAction(self._undoAction)
        # toolBar.addAction(self._redoAction)
        self._undoAction.triggered.connect(self._undo)
        # self._redoAction.triggered.connect(self._redo)

    def _undo(self) -> None:
        if self._undoStack:
            rowId, values, action = self._undoStack.pop()
            # self._addRowToRedoStack(rowId, action)
            self._tableWidget.updateRow(rowId, values)
            if not self._undoStack:
                self._undoAction.setDisabled(True)
                # self._flag = True
            # self._redoAction.setDisabled(False)
            self._rowChanged(rowId, action)

    # def _redo(self) -> None:
    #     if self._redoStack:
    #         rowId, values, action = self._redoStack.pop()
    #         self._addRowToUndoStack(rowId, action)
    #         self._tableWidget.updateRow(rowId, values)
    #         if not self._redoStack:
    #             self._redoAction.setDisabled(True)
    #         self._undoAction.setDisabled(False)
    #         self._rowChanged(rowId, action)

    def _createSearchBar(self) -> None:
        self._searchedElement = QtWidgets.QLineEdit()
        self._searchedElement.setStyleSheet(
            """
            QLineEdit {
                border-radius: 5px;
                border: 1px solid gray;
                padding: 5px 2px;
            }
            QLineEdit:focus {
                border: 1px solid black;
            }
        """
        )
        self._searchedElement.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._searchedRadiation = QtWidgets.QComboBox()
        self._searchedRadiation.setStyleSheet(
            """
            QComboBox {
                border: 1px solid gray;
                border-radius: 3px;
                padding: 5px;
                width: 20px;
            }
            QComboBox:hover {
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
                selection-background-color: lightgray;
                background-color: rgba(135, 206, 250, 128); /* Custom background color for the drop-down menu */
            }
        """
        )
        items = self._df["radiation_type"].unique().tolist()
        items.insert(0, "")
        self._searchedRadiation.addItems(items)
        self._searchedRadiation.setCurrentIndex(0)
        self._searchedElement.setDisabled(True)
        self._searchedRadiation.setDisabled(True)
        hLayout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Element Symbol: ")
        hLayout.addWidget(label)
        hLayout.addWidget(self._searchedElement)
        label = QtWidgets.QLabel("Radiation Type: ")
        hLayout.addWidget(label)
        hLayout.addWidget(self._searchedRadiation)
        spacerItem = QtWidgets.QSpacerItem(
            0,
            0,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        hLayout.addItem(spacerItem)
        self._mainLayout.addLayout(hLayout)
        self._searchedElement.editingFinished.connect(self._search)
        self._searchedRadiation.currentTextChanged.connect(self._search)

    @QtCore.pyqtSlot()
    def _search(self) -> None:
        symbol = self._searchedElement.text()
        radiation = self._searchedRadiation.currentText()
        if symbol != "":
            df = self._df.query(f"symbol == '{self._searchedElement.text()}'")
            if radiation != "":
                df = df.query(
                    f"radiation_type == '{self._searchedRadiation.currentText()}'"
                )
        elif radiation != "":
            df = self._df.query(
                f"radiation_type == '{self._searchedRadiation.currentText()}'"
            )
        else:
            self._fillTable()
            return
        if not df.empty:
            self._tableWidget.resetTable()
            for rowId in df.index:
                data = self._plotDataList[rowId]
                self._addPlotData(data)

    def _createTableWidget(self) -> None:
        self._tableWidget = ElementsTableWidget(self, df=self._df)
        self._tableWidget.setSelectionMode(
            QtWidgets.QTableWidget.SelectionMode.ExtendedSelection
        )
        self._tableWidget.setSelectionBehavior(
            QtWidgets.QTableWidget.SelectionBehavior.SelectRows
        )
        self._tableWidget.setMaximumHeight(int(self.size().height() / 3))
        self._tableWidget.setAlternatingRowColors(True)
        self._mainLayout.addWidget(self._tableWidget)
        self._tableWidget.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self._tableWidget.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self._tableWidget.rowChanged.connect(self._rowChangedSlotHandler)
        self._tableWidget.itemClicked.connect(self._itemClicked)

    def _createPlotViewBox(self) -> None:
        self._createCoordinateLabel()
        self._graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self._createPeakPlot()
        self._createSpectrumPlot()
        self._mainLayout.addWidget(self._graphicsLayoutWidget)

    def _createCoordinateLabel(self) -> None:
        self._coordinateLabel = QtWidgets.QLabel()
        self._coordinateLabel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._coordinateLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self._mainLayout.addWidget(self._coordinateLabel)

    def _createPeakPlot(self):
        self._peakPlot = self._graphicsLayoutWidget.addPlot(row=0, col=0)
        self._peakPlot.showGrid(x=True, y=True)
        self._vLine = pg.InfiniteLine(angle=90, movable=False)
        self._hLine = pg.InfiniteLine(angle=0, movable=False)
        self._peakPlot.vb.scaleBy(center=(0, 0))
        self._peakPlot.vb.menu.clear()
        self._peakPlot.setMinimumHeight(
            int(self._graphicsLayoutWidget.sizeHint().height() * 3 / 5)
        )
        self._peakPlot.sigRangeChanged.connect(self._adjustZoom)
        self._peakPlot.scene().sigMouseMoved.connect(self._mouseMoved)
        self._peakPlot.scene().sigMouseClicked.connect(self._openPopUp)

    def _createSpectrumPlot(self) -> None:
        self._spectrumPlot = self._graphicsLayoutWidget.addPlot(row=1, col=0)
        self._spectrumPlot.setMouseEnabled(x=False, y=False)
        self._spectrumPlot.showGrid(x=True, y=True)
        self._spectrumPlot.showGrid(x=True, y=True)
        self._zoomRegion = pg.LinearRegionItem(clipItem=self._spectrumPlot)
        self._zoomRegion.sigRegionChanged.connect(self._showZoomedRegion)

    def _createMenuBar(self) -> None:
        self._menuBar = QtWidgets.QMenuBar()
        saveAction = self._menuBar.addAction("&Save")
        saveAction.triggered.connect(self._saveIntensities)
        self._menuBar.addAction(saveAction)
        self.setMenuBar(self._menuBar)

    def _saveIntensities(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save calibration results", "./", "Text Files (*.txt)"
        )
        if path:
            with open(path, "w") as f:
                for row in self._tableWidget.rows:
                    symbol = row.get(1).text()
                    radiation = row.get(2).text()
                    f.write(f"{symbol}-{radiation}: {row.get(6).text()}\n")

    def _setupView(self) -> None:
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(self._mainLayout)
        self.setCentralWidget(centralWidget)

    def _fillTable(self) -> None:
        self._tableWidget.resetTable()
        for data in self._plotDataList:
            self._addPlotData(data)

    def _addPlotData(self, data: datatypes.PlotData) -> None:
        series: pd.Series = self._df.iloc[data.rowId]
        minX, maxX = data.region.getRegion()
        if data.condition is None:
            intensity = "NA"
        else:
            # TODO remove when proper analyse files where available
            try:
                y = list(
                    filter(
                        lambda d: d.condition == int(series["condition_id"]),
                        self._analyse.data,
                    )
                )[0].y
                intensity = y[round(minX):round(maxX)].sum()
            except IndexError:
                intensity = "NA"
        self._tableWidget.addRow(data, series["symbol":"active"], intensity)
        data.region.sigRegionChangeFinished.connect(
            partial(self._changeRangeOfData, data)
        )
        data.peakLine.sigClicked.connect(partial(self._selectData, data))
        data.spectrumLine.sigClicked.connect(partial(self._selectData, data))
        QtWidgets.QApplication.processEvents()

    @QtCore.pyqtSlot()
    def _changeRangeOfData(self, data: datatypes.PlotData) -> None:
        self._addRowToUndoStack(data.rowId, "region")

        row = self._tableWidget.getRow(data.rowId)

        minX, maxX = data.region.getRegion()
        try:
            minKev = self._kev[int(minX)]
        except IndexError:
            minKev = 0
        try:
            maxKev = self._kev[int(maxX)]
        except IndexError:
            maxKev = self._kev[-1]
        row.get(4).setText(str(minKev))
        row.get(5).setText(str(maxKev))

        try:
            conditionId = data.condition
            y = list(filter(lambda d: d.condition == conditionId, self._analyse.data))[0].y
            intensity = y[round(minX):round(maxX)].sum()
        except IndexError:
            intensity = "NA"
        row.get(6).setText(str(intensity))

    @QtCore.pyqtSlot()
    def _selectData(self, data: datatypes.PlotData) -> None:
        if data.rowId in self._tableWidget.rowIds:
            index = self._tableWidget.rowIds.index(data.rowId)
            self._tableWidget.selectRow(index)
            self._hoverOverData(data)

    def _hoverOverData(self, data: datatypes.PlotData):
        minX, maxX = data.region.getRegion()
        viewMinX, viewMaxX = self._peakPlot.viewRange()[0]
        if viewMinX > minX or viewMaxX < maxX:
            zoomedArea = (minX - 50, maxX + 50)
            self._zoomRegion.setRegion(zoomedArea)

    def _rowChangedSlotHandler(self, rowId: int, action: str) -> None:
        if self._rowChanged(rowId, action):
            self._addRowToUndoStack(rowId, action)

    def _rowChanged(self, rowId: int, action: str) -> bool:
        data = self._plotDataList[rowId]
        if action == "hide":
            return self._dataVisibilityChanged(data)
        elif action == "condition":
            return self._dataConditionChanged(data)
        elif action == "status":
            return self._dataStatusChanged(data)
        elif action == "region":
            return self._dataRegionChanged(data)
        return False

    def _addRowToUndoStack(self, rowId: int, action: str) -> None:
        if not self._undoStack:
            self._undoAction.setDisabled(False)
        if len(self._undoStack) > 30:
            self._undoStack.popleft()
        # if self._flag:
        #     self._redoStack.clear()
        #     self._redoAction.setDisabled(True)
        row = self._tableWidget.getRow(rowId)
        values = list()
        for index, component in row.items():
            if isinstance(component, HideButton):
                if action == "hide":
                    values.insert(index, component.previousIcon)
                else:
                    values.insert(index, component.currentIcon)
            elif isinstance(component, StatusButton):
                if action == "status":
                    values.insert(index, component.previousText)
                else:
                    values.insert(index, component.currentText)
            elif isinstance(component, ConditionComboBox):
                if action == "condition":
                    values.insert(index, component.previousText)
                else:
                    values.insert(index, component.currentText_)
            else:
                values.insert(index, component.currentText)
        self._undoStack.append((rowId, values, action))
        # print(f"added to undo stack : {values}-{action}")

    # def _addRowToRedoStack(self, rowId: int, action: str) -> None:
    #     if not self._redoStack:
    #         self._redoAction.setDisabled(False)
    #     row = self._tableWidget.getRow(rowId)
    #     values = list()
    #     for index, component in row.items():
    #         if isinstance(component, HideButton):
    #             if action == "hide":
    #                 values.insert(index, component.previousIcon)
    #             else:
    #                 values.insert(index, component.currentIcon)
    #         elif isinstance(component, StatusButton):
    #             if action == "status":
    #                 values.insert(index, component.previousText)
    #             else:
    #                 values.insert(index, component.currentText)
    #         elif isinstance(component, ConditionComboBox):
    #             if action == "condition":
    #                 values.insert(index, component.currentText_)
    #             else:
    #                 values.insert(index, component.previousText)
    #         else:
    #             values.insert(index, component.currentText)
    #     self._redoStack.append((rowId, values, action))
    #     print(f"added to redo stack:{values}")

    def _dataVisibilityChanged(self, data: datatypes.PlotData) -> bool:
        row = self._tableWidget.getRow(data.rowId)
        hideButton = row.get(0)
        if data.visible:
            self._erasePlotData(data)
            hideButton.setIcon(QtGui.QIcon(resourcePath("icons/hide.png")))
        else:
            self._selectData(data)
            self._drawPlotData(data)
            hideButton.setIcon(QtGui.QIcon(resourcePath("icons/show.png")))
        data.visible = not data.visible
        return True

    def _dataConditionChanged(self, data: datatypes.PlotData) -> bool:
        row = self._tableWidget.getRow(data.rowId)
        data = self._plotDataList[data.rowId]
        minX, maxX = data.region.getRegion()
        if row.get(7).currentText() != "":
            conditionId = int(row.get(7).currentText().split(" ")[-1])
            data.condition = conditionId
            self._df.at[data.rowId, "condition_id"] = conditionId
            try:
                y = list(
                    filter(lambda d: d.condition == conditionId, self._analyse.data)
                )[0].y
                intensity = y[round(minX): round(maxX)].sum()
            except IndexError:
                intensity = "NA"
        else:
            intensity = "NA"
        row.get(6).setText(str(intensity))
        return True

    def _dataStatusChanged(self, data: datatypes.PlotData) -> bool:
        changed = False
        row = self._tableWidget.getRow(data.rowId)
        conditionComboBox = row.get(7)
        statusItem = row.get(8)
        statusButton = row.get(9)
        if data.active:
            changed = True
            data.deactivate()
            self._df.at[data.rowId, "active"] = 0
            statusItem.setText("Deactivated")
            statusItem.setForeground(QtGui.QColor(255, 0, 0))
            statusButton.setText("Activate")
            conditionComboBox.setDisabled(False)
        else:
            symbol = self._df.at[data.rowId, "symbol"]
            df = self._df.query(f"symbol == '{symbol}' and active == 1")
            if df.empty:
                if conditionComboBox.currentText():
                    changed = True
                    data.activate()
                    self._df.at[data.rowId, "active"] = 1
                    statusItem.setText("Activated")
                    statusItem.setForeground(QtGui.QColor(0, 255, 0))
                    statusButton.setText("Deactivate")
                    conditionComboBox.setDisabled(True)
                else:
                    messageBox = QtWidgets.QMessageBox(self)
                    messageBox.setIcon(QtWidgets.QMessageBox.Icon.Critical)
                    messageBox.setText(
                        "No condition is selected. Please select one before activating again."
                    )
                    messageBox.setWindowTitle("Activation failed")
                    messageBox.setStandardButtons(
                        QtWidgets.QMessageBox.StandardButton.Ok
                    )
                    messageBox.exec()
            else:
                messageBox = QtWidgets.QMessageBox(self)
                messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
                messageBox.setText(
                    f"One line of {symbol} is already identified as the main line.\n"
                    "Activating this will replace it with the previous.\n"
                    "Would you like to continue?"
                )
                messageBox.setWindowTitle("Activation failed")
                messageBox.setStandardButtons(
                    QtWidgets.QMessageBox.StandardButton.Yes
                    | QtWidgets.QMessageBox.StandardButton.No
                )
                result = messageBox.exec()
                if result == QtWidgets.QMessageBox.StandardButton.Yes:
                    self._dataStatusChanged(self._plotDataList[df.index[0]])
                    self._dataStatusChanged(data)
        if data.visible:
            self._erasePlotData(data)
            self._selectData(data)
            self._drawPlotData(data)
        return changed

    def _dataRegionChanged(self, data: datatypes.PlotData) -> bool:
        row = self._tableWidget.getRow(data.rowId)
        lowKev = float(row.get(4).text())
        highKev = float(row.get(5).text())
        minX = calculation.evToPx(lowKev)
        maxX = calculation.evToPx(highKev)
        self._df.at[data.rowId, "low_kiloelectron_volt"] = lowKev
        self._df.at[data.rowId, "high_kiloelectron_volt"] = highKev
        data.region.blockSignals(True)
        data.region.setRegion((minX, maxX))
        data.region.blockSignals(False)
        return True

    def _drawPlotData(self, data: datatypes.PlotData) -> None:
        if data.peakLine not in self._peakPlot.items:
            self._peakPlot.addItem(data.peakLine)
        if data.spectrumLine not in self._spectrumPlot.items:
            self._spectrumPlot.addItem(data.spectrumLine)
        if self._analyse.classification == "CAL" and data.region not in self._peakPlot.items and data.active is False:
            self._peakPlot.addItem(data.region)

    def _erasePlotData(self, data: datatypes.PlotData) -> None:
        if data.peakLine in self._peakPlot.items:
            self._peakPlot.removeItem(data.peakLine)
        if data.spectrumLine in self._spectrumPlot.items:
            self._spectrumPlot.removeItem(data.spectrumLine)
        if data.region in self._peakPlot.items:
            self._peakPlot.removeItem(data.region)

    @QtCore.pyqtSlot(QtWidgets.QTableWidgetItem)
    def _itemClicked(self, item: QtWidgets.QTableWidgetItem) -> None:
        rowId = self._tableWidget.rowIds[item.row()]
        data = self._plotDataList[rowId]
        if data.visible:
            self._hoverOverData(data)

    def _setCoordinate(self, x: float, y: float) -> None:
        try:
            kev = self._kev[int(x)]
            self._coordinateLabel.setText(
                f"""
                <span style="font-size: 14px; 
                            color: rgb(128, 128, 128);
                            padding: 5px;
                            letter-spacing: 2px">x= {x} y= {y} KeV= {kev}</span>
                """
            )
        except IndexError:
            pass

    def _adjustZoom(self, window, viewRange):
        rng = viewRange[0]
        self._zoomRegion.setRegion(rng)

    def _mouseMoved(self, event: QtCore.QEvent) -> None:
        pos = self._peakPlot.vb.mapSceneToView(event)
        x = round(pos.x(), 2)
        y = round(pos.y(), 2)
        self._showCoordinate(x, y)

    def _showCoordinate(self, x: float, y: float):
        self._vLine.setPos(x)
        self._hLine.setPos(y)
        self._setCoordinate(x, y)

    def _showZoomedRegion(self):
        minX, maxX = self._zoomRegion.getRegion()
        self._peakPlot.setXRange(minX, maxX, padding=0)

    def _openPopUp(self, event):
        pos = event.pos()
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            mousePoint = self._peakPlot.vb.mapSceneToView(pos)
            kev = calculation.pxToEv(mousePoint.x())
            self._peakPlot.vb.menu.clear()
            greater = self._df["low_kiloelectron_volt"] <= kev
            smaller = kev <= self._df["high_kiloelectron_volt"]
            mask = np.logical_and(greater, smaller)
            self._elementsInRange = self._df[mask]
            for radiationLabel in self._df["radiation_type"].unique():
                filteredData = self._elementsInRange[
                    self._elementsInRange["radiation_type"] == radiationLabel
                    ]
                if not filteredData.empty:
                    menu = self._peakPlot.vb.menu.addMenu(radiationLabel)
                    menu.triggered.connect(self._actionClicked)
                    for symbol in filteredData["symbol"]:
                        menu.addAction(symbol)
            showAllAction = self._peakPlot.vb.menu.addAction("Show All")
            showAllAction.triggered.connect(self._showAll)

    def _actionClicked(self, action: QtGui.QAction):
        elementSymbol = action.text()
        radiationType = action.parent().title()
        df = self._elementsInRange.query(
            f"symbol == '{elementSymbol}' and radiation_type == '{radiationType}'"
        )
        rowId = df.index.values[0]
        self._tableWidget.rowChanged.emit(rowId, "hide")

    def _showAll(self) -> None:
        for rowId in self._elementsInRange.index:
            self._tableWidget.rowChanged.emit(rowId, "hide")

    def addAnalyse(self, analyse: Analyse) -> None:
        self._analyse = analyse

    def displayAnalyseData(self, analyseDataIndex: int) -> None:
        # TODO if analyse.classification == "DEF" remove region privileges
        analyseData = self._analyse.data[analyseDataIndex]
        self._peakPlot.clear()
        self._spectrumPlot.clear()
        self._spectrumPlot.addItem(self._zoomRegion, ignoreBounds=True)
        self._peakPlot.addItem(self._vLine, ignoreBounds=True)
        self._peakPlot.addItem(self._hLine, ignoreBounds=True)
        x = analyseData.x
        y = analyseData.y
        self._conditionId = analyseData.condition
        self.setWindowTitle(f"Condition {analyseData.condition}")
        self._kev = [calculation.pxToEv(i) for i in x]
        self._spectrumPlot.plot(x=x, y=y, pen=pg.mkPen("w", width=2))
        self._peakPlot.plot(x=x, y=y, pen=pg.mkPen("w", width=2))
        self._spectrumPlot.setLimits(xMin=0, xMax=max(x), yMin=0, yMax=1.1 * max(y))
        self._peakPlot.setLimits(xMin=0, xMax=max(x), yMin=0, yMax=1.1 * max(y))
        self._zoomRegion.setBounds((0, max(x)))
        self._zoomRegion.setRegion((0, 100))
        self._peakPlot.setXRange(0, 100, padding=0)
        self._setCoordinate(0, 0)
        self._fillTable()
        self._searchedElement.setDisabled(False)
        self._searchedRadiation.setDisabled(False)

    def mousePressEvent(self, a0):
        if (
                not self._searchedElement.geometry().contains(a0.pos())
                and self._searchedElement.hasFocus()
        ):
            self._searchedElement.clearFocus()
        return super().mousePressEvent(a0)

    def closeEvent(self, a0):
        # self._saveToDatabase()
        return super().closeEvent(a0)

    def _saveToDatabase(self) -> None:
        for row in self._df.itertuples(index=False):
            conditionId = row.condition_id
            query = f"""
                UPDATE Lines
                SET low_kiloelectron_volt = {row.low_kiloelectron_volt},
                    high_kiloelectron_volt = {row.high_kiloelectron_volt},
                    active = {row.active},
                    condition_id = {int(conditionId) if not np.isnan(conditionId) else "NULL"}
                WHERE line_id = {row.line_id};
            """
            self._db.executeQuery(query)
