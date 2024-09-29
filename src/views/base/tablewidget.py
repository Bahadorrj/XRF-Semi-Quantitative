import pandas

from PyQt6 import QtWidgets, QtCore


class TableItem(QtWidgets.QTableWidgetItem):
    def __init__(self, text: str | None = None, editable: bool = False):
        super().__init__(text)
        self._editable = editable
        if not self._editable:
            self.setFlags(self.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        self.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)


class TableWidget(QtWidgets.QTableWidget):
    """
    TableWidget is a custom QTableWidget that manages rows of data, allowing for dynamic updates and selections. It provides methods to add, remove, and manipulate rows while maintaining a clear structure for the data.

    Attributes:
        rowChanged (pyqtSignal): Signal emitted when a row is changed.

    Args:
        parent (QWidget | None): Optional parent widget for the table.

    Methods(Beside the original class methods):
        setHeaders(headers: list | tuple) -> None:
            Sets the headers for the table columns.

        setHorizontalHeaderLabels(labels: list | tuple) -> None:
            Configures the horizontal header labels and their resize modes.

        addRow(row: dict) -> None:
            Adds a new row to the table with the specified data.

        removeRow(rowIndex: int) -> None:
            Removes the row at the specified index from the table.

        getRow(rowIndex: int) -> dict:
            Retrieves the data of the row at the specified index.

        getRowById(rowId: int) -> dict:
            Finds and returns the row data associated with the given row ID.

        getCurrentRow() -> dict:
            Returns the data of the currently selected row.

        selectRowByID(rowId: int) -> None:
            Selects the row that matches the specified row ID.

        resetTable() -> None:
            Clears all rows from the table and resets its state.

        updateRow(rowIndex: int, row: dict) -> None:
            Updates the data of the specified row with new values.
    """

    rowChanged = QtCore.pyqtSignal(int, str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.rows = {}
        self.setAlternatingRowColors(True)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setSelectionMode(QtWidgets.QTableWidget.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QTableWidget.SelectionBehavior.SelectRows)

    def setHeaders(self, headers: list | tuple):
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

    def setHorizontalHeaderLabels(self, labels: list | tuple) -> None:
        for column, label in enumerate(labels):
            if label:
                self.horizontalHeader().setSectionResizeMode(
                    column, QtWidgets.QHeaderView.ResizeMode.Stretch
                )
            else:
                self.horizontalHeader().setSectionResizeMode(
                    column, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
                )
            item = QtWidgets.QTableWidgetItem(label)
            self.setHorizontalHeaderItem(column, item)

    def addRow(self, row: dict) -> None:
        self.setRowCount(self.rowCount() + 1)
        rowIndex, columnIndex = self.rowCount() - 1, 0
        for component in row.values():
            if isinstance(component, QtWidgets.QWidget):
                self.setCellWidget(rowIndex, columnIndex, component)
                columnIndex += 1
            elif isinstance(component, QtWidgets.QTableWidgetItem):
                self.setItem(rowIndex, columnIndex, component)
                columnIndex += 1
        self.rows[rowIndex] = row
        self.selectRow(rowIndex)

    def removeRow(self, rowIndex: int) -> None:
        if rowIndex < 0 or rowIndex >= self.rowCount():
            return
        super().removeRow(rowIndex)
        self.rows.pop(rowIndex)
        self.rows = dict(zip(range(self.rowCount()), self.rows.values()))

    def getRow(self, rowIndex: int) -> dict:
        if rowIndex < 0 or rowIndex >= self.rowCount():
            return None
        return self.rows[rowIndex]

    def getCurrentRow(self) -> dict:
        return self.rows[self.currentRow()] if self.currentRow() != -1 else None

    def resetTable(self) -> None:
        self.setRowCount(0)
        self.rows.clear()

    def updateRow(self, rowIndex: int, row: dict) -> None:
        self.blockSignals(True)
        rowIndex = self.rows[rowIndex]
        for columnIndex, component in row.items():
            if isinstance(component, QtWidgets.QWidget):
                self.setCellWidget(rowIndex, columnIndex, component)
            else:
                self.setItem(rowIndex, columnIndex, component)
        self.blockSignals(False)


class DataframeTableWidget(TableWidget):
    """
    DataframeTableWidget is a specialized TableWidget designed to display and manage data from a pandas DataFrame. It allows for automatic filling of the table based on the DataFrame's content and provides a clear interface for updating the displayed data.

    Args:
        parent (QWidget | None): Optional parent widget for the table.
        dataframe (DataFrame | None): Optional pandas DataFrame to initialize the table with.
        autoFill (bool): If True, the table will be automatically filled with data from the DataFrame upon initialization.

    Methods:
        _fillTable() -> None:
            Populates the table with data from the DataFrame, formatting specific columns for better readability.

        supply(dataframe: DataFrame) -> None:
            Updates the table with a new DataFrame, resetting the current content and optionally refilling the table.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        dataframe: pandas.DataFrame | None = None,
        autoFill: bool = False,
        editable: bool = False,
    ) -> None:
        super().__init__(parent)
        self._df = None
        self._autoFill = autoFill
        self._editable = editable
        if dataframe is not None:
            self.supply(dataframe)

    def _fillTable(self) -> None:
        if self._df.empty:
            return
        for rowIndex, row in enumerate(self._df.itertuples(index=False)):
            items = {"rowId": rowIndex}
            for columnIndex, value in enumerate(row):
                item = TableItem(str(value), self._editable)
                items[self._df.columns[columnIndex]] = item
            self.addRow(items)
        if "active" in self.rows[0]:
            self.blockSignals(True)
            for row in self.rows.values():
                if int(row["active"].text()) == 1:
                    row["active"].setForeground(QtCore.Qt.GlobalColor.darkGreen)
                    row["active"].setText("True")
                else:
                    row["active"].setForeground(QtCore.Qt.GlobalColor.red)
                    row["active"].setText("False")
            self.blockSignals(False)
        if "rotation" in self.rows[0]:
            self.blockSignals(True)
            for row in self.rows.values():
                if int(row["rotation"].text()) == 1:
                    row["rotation"].setForeground(QtCore.Qt.GlobalColor.darkGreen)
                    row["rotation"].setText("True")
                else:
                    row["rotation"].setForeground(QtCore.Qt.GlobalColor.red)
                    row["rotation"].setText("False")
            self.blockSignals(False)
        if "condition_id" in self.rows[0]:
            self.blockSignals(True)
            for row in self.rows.values():
                if (conditionId := row["condition_id"].text()) != "nan":
                    row["condition_id"].setText(conditionId.split(".")[0])
                else:
                    row["condition_id"].setText(None)
            self.blockSignals(False)

    def supply(self, dataframe: pandas.DataFrame):
        if dataframe is None:
            return
        if self._df is not None and self._df.equals(dataframe):
            return
        self.blockSignals(True)
        self._df = dataframe
        self.resetTable()
        if self._autoFill:
            self.setHeaders(
                [" ".join(column.split("_")).title() for column in self._df.columns]
            )
            self._fillTable()
        self.blockSignals(False)
