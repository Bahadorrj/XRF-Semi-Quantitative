from functools import partial

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTableWidgetItem

from python.utils import calculation, datatypes
from python.utils.database import getDatabase
from python.utils.datatypes import Analyse
from python.utils.paths import resource_path


class ElementsTableWidget(QtWidgets.QTableWidget):
    rowChanged = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super(ElementsTableWidget, self).__init__(parent)
        self.rowIds = list()
        self.intensities = list()
        self.setModifiedSections()

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
            ""
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

    def setHorizontalHeaderLabels(self, labels: list) -> None:
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

    def addRow(self, rowId: int, row: pd.Series, intensity: int, conditionId: int) -> None:
        self.rowIds.append(rowId)
        self.intensities.append(intensity)
        self.setRowCount(self.rowCount() + 1)
        self._createButtons(rowId, row, conditionId)
        self._createItems(row, intensity)

    def _createButtons(self, rowId: int, row: pd.Series, conditionId: int) -> None:
        rowIndex = self.rowCount() - 1
        mapper = {"hide": 0, "condition": 7, "status": 9}
        for label, column in mapper.items():
            if label == "hide":
                widget = QtWidgets.QPushButton(
                    icon=QtGui.QIcon(resource_path(f"icons/{label}.png"))
                )
                widget.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                    }
                """)
                widget.clicked.connect(partial(self._emitRowChanged, label, rowId))
            elif label == "condition":
                widget = QtWidgets.QComboBox()
                values = [
                    'Condition 1', 'Condition 2', 'Condition 3',
                    'Condition 4', 'Condition 5', 'Condition 6',
                    'Condition 7', 'Condition 8', 'Condition 9'
                ]
                widget.addItems(values)
                widget.setCurrentText(f"Condition {conditionId}")
                widget.setStyleSheet("""
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
                        background-color: lightblue; /* Custom background color for the drop-down menu */
                    }
                """)
                widget.currentTextChanged.connect(partial(self._emitRowChanged, label, rowId))
            else:
                if row['active'] == 0:
                    widget = QtWidgets.QPushButton("Activate")
                else:
                    widget = QtWidgets.QPushButton("Deactivate")
                widget.setStyleSheet("""
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
                    """)
                widget.clicked.connect(partial(self._emitRowChanged, label, rowId))
            self.setCellWidget(rowIndex, column, widget)

    def _createItems(self, row: pd.Series, intensity: int) -> None:
        rowIndex = self.rowCount() - 1
        mapper = {
            0: str(row['symbol']),
            1: str(row['radiation_type']),
            2: str(row['kiloelectron_volt']),
            3: str(row['low_kiloelectron_volt']),
            4: str(row['high_kiloelectron_volt']),
            5: str(intensity),
            6: str(int(row['condition_id'])) if not np.isnan(row['condition_id']) else "",
            7: "Activated" if row['active'] == 1 else "Deactivated"
        }
        for column, value in mapper.items():
            item = QTableWidgetItem(value)
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            if column == 7:
                if value == "Activated":
                    item.setForeground(QtGui.QColor(0, 255, 0))
                else:
                    item.setForeground(QtGui.QColor(255, 0, 0))
            self.setItem(rowIndex, column + 1, item)

    def getRow(self, row: int) -> dict:
        rowDict = dict()
        for column in range(self.columnCount()):
            header = self.horizontalHeaderItem(column).text()
            if header == "" or header == "Condition":
                rowDict[column] = self.cellWidget(row, column)
            else:
                key = header.lower().replace(" ", "-")
                rowDict[key] = self.item(row, column)
        return rowDict

    def getRowById(self, rowId: int) -> dict:
        rowIndex = self.rowIds.index(rowId)
        return self.getRow(rowIndex)

    def _emitRowChanged(self, label: str, rowId: int) -> None:
        self.rowChanged.emit(label, rowId)

    def removeRow(self, row):
        super().removeRow(row)
        self.rowIds.pop(row)
        self.intensities.pop(row)


class PeakSearchWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(PeakSearchWindow, self).__init__(parent)
        self._analyse = None
        self._conditionId = None
        self._kev = None
        self._db = getDatabase(resource_path("fundamentals.db"))
        self._df = self._db.dataframe("SELECT * FROM Lines")
        self._plotDataList = [datatypes.PlotData.fromSeries(rowId, s) for rowId, s in self._df.iterrows()]
        self.resize(1200, 800)
        self._createTableWidget()
        self._createPlotViewBox()
        self._createMenuBar()
        self._setupView()

    def _createTableWidget(self) -> None:
        self._tableWidget = ElementsTableWidget(self)
        self._tableWidget.setMinimumHeight(115)
        self._tableWidget.setMaximumHeight(int(self.size().height() / 3))
        self._tableWidget.setAlternatingRowColors(True)
        self._tableWidget.rowChanged.connect(self._rowChanged)
        self._tableWidget.itemClicked.connect(self._itemClicked)

    def _createPlotViewBox(self) -> None:
        self._graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self._createPeakPlot()
        self._createSpectrumPlot()
        self._createCoordinateLabel()

    def _createPeakPlot(self):
        self._peakPlot = self._graphicsLayoutWidget.addPlot(row=0, col=0)
        self._peakPlot.showGrid(x=True, y=True)
        self._vLine = pg.InfiniteLine(angle=90, movable=False)
        self._hLine = pg.InfiniteLine(angle=0, movable=False)
        self._peakPlot.vb.scaleBy(center=(0, 0))
        self._peakPlot.vb.menu.clear()
        self._peakPlot.setMinimumHeight(
            self._graphicsLayoutWidget.sizeHint().height() * 2 / 3
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

    def _createCoordinateLabel(self) -> None:
        self._coordinateLabel = QtWidgets.QLabel()
        self._coordinateLabel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._coordinateLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

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
        with open(path, "w") as f:
            for rowId, intensity in zip(self._tableWidget.rowIds, self._tableWidget.intensities):
                symbol = self._df.at[rowId, "symbol"]
                radiation = self._df.at[rowId, "radiation_type"]
                f.write(f"{symbol}-{radiation}: {intensity}\n")

    def _setupView(self) -> None:
        centralWidget = QtWidgets.QSplitter(self)
        centralWidget.setOrientation(QtCore.Qt.Orientation.Vertical)
        centralWidget.addWidget(self._tableWidget)
        graphicWidget = QtWidgets.QWidget()
        graphicWidgetLayout = QtWidgets.QVBoxLayout(graphicWidget)
        graphicWidgetLayout.addWidget(self._coordinateLabel)
        graphicWidgetLayout.addWidget(self._graphicsLayoutWidget)
        graphicWidgetLayout.setStretch(1, 1)
        graphicWidget.setLayout(graphicWidgetLayout)
        centralWidget.addWidget(graphicWidget)
        self.setCentralWidget(centralWidget)

    def _fillTable(self) -> None:
        for data in self._plotDataList:
            self._addPlotData(data)

    def _addPlotData(self, plotData: datatypes.PlotData) -> None:
        series: pd.Series = self._df.iloc[plotData.rowId]
        minX, maxX = plotData.region.getRegion()
        y = list(filter(lambda d: d.condition == self._conditionId, self._analyse.data))[0].y
        intensity = y[int(minX):int(maxX)].sum()
        self._tableWidget.addRow(plotData.rowId, series["symbol":"active"], intensity, self._conditionId)
        plotData.region.sigRegionChanged.connect(partial(self._changeRangeOfData, plotData))
        plotData.peakLine.sigClicked.connect(partial(self._selectData, plotData))
        plotData.spectrumLine.sigClicked.connect(partial(self._selectData, plotData))

    @QtCore.pyqtSlot()
    def _changeRangeOfData(self, data: datatypes.PlotData) -> None:
        minX, maxX = data.region.getRegion()
        minKev = self._kev[int(minX)]
        maxKev = self._kev[int(maxX)]
        row = self._tableWidget.getRowById(data.rowId)
        conditionId = int(row.get(7).currentText().split(" ")[-1])
        y = list(filter(lambda d: d.condition == conditionId, self._analyse.data))[0].y
        intensity = y[int(minX):int(maxX)].sum()
        row.get("low-kev").setText(str(minKev))
        row.get("high-kev").setText(str(maxKev))
        row.get("intensity").setText(str(intensity))
        self._df.at[data.rowId, "low-kev"] = minKev
        self._df.at[data.rowId, "high-kev"] = maxKev

    @QtCore.pyqtSlot()
    def _selectData(self, data: datatypes.PlotData) -> None:
        self._tableWidget.setCurrentCell(self._tableWidget.rowIds.index(data.rowId), 0)
        self._hoverOverData(data)

    def _hoverOverData(self, data: datatypes.PlotData):
        minX, maxX = data.region.getRegion()
        viewMinX, viewMaxX = self._peakPlot.viewRange()[0]
        if viewMinX > minX or viewMaxX < maxX:
            zoomedArea = (minX - 50, maxX + 50)
            self._zoomRegion.setRegion(zoomedArea)

    @QtCore.pyqtSlot(str, int)
    def _rowChanged(self, buttonLabel: str, rowId: int) -> None:
        if buttonLabel == "hide":
            data = self._plotDataList[rowId]
            self._dataVisibilityChanged(data)
        elif buttonLabel == "condition":
            data = self._plotDataList[rowId]
            minX, maxX = data.region.getRegion()
            row = self._tableWidget.getRowById(rowId)
            conditionId = int(row.get(7).currentText().split(" ")[-1])
            y = list(filter(lambda d: d.condition == conditionId, self._analyse.data))[0].y
            intensity = y[int(minX):int(maxX)].sum()
            row.get("intensity").setText(str(intensity))
        else:
            data = self._plotDataList[rowId]
            self._dataStatusChanged(data)

    def _dataVisibilityChanged(self, data: datatypes.PlotData) -> None:
        row = self._tableWidget.getRowById(data.rowId)
        hideButton = row.get(0)
        if data.visible:
            self._erasePlotData(data)
            hideButton.setIcon(QtGui.QIcon(resource_path("icons/hide.png")))
        else:
            self._selectData(data)
            self._drawPlotData(data)
            hideButton.setIcon(QtGui.QIcon(resource_path("icons/show.png")))
        data.visible = not data.visible

    def _dataStatusChanged(self, data: datatypes.PlotData) -> None:
        row = self._tableWidget.getRowById(data.rowId)
        statusItem = row.get("status")
        statusButton = row.get(self._tableWidget.columnCount() - 1)
        if data.active:
            data.deactivate()
            self._df.at[data.rowId, 'active'] = 0
            statusItem.setText("Deactivated")
            statusItem.setForeground(QtGui.QColor(255, 0, 0))
            statusButton.setText("Activate")
        else:
            symbol = self._df.at[data.rowId, 'symbol']
            df = self._df.query(f"symbol == '{symbol}' and active == 1")
            if df.empty:
                data.activate()
                self._df.at[data.rowId, 'active'] = 1
                statusItem.setText("Activated")
                statusItem.setForeground(QtGui.QColor(0, 255, 0))
                statusButton.setText("Deactivate")
            else:
                messageBox = QtWidgets.QMessageBox(self)
                messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
                messageBox.setText(
                    f"One Line Of {symbol} Is Already Identified As The Main Line.\n"
                    "Activating This Line Will Deactivate The Previous Line And Replace It With The Current.\n"
                    "Would You Like To Continue?"
                )
                messageBox.setWindowTitle("Activation Failed")
                messageBox.setStandardButtons(
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
                )
                result = messageBox.exec()
                if result == QtWidgets.QMessageBox.StandardButton.Yes:
                    self._dataStatusChanged(self._plotDataList[df.index[0]])
                    data.activate()
                    self._df.at[data.rowId, 'active'] = 1
                    statusItem.setText("Activated")
                    statusItem.setForeground(QtGui.QColor(0, 255, 0))
                    statusButton.setText("Deactivate")
        if data.visible:
            self._erasePlotData(data)
            self._selectData(data)
            self._drawPlotData(data)

    def _drawPlotData(self, data: datatypes.PlotData) -> None:
        if data.peakLine not in self._peakPlot.items:
            self._peakPlot.addItem(data.peakLine)
        if data.spectrumLine not in self._spectrumPlot.items:
            self._spectrumPlot.addItem(data.spectrumLine)
        if data.region not in self._peakPlot.items and data.active is False:
            self._peakPlot.addItem(data.region)

    def _erasePlotData(self, data: datatypes.PlotData) -> None:
        if data.peakLine in self._peakPlot.items:
            self._peakPlot.removeItem(data.peakLine)
        if data.spectrumLine in self._spectrumPlot.items:
            self._spectrumPlot.removeItem(data.spectrumLine)
        if data.region in self._peakPlot.items:
            self._peakPlot.removeItem(data.region)

    def _showCorrelatedToData(self, data: datatypes.PlotData) -> None:
        symbol = self._df.at[data.rowId, 'symbol']
        correlatedIndexes = self._df[self._df['symbol'] == symbol].index
        for i in correlatedIndexes:
            if i != data.rowId:
                d = self._plotDataList[i]
                if i in self._tableWidget.rowIds:
                    row = self._tableWidget.getRowById(i)
                    row.get(0).setIcon(QtGui.QIcon(resource_path("icons/show.png")))
                else:
                    d.neutralize()
                if d.peakLine not in self._peakPlot.items:
                    self._peakPlot.addItem(d.peakLine)
                if d.spectrumLine not in self._spectrumPlot.items:
                    self._spectrumPlot.addItem(d.spectrumLine)

    def _hideCorrelatedToData(self, data: datatypes.PlotData) -> None:
        symbol = self._df.at[data.rowId, 'symbol']
        correlatedIndexes = self._df[self._df['symbol'] == symbol].index
        for i in correlatedIndexes:
            if i != data.rowId:
                d = self._plotDataList[i]
                if i in self._tableWidget.rowIds:
                    row = self._tableWidget.getRowById(i)
                    row.get(0).setIcon(QtGui.QIcon(resource_path("icons/hide.png")))
                else:
                    d.deactivate()
                if d.peakLine in self._peakPlot.items:
                    self._peakPlot.removeItem(d.peakLine)
                if d.spectrumLine in self._spectrumPlot.items:
                    self._spectrumPlot.removeItem(d.spectrumLine)

    @QtCore.pyqtSlot(QtWidgets.QTableWidgetItem)
    def _itemClicked(self, item: QtWidgets.QTableWidgetItem) -> None:
        rowId = self._tableWidget.rowIds[item.row()]
        data = self._plotDataList[rowId]
        self._hoverOverData(data)

    def _setCoordinate(self, x: float, y: float) -> None:
        kev = self._kev[int(x)]
        self._coordinateLabel.setText(
            f"""
            <span style="font-size: 14px; 
                        color: rgb(128, 128, 128);
                        padding: 5px;
                        letter-spacing: 2px">x= {x} y= {y} KeV= {kev}</span>
            """
        )

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
            filteredDataframe = self._df[mask]
            for radiationLabel in self._df["radiation_type"].unique():
                filteredData = filteredDataframe[filteredDataframe["radiation_type"] == radiationLabel]
                if not filteredData.empty:
                    menu = self._peakPlot.vb.menu.addMenu(radiationLabel)
                    menu.triggered.connect(self._actionClicked)
                    for symbol in filteredData["symbol"]:
                        menu.addAction(symbol)

    def _actionClicked(self, action: QtGui.QAction):
        elementSymbol = action.text()
        radiationType = action.parent().title()
        mask = np.logical_and(
            self._df["symbol"] == elementSymbol,
            self._df["radiation_type"] == radiationType
        )
        rowId = self._df[mask].index.values[0]
        data = self._plotDataList[rowId]
        data.visible = True
        self._addPlotData(data)
        self._tableWidget.getRowById(rowId).get(1).setIcon(QtGui.QIcon(resource_path('icons/show.png')))
        self._drawPlotData(data)
        self._selectData(data)

    def addAnalyse(self, analyse: Analyse) -> None:
        self._analyse = analyse

    def displayAnalyseData(self, analyseDataIndex: int) -> None:
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
        self._fillTable()

    def closeEvent(self, event):
        # self._saveToDatabase()
        event.accept()

    def _saveToDatabase(self):
        for _, row in self._df.iterrows():
            if row['active'] == 1:
                query = f"""
                    UPDATE Lines
                    SET low_kiloelectron_volt = {row['low_kiloelectron_volt']},
                        high_kiloelectron_volt = {row['high_kiloelectron_volt']},
                        active = {row['active']},
                        condition_id = {self._conditionId}
                    WHERE line_id = {row['line_id']};
                """
            else:
                query = f"""
                    UPDATE Lines
                    SET active = {row['active']},
                        condition_id = "NULL"
                    WHERE line_id = {row['line_id']};
                """
            self._db.executeQuery(query)
