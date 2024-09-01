from functools import partial

import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore

from src.utils import datatypes, calculation
from src.utils.database import getDataframe

pg.setConfigOptions(antialias=True)

COLORS = [
    "#FF0000",
    "#FFD700",
    "#00FF7F",
    "#00FFFF",
    "#000080",
    "#0000FF",
    "#8B00FF",
    "#FF1493",
    "#FF7F00",
    "#FF4500",
    "#FFC0CB",
    "#00FF00",
    "#FFFF00",
    "#FF00FF",
]


class GeneralDataWidget(QtWidgets.QWidget):
    """
    GeneralDataWidget is a custom QWidget that displays general data and visualizations related to calibration analysis. It provides an interactive interface for viewing and editing calibration data, along with a plot for graphical representation.

    Args:
        parent (QWidget | None): Optional parent widget for the general data widget.
        calibration (Calibration | None): Optional calibration data to initialize the widget with.
        editable (bool): If True, allows editing of the displayed general data.

    Methods:
        _initializeUi() -> None:
            Sets up the user interface components for the widget.

        _createPlotWidget() -> None:
            Initializes the plot widget for visualizing calibration data.

        _mouseMoved(pos: QPointF) -> None:
            Updates the coordinate label based on the mouse position within the plot.

        _setCoordinate(x: float, y: float) -> None:
            Sets the coordinate label to display the current x and y values.

        _createCoordinateLabel() -> None:
            Creates a label to display the coordinates of the mouse pointer.

        _createGeneralDataGroupBox() -> None:
            Constructs a group box containing labels and editable fields for general data.

        _fillGeneralData() -> None:
            Populates the general data fields with values from the calibration data.

        _setUpView() -> None:
            Configures the main layout of the widget, combining the plot and general data display.

        _drawCanvas() -> None:
            Clears the plot and draws the calibration data based on the current settings.

        _setPlotLimits(maxIntensity: int) -> None:
            Sets the limits for the plot axes based on the maximum intensity value.

        _addToGeneralData(key: str, widget: QLineEdit) -> None:
            Updates the calibration's general data with the value from the specified widget.

        supply(calibration: Calibration) -> None:
            Updates the widget with new calibration data and refreshes the display.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        calibration: datatypes.Calibration | None = None,
        editable: bool = False,
    ) -> None:
        super().__init__(parent)
        self._calibration = None
        self._editable = editable
        self._element = None
        self._initializeUi()
        if calibration is not None:
            self.supply(calibration)

    def _initializeUi(self) -> None:
        self._createPlotWidget()
        self._createCoordinateLabel()
        self._createGeneralDataGroupBox()
        self._setUpView()

    def _createPlotWidget(self) -> None:
        self._plotWidget = pg.PlotWidget()
        self._plotWidget.setObjectName("plot-widget")
        self._plotWidget.setBackground("#FFFFFF")
        # self._plotWidget.showGrid(x=True, y=True)
        self._plotWidget.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        plotItem = self._plotWidget.getPlotItem()
        plotItem.setContentsMargins(10, 10, 10, 10)
        self._legend = plotItem.addLegend(
            offset=(-25, 25),
            pen=pg.mkPen(color="#E0E0E0", width=1),
            brush=pg.mkBrush(color="#F2F2F2"),
            labelTextColor="#000000",
        )
        self._plotWidget.scene().sigMouseMoved.connect(self._mouseMoved)

    def _mouseMoved(self, pos: QtCore.QPointF) -> None:
        if self._plotWidget.sceneBoundingRect().contains(pos):
            mousePoint = self._plotWidget.getPlotItem().vb.mapSceneToView(pos)
            self._setCoordinate(mousePoint.x(), mousePoint.y())

    def _setCoordinate(self, x: float, y: float) -> None:
        self._coordinateLabel.setText(f"x= {round(x, 2)} y= {round(y, 2)}")

    def _createCoordinateLabel(self) -> None:
        self._coordinateLabel = QtWidgets.QLabel(self)
        self._coordinateLabel.setObjectName("coordinate-label")
        self._coordinateLabel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._setCoordinate(0, 0)

    def _createGeneralDataGroupBox(self) -> None:
        self._generalDataGroupBox = QtWidgets.QGroupBox()
        self._generalDataGroupBox.setTitle("General Data")
        self._widgetsMap = {}
        labels = [
            QtWidgets.QLabel(text)
            for text in (
                "Element:",
                "Concentration:",
                "Chemistry:",
                "Kappa List:",
                "Area:",
                "Diameter:",
                "Height:",
                "Mass:",
                "Rho:",
            )
        ]
        if self._editable:
            widgets = [QtWidgets.QLineEdit() for _ in labels]
        else:
            widgets = [QtWidgets.QLabel() for _ in labels]
        self._generalDataLayout = QtWidgets.QVBoxLayout()
        self._generalDataLayout.setSpacing(25)
        for label, widget in zip(labels, widgets):
            widget.setFixedSize(100, 25)
            widget.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )
            hLayout = QtWidgets.QHBoxLayout()
            hLayout.addWidget(label)
            hLayout.addWidget(widget)
            self._generalDataLayout.addLayout(hLayout)
            key = "-".join(label.text()[:-1].lower().split(" "))
            self._widgetsMap[key] = widget
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.editingFinished.connect(
                    partial(self._addToGeneralData, key, widget)
                )
        self._generalDataGroupBox.setLayout(self._generalDataLayout)

    def _fillGeneralData(self) -> None:
        for key, widget in self._widgetsMap.items():
            widget.setText(str(self._calibration.analyse.generalData.get(key, "")))
        self._widgetsMap["element"].setText(self._element)
        self._widgetsMap["concentration"].setText(
            f"{self._calibration.concentration:.1f}"
        )

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QGridLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(10)
        self.mainLayout.addWidget(self._plotWidget, 0, 0)
        self.mainLayout.addWidget(self._generalDataGroupBox, 0, 1, 1, 2)
        self.mainLayout.addWidget(self._coordinateLabel, 1, 0)
        self.setLayout(self.mainLayout)

    def _drawCanvas(self) -> None:
        self._plotWidget.clear()
        maxIntensity = 0
        for index, data in enumerate(self._calibration.analyse.data):
            x, y = data.x, data.y
            maxIntensity = max(maxIntensity, max(y))
            color = COLORS[index]
            self._plotWidget.plot(
                x,
                y,
                name=f"Condition {data.conditionId}",
                pen=pg.mkPen(color=color, width=2),
            )
        self._setPlotLimits(maxIntensity)
        if self._element is not None:
            for row in (
                getDataframe("Lines")
                .query(f"symbol == '{self._element}'")
                .itertuples(index=False)
            ):
                kev = row.kiloelectron_volt
                radiationType = row.radiation_type
                value = calculation.evToPx(kev)
                infiniteLine = pg.InfiniteLine(
                    pos=value,
                    angle=90,
                    pen=pg.mkPen(color="#000800", width=1),
                    movable=False,
                    label=radiationType,
                    labelOpts={"position": 0.98, "color": "#000800"},
                )
                self._plotWidget.addItem(infiniteLine)

    def _setPlotLimits(self, maxIntensity: int) -> None:
        xMin = -100
        xMax = 2048 + 100
        yMin = -maxIntensity * 0.1
        yMax = maxIntensity * 1.1
        self._plotWidget.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

    def _addToGeneralData(self, key: str, widget: QtWidgets.QLineEdit) -> None:
        self._calibration.generalData[key] = widget.text()

    def supply(self, calibration: datatypes.Calibration) -> None:
        """Updates the widget with the specified calibration data.

        This method assigns the provided calibration to the widget, updates the element
        associated with the calibration, and refreshes the canvas and general data display.
        It temporarily blocks signals to prevent any unwanted events during the update process.

        Args:
            calibration (datatypes.Calibration): The calibration data to be supplied to the widget.

        Returns:
            None
        """
        self.blockSignals(True)
        self._calibration = calibration
        self._element = calibration.element
        self._drawCanvas()
        self._fillGeneralData()
        self.blockSignals(False)
