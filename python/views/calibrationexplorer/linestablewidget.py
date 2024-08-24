from PyQt6 import QtCore, QtWidgets

from python.utils import datatypes
from python.views.base.tablewidgets import DataframeTableWidget


class LinesTableWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None, calibration: datatypes.Calibration | None = None):
        super().__init__(parent)
        self._calibration = calibration
        self._initializeUi()
        if self._calibration is not None:
            self._linesDf = self._calibration.lines.drop(
                ["line_id", "element_id"], axis=1
            )
            self._activeDf = (
                self._linesDf.query("active == 1")
            )
            self._linesTableWidget.reinitialize(self._linesDf)
            self._activeTableWidget.reinitialize(self._activeDf)
            self._connectSignalsAndSlots()

    def _initializeUi(self) -> None:
        self._createFilterLayout()
        self._createTableWidgets()
        self._setUpView()

    def _connectSignalsAndSlots(self) -> None:
        self._searchComboBox.currentTextChanged.connect(self.setFilter)

    def _resetClassVariables(self, calibration: datatypes.Calibration) -> None:
        self._calibration = calibration
        self._linesDf = self._calibration.lines.drop(
            ["line_id", "element_id"], axis=1
        )
        self._activeDf = (
            self._linesDf.query("active == 1")
        )

    def _createFilterLayout(self) -> None:
        self._searchComboBox = QtWidgets.QComboBox()
        self._searchComboBox.setObjectName("search-combo-box")
        self._searchComboBox.addItems(
            ["All Lines", "Active Lines"]
        )
        self._searchLayout = QtWidgets.QHBoxLayout()
        self._searchLayout.addWidget(QtWidgets.QLabel("Filter by: "))
        self._searchLayout.addWidget(self._searchComboBox)
        self._searchLayout.addStretch()

    def _setUpView(self) -> None:
        self._mainLayout = QtWidgets.QVBoxLayout(self)
        # self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.addLayout(self._searchLayout)
        self._mainLayout.addWidget(self._linesTableWidget)

    @QtCore.pyqtSlot(str)
    def setFilter(self, filterName: str) -> None:
        oldWidget = self._mainLayout.itemAt(1).widget()
        oldWidget.hide()
        if filterName == "All Lines":
            self._mainLayout.replaceWidget(oldWidget, self._linesTableWidget)
            self._linesTableWidget.show()
        else:
            self._mainLayout.replaceWidget(oldWidget, self._activeTableWidget)
            self._activeTableWidget.show()

    def _createTableWidgets(self) -> None:
        self._linesTableWidget = DataframeTableWidget(autofill=True)
        self._activeTableWidget = DataframeTableWidget(autofill=True)

    def reinitialize(self, calibration: datatypes.Calibration) -> None:
        self._resetClassVariables(calibration)
        self._linesTableWidget.reinitialize(self._linesDf)
        self._activeTableWidget.reinitialize(self._activeDf)
