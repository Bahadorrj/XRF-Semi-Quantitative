from PyQt6 import QtWidgets

from src.utils import datatypes
from src.utils.datatypes import Calibration
from src.views.base.tablewidget import DataframeTableWidget


class CalibrationsTableWidget(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
    ) -> None:
        super().__init__(parent)
        self._method = None
        self._initializeUi()
        if method is not None:
            self._tableWidget.supply(
                self._method.calibrations.drop("calibration_id", axis=1)
            )

    def _initializeUi(self) -> None:
        self._tableWidget = DataframeTableWidget(self, autoFill=True)
        self._setUpView()

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.addWidget(self._tableWidget)
        self.setLayout(self.mainLayout)

    def supply(self, method: datatypes.Method) -> None:
        if method is None:
            return
        if self._method and self._method == method:
            return
        self.blockSignals(True)
        self._method = method
        df = method.calibrations.drop("calibration_id", axis=1)
        df["state"] = df["state"].apply(Calibration.convertStateToStatus)
        self._tableWidget.supply(df)
        self._tableWidget.clearSelection()
        self._tableWidget.selectRow(0)
        self.blockSignals(False)

    @property
    def method(self):
        return self._method
