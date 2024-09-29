import contextlib

import pandas as pd
import pyqtgraph as pg

from PyQt6 import QtWidgets, QtCore, QtGui
from dataclasses import dataclass
from collections import deque
from functools import partial

from src.utils import calculation, datatypes
from src.utils.paths import resourcePath

from src.views.base.tablewidget import DataframeTableWidget, TableItem


@dataclass(order=True)
class PlotData:
    spectrumLine: pg.InfiniteLine
    peakLine: pg.InfiniteLine
    region: pg.LinearRegionItem

    def activate(self):
        self.active = True
        self.peakLine.pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
        self.spectrumLine.pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
        self.region.setMovable(False)

    def deactivate(self):
        self.active = False
        self.peakLine.pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        self.spectrumLine.pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        self.region.setMovable(True)

    @classmethod
    def fromSeries(cls, series: pd.Series) -> "PlotData":
        spectrumLine = cls._generateLine(series)
        peakLine = cls._generateLine(series, lineType="peak")
        rng = (
            calculation.evToPx(float(series["low_kiloelectron_volt"])),
            calculation.evToPx(float(series["high_kiloelectron_volt"])),
        )
        region = cls._generateRegion(rng, not bool(series["active"]))
        return PlotData(spectrumLine, peakLine, region)

    @staticmethod
    def _generateLine(series: pd.Series, lineType: str = "spectrum") -> pg.InfiniteLine:
        value = calculation.evToPx(float(series["kiloelectron_volt"]))
        line = pg.InfiniteLine()
        line.setAngle(90)
        line.setMovable(False)
        line.setValue(value)
        active = bool(series["active"])
        pen = pg.mkPen()
        if active:
            pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
        else:
            pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        radiation = series["radiation_type"]
        match radiation:
            case "Ka":
                pen.setColor(pg.mkColor("#00FFFF"))
            case "Kb":
                pen.setColor(pg.mkColor("#FF00FF"))
            case "La":
                pen.setColor(pg.mkColor("#FFFF00"))
            case "Lb":
                pen.setColor(pg.mkColor("#00FF00"))
            case "Ly":
                pen.setColor(pg.mkColor("#FFA500"))
            case "Ma":
                pen.setColor(pg.mkColor("#ADD8E6"))
        if lineType == "peak":
            pen.setWidth(2)
            pos = 1
            for label in [radiation, series["symbol"]]:
                pos -= 0.1
                pg.InfLineLabel(line, text=label, movable=False, position=pos)
        else:
            pen.setWidth(1)
        line.setPen(pen)
        return line

    @staticmethod
    def _generateRegion(
        rng: list[float, float] | tuple[float, float], movable: bool = True
    ):
        region = pg.LinearRegionItem(swapMode="push")
        region.setZValue(10)
        region.setRegion(rng)
        region.setBounds((0, 2048))
        region.setMovable(movable)
        return region


@dataclass
class DataPacket:
    packetId: int
    plotData: PlotData
    tableRow: dict


class ConditionComboBox(QtWidgets.QComboBox):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.currentText_ = super().currentText()
        self.previousText = self.currentText_
        self.setObjectName("condition-combo-box")
        self.currentTextChanged.connect(self._currentTextChanged)

    @QtCore.pyqtSlot(str)
    def _currentTextChanged(self, text: str) -> None:
        self.previousText = self.currentText_
        self.currentText_ = text

    def setCurrentText(self, text: str | None) -> None:
        self.previousText = self.currentText_
        self.currentText_ = text
        return super().setCurrentText(text)


class PeakSearchTableWidget(DataframeTableWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        dataframe: pd.DataFrame | None = None,
        autoFill: bool = False,
        editable: bool = False,
    ) -> None:
        super().__init__(parent, dataframe, autoFill, editable)
        self.setObjectName("peak-lines-table")
        self.setHeaders(
            [
                "",
                "Element",
                "Type",
                "KeV",
                "Low KeV",
                "High KeV",
                "Intensity",
                "Condition",
                "Status",
                "",
            ]
        )

    def currentPacketId(self) -> int:
        return self.getCurrentRow().get("packetId") if self.getCurrentRow() else -1

    def getRowByPacketId(self, packetId: int) -> dict:
        return next((d for d in self.rows.values() if d["packetId"] == packetId), None)

    def selectRowByPacketID(self, packetId: int) -> None:
        for rowIndex, row in self.rows.items():
            if row["packetId"] == packetId:
                self.selectRow(rowIndex)
                break


class PeakSearchWidget(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        analyse: datatypes.Analyse | None = None,
        dataframe: pd.DataFrame | None = None,
    ):
        super().__init__(parent)
        self._analyse = None
        self._df = None
        self._activeIntensities = None
        self._dataPackets = None
        self._stack = None
        self._visible = None
        self._elementsInRange = None
        self._kev = [calculation.pxToEv(i) for i in range(2048)]
        self._initializeUi()
        if analyse is not None and dataframe is not None:
            self.supply(analyse, dataframe)
        self.hide()

    def _initializeUi(self) -> None:
        self._createActions(
            {
                "undo": True,
                "region": False,
            }
        )
        self._createToolBar()
        self._createSearchLayout()
        self._createStatusLayout()
        self._createTableWidget()
        self._createPlotViewBox()
        self._setUpView()

    def _createActions(self, labels: dict) -> None:
        self._actionsMap = {}
        for label, disabled in labels.items():
            action = QtGui.QAction(label, self)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"resources/icons/{key}.png")))
            action.setDisabled(disabled)
            self._actionsMap[key] = action
            if label == "region":
                action.setCheckable(True)
                action.triggered.connect(self._toggleRegions)
            else:
                action.triggered.connect(self._undo)

    def _undo(self) -> None:
        packetId, region, condition, action = self._stack.pop()
        if not self._stack:
            self._actionsMap["undo"].setDisabled(True)
        dataPacket = self._dataPackets[packetId]
        if action == "region":
            dataPacket.plotData.region.blockSignals(True)
            dataPacket.plotData.region.setRegion(region)
            dataPacket.plotData.region.blockSignals(False)
        elif action == "condition":
            dataPacket.tableRow["conditionComboBox"].blockSignals(True)
            dataPacket.tableRow["conditionComboBox"].setCurrentText(condition)
            dataPacket.tableRow["conditionComboBox"].blockSignals(False)
        self._isDataPacketChanged(packetId, action)

    def _toggleRegions(self, checked: bool) -> None:
        for dataPacket in self._dataPackets:
            if self._visible[dataPacket.packetId]:
                if checked:
                    self._peakPlot.addItem(dataPacket.plotData.region)
                else:
                    self._peakPlot.removeItem(dataPacket.plotData.region)

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar(self)
        self._toolBar.setIconSize(QtCore.QSize(16, 16))
        self._toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._toolBar.setMovable(False)
        self._fillToolBarWithActions()

    def _fillToolBarWithActions(self) -> None:
        self._toolBar.addAction(self._actionsMap["undo"])
        self._toolBar.addAction(self._actionsMap["region"])

    def _createSearchLayout(self) -> None:
        self._searchLineEdit = QtWidgets.QLineEdit(self)
        self._searchLineEdit.setObjectName("search-line-edit")
        self._searchLineEdit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._searchLineEdit.editingFinished.connect(self._search)
        self._searchComboBox = QtWidgets.QComboBox(self)
        self._searchComboBox.setObjectName("search-combo-box")
        self._searchComboBox.setCurrentIndex(0)
        self._searchComboBox.currentTextChanged.connect(self._search)
        self._searchLayout = QtWidgets.QHBoxLayout()
        self._searchLayout.addWidget(QtWidgets.QLabel("Element Symbol: ", self))
        self._searchLayout.addWidget(self._searchLineEdit)
        self._searchLayout.addWidget(QtWidgets.QLabel("Radiation Type: ", self))
        self._searchLayout.addWidget(self._searchComboBox)
        self._searchLayout.addStretch()

    @QtCore.pyqtSlot()
    def _search(self) -> None:
        symbol = self._searchLineEdit.text()
        radiation = self._searchComboBox.currentText()
        if symbol != "":
            df = self._df.query(f"symbol == '{self._searchLineEdit.text()}'")
            if radiation != "":
                df = df.query(
                    f"radiation_type == '{self._searchComboBox.currentText()}'"
                )
        elif radiation != "":
            df = self._df.query(
                f"radiation_type == '{self._searchComboBox.currentText()}'"
            )
        else:
            for packetId in self._df.index:
                self._tableWidget.setRowHidden(packetId, False)
            return
        if not df.empty:
            for packetId in self._df.index:
                if packetId not in df.index:
                    self._tableWidget.setRowHidden(packetId, True)
                else:
                    self._tableWidget.setRowHidden(packetId, False)

    def _addRow(self, row: dict) -> None:
        self._tableWidget.setRowCount(self._tableWidget.rowCount() + 1)
        rowIndex, columnIndex = self._tableWidget.rowCount() - 1, 0
        for component in row.values():
            if isinstance(component, QtWidgets.QWidget):
                self._tableWidget.setCellWidget(rowIndex, columnIndex, component)
                columnIndex += 1
            elif isinstance(component, QtWidgets.QTableWidgetItem):
                item = component.clone()
                self._tableWidget.setItem(rowIndex, columnIndex, item)
                columnIndex += 1

    def _createTableWidget(self) -> None:
        self._tableWidget = PeakSearchTableWidget(self)
        self._tableWidget.setMaximumHeight(200)
        self._tableWidget.itemSelectionChanged.connect(self._itemSelectionChanged)

    @QtCore.pyqtSlot()
    def _itemSelectionChanged(self) -> None:
        if packetId := self._tableWidget.currentPacketId() == -1:
            return
        if self._visible[packetId]:
            dataPacket = self._dataPackets[packetId]
            self._hoverOverPlotData(dataPacket.plotData)

    def _hoverOverPlotData(self, plotData: datatypes.PlotData):
        minX, maxX = plotData.region.getRegion()
        viewMinX, viewMaxX = self._peakPlot.viewRange()[0]
        if viewMinX > minX or viewMaxX < maxX:
            zoomedArea = (minX - 50, maxX + 50)
            self._zoomRegion.setRegion(zoomedArea)

    @QtCore.pyqtSlot()
    def _selectDataPacket(self, dataPacket: DataPacket) -> None:
        if dataPacket.packetId in [row["packetId"] for row in self._tableWidget.rows]:
            self._tableWidget.selectRowByPacketID(dataPacket.packetId)
            self._hoverOverPlotData(dataPacket.plotData)

    def _createTableRow(self, packetId: int, series: pd.Series) -> dict:
        try:
            intensity = self._activeIntensities[series["symbol"]][
                series["radiation_type"]
            ]
        except KeyError:
            intensity = "NA"
        tableRow = {
            "packetId": packetId,
            "hideButton": self._createHideWidget(packetId),
            "symbol": TableItem(series["symbol"]),
            "radiation-type": TableItem(series["radiation_type"]),
            "kiloelectronVolt": TableItem(str(series["kiloelectron_volt"])),
            "lowKiloelectronVolt": TableItem(str(series["low_kiloelectron_volt"])),
            "highKiloelectronVolt": TableItem(str(series["high_kiloelectron_volt"])),
            "intensity": TableItem(str(intensity)),
            "conditionComboBox": self._createConditionComboBox(packetId, series),
            "status": (
                TableItem("Activated")
                if series["active"] == 1
                else TableItem("Deactivated")
            ),
            "statusButton": self._createStatusButton(packetId, series),
        }
        if tableRow["status"].text() == "Activated":
            tableRow["status"].setForeground(QtCore.Qt.GlobalColor.darkGreen)
        else:
            tableRow["status"].setForeground(QtCore.Qt.GlobalColor.red)
        return tableRow

    def _createHideWidget(self, packetId: int) -> QtWidgets.QPushButton:
        if self._visible[packetId]:
            widget = QtWidgets.QPushButton(
                parent=self, icon=QtGui.QIcon(resourcePath("resources/icons/show.png"))
            )
        else:
            widget = QtWidgets.QPushButton(
                parent=self, icon=QtGui.QIcon(resourcePath("resources/icons/hide.png"))
            )
        widget.setObjectName("hide-button")
        widget.clicked.connect(partial(self._dataPacketChanged, packetId, "visibility"))
        return widget

    def _createConditionComboBox(
        self, packetId: int, series: pd.Series
    ) -> QtWidgets.QPushButton:
        widget = ConditionComboBox(self)
        items = [f"Condition {d.conditionId}" for d in self._analyse.data]
        items.insert(0, "")
        widget.addItems(items)
        if series["active"]:
            widget.setDisabled(True)
        if pd.isna(series["condition_id"]) is False:
            widget.setCurrentText(f"Condition {int(series['condition_id'])}")
        widget.currentTextChanged.connect(
            partial(self._dataPacketChanged, packetId, "condition")
        )
        return widget

    def _createStatusButton(
        self, packetId: int, series: pd.Series
    ) -> QtWidgets.QPushButton:
        if not series["active"]:
            widget = QtWidgets.QPushButton("Activate", self)
        else:
            widget = QtWidgets.QPushButton("Deactivate", self)
        widget.setObjectName("status-button")
        widget.clicked.connect(partial(self._dataPacketChanged, packetId, "status"))
        return widget

    def _fillTable(self) -> None:
        self._tableWidget.supply(self._df)
        for packet in self._dataPackets:
            self._tableWidget.addRow(packet.tableRow)

    def _createStatusLayout(self) -> None:
        self._statusLabel = QtWidgets.QLabel(self)
        self._statusLabel.setObjectName("status-label")
        self._coordinateLabel = QtWidgets.QLabel(self)
        self._coordinateLabel.setObjectName("coordinate-label")
        self._coordinateLabel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._coordinateLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self._statusLayout = QtWidgets.QHBoxLayout()
        self._statusLayout.addWidget(self._statusLabel)
        self._statusLayout.addWidget(self._coordinateLabel)

    def _createPlotViewBox(self) -> None:
        self._createStatusLayout()
        self._graphicsLayoutWidget = pg.GraphicsLayoutWidget(self)
        self._createPeakPlot()
        self._createSpectrumPlot()

    def _createPeakPlot(self) -> None:
        self._peakPlot = self._graphicsLayoutWidget.addPlot(row=0, col=0)
        self._peakPlot.showGrid(x=True, y=True)
        self._vLine = pg.InfiniteLine(angle=90, movable=False)
        self._hLine = pg.InfiniteLine(angle=0, movable=False)
        self._peakPlot.vb.scaleBy(center=(0, 0))
        self._peakPlot.vb.menu.clear()
        self._peakPlot.setMinimumHeight(250)
        self._peakPlot.sigRangeChanged.connect(self._adjustZoom)
        self._peakPlot.scene().sigMouseMoved.connect(self._mouseMoved)
        self._peakPlot.scene().sigMouseClicked.connect(self._openPopUp)

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

    def _setCoordinate(self, x: float, y: float) -> None:
        with contextlib.suppress(IndexError):
            kev = self._kev[int(x)]
            self._coordinateLabel.setText(f"x= {x} y= {y} KeV= {kev}")

    def _openPopUp(self, event):
        if event.button() != QtCore.Qt.MouseButton.RightButton:
            return
        minX, maxX = self._zoomRegion.getRegion()
        minKev = calculation.pxToEv(minX)
        maxKev = calculation.pxToEv(maxX)
        self._peakPlot.vb.menu.clear()
        self._elementsInRange = self._df.query(
            f"kiloelectron_volt <= {maxKev} and high_kiloelectron_volt >= {minKev}"
        )
        if self._elementsInRange.empty:
            return
        grouped = self._elementsInRange.groupby("radiation_type")
        for radiationType, group in grouped:
            menu = self._peakPlot.vb.menu.addMenu(radiationType)
            menu.triggered.connect(self._actionClicked)
            for symbol in group["symbol"]:
                menu.addAction(symbol)
        showAllAction = self._peakPlot.vb.menu.addAction("Show All")
        showAllAction.triggered.connect(self._showAll)
        hideAllAction = self._peakPlot.vb.menu.addAction("Hide All")
        hideAllAction.triggered.connect(self._hideAll)

    def _actionClicked(self, action: QtGui.QAction):
        elementSymbol = action.text()
        radiationType = action.parent().title()
        df = self._elementsInRange.query(
            f"symbol == '{elementSymbol}' and radiation_type == '{radiationType}'"
        )
        packetId = df.index.values[0]
        self._tableWidget.selectRowByPacketID(packetId)
        self._dataPacketChanged(packetId, "visibility")

    def _showAll(self) -> None:
        for packetId in self._elementsInRange.index:
            if self._visible[packetId] is False:
                self._tableWidget.selectRowByPacketID(packetId)
                self._dataPacketChanged(packetId, "visibility")

    def _hideAll(self) -> None:
        for packetId in self._elementsInRange.index:
            if self._visible[packetId] is True:
                self._tableWidget.selectRowByPacketID(packetId)
                self._dataPacketChanged(packetId, "visibility")

    def _createSpectrumPlot(self) -> None:
        self._spectrumPlot = self._graphicsLayoutWidget.addPlot(row=1, col=0)
        self._spectrumPlot.setMouseEnabled(x=False, y=False)
        self._spectrumPlot.showGrid(x=True, y=True)
        self._spectrumPlot.showGrid(x=True, y=True)
        self._zoomRegion = pg.LinearRegionItem(clipItem=self._spectrumPlot)
        self._zoomRegion.sigRegionChanged.connect(self._showZoomedRegion)

    def _showZoomedRegion(self):
        minX, maxX = self._zoomRegion.getRegion()
        self._peakPlot.setXRange(minX, maxX, padding=0)

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(self._toolBar)
        self.mainLayout.addLayout(self._searchLayout)
        self.mainLayout.addWidget(self._tableWidget)
        self.mainLayout.addLayout(self._statusLayout)
        self.mainLayout.addWidget(self._graphicsLayoutWidget)
        self.setLayout(self.mainLayout)

    def _dataPacketChanged(self, packetId: int, action: str) -> bool:
        dataPacket = self._dataPackets[packetId]
        condition = dataPacket.tableRow["conditionComboBox"].previousText
        region = (
            calculation.evToPx(
                float(dataPacket.tableRow["lowKiloelectronVolt"].text())
            ),
            calculation.evToPx(
                float(dataPacket.tableRow["highKiloelectronVolt"].text())
            ),
        )
        if self._isDataPacketChanged(packetId, action):
            self._stack.append((packetId, region, condition, action))
            self._actionsMap["undo"].setDisabled(False)

    def _isDataPacketChanged(self, packetId: int, action: str) -> bool:
        dataPacket = self._dataPackets[packetId]
        if action == "visibility":
            return self._visibilityChanged(dataPacket)
        elif action == "condition":
            return self._conditionChanged(dataPacket)
        elif action == "status":
            return self._statusChanged(dataPacket)
        elif action == "region":
            return self._regionChanged(dataPacket)

    def _visibilityChanged(self, dataPacket: DataPacket) -> bool:
        hideButton = dataPacket.tableRow.get("hideButton")
        if self._visible[dataPacket.packetId]:
            hideButton.setIcon(QtGui.QIcon(resourcePath("resources/icons/hide.png")))
            self._erasePlotData(dataPacket.plotData)
        else:
            hideButton.setIcon(QtGui.QIcon(resourcePath("resources/icons/show.png")))
            self._drawPlotData(dataPacket.plotData)
            self._hoverOverPlotData(dataPacket.plotData)
        self._visible[dataPacket.packetId] = not self._visible[dataPacket.packetId]
        return True

    def _drawPlotData(self, plotData: datatypes.PlotData) -> None:
        if plotData.peakLine not in self._peakPlot.items:
            self._peakPlot.addItem(plotData.peakLine)
        if plotData.spectrumLine not in self._spectrumPlot.items:
            self._spectrumPlot.addItem(plotData.spectrumLine)
        if (
            self._actionsMap["region"].isChecked()
            and plotData.region not in self._peakPlot.items
        ):
            self._peakPlot.addItem(plotData.region)

    def _erasePlotData(self, plotData: datatypes.PlotData) -> None:
        if plotData.peakLine in self._peakPlot.items:
            self._peakPlot.removeItem(plotData.peakLine)
        if plotData.spectrumLine in self._spectrumPlot.items:
            self._spectrumPlot.removeItem(plotData.spectrumLine)
        if plotData.region in self._peakPlot.items:
            self._peakPlot.removeItem(plotData.region)

    def _conditionChanged(self, dataPacket: DataPacket) -> bool:
        if conditionId := dataPacket.tableRow.get("conditionComboBox").currentText():
            conditionId = int(conditionId.split(" ")[-1])
            dataPacket.plotData.conditionId = conditionId
            self._df.at[dataPacket.packetId, "condition_id"] = conditionId
            if analyseData := next(
                (
                    d
                    for d in self._analyse.data
                    if d.conditionId == dataPacket.plotData.conditionId
                ),
                None,
            ):
                y = analyseData.y
                minX = calculation.evToPx(
                    self._df.at[dataPacket.packetId, "low_kiloelectron_volt"]
                )
                maxX = calculation.evToPx(
                    self._df.at[dataPacket.packetId, "high_kiloelectron_volt"]
                )
                intensity = y[round(minX) : round(maxX)].sum()
            else:
                intensity = "NA"
        else:
            intensity = "NA"
        dataPacket.tableRow.get("intensity").setText(str(intensity))
        return True

    def _statusChanged(self, dataPacket: DataPacket) -> bool:
        conditionComboBox = dataPacket.tableRow.get("conditionComboBox")
        if conditionComboBox.currentText() == "":
            messageBox = QtWidgets.QMessageBox(self)
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            messageBox.setText(
                "No condition is selected. Please select one before activating again."
            )
            messageBox.setWindowTitle("Activation failed")
            messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            messageBox.exec()
            return False
        self._df.at[dataPacket.packetId, "active"] = int(
            not self._df.at[dataPacket.packetId, "active"]
        )
        statusItem = dataPacket.tableRow.get("status")
        statusButton = dataPacket.tableRow.get("statusButton")
        if self._df.at[dataPacket.packetId, "active"]:
            dataPacket.plotData.activate()
            statusItem.setText("Activated")
            statusItem.setForeground(QtCore.Qt.GlobalColor.darkGreen)
            statusButton.setText("Deactivate")
            conditionComboBox.setDisabled(True)
        else:
            dataPacket.plotData.deactivate()
            statusItem.setText("Deactivated")
            statusItem.setForeground(QtCore.Qt.GlobalColor.red)
            statusButton.setText("Activate")
            conditionComboBox.setDisabled(False)
        if self._visible[dataPacket.packetId]:
            self._erasePlotData(dataPacket.plotData)
            self._hoverOverPlotData(dataPacket.plotData)
            self._drawPlotData(dataPacket.plotData)
        return True

    def _regionChanged(self, dataPacket: DataPacket) -> bool:
        def getKev(index, default):
            try:
                return self._kev[int(index)]
            except IndexError:
                return default

        minX, maxX = dataPacket.plotData.region.getRegion()
        minKev = getKev(minX, 0)
        maxKev = getKev(maxX, self._kev[-1])

        if analyseData := next(
            (
                d
                for d in self._analyse.data
                if d.conditionId == self._df.at[dataPacket.packetId, "condition_id"]
            ),
            None,
        ):
            intensity = analyseData.y[round(minX) : round(maxX)].sum()
        else:
            intensity = "NA"

        self._df.at[dataPacket.packetId, "low_kiloelectron_volt"] = minKev
        self._df.at[dataPacket.packetId, "high_kiloelectron_volt"] = maxKev

        dataPacket.tableRow.get("lowKiloelectronVolt").setText(str(minKev))
        dataPacket.tableRow.get("highKiloelectronVolt").setText(str(maxKev))
        dataPacket.tableRow.get("intensity").setText(str(intensity))
        return True

    def displayAnalyseData(self, analyseDataConditionId: int) -> None:
        analyseData = self._analyse.getDataByConditionId(analyseDataConditionId)
        x = analyseData.x
        y = analyseData.y
        self._peakPlot.clear()
        self._spectrumPlot.clear()
        self._spectrumPlot.addItem(self._zoomRegion, ignoreBounds=True)
        self._peakPlot.addItem(self._vLine, ignoreBounds=True)
        self._peakPlot.addItem(self._hLine, ignoreBounds=True)
        self._spectrumPlot.setLimits(xMin=0, xMax=max(x), yMin=0, yMax=1.1 * max(y))
        self._spectrumPlot.setXRange(0, max(x))
        self._spectrumPlot.setYRange(0, 1.1 * max(y))
        self._peakPlot.setLimits(xMin=0, xMax=max(x), yMin=0, yMax=1.1 * max(y))
        self._peakPlot.setXRange(0, 100)
        self._spectrumPlot.plot(x=x, y=y, pen=pg.mkPen("w", width=2))
        self._peakPlot.plot(x=x, y=y, pen=pg.mkPen("w", width=2))
        for dataPacket in self._dataPackets:
            if self._visible[dataPacket.packetId]:
                self._drawPlotData(dataPacket.plotData)
        self._zoomRegion.setBounds((0, max(x)))
        self._zoomRegion.setRegion((0, 100))
        self._setCoordinate(0, 0)

    def supply(self, analyse: datatypes.Analyse, dataframe: pd.DataFrame) -> None:
        if (
            self._analyse
            and self._analyse == analyse
            and self._df is not None
            and self._df.equals(dataframe)
        ):
            return
        self.blockSignals(True)
        self._analyse = analyse
        self._df = dataframe
        self._visible = [False for _ in range(len(self._df))]
        self._activeIntensities = self._analyse.calculateActiveIntensities(self._df)
        self._dataPackets = []
        for packetId, s in self._df.iterrows():
            plotData = PlotData.fromSeries(s)
            plotData.region.sigRegionChangeFinished.connect(
                partial(self._dataPacketChanged, packetId, "region")
            )
            plotData.peakLine.sigClicked.connect(
                partial(self._selectDataPacket, plotData)
            )
            plotData.spectrumLine.sigClicked.connect(
                partial(self._selectDataPacket, plotData)
            )
            dataPacket = DataPacket(
                packetId, plotData, self._createTableRow(packetId, s)
            )
            self._dataPackets.append(dataPacket)
        self._stack = deque()
        items = self._df["radiation_type"].unique().tolist()
        items.insert(0, "")
        self._searchComboBox.addItems(items)
        self._searchLineEdit.clear()
        self._fillTable()
        self.blockSignals(False)
