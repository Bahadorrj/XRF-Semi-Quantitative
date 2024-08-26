import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets

from python.utils import datatypes


class CoefficientWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None, calibration: datatypes.Calibration | None = None):
        super(CoefficientWidget, self).__init__(parent)
        self._calibration = calibration
        self._initializeUi()
        if self._calibration is not None:
            self._connectSignalsAndSlots()
            self._initializeRadiations()

    def _initializeUi(self) -> None:
        self._createLineSelectionLayout()
        self._createPlotWidget()
        self._setUpView()

    def _connectSignalsAndSlots(self) -> None:
        self._searchComboBox.currentTextChanged.connect(self._drawCanvas)

    def _resetClassVariables(self, calibration: datatypes.Calibration) -> None:
        self._calibration = calibration

    def _createLineSelectionLayout(self) -> None:
        self._lineSelectLayout = QtWidgets.QHBoxLayout()
        self._lineSelectLayout.addWidget(QtWidgets.QLabel("Active Lines:"))
        self._searchComboBox = QtWidgets.QComboBox()
        self._searchComboBox.setObjectName("search-combo-box")
        self._lineSelectLayout.addWidget(self._searchComboBox)
        self._lineSelectLayout.addStretch()
        self._slopeLabel = QtWidgets.QLabel("Slope:")
        self._lineSelectLayout.addWidget(self._slopeLabel)
        self._lineSelectLayout.addStretch()

    def _createPlotWidget(self) -> None:
        self._plotWidget = pg.PlotWidget()
        self._plotWidget.setObjectName("plot-widget")
        self._plotWidget.setBackground("#FFFFFF")
        self._plotWidget.showGrid(x=True, y=True)
        self._plotWidget.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        plotItem = self._plotWidget.getPlotItem()
        plotItem.setContentsMargins(10, 10, 10, 10)

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addLayout(self._lineSelectLayout)
        self.mainLayout.addWidget(self._plotWidget)
        self.setLayout(self.mainLayout)

    def _drawCanvas(self) -> None:
        self._plotWidget.clear()
        currentRadiationType = self._searchComboBox.currentText()
        if currentRadiationType:
            conditionId = self._calibration.lines.query(
                f"symbol == '{self._calibration.element}' and radiation_type == '{currentRadiationType}'"
            )['condition_id'].values[0]
            data = self._calibration.analyse.getDataByConditionId(conditionId)
            intensity = data.calculateIntensities(
                self._calibration.lines
            )[self._calibration.element][currentRadiationType]

            # Calculate the line points
            x = np.arange(0, intensity, 1)
            y = np.arange(0, 100, 100 / x.size)

            # Plot the line
            self._plotWidget.plot(x=x, y=y, pen=pg.mkPen(color="r", width=2))
            slope = self._calibration.coefficients[currentRadiationType]
            self._slopeLabel.setText(f"Slope: {slope:.5f}")

    def _initializeRadiations(self) -> None:
        if self._calibration.analyse.data:
            try:
                items = self._calibration.lines.query(
                    f"symbol == '{self._calibration.analyse.filename}' and active == 1"
                )["radiation_type"].unique().tolist()
                items = list(map(str, items))
            except IndexError:
                items = [""]
            self._searchComboBox.addItems(items)

    def reinitializeRadiations(self) -> None:
        self._searchComboBox.clear()
        self._initializeRadiations()

    def reinitialize(self, calibration: datatypes.Calibration):
        self._resetClassVariables(calibration)
        self.reinitializeRadiations()
