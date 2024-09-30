import numpy as np
import pyqtgraph as pg

from PyQt6 import QtWidgets, QtCore
from src.utils import datatypes


class CoefficientWidget(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        calibration: datatypes.Calibration | None = None,
    ):
        super().__init__(parent)
        self._calibration = None
        self._initializeUi()
        if calibration is not None:
            self.supply(calibration)
        self.hide()

    def _initializeUi(self) -> None:
        self._createLineSelectionLayout()
        self._createPlotWidget()
        self._setUpView()

    def _createLineSelectionLayout(self) -> None:
        # sourcery skip: extract-duplicate-method
        self._lineSelectLayout = QtWidgets.QHBoxLayout()
        self._lineSelectLayout.addWidget(QtWidgets.QLabel("Element:"))
        self._elementSearchComboBox = QtWidgets.QComboBox(self)
        self._elementSearchComboBox.setObjectName("search-combo-box")
        self._elementSearchComboBox.currentTextChanged.connect(self._elementChanged)
        self._lineSelectLayout.addWidget(self._elementSearchComboBox)
        self._lineSelectLayout.addWidget(QtWidgets.QLabel("Active Line:"))
        self._lineSearchComboBox = QtWidgets.QComboBox(self)
        self._lineSearchComboBox.setObjectName("search-combo-box")
        self._lineSearchComboBox.currentTextChanged.connect(self._drawCanvas)
        self._lineSelectLayout.addWidget(self._lineSearchComboBox)
        self._lineSelectLayout.addStretch()
        self._slopeLabel = QtWidgets.QLabel("Slope:", self)
        self._lineSelectLayout.addWidget(self._slopeLabel)
        self._lineSelectLayout.addStretch()

    @QtCore.pyqtSlot(str)
    def _elementChanged(self, text: str) -> None:
        self._lineSearchComboBox.clear()
        try:
            items = (
                self._calibration.lines.query(f"symbol == '{text}' and active == 1")[
                    "radiation_type"
                ]
                .unique()
                .tolist()
            )
        except IndexError:
            items = [""]
        self._lineSearchComboBox.addItems(items)

    def _createPlotWidget(self) -> None:
        self._plotWidget = pg.PlotWidget(self)
        self._plotWidget.setObjectName("plot-widget")
        self._plotWidget.setBackground("#FFFFFF")
        self._plotWidget.showGrid(x=True, y=True)
        self._plotWidget.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        plotItem = self._plotWidget.getPlotItem()
        plotItem.setContentsMargins(10, 10, 10, 10)

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(self._lineSelectLayout)
        self.mainLayout.addWidget(self._plotWidget)
        self.setLayout(self.mainLayout)

    def _drawCanvas(self) -> None:
        self._plotWidget.clear()
        currentElement = self._elementSearchComboBox.currentText()
        if currentElement == "":
            return
        currentRadiationType = self._lineSearchComboBox.currentText()
        if currentRadiationType == "":
            return
        conditionId = int(
            self._calibration.lines.query(
                f"symbol == '{currentElement}' and radiation_type == '{currentRadiationType}'"
            )["condition_id"].values[0]
        )

        if data := self._calibration.analyse.getDataByConditionId(conditionId):
            intensity = data.calculateIntensities(self._calibration.lines)[
                currentElement
            ][currentRadiationType]

            # Calculate the line points
            x = np.arange(0, intensity, 1)
            y = np.linspace(0, 100, x.size)

            # Plot the line
            self._plotWidget.plot(x=x, y=y, pen=pg.mkPen(color="r", width=2))
            slope = self._calibration.coefficients[currentElement][currentRadiationType]
            self._slopeLabel.setText(f"Slope: {slope:.5f}")

    def _initializeComboBoxes(self) -> None:
        self._elementSearchComboBox.clear()
        elements = list(self._calibration.concentrations.keys())
        self._elementSearchComboBox.addItems(elements)

    def supply(self, calibration: datatypes.Calibration):
        """Updates the widget with the provided calibration data.

        This method sets the calibration for the widget, initializes the radiation settings,
        and redraws the canvas to reflect the new calibration. It temporarily blocks signals
        to prevent unwanted events during the update process.

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
        self._initializeComboBoxes()
        self.blockSignals(False)
