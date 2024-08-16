from PyQt6 import QtCore, QtWidgets

class ConditionTableWidget(QtWidgets.QTableWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None, method: dict | None = None):
        assert method is not None, "method must be provided"
        super(ConditionTableWidget, self).__init__(parent)
        self._method = method

        self.setObjectName("condition-table")
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        # self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)

        self._setHeaders()
        self._setUpTable()
        self.selectCondition(1)

        self.cellClicked.connect(self._cellClicked)

    def _setHeaders(self) -> None:
        labels = self._method["conditions"].columns.str.title()
        self.setColumnCount(self._method["conditions"].shape[1])
        self.setHorizontalHeaderLabels(labels)

    def _setUpTable(self) -> None:
        self.setRowCount(self._method["conditions"].shape[0])
        for rowIndex, row in enumerate(self._method["conditions"].itertuples(index=False)):
            for columnIndex, value in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                self.setItem(rowIndex, columnIndex, item)

    @QtCore.pyqtSlot(int, int)
    def _cellClicked(self, row: int, column: int) -> None:
        conditionId = self.item(row, 0).text().split(' ')[-1]
        self._toggleConditionElements(conditionId)

    def _toggleConditionElements(self, conditionId: int) -> None:
        symbols = self._method["lines"].query(f"condition_id == {conditionId} and active == 1")['symbol'].values
        for symbol, button in self.parent().buttonMap.items():
            button.blockSignals(True)
            button.setChecked(symbol in symbols)
            button.blockSignals(False)
    
    def selectCondition(self, conditionId: int) -> None:
        self.selectRow(conditionId - 1)
        self._toggleConditionElements(conditionId)
