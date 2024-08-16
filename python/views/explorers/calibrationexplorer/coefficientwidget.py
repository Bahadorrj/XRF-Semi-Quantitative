import pyqtgraph as pg
import numpy as np

from PyQt6 import QtWidgets, QtCore, QtGui

from python.utils.calculation import evToPx


class CoefficientWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None, calibration: dict | None = None):
        assert calibration is not None, "Calibration must be provided"
        super(CoefficientWidget, self).__init__(parent)
        self._calibration = calibration
        
        self._createLineSelectLayout()
        self._createPlotWidget()
        self._setUpView()
        self._drawCanvas()
    
    def _createLineSelectLayout(self) -> None:
        self._lineSelectLayout = QtWidgets.QHBoxLayout()
        self._lineSelectLayout.addWidget(QtWidgets.QLabel("Active Lines:"))
        self._searchComboBox = QtWidgets.QComboBox()
        self._searchComboBox.setObjectName("search-combo-box")
        try:
            items = self._calibration["lines"].query(
                f"symbol == '{self._calibration['analyse'].name}' and active == 1"
            )["radiation_type"].unique().tolist()
            items = list(map(str, items))
        except IndexError:
            items = [""]
        self._searchComboBox.addItems(items)
        self._lineSelectLayout.addWidget(self._searchComboBox)
        self._lineSelectLayout.addStretch()
        self._searchComboBox.currentTextChanged.connect(self._drawCanvas)
        
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
        plotItem = self._plotWidget.getPlotItem()
        plotItem.setContentsMargins(10, 10, 10, 10)
        
    def _setUpView(self) -> None:
        self._mainLayout = QtWidgets.QVBoxLayout()
        self._mainLayout.addLayout(self._lineSelectLayout)
        self._mainLayout.addWidget(self._plotWidget)
        self.setLayout(self._mainLayout)
    
    def _drawCanvas(self) -> None:
        self._plotWidget.clear()
        currentLine = self._searchComboBox.currentText()
        if currentLine:
            row = self._calibration["lines"].query(
                f"symbol == '{self._calibration['analyse'].name}' and radiation_type == '{currentLine}'"
            )
            conditionId = int(row['condition_id'].values[0])
            data = list(filter(lambda d: d.condition == conditionId, self._calibration["analyse"].data))[0]
            minX, maxX = evToPx(row['low_kiloelectron_volt'].values[0]), evToPx(row['high_kiloelectron_volt'].values[0])
            intensity = data.y[round(minX) : round(maxX)].sum()
            y = np.arange(0, intensity, 1)
            x = np.arange(0, 100, 100/y.size)
            self._plotWidget.plot(x=x, y=y, pen=pg.mkPen(color="r", width=2))
            