from functools import partial

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import pyqtSignal

from python.utils import calculation, datatypes
from python.utils.database import getDatabase
from python.utils.paths import resource_path


class ElementsTableWidget(QtWidgets.QTableWidget):
    rowChanged = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super(ElementsTableWidget, self).__init__(parent)
        self.rowIds = list()
        self.intensities = list()
        self.setBaseSections()
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def setBaseSections(self):
        headers = [
            "Element",
            "Type",
            "Kev",
            "Low Kev",
            "High Kev",
            "Intensity",
            "Status",
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

    def setModifiedSections(self):
        headers = [
            "",
            "",
            "Element",
            "Type",
            "Kev",
            "Low Kev",
            "High Kev",
            "Intensity",
            "Status",
            "",
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

    def addRow(self, rowId: int, row: pd.Series, intensity: int):
        if self.rowCount() == 0:
            self.setModifiedSections()
        self.rowIds.append(rowId)
        self.intensities.append(intensity)
        self.setRowCount(self.rowCount() + 1)
        self._createButtons(rowId, row)
        self._createItems(row, intensity)

    def _createButtons(self, rowId: int, row: pd.Series) -> None:
        rowIndex = self.rowCount() - 1
        mapper = {"remove": 0, "hide": 1, "status": self.columnCount() - 1}
        for label, column in mapper.items():
            if label in ["remove", "hide"]:
                button = QtWidgets.QPushButton(
                    icon=QtGui.QIcon(resource_path(f"icons/{label}.png"))
                )
                button.setStyleSheet(
                    """
                    QPushButton {
                        background-color: transparent;
                    }"""
                )
            else:
                if row['active'] == 0:
                    button = QtWidgets.QPushButton("Activate")
                else:
                    button = QtWidgets.QPushButton("Deactivate")
                button.setStyleSheet(
                    """
                    QPushButton {
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
            self.setCellWidget(rowIndex, column, button)
            button.clicked.connect(partial(self._emitRowChanged, label, rowId))

    def _createItems(self, row: pd.Series, intensity: int) -> None:
        rowIndex = self.rowCount() - 1
        for column, value in enumerate(row):
            if column == 6:
                mapper = {1: ("Activated", QtGui.QColor(0, 255, 0)), 0: ("Deactivated", QtGui.QColor(255, 0, 0))}
                label, color = mapper[value]
                item = QtWidgets.QTableWidgetItem(label)
                item.setForeground(color)
            elif column == 5:
                item = QtWidgets.QTableWidgetItem(str(intensity))
            else:
                item = QtWidgets.QTableWidgetItem(str(value))
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.setItem(rowIndex, column + 2, item)
        item = QtWidgets.QTableWidgetItem(str(intensity))
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setItem(rowIndex, 7, item)

    def getRow(self, row: int) -> dict:
        rowDict = dict()
        for column in range(self.columnCount()):
            header = self.horizontalHeaderItem(column).text()
            if header == "":
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

    def clear(self):
        super().clear()
        self.setRowCount(0)
        self.rowIds.clear()
        self.setBaseSections()


class PeakSearchWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(PeakSearchWindow, self).__init__(parent)
        self._conditionId = None
        self._x = None
        self._y = None
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
        self._tableWidget.horizontalHeader().sectionClicked.connect(self._headerClicked)

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
                f.write(f"{symbol}: {intensity}\n")

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
        if not self._df[self._df["active"] == 1].empty:
            for rowId, row in self._df.iterrows():
                if row["active"] == 1:
                    data = self._plotDataList[rowId]
                    self._addPlotData(data)

    def _addPlotData(self, data: datatypes.PlotData) -> None:
        series: pd.Series = self._df.iloc[data.rowId]
        minX, maxX = data.region.getRegion()
        intensity = self._y[int(minX):int(maxX)].sum()
        self._tableWidget.addRow(data.rowId, series["symbol":"active"], intensity)
        data.region.sigRegionChanged.connect(partial(self._changeRangeOfData, data))
        data.peakLine.sigClicked.connect(partial(self._selectData, data))
        data.spectrumLine.sigClicked.connect(partial(self._selectData, data))

    @QtCore.pyqtSlot()
    def _changeRangeOfData(self, data: datatypes.PlotData) -> None:
        minX, maxX = data.region.getRegion()
        minKev = self._kev[int(minX)]
        maxKev = self._kev[int(maxX)]
        intensity = self._y[int(minX):int(maxX)].sum()
        row = self._tableWidget.getRowById(data.rowId)
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
        if buttonLabel == "remove":
            symbol = self._df.at[rowId, "symbol"]
            radiationType = self._df.at[rowId, "radiation_type"]
            messageBox = QtWidgets.QMessageBox()
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            messageBox.setText(f"Are you sure you want to remove {symbol}-{radiationType}?")
            messageBox.setWindowTitle("Remove?")
            messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes
                                          | QtWidgets.QMessageBox.StandardButton.No)
            result = messageBox.exec()
            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                data = self._plotDataList[rowId]
                self._removeData(data)
                self._popFromTree(data)
        elif buttonLabel == "hide":
            data = self._plotDataList[rowId]
            self._dataVisibilityChanged(data)
        else:
            data = self._plotDataList[rowId]
            self._dataStatusChanged(data)

    def _removeData(self, data: datatypes.PlotData) -> None:
        if data.visible:
            self._erasePlotData(data)
            if data.active is False:
                self._hideCorrelatedToData(data)
        data.deactivate()
        self._df.at[data.rowId, "active"] = 0

    def _popFromTree(self, data: datatypes.PlotData) -> None:
        index = self._tableWidget.rowIds.index(data.rowId)
        self._tableWidget.removeRow(index)
        if self._tableWidget.rowCount() == 0:
            self._tableWidget.setBaseSections()

    def _dataVisibilityChanged(self, data: datatypes.PlotData) -> None:
        row = self._tableWidget.getRowById(data.rowId)
        hideButton = row.get(1)
        if data.visible:
            self._erasePlotData(data)
            if data.active is False:
                self._hideCorrelatedToData(data)
            hideButton.setIcon(QtGui.QIcon(resource_path("icons/hide.png")))
        else:
            self._selectData(data)
            self._drawPlotData(data)
            if data.active is False:
                self._showCorrelatedToData(data)
            hideButton.setIcon(QtGui.QIcon(resource_path("icons/show.png")))
        data.visible = not data.visible

    def _dataStatusChanged(self, data: datatypes.PlotData) -> None:
        data.visible = True
        self._erasePlotData(data)
        row = self._tableWidget.getRowById(data.rowId)
        statusItem = row.get("status")
        hideButton = row.get(1)
        hideButton.setIcon(QtGui.QIcon(resource_path("icons/show.png")))
        statusButton = row.get(self._tableWidget.columnCount() - 1)
        if data.active:
            data.deactivate()
            self._df.at[data.rowId, 'active'] = 0
            statusItem.setText("Deactivated")
            statusItem.setForeground(QtGui.QColor(255, 0, 0))
            statusButton.setText("Activate")
            self._showCorrelatedToData(data)
        else:
            data.activate()
            self._df.at[data.rowId, 'active'] = 1
            low, high = data.region.getRegion()
            statusItem.setText("Activated")
            statusItem.setForeground(QtGui.QColor(0, 255, 0))
            statusButton.setText("Deactivate")
            self._hideCorrelatedToData(data)
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
                    row.get(1).setIcon(QtGui.QIcon(resource_path("icons/show.png")))
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
                    row.get(1).setIcon(QtGui.QIcon(resource_path("icons/hide.png")))
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

    @QtCore.pyqtSlot(int)
    def _headerClicked(self, column: int) -> None:
        if column == 0:
            messageBox = QtWidgets.QMessageBox()
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            messageBox.setText(f"This will deactivate all lines.\n"
                               f"Are you sure you want to continue?")
            messageBox.setWindowTitle("Remove All?")
            messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes
                                          | QtWidgets.QMessageBox.StandardButton.No)
            result = messageBox.exec()
            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                self._removeAll()
        elif column == 1:
            self._hideALL()

    def _removeAll(self):
        for rowId in self._tableWidget.rowIds:
            data = self._plotDataList[rowId]
            self._removeData(data)
        self._tableWidget.clear()

    def _hideALL(self):
        pass

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
        if rowId in self._tableWidget.rowIds:
            messageBox = QtWidgets.QMessageBox()
            messageBox.setText(
                f"{elementSymbol} - {radiationType} is already added to the table.\n"
                f"Would you like this line to be shown?"
            )
            messageBox.setWindowTitle("Duplicate  element!")
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
            messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes
                                          | QtWidgets.QMessageBox.StandardButton.No)
            returnValue = messageBox.exec()
            if returnValue == QtWidgets.QMessageBox.StandardButton.Yes:
                data = self._plotDataList[rowId]
                data.visible = True
                self._drawPlotData(data)
                if data.active is False:
                    self._showCorrelatedToData(data)
                self._selectData(data)
        else:
            data = self._plotDataList[rowId]
            data.visible = True
            self._addPlotData(data)
            self._tableWidget.getRowById(rowId).get(1).setIcon(QtGui.QIcon(resource_path('icons/show.png')))
            self._drawPlotData(data)
            self._showCorrelatedToData(data)
            self._selectData(data)

    def displayAnalyseData(self, analyseData: datatypes.AnalyseData) -> None:
        self._peakPlot.clear()
        self._spectrumPlot.clear()
        self._spectrumPlot.addItem(self._zoomRegion, ignoreBounds=True)
        self._peakPlot.addItem(self._vLine, ignoreBounds=True)
        self._peakPlot.addItem(self._hLine, ignoreBounds=True)
        self._x = analyseData.x
        self._y = analyseData.y
        self._conditionId = analyseData.condition
        self.setWindowTitle(f"Condition {analyseData.condition}")
        self._kev = [calculation.pxToEv(x) for x in self._x]
        self._spectrumPlot.plot(x=self._x, y=self._y, pen=pg.mkPen("w", width=2))
        self._peakPlot.plot(x=self._x, y=self._y, pen=pg.mkPen("w", width=2))
        self._spectrumPlot.setLimits(xMin=0, xMax=max(self._x), yMin=0, yMax=1.1 * max(self._y))
        self._peakPlot.setLimits(xMin=0, xMax=max(self._x), yMin=0, yMax=1.1 * max(self._y))
        self._zoomRegion.setBounds((0, max(self._x)))
        self._zoomRegion.setRegion((0, 100))
        self._peakPlot.setXRange(0, 100, padding=0)
        self._fillTable()

    def closeEvent(self, event):
        self._saveToDatabase()
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
