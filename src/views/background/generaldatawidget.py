import re
import numpy as np
import pyqtgraph as pg

from functools import partial
from PyQt6 import QtWidgets
from scipy.interpolate import CubicSpline
from scipy.signal import find_peaks

from src.utils import datatypes
from src.views.base.generaldatawidget import GeneralDataWidget


class BackgroundGeneralDataWidget(GeneralDataWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        profile: datatypes.BackgroundProfile | None = None,
        editable: bool = False,
    ) -> None:
        super().__init__(parent, editable)
        self._createWidgets()
        self._profile = None
        self._data = None
        if profile is not None:
            self.supply(profile)
        self.hide()

    def _createWidgets(self) -> None:
        editable = self._editable
        widget_class = QtWidgets.QLineEdit if editable else QtWidgets.QLabel
        keys = [
            "smoothness",
            "height",
            "threshold",
            "distance",
            "prominence",
            "width",
            "wlen",
            "rel_height",
            "plateau_size",
        ]
        self._generalDataWidgetsMap = {key: widget_class(self) for key in keys}
        self._fillGeneralDataGroupBox()
        if editable:
            for key, widget in self._generalDataWidgetsMap.items():
                widget.editingFinished.connect(
                    partial(self._generalDataChanged, key, widget)
                )

    def _generalDataChanged(self, key: str, lineEdit: QtWidgets.QLineEdit) -> None:
        if lineEdit.text() == "":
            setattr(self._profile, key, None)
            self._drawCanvas()
            return
        if key in {"smoothness", "rel_height", "distance"}:
            pattern = re.compile(r"^\d+(\.\d+)?$|^$")
        elif key == "wlen":
            pattern = re.compile(r"^\d+$|^$")
        else:
            pattern = re.compile(
                r"^-?\d+(\.\d+)?$|^\(-?\d+(\.\d+)?, *-?\d+(\.\d+)?\)$|^$"
            )
        if not re.match(pattern, lineEdit.text()):
            value = getattr(self._profile, key)
            lineEdit.setText(str(value)) if value else lineEdit.setText(None)
        elif key == "smoothness" and not 1 <= float(lineEdit.text()) <= 25:
            lineEdit.setText(str(getattr(self._profile), key))
        elif key == "rel_height" and not 0 <= float(lineEdit.text()) <= 1:
            lineEdit.setText(str(getattr(self._profile), key))
        self._addToProfile(key, lineEdit)
        self._drawCanvas()

    def _addToProfile(self, key: str, lineEdit: QtWidgets.QLineEdit) -> None:
        (
            setattr(self._profile, key, lineEdit.text())
            if key != "smoothness"
            else setattr(self._profile, key, float(lineEdit.text()))
        )

    def _fillWidgetsFromProfile(self) -> None:
        for key, widget in self._generalDataWidgetsMap.items():
            value = getattr(self._profile, key)
            widget.setText(str(value)) if value else widget.setText(None)

    def _drawCanvas(self) -> None:
        self._plotWidget.clear()
        x = self._data.x
        y = self._data.y
        self._optimalY = self._calculateOptimalY()
        self._plotWidget.plot(
            x, y, name="Original", pen=pg.mkPen(color="#FF7F0EFF", width=2)
        )
        self._plotWidget.plot(
            x, self._optimalY, name="Optimal", pen=pg.mkPen(color="#1F77B4FF", width=2)
        )
        self._setPlotLimits(self._optimalY.max())

    def _calculateOptimalY(self) -> np.ndarray:
        optimalY = self._data.y.copy()
        xSmooth, ySmooth = self.smooth(self._data.x, optimalY, self._profile.smoothness)
        if kwargs := self._profile.peakKwargs():
            peaks, _ = find_peaks(-ySmooth, **kwargs)
        else:
            peaks, _ = find_peaks(-ySmooth)
        if peaks.size != 0:
            regressionCurve = np.interp(self._data.x, xSmooth[peaks], ySmooth[peaks])
            optimalY = (optimalY - regressionCurve).clip(0)
        return optimalY

    @staticmethod
    def smooth(
        x: np.ndarray, y: np.ndarray, level: float
    ) -> tuple[np.ndarray, np.ndarray]:
        cs = CubicSpline(x, y)
        # Generate finer x values for smoother plot
        X = np.linspace(0, x.size, int(x.size / level))
        # Interpolate y values for the smoother plot
        Y = cs(X)
        return X, Y

    def supply(self, profile: datatypes.BackgroundProfile) -> None:
        if profile is None:
            return
        if self._profile and self._profile == profile:
            return
        self.blockSignals(True)
        self._profile = profile
        self._data = datatypes.Analyse.fromTXTFile(
            r"F:\CSAN\Additional\Additional\Pure samples\8 Mehr\Au.txt"
        ).data[7]
        self._fillWidgetsFromProfile()
        self._drawCanvas()
        self.blockSignals(False)
