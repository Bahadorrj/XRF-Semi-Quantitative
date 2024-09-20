from PyQt6 import QtWidgets

from src.utils import datatypes
from src.views.base.tablewidget import DataframeTableWidget


class InterferencesTableWidget(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
    ):
        super().__init__(parent)
        self._method = None
        self._initializeUi()
        if method is not None:
            self.supply(method)
        self.hide()

    def _initializeUi(self) -> None:
        self._tableWidget = DataframeTableWidget(self, autoFill=True)
        self._setUpView()

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.addWidget(self._tableWidget)
        self.setLayout(self.mainLayout)

    def supply(self, method: datatypes.Method):
        if method is None:
            return
        self.blockSignals(True)
        self._method = method
        self._tableWidget.supply(method.interferences)
        self._tableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self._tableWidget.setVerticalHeaderLabels(self._method.interferences.index)
        self.blockSignals(False)
