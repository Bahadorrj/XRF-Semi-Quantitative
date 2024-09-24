import contextlib
import numpy as np
import pyqtgraph as pg

from collections import deque
from functools import partial
from PyQt6 import QtWidgets, QtCore, QtGui
from pandas import DataFrame

from src.utils import calculation, datatypes
from src.utils.database import getDataframe
from src.utils.paths import resourcePath

from src.views.base.tablewidget import DataframeTableWidget, TableItem


class StatusButton(QtWidgets.QPushButton):
    def __init__(self, text: str, parent: QtWidgets.QWidget | None):
        super().__init__(text, parent)
        self.currentText = self.text()
        self.previousText = self.currentText
        self.setObjectName("status-button")

    def setText(self, text: str | None) -> None:
        self.previousText = self.currentText
        self.currentText = text
        return super().setText(text)


class HideButton(QtWidgets.QPushButton):
    def __init__(
        self, parent: QtWidgets.QWidget | None = None, icon: QtGui.QIcon = None
    ):
        super().__init__(parent)
        super().setIcon(icon)
        self.currentIcon = icon
        self.previousIcon = self.currentIcon
        self.setObjectName("hide-button")

    def setIcon(self, icon):
        self.previousIcon = self.currentIcon
        self.currentIcon = icon
        return super().setIcon(icon)


class ConditionComboBox(QtWidgets.QComboBox):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        values = sorted(
            map(
                lambda i: "" if np.isnan(i) else f"Condition {int(i)}",
                getDataframe("Lines")["condition_id"].unique().tolist(),
            )
        )
        self.addItems(values)
        self.setCurrentIndex(0)
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


class TableItemWithMemory(TableItem):
    def __init__(self, text: str | None = None, editable: bool = False):
        super().__init__(text, editable)
        self.currentText = self.text()
        self.previousText = self.currentText

    def setText(self, text: str | None) -> None:
        self.previousText = self.currentText
        self.currentText = text
        return super().setText(text)


class PeakSearchTableWidget(DataframeTableWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        dataframe: DataFrame | None = None,
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

    def updateRow(self, rowId: int, values: list) -> None:
        if listObject := [
            key for key, value in self.rows.items() if value["rowId"] == rowId
        ]:
            rowIndex = listObject[0]
        else:
            return
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


class PeakSearchWidget(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        calibration: datatypes.Calibration | None = None,
    ):
        super().__init__(parent)
        self._calibration = None
        self._df = None
        self._activeIntensities = None
        self._kev = None
        self._plotDataList = None
        self._undoStack = None
        self._redoStack = None
        self._flag = None
        self._regionActive = None
        self._initializeUi()
        if calibration is not None:
            self.supply(calibration)
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

    @QtCore.pyqtSlot(str)
    def _actionTriggered(self, key: str) -> None:
        if key == "undo":
            self._undo()
        elif key == "region":
            self._toggleRegions()

    def _undo(self) -> None:
        if not self._undoStack:
            return
        temp = self._undoStack.pop()
        if not self._undoStack:
            self._actionsMap["undo"].setDisabled(True)
        items = temp if isinstance(temp, list) else [temp]
        for package in items:
            rowId, values, action = package
            self._tableWidget.updateRow(rowId, values)
            self._tableWidget.selectRowByID(rowId)
            if self._isPlotDataChanged(rowId, action):
                self._hoverOverPlotData(self._plotDataList[rowId])
            if action == "region":
                plotData = self._plotDataList[rowId]
                minX = calculation.evToPx(float(values[4]))
                maxX = calculation.evToPx(float(values[5]))
                plotData.region.blockSignals(True)
                plotData.region.setRegion((minX, maxX))
                plotData.region.blockSignals(True)

    # def _redo(self) -> None:
    #     if self._redoStack:
    #         rowId, values, action = self._redoStack.pop()
    #         self._addRowToUndoStack(rowId, action)
    #         self._tableWidget.updateRow(rowId, values)
    #         if not self._redoStack:
    #             self._redoAction.setDisabled(True)
    #         self._actionsMap["undo"].setDisabled(False)
    #         self._rowChanged(rowId, action)

    def _toggleRegions(self, checked: bool) -> None:
        self._regionActive = checked
        for data in self._plotDataList:
            if data.visible:
                if checked:
                    self._peakPlot.addItem(data.region)
                else:
                    self._peakPlot.removeItem(data.region)

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
        self._searchComboBox = QtWidgets.QComboBox(self)
        self._searchComboBox.setObjectName("search-combo-box")
        self._searchComboBox.setCurrentIndex(0)
        self._searchLineEdit.setDisabled(True)
        self._searchComboBox.setDisabled(True)
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
            self._fillTable()
            return
        if not df.empty:
            self._tableWidget.resetTable()
            for rowId in df.index:
                plotData = self._plotDataList[rowId]
                self._tableWidget.addRow(self._createTableRow(plotData))

    def _createTableWidget(self) -> None:
        self._tableWidget = PeakSearchTableWidget(self)
        self._tableWidget.setMaximumHeight(200)
        self._tableWidget.cellClicked.connect(self._cellClicked)

    @QtCore.pyqtSlot(int, int)
    def _cellClicked(self, row: int, column: int) -> None:
        tableRow = self._tableWidget.rows[row]
        plotData = self._plotDataList[tableRow.get("rowId")]
        self._hoverOverPlotData(plotData)

    def _fillTable(self) -> None:
        self._statusLabel.setText("Adding lines...")
        self._tableWidget.supply(self._calibration.lines)
        for plotData in self._plotDataList:
            self._tableWidget.addRow(self._createTableRow(plotData))
        self._statusLabel.setText(None)

    def _createTableRow(self, plotData: datatypes.PlotData) -> dict:
        row = self._df.iloc[plotData.rowId]
        try:
            intensity = self._activeIntensities[row["symbol"]][row["radiation_type"]]
        except KeyError:
            intensity = 0
        tableRow = {
            "rowId": plotData.rowId,
            "hide-button": self._createHideWidget(plotData),
            "symbol": TableItem(row["symbol"]),
            "radiation-type": TableItem(row["radiation_type"]),
            "kiloelectron-volt": TableItem(str(row["kiloelectron_volt"])),
            "low_kiloelectron_volt": TableItemWithMemory(
                str(row["low_kiloelectron_volt"])
            ),
            "high_kiloelectron_volt": TableItemWithMemory(
                str(row["high_kiloelectron_volt"])
            ),
            "intensity": TableItemWithMemory(str(intensity)),
            "condition-combo-box": self._createConditionComboBox(plotData),
            "status": (
                TableItem("Activated")
                if row["active"] == 1
                else TableItem("Deactivated")
            ),
            "status-button": self._createStatusButton(plotData),
        }
        if tableRow["status"].text() == "Activated":
            tableRow["status"].setForeground(QtCore.Qt.GlobalColor.darkGreen)
        else:
            tableRow["status"].setForeground(QtCore.Qt.GlobalColor.red)
        return tableRow

    def _createHideWidget(self, plotData: datatypes.PlotData) -> HideButton:
        if plotData.visible:
            widget = HideButton(
                parent=self, icon=QtGui.QIcon(resourcePath("resources/icons/show.png"))
            )
        else:
            widget = HideButton(
                parent=self, icon=QtGui.QIcon(resourcePath("resources/icons/hide.png"))
            )
        widget.clicked.connect(partial(self._plotDataChanged, plotData.rowId, "hide"))
        return widget

    def _createConditionComboBox(
        self, plotData: datatypes.PlotData
    ) -> ConditionComboBox:
        widget = ConditionComboBox(self)
        if plotData.active:
            widget.setDisabled(True)
        if plotData.conditionId is not None:
            widget.setCurrentText(f"Condition {plotData.conditionId}")
        widget.currentTextChanged.connect(
            partial(self._plotDataChanged, plotData.rowId, "condition")
        )
        return widget

    def _createStatusButton(self, plotData: datatypes.PlotData) -> StatusButton:
        if not plotData.active:
            widget = StatusButton("Activate", self)
        else:
            widget = StatusButton("Deactivate", self)
        widget.clicked.connect(partial(self._plotDataChanged, plotData.rowId, "status"))
        return widget

    @QtCore.pyqtSlot(int, str)
    def _plotDataChanged(self, rowId: int, action: str) -> None:
        self._tableWidget.selectRowByID(rowId)
        if self._isPlotDataChanged(rowId, action):
            self._hoverOverPlotData(self._plotDataList[rowId])
            self._addPlotDataToUndoStack(rowId, action)

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

    def _createSpectrumPlot(self) -> None:
        self._spectrumPlot = self._graphicsLayoutWidget.addPlot(row=1, col=0)
        self._spectrumPlot.setMouseEnabled(x=False, y=False)
        self._spectrumPlot.showGrid(x=True, y=True)
        self._spectrumPlot.showGrid(x=True, y=True)
        self._zoomRegion = pg.LinearRegionItem(clipItem=self._spectrumPlot)

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(self._toolBar)
        self.mainLayout.addLayout(self._searchLayout)
        self.mainLayout.addWidget(self._tableWidget)
        self.mainLayout.addLayout(self._statusLayout)
        self.mainLayout.addWidget(self._graphicsLayoutWidget)
        self.setLayout(self.mainLayout)

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

    def _isPlotDataChanged(self, rowId: int, action: str) -> bool:
        plotData = self._plotDataList[rowId]
        if action == "hide":
            return self._plotDataVisibilityChanged(plotData)
        elif action == "condition":
            return self._plotDataConditionChanged(plotData)
        elif action == "status":
            return self._plotDataStatusChanged(plotData)
        elif action == "region":
            return self._plotDataRegionChanged(plotData)
        return False

    def _plotDataVisibilityChanged(self, plotData: datatypes.PlotData) -> bool:
        if tableRow := self._tableWidget.getRowById(plotData.rowId):
            hideButton = tableRow.get("hide-button")
            if plotData.visible:
                hideButton.setIcon(
                    QtGui.QIcon(resourcePath("resources/icons/hide.png"))
                )
            else:
                hideButton.setIcon(
                    QtGui.QIcon(resourcePath("resources/icons/show.png"))
                )
        if plotData.visible:
            self._erasePlotData(plotData)
        else:
            self._selectPlotData(plotData)
            self._drawPlotData(plotData)
        plotData.visible = not plotData.visible
        return True

    def _plotDataConditionChanged(self, plotData: datatypes.PlotData) -> bool:
        tableRow = self._tableWidget.getRowById(plotData.rowId)
        minX, maxX = plotData.region.getRegion()
        if (conditionId := tableRow.get("condition-combo-box").currentText()) != "":
            conditionId = int(conditionId.split(" ")[-1])
            plotData.conditionId = conditionId
            self._df.at[plotData.rowId, "condition_id"] = conditionId
            if plotData.conditionId and plotData.conditionId in [
                d.conditionId for d in self._analyse.data
            ]:
                analyseData = next(
                    filter(
                        lambda d: d.conditionId == plotData.conditionId,
                        self._analyse.data,
                    )
                )
                y = analyseData.y
                intensity = y[round(minX) : round(maxX)].sum()
            else:
                intensity = 0
        else:
            intensity = 0
        tableRow.get("intensity").setText(str(intensity))
        # self._activeIntensities[self._df.at[plotData.rowId, "symbol"]][
        #     self._df.at[plotData.rowId, "radiation_type"]
        # ] = intensity
        return True

    def _plotDataStatusChanged(self, plotData: datatypes.PlotData) -> bool:
        changed = False
        tableRow = self._tableWidget.getRowById(plotData.rowId)
        conditionComboBox = tableRow.get("condition-combo-box")
        statusItem = tableRow.get("status")
        statusButton = tableRow.get("status-button")
        if plotData.active:
            changed = True
            plotData.deactivate()
            self._df.at[plotData.rowId, "active"] = 0
            statusItem.setText("Deactivated")
            statusItem.setForeground(QtCore.Qt.GlobalColor.red)
            statusButton.setText("Activate")
            conditionComboBox.setDisabled(False)
        elif conditionComboBox.currentText():
            changed = True
            plotData.activate()
            self._df.at[plotData.rowId, "active"] = 1
            statusItem.setText("Activated")
            statusItem.setForeground(QtCore.Qt.GlobalColor.darkGreen)
            statusButton.setText("Deactivate")
            conditionComboBox.setDisabled(True)
        else:
            messageBox = QtWidgets.QMessageBox(self)
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            messageBox.setText(
                "No condition is selected. Please select one before activating again."
            )
            messageBox.setWindowTitle("Activation failed")
            messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            messageBox.exec()
        if plotData.visible:
            self._erasePlotData(plotData)
            self._selectPlotData(plotData)
            self._drawPlotData(plotData)
        return changed

    def _plotDataRegionChanged(self, plotData: datatypes.PlotData) -> bool:
        def getKev(index, default):
            try:
                return self._kev[int(index)]
            except IndexError:
                return default

        minX, maxX = plotData.region.getRegion()
        minKev = getKev(minX, 0)
        maxKev = getKev(maxX, self._kev[-1])

        intensity = 0
        if plotData.conditionId:
            analyseData = next(
                (
                    d
                    for d in self._analyse.data
                    if d.conditionId == plotData.conditionId
                ),
                None,
            )
            if analyseData:
                y = analyseData.y
                intensity = y[round(minX) : round(maxX)].sum()

        self._df.at[plotData.rowId, "low_kiloelectron_volt"] = minKev
        self._df.at[plotData.rowId, "high_kiloelectron_volt"] = maxKev
        if tableRow := self._tableWidget.getRowById(plotData.rowId):
            tableRow.get("low_kiloelectron_volt").setText(str(minKev))
            tableRow.get("high_kiloelectron_volt").setText(str(maxKev))
            tableRow.get("intensity").setText(str(intensity))
        # self._activeIntensities[self._df.at[plotData.rowId, "symbol"]][
        #     self._df.at[plotData.rowId, "radiation_type"]
        # ] = intensity
        return True

    @QtCore.pyqtSlot()
    def _selectPlotData(self, plotData: datatypes.PlotData) -> None:
        if plotData.rowId in self._tableWidget.rows:
            self._tableWidget.selectRowByID(plotData.rowId)
            self._hoverOverPlotData(plotData)

    def _hoverOverPlotData(self, plotData: datatypes.PlotData):
        if plotData.visible is False:
            return
        minX, maxX = plotData.region.getRegion()
        viewMinX, viewMaxX = self._peakPlot.viewRange()[0]
        if viewMinX > minX or viewMaxX < maxX:
            zoomedArea = (minX - 50, maxX + 50)
            self._zoomRegion.setRegion(zoomedArea)

    def _addPlotDataToUndoStack(self, rowId: int, action: str) -> None:
        if not self._undoStack:
            self._actionsMap["undo"].setDisabled(False)
        # if len(self._undoStack) > 30:
        #     self._undoStack.popleft()
        # if self._flag:
        #     self._redoStack.clear()
        #     self._redoAction.setDisabled(True)
        tableRow = self._tableWidget.getRowById(rowId)
        values = []
        for index, component in enumerate(tableRow.values()):
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
            elif isinstance(component, TableItemWithMemory):
                if action == "region":
                    values.insert(index, component.previousText)
                else:
                    values.insert(index, component.currentText)
            elif isinstance(component, TableItem):
                values.insert(index, component.text())
        self._undoStack.append((rowId, values, action))
        # print(f"added to undo stack : {values}-{action}")

    def _drawPlotData(self, plotData: datatypes.PlotData) -> None:
        if plotData.peakLine not in self._peakPlot.items:
            self._peakPlot.addItem(plotData.peakLine)
        if plotData.spectrumLine not in self._spectrumPlot.items:
            self._spectrumPlot.addItem(plotData.spectrumLine)
        if self._regionActive and plotData.region not in self._peakPlot.items:
            self._peakPlot.addItem(plotData.region)

    def _erasePlotData(self, plotData: datatypes.PlotData) -> None:
        if plotData.peakLine in self._peakPlot.items:
            self._peakPlot.removeItem(plotData.peakLine)
        if plotData.spectrumLine in self._spectrumPlot.items:
            self._spectrumPlot.removeItem(plotData.spectrumLine)
        if self._regionActive and plotData.region in self._peakPlot.items:
            self._peakPlot.removeItem(plotData.region)

    def _setCoordinate(self, x: float, y: float) -> None:
        with contextlib.suppress(IndexError):
            kev = self._kev[int(x)]
            self._coordinateLabel.setText(f"x= {x} y= {y} KeV= {kev}")

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
        if event.button() != QtCore.Qt.MouseButton.RightButton:
            return
        minX, maxX = self._zoomRegion.getRegion()
        minKev = calculation.pxToEv(minX)
        maxKev = calculation.pxToEv(maxX)
        self._peakPlot.vb.menu.clear()
        self._elementsInRange = self._df.query(
            f"kiloelectron_volt <= {maxKev} and high_kiloelectron_volt >= {minKev}"
        )
        if not self._elementsInRange.empty:
            grouped = self._elementsInRange.groupby("radiation_type")
            for radiationType, group in grouped:
                menu = self._peakPlot.vb.menu.addMenu(radiationType)
                menu.triggered.connect(self._actionClicked)
                for symbol in group["symbol"]:
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
        self._plotDataChanged(rowId, "hide")

    def _showAll(self) -> None:
        temp = self._undoStack.copy()
        for rowId in self._elementsInRange.index:
            if self._plotDataList[rowId].visible is False:
                self._plotDataChanged(rowId, "hide")
        stack = [self._undoStack[i] for i in range(len(temp), len(self._undoStack))]
        temp.append(stack)
        self._undoStack = temp.copy()

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
        for plotData in self._plotDataList:
            if plotData.visible:
                self._drawPlotData(plotData)
        self._zoomRegion.setBounds((0, max(x)))
        self._zoomRegion.setRegion((0, 100))
        self._setCoordinate(0, 0)
        self._searchLineEdit.setDisabled(False)
        self._searchComboBox.setDisabled(False)
        self._searchLineEdit.editingFinished.connect(self._search)
        self._searchComboBox.currentTextChanged.connect(self._search)
        self._peakPlot.sigRangeChanged.connect(self._adjustZoom)
        self._peakPlot.scene().sigMouseMoved.connect(self._mouseMoved)
        self._peakPlot.scene().sigMouseClicked.connect(self._openPopUp)
        self._zoomRegion.sigRegionChanged.connect(self._showZoomedRegion)

    def mousePressEvent(self, a0):
        if (
            not self._searchLineEdit.geometry().contains(a0.pos())
            and self._searchLineEdit.hasFocus()
        ):
            self._searchLineEdit.clearFocus()
        return super().mousePressEvent(a0)

    def supply(self, calibration: datatypes.Calibration) -> None:
        """Updates the widget with the specified calibration data.

        This method assigns the calibration to the widget, processes the associated data,
        and prepares the necessary elements for plotting and interaction. It also populates
        the search combo box with available radiation types and resets the table display.

        Args:
            calibration (datatypes.Calibration): The calibration data to be supplied to the widget.

        Returns:
            None
        """
        if calibration is None:
            return
        if self._calibration and self._calibration == calibration:
            return
        self.blockSignals(True)
        self._calibration = calibration
        self._analyse = self._calibration.analyse
        self._df = self._calibration.lines
        self._activeIntensities = self._calibration.activeIntensities
        self._kev = [calculation.pxToEv(i) for i in self._analyse.data[0].x]
        self._plotDataList = [
            datatypes.PlotData.fromSeries(rowId, s) for rowId, s in self._df.iterrows()
        ]
        for plotData in self._plotDataList:
            plotData.region.sigRegionChangeFinished.connect(
                partial(self._plotDataChanged, plotData.rowId, "region")
            )
            plotData.peakLine.sigClicked.connect(
                partial(self._selectPlotData, plotData)
            )
            plotData.spectrumLine.sigClicked.connect(
                partial(self._selectPlotData, plotData)
            )
        self._undoStack = deque()
        self._redoStack = deque()
        self._flag = False
        self._regionActive = False
        items = self._df["radiation_type"].unique().tolist()
        items.insert(0, "")
        self._searchComboBox.addItems(items)
        self._searchLineEdit.clear()
        self._fillTable()
        self.blockSignals(False)
