from PyQt6 import QtCore, QtWidgets

from src.utils import datatypes
from src.views.base.tablewidget import DataframeTableWidget


class LinesTableWidget(QtWidgets.QWidget):
    """
    LinesTableWidget is a custom QWidget that displays a table of lines from calibration data, allowing users to filter between all lines and active lines. It provides an interactive interface for managing and viewing line data in a structured format.

    Args:
        parent (QWidget | None): Optional parent widget for the lines table widget.
        calibration (Calibration | None): Optional calibration data to initialize the widget with.

    Methods:
        _initializeUi() -> None:
            Sets up the user interface components for the widget.

        _createFilterLayout() -> None:
            Creates a layout for filtering the displayed lines based on user selection.

        _setUpView() -> None:
            Configures the main layout of the widget, combining the filter and table display.

        setFilter(filterName: str) -> None:
            Updates the displayed table based on the selected filter option.

        _createTableWidgets() -> None:
            Initializes the table widgets for displaying all lines and active lines.

        supply(calibration: Calibration) -> None:
            Updates the widget with new calibration data and refreshes the displayed line tables.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        calibration: datatypes.Calibration | None = None,
    ):
        super().__init__(parent)
        self._calibration = None
        self._activeDf = None
        self._linesDf = None
        self._initializeUi()
        if calibration is not None:
            self.supply(calibration)
        self.hide()

    def _initializeUi(self) -> None:
        self._createFilterLayout()
        self._createTableWidgets()
        self._setUpView()

    def _createFilterLayout(self) -> None:
        self._searchComboBox = QtWidgets.QComboBox(self)
        self._searchComboBox.setObjectName("search-combo-box")
        self._searchComboBox.currentTextChanged.connect(self.setFilter)
        self._searchLayout = QtWidgets.QHBoxLayout()
        self._searchLayout.addWidget(QtWidgets.QLabel("Filter by: ", self))
        self._searchLayout.addWidget(self._searchComboBox)
        self._searchLayout.addStretch()

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(self._searchLayout)
        self.mainLayout.addWidget(self._linesTableWidget)
        self.setLayout(self.mainLayout)

    @QtCore.pyqtSlot(str)
    def setFilter(self, filterName: str) -> None:
        oldWidget = self.mainLayout.itemAt(1).widget()
        oldWidget.hide()
        if filterName == "All Lines":
            self.mainLayout.replaceWidget(oldWidget, self._linesTableWidget)
            self._linesTableWidget.selectRow(0)
            self._linesTableWidget.show()
        else:
            self.mainLayout.replaceWidget(oldWidget, self._activeTableWidget)
            self._activeTableWidget.selectRow(0)
            self._activeTableWidget.show()

    def _createTableWidgets(self) -> None:
        self._linesTableWidget = DataframeTableWidget(self, autoFill=True)
        self._linesTableWidget.hide()
        self._activeTableWidget = DataframeTableWidget(self, autoFill=True)
        self._activeTableWidget.hide()

    def supply(self, calibration: datatypes.Calibration) -> None:
        """Updates the widget with the provided calibration data.

        This method assigns the calibration to the widget, processes the lines associated
        with the calibration, and updates the corresponding tables. It also manages the
        search combo box to ensure it reflects the available options.

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
        self._linesDf = self._calibration.lines.drop(["line_id", "element_id"], axis=1)
        self._activeDf = self._linesDf.query("active == 1")
        self._linesTableWidget.supply(self._linesDf)
        self._activeTableWidget.supply(self._activeDf)
        if self._searchComboBox.count() == 0:
            self._searchComboBox.clear()
            self._searchComboBox.addItems(["All Lines", "Active Lines"])
        self.setFilter(self._searchComboBox.currentText())
        self.blockSignals(False)
