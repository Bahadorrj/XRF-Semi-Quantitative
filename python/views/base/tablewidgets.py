import pandas

from PyQt6 import QtWidgets, QtCore, QtGui

from python.utils.database import getDataframe
from python.utils.paths import resourcePath


class TableItem(QtWidgets.QTableWidgetItem):
    def __init__(self, text: str):
        super().__init__(text)
        self.setFlags(self.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        self.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.currentText = self.text()
        self.previousText = self.currentText

    def setText(self, text: str | None) -> None:
        self.previousText = self.currentText
        self.currentText = text
        return super().setText(text)

class TableWidget(QtWidgets.QTableWidget):
    rowChanged = QtCore.pyqtSignal(int, str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super(TableWidget, self).__init__(parent)
        self.rows = dict()
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
        rowIndex = self.rowCount() - 1
        for columnIndex, component in enumerate(list(row.values())[1:]):
            if isinstance(component, QtWidgets.QWidget):
                self.setCellWidget(rowIndex, columnIndex, component)
            elif isinstance(component, QtWidgets.QTableWidgetItem):
                self.setItem(rowIndex, columnIndex, component)
        self.rows[rowIndex] = row

    def getRow(self, rowIndex: int) -> dict:
        return self.rows[rowIndex]

    def getRowById(self, rowId: int) -> dict:
        return list(filter(lambda d: d["rowId"] == rowId, self.rows.values()))[0]

    def selectRowByID(self, rowId: int) -> None:
        for rowIndex, row in self.rows.items():
            if row["rowId"] == rowId:
                self.selectRow(rowIndex)
                break

    def resetTable(self) -> None:
        self.setRowCount(0)
        self.rows.clear()

    def updateRow(self, rowIndex: int, row: dict) -> None:
        rowIndex = self.rows[rowIndex]
        self.blockSignals(True)
        for columnIndex, component in row.items():
            if isinstance(component, QtWidgets.QWidget):
                self.setCellWidget(rowIndex, columnIndex, component)
            else:
                self.setItem(rowIndex, columnIndex, component)
        self.blockSignals(False)


class DataframeTableWidget(TableWidget):
    def __init__(
        self, parent: QtWidgets.QWidget | None = None, dataframe: pandas.DataFrame | None = None, autofill: bool = False
    ) -> None:
        assert dataframe is not None, "dataframe must be provided"
        super(DataframeTableWidget, self).__init__(parent)
        self._df = dataframe
        self._autofill = autofill
        if self._autofill:
            self.setHeaders(self._df.columns.str.title())
            self.fillTable()
            self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
            self.horizontalHeader().setStretchLastSection(True)

    def fillTable(self) -> None:
        for rowIndex, row in enumerate(self._df.itertuples(index=False)):
            items = {"rowId": rowIndex}
            for columnIndex, value in enumerate(row):
                item = TableItem(str(value))
                items[self._df.columns[columnIndex]] = item
            self.addRow(items)
        if "active" in self.rows[0]:
            for row in self.rows.values():
                if int(row['active'].text()) == 1:
                    row["active"].setForeground(QtCore.Qt.GlobalColor.darkGreen)
                    row["active"].setText("True")
                else:
                    row["active"].setForeground(QtCore.Qt.GlobalColor.red)
                    row["active"].setText("False")
        if "condition_id" in self.rows[0]:
            for row in self.rows.values():
                if (conditionId := row["condition_id"].text()) != "nan":
                    row["condition_id"].setText(conditionId.split(".")[0])
                else:
                    row["condition_id"].setText(None)

    def reinitialize(self, dataframe: pandas.DataFrame):
        self.setRowCount(0)
        self._df = dataframe
        if self._autofill:
            self.setHeaders(self._df.columns.str.title())
            self.fillTable()
