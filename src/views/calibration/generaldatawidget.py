import pyqtgraph as pg

from functools import partial
from PyQt6 import QtWidgets

from src.utils import datatypes, calculation
from src.utils.database import getDataframe

from src.views.base.generaldatawidget import GeneralDataWidget
from src.utils.paths import resourcePath

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
        if calibration is not None:
            self.supply(calibration)
        self.hide()

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
        else:
            self._calibration.analyse.generalData[key] = (
                widget.text()
                if isinstance(widget, QtWidgets.QLineEdit)
                else widget.currentText()
            )
        self._drawCanvas()

    def _fillWidgetsFromCalibration(self) -> None:
        for key, widget in self._generalDataWidgetsMap.items():
            value = str(self._calibration.analyse.generalData.get(key, ""))
            if isinstance(widget, (QtWidgets.QLineEdit, QtWidgets.QLabel)):
                widget.setText(value)
            else:
                widget.setCurrentText(value)

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
        for row in self._calibration.lines.query(
            f"symbol == '{self._element}'"
        ).itertuples(index=False):
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

    def supply(self, calibration: datatypes.Calibration) -> None:
        if calibration is None:
            return
        if self._calibration and self._calibration == calibration:
            return
        self.blockSignals(True)
        self._calibration = calibration
        self._element = calibration.element
        self._drawCanvas()
        self._fillWidgetsFromCalibration()
        self.blockSignals(False)
