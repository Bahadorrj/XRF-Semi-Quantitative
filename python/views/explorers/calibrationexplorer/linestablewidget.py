from PyQt6 import QtCore, QtWidgets


class LinesTableWidget(QtWidgets.QWidget):
    def __init__(
        self, parent: QtWidgets.QWidget | None = None, calibration: dict | None = None
    ):
        super().__init__(parent)
        self._calibration = calibration
        self._linesDf = self._calibration["lines"].drop(
            ["line_id", "element_id"], axis=1
        )
        self._activeDf = (
            self._linesDf.query("active == 1")
        )
        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._createFilterLayout()
        self._createTableWidget()
        self.setFilter(self._filterComboBox.currentText())

    def _createFilterLayout(self) -> None:
        label = QtWidgets.QLabel("Filter by: ")
        self._filterComboBox = QtWidgets.QComboBox()
        self._filterComboBox.setObjectName("filter-combo-box")
        self._filterComboBox.addItems(
            ["All Lines", "Active Lines"]
        )
        self._filterComboBox.currentTextChanged.connect(self.setFilter)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self._filterComboBox)
        layout.addStretch()
        self._mainLayout.addLayout(layout)

    def _createTableWidget(self) -> None:
        self._tableWidget = QtWidgets.QTableWidget(self)
        self._tableWidget.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self._tableWidget.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self._tableWidget.setColumnCount(len(self._linesDf.columns))
        self._tableWidget.setHorizontalHeaderLabels(self._linesDf.columns)
        self._tableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self._tableWidget.horizontalHeader().setStretchLastSection(True)
        self._tableWidget.setAlternatingRowColors(True)
        self._mainLayout.addWidget(self._tableWidget)

    def _fillTable(self, tableName: str) -> None:
        df = None
        if tableName == "all-lines":
            df = self._linesDf
        elif tableName == "active-lines":
            df = self._activeDf
        if df is not None:
            self._tableWidget.setRowCount(0)
            for row in df.itertuples(index=False):
                self._tableWidget.setRowCount(self._tableWidget.rowCount() + 1)
                for column, value in enumerate(row):
                    item = QtWidgets.QTableWidgetItem()
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                    item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
                    if df.columns[column] == "condition_id":
                        try:
                            value = int(value)
                        except ValueError:
                            value = ""
                    elif df.columns[column] == "active":
                        value = bool(value)
                        if value is True:
                            item.setForeground(QtCore.Qt.GlobalColor.green)
                        else:
                            item.setForeground(QtCore.Qt.GlobalColor.red)
                    item.setText(str(value))
                    self._tableWidget.setItem(
                        self._tableWidget.rowCount() - 1, column, item
                    )

    @QtCore.pyqtSlot(str)
    def setFilter(self, filterName: str) -> None:
        key = filterName.lower().replace(" ", "-")
        self._fillTable(key)
