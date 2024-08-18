from PyQt6 import QtCore, QtWidgets

from python.utils import datatypes

from python.views.base.tablewidgets import DataframeTableWidget


class LinesTableWidget(QtWidgets.QWidget):
    def __init__(
        self, parent: QtWidgets.QWidget | None = None, calibration: datatypes.Calibration | None = None
    ):
        assert calibration is not None, "calibration must be provided"
        super().__init__(parent)
        self._initializeClassVariables(calibration)

        self._createFilterLayout()
        self._createTableWidgets()
        self._setUpView()
        self.setFilter(self._filterComboBox.currentText())

    def _initializeClassVariables(self, calibration: datatypes.Calibration) -> None:
        self._calibration = calibration
        self._linesDf = self._calibration.lines.drop(
            ["line_id", "element_id"], axis=1
        )
        self._activeDf = (
            self._linesDf.query("active == 1")
        )

    def _createFilterLayout(self) -> None:
        self._filterComboBox = QtWidgets.QComboBox()
        self._filterComboBox.setObjectName("filter-combo-box")
        self._filterComboBox.addItems(
            ["All Lines", "Active Lines"]
        )
        self._filterComboBox.currentTextChanged.connect(self.setFilter)
        self._searchLayout = QtWidgets.QHBoxLayout()
        self._searchLayout.addWidget(QtWidgets.QLabel("Filter by: "))
        self._searchLayout.addWidget(self._filterComboBox)
        self._searchLayout.addStretch()

    def _setUpView(self) -> None:
        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.addLayout(self._searchLayout)
        self._mainLayout.addWidget(QtWidgets.QWidget(self))

    @QtCore.pyqtSlot(str)
    def setFilter(self, filterName: str) -> None:
        oldWidget = self._mainLayout.itemAt(1).widget()
        oldWidget.hide()
        if filterName == "All Lines":
            self._mainLayout.replaceWidget(oldWidget, self._linesTableWidget)
        else:
            self._mainLayout.replaceWidget(oldWidget, self._activeTableWidget)

    def _createTableWidgets(self) -> None:
        self._linesTableWidget = DataframeTableWidget(dataframe=self._linesDf, autofill=True)
        self._activeTableWidget = DataframeTableWidget(dataframe=self._activeDf, autofill=True)

    def reinitialize(self, calibration: datatypes.Calibration) -> None:
        self._initializeClassVariables(calibration)
        self._linesTableWidget.reinitialize(self._linesDf)
        self._activeTableWidget.reinitialize(self._activeDf)
