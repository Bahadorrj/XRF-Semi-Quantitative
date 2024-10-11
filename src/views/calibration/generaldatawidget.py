import pyqtgraph as pg

from functools import partial
from PyQt6 import QtWidgets

from src.utils import datatypes, calculation
from src.utils.database import getDataframe

from src.views.base.generaldatawidget import GeneralDataWidget
from src.utils.paths import resourcePath
from src.views.calibration.elementsandconcentrationswidget import (
    ElementsAndConcentrationsWidget,
)

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


class CalibrationGeneralDataWidget(GeneralDataWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        calibration: datatypes.Calibration | None = None,
        editable: bool = False,
    ) -> None:
        super().__init__(parent, editable)
        self._createWidgets()
        self._calibration = None
        self._element = None
        self._plotDataItems = None
        if calibration is not None:
            self.supply(calibration)
        self.hide()

    def _initializeUi(self) -> None:
        self._createPlotWidget()
        self._createBackgroundRegion()
        self._createCoordinateLabel()
        self._createElementAndConcentrationGroupBox()
        self._createGeneralDataGroupBox()
        self._setUpView()

    def _createBackgroundRegion(self) -> None:
        self._backgroundRegion = pg.LinearRegionItem(
            pen=pg.mkPen(color="#330311", width=2),
            brush=pg.mkBrush(192, 192, 192, 100),
            hoverBrush=pg.mkBrush(169, 169, 169, 100),
            bounds=(0, 2048),
        )
        self._backgroundRegion.setZValue(10)
        self._backgroundRegion.sigRegionChanged.connect(self._backgroundRegionChanged)

    def _backgroundRegionChanged(self) -> None:
        self._calibration.analyse.backgroundRegion = self._backgroundRegion.getRegion()
        for i, plotDataItem in enumerate(self._plotDataItems):
            plotDataItem.setData(
                self._calibration.analyse.data[i].x,
                self._calibration.analyse.data[i].optimalY,
            )

    def _createElementAndConcentrationGroupBox(self) -> None:
        self._elementsAndConcentrationsWidget = ElementsAndConcentrationsWidget(
            self, editable=self._editable
        )
        self._elementsAndConcentrationsGroupBox = QtWidgets.QGroupBox("Concentrations")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._elementsAndConcentrationsWidget)
        self._elementsAndConcentrationsGroupBox.setLayout(layout)
        self._elementsAndConcentrationsWidget.concentrationAdded.connect(
            self._addInfiniteLine
        )
        self._elementsAndConcentrationsWidget.concentrationRemoved.connect(
            self._removeInfiniteLine
        )

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QGridLayout()
        self.mainLayout.setSpacing(10)
        self.mainLayout.addWidget(self._plotWidget, 0, 0)
        self.mainLayout.addWidget(self._coordinateLabel, 1, 0)
        vLayout = QtWidgets.QVBoxLayout()
        vLayout.setSpacing(10)
        vLayout.addWidget(self._elementsAndConcentrationsGroupBox)
        vLayout.addWidget(self._generalDataGroupBox)
        vLayout.setStretch(0, 0)
        vLayout.setStretch(1, 1)
        self.mainLayout.addLayout(vLayout, 0, 1, 1, 2)
        self.setLayout(self.mainLayout)

    def _createWidgets(self) -> None:
        editable = self._editable
        keys = [
            "Type",
            "Area",
            "Mass",
            "Rho",
            "Background Profile",
            "Rest",
            "Diluent",
        ]
        if editable:
            for key in keys:
                if key == "Background Profile":
                    widget = QtWidgets.QComboBox(self)
                    items = getDataframe("BackgroundProfiles")["filename"].to_list()
                    items.insert(0, "")
                    widget.addItems(items)
                    widget.currentTextChanged.connect(
                        partial(self._generalDataChanged, key, widget)
                    )
                else:
                    widget = QtWidgets.QLineEdit(self)
                    widget.textEdited.connect(
                        partial(self._generalDataChanged, key, widget)
                    )
                self._generalDataWidgetsMap[key] = widget
        else:
            self._generalDataWidgetsMap = {k: QtWidgets.QLabel(self) for k in keys}
        self._fillGeneralDataGroupBox()

    def _generalDataChanged(
        self, key: str, widget: QtWidgets.QLineEdit | QtWidgets.QComboBox
    ) -> None:
        if key == "Background Profile":
            if filename := widget.currentText():
                profile = datatypes.BackgroundProfile.fromATXBFile(
                    resourcePath(f"backgrounds/{filename}.atxb")
                )
                self._calibration.analyse.backgroundProfile = profile
                self._backgroundRegion.setRegion(
                    self._calibration.analyse.backgroundRegion
                )
                self._plotWidget.addItem(self._backgroundRegion)
            else:
                self._calibration.analyse.backgroundProfile = None
                self._plotWidget.removeItem(self._backgroundRegion)
        else:
            self._calibration.analyse.generalData[key] = (
                widget.text()
                if isinstance(widget, QtWidgets.QLineEdit)
                else widget.currentText()
            )

    def _fillWidgetsFromCalibration(self) -> None:
        for key, widget in self._generalDataWidgetsMap.items():
            value = self._calibration.analyse.generalData.get(key)
            if value is None and not self._editable:
                value = "None"
            if isinstance(widget, (QtWidgets.QLineEdit, QtWidgets.QLabel)):
                widget.setText(value)
            else:
                widget.setCurrentText(value)

    def _drawCanvas(self) -> None:
        self._plotWidget.clear()
        yMax = 0
        for plotDataItem in self._plotDataItems:
            self._plotWidget.addItem(plotDataItem)
            yMax = max(max(plotDataItem.getData()[1]), yMax)
        self._addInfiniteLines()
        self._plotWidget.setLimits(yMin=-0.1 * yMax, yMax=1.1 * yMax)

    def _addInfiniteLines(self):
        for element in self._calibration.concentrations:
            self._addInfiniteLine(element)

    def _addInfiniteLine(self, element: str) -> None:
        for row in self._calibration.lines.query(f"symbol == '{element}'").itertuples(
            index=False
        ):
            kev = row.kiloelectron_volt
            radiationType = row.radiation_type
            value = calculation.evToPx(kev)
            infiniteLine = pg.InfiniteLine(
                pos=value,
                angle=90,
                pen=pg.mkPen(color="#000800", width=1),
                movable=False,
                label=f"{element}-{radiationType}",
                labelOpts={"position": 0.98, "color": "#000800"},
            )
            self._plotWidget.addItem(infiniteLine)

    def _removeInfiniteLine(self, element: str) -> None:
        # Retrieve all items in the PlotWidget
        allItems = self._plotWidget.plotItem.items
        # Filter for InfiniteLine items
        infiniteLines = [item for item in allItems if isinstance(item, pg.InfiniteLine)]
        # Print the positions of the InfiniteLines
        for line in infiniteLines:
            if element in line.label.format:
                self._plotWidget.removeItem(line)

    def supply(self, calibration: datatypes.Calibration) -> None:
        if calibration is None:
            return
        if self._calibration and self._calibration == calibration:
            return
        self.blockSignals(True)
        self._calibration = calibration
        self._element = calibration.element
        self._plotDataItems = [
            pg.PlotDataItem(
                d.x,
                d.optimalY,
                pen=pg.mkPen(color=COLORS[i], width=2),
                name=f"Condition {d.conditionId}",
            )
            for i, d in enumerate(self._calibration.analyse.data)
        ]
        self._drawCanvas()
        self._elementsAndConcentrationsWidget.supply(self._calibration)
        self._fillWidgetsFromCalibration()
        self.blockSignals(False)
