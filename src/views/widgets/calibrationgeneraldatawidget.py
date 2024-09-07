from functools import partial

import pyqtgraph as pg
from PyQt6 import QtWidgets

from src.utils import datatypes, calculation
from src.utils.database import getDataframe
from src.views.base.generaldatawidget import GeneralDataWidget

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
        super(CalibrationGeneralDataWidget, self).__init__(parent, editable)
        self._generalDataWidgetsMap = (
            {
                "element": QtWidgets.QLineEdit(),
                "concentration": QtWidgets.QLineEdit(),
                "type": QtWidgets.QComboBox(),
                "area": QtWidgets.QLineEdit(),
                "mass": QtWidgets.QLineEdit(),
                "rho": QtWidgets.QLineEdit(),
                "background Model": QtWidgets.QComboBox(),
                "rest": QtWidgets.QComboBox(),
                "diluent": QtWidgets.QComboBox(),
            }
            if self._editable
            else {
                "element": QtWidgets.QLabel(),
                "concentration": QtWidgets.QLabel(),
                "type": QtWidgets.QLabel(),
                "area": QtWidgets.QLabel(),
                "mass": QtWidgets.QLabel(),
                "rho": QtWidgets.QLabel(),
                "background Model": QtWidgets.QLabel(),
                "rest": QtWidgets.QLabel(),
                "diluent": QtWidgets.QLabel(),
            }
        )
        self._fillGeneralDataGroupBox()
        for key, widget in self._generalDataWidgetsMap.items():
            if isinstance(widget, QtWidgets.QComboBox):
                widget.currentTextChanged.connect(partial(self._addToGeneralData, key, widget))
            elif isinstance(widget, QtWidgets.QLineEdit):
                widget.textEdited.connect(partial(self._addToGeneralData, key, widget))
        self._calibration = None
        self._element = None
        if calibration is not None:
            self.supply(calibration)

    def _fillWidgetsFromCalibration(self) -> None:
        for key, widget in self._generalDataWidgetsMap.items():
            value = str(self._calibration.analyse.generalData.get(key, ""))
            if isinstance(widget, (QtWidgets.QLineEdit, QtWidgets.QLabel)):
                widget.setText(value)
            else:
                widget.setCurrentText(value)
        self._generalDataWidgetsMap["element"].setText(self._element)
        self._generalDataWidgetsMap["concentration"].setText(
            f"{self._calibration.concentration:.1f}"
        )

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
            self._addInfiniteLines()

    def _addInfiniteLines(self):
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

    def _addToGeneralData(
        self, key: str, widget: QtWidgets.QLineEdit | QtWidgets.QComboBox
    ) -> None:
        if key == "element":
            self._calibration.element = widget.text()
            return
        if key == "concentration":
            self._calibration.concentration = float(widget.text())
            return
        self._calibration.analyse.generalData[key] = (
            widget.text()
            if isinstance(widget, QtWidgets.QLineEdit)
            else widget.currentText()
        )

    def supply(self, calibration: datatypes.Calibration) -> None:
        self.blockSignals(True)
        self._calibration = calibration
        self._element = calibration.element
        self._drawCanvas()
        self._fillWidgetsFromCalibration()
        self.blockSignals(False)
