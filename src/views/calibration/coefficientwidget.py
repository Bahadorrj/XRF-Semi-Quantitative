import numpy as np
import pyqtgraph as pg

from PyQt6 import QtWidgets
from src.utils import datatypes


class CoefficientWidget(QtWidgets.QWidget):
    """
    CoefficientWidget is a custom QWidget designed to display and manage calibration coefficients and their corresponding plots. It provides an interface for selecting active lines and visualizing their intensity data through a graphical plot.

    Args:
        parent (QWidget | None): Optional parent widget for the coefficient widget.
        calibration (Calibration | None): Optional calibration data to initialize the widget with.

    Methods:
        _initializeUi() -> None:
            Sets up the user interface components for the widget.

        _createLineSelectionLayout() -> None:
            Creates the layout for selecting active lines and displaying slope information.

        _createPlotWidget() -> None:
            Initializes the plot widget for visualizing intensity data.

        _setUpView() -> None:
            Configures the main layout of the widget, combining line selection and the plot.

        _drawCanvas() -> None:
            Clears the plot and draws the intensity line based on the selected radiation type.

        _initializeRadiations() -> None:
            Populates the combo box with available radiation types from the calibration data.

        supply(calibration: Calibration) -> None:
            Updates the widget with new calibration data and refreshes the available radiation types.
    """

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
        self._lineSelectLayout = QtWidgets.QHBoxLayout()
        self._lineSelectLayout.addWidget(QtWidgets.QLabel("Active Lines:"))
        self._searchComboBox = QtWidgets.QComboBox(self)
        self._searchComboBox.setObjectName("search-combo-box")
        self._searchComboBox.currentTextChanged.connect(self._drawCanvas)
        self._lineSelectLayout.addWidget(self._searchComboBox)
        self._lineSelectLayout.addStretch()
        self._slopeLabel = QtWidgets.QLabel("Slope:", self)
        self._lineSelectLayout.addWidget(self._slopeLabel)
        self._lineSelectLayout.addStretch()

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
        self._calibration.calculateCoefficients()
        if currentRadiationType := self._searchComboBox.currentText():
            conditionId = self._calibration.lines.query(
                f"symbol == '{self._calibration.element}' and radiation_type == '{currentRadiationType}'"
            )["condition_id"].values[0]
            if data := self._calibration.analyse.getDataByConditionId(conditionId):
                intensity = data.calculateIntensities(self._calibration.lines)[
                    self._calibration.element
                ][currentRadiationType]

                # Calculate the line points
                x = np.arange(0, intensity, 1)
                y = np.arange(0, 100, 100 / x.size)

                # Plot the line
                self._plotWidget.plot(x=x, y=y, pen=pg.mkPen(color="r", width=2))
                slope = self._calibration.coefficients[currentRadiationType]
                self._slopeLabel.setText(f"Slope: {slope:.5f}")

    def _initializeRadiations(self) -> None:
        self._searchComboBox.clear()
        if self._calibration.analyse.data:
            try:
                items = (
                    self._calibration.lines.query(
                        f"symbol == '{self._calibration.analyse.filename}' and active == 1"
                    )["radiation_type"]
                    .unique()
                    .tolist()
                )
                items = list(map(str, items))
            except IndexError:
                items = [""]
            self._searchComboBox.addItems(items)

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
        self._initializeRadiations()
        self._drawCanvas()
        self.blockSignals(False)
