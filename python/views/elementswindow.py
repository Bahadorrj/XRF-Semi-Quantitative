from typing import Optional

import pandas
from PyQt6 import QtCore, QtWidgets

from python.utils import paths
from python.utils.database import getDatabase


class ElementsWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(1200, 800)
        self.setWindowTitle('Elements')
        db = getDatabase(paths.resource_path("fundamentals.db"))
        self._df = db.dataframe('SELECT * FROM elements')
        query = "SELECT * FROM elements WHERE element_id IN (SELECT element_id FROM UQ ORDER BY element_id)"
        self._uqr = db.dataframe(query)
        self._mainLayout = QtWidgets.QVBoxLayout(self)
        self._createFilterLayout()
        self._createTableWidget()
        self.setFilter(self._filterComboBox.currentText())

    def _createFilterLayout(self) -> None:
        label = QtWidgets.QLabel('Filter by: ')
        self._filterComboBox = QtWidgets.QComboBox()
        self._filterComboBox.addItems(['All Elements', 'Active Elements', 'UQR Elements'])
        self._filterComboBox.currentTextChanged.connect(self.setFilter)
        spacerItem = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum
        )
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self._filterComboBox)
        layout.addItem(spacerItem)
        self._mainLayout.addLayout(layout)

    def _createTableWidget(self) -> None:
        self._tableWidget = QtWidgets.QTableWidget(self)
        self._tableWidget.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self._tableWidget.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self._tableWidget.setColumnCount(len(self._df.columns))
        self._tableWidget.setHorizontalHeaderLabels(self._df.columns)
        self._tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self._tableWidget.setAlternatingRowColors(True)
        self._mainLayout.addWidget(self._tableWidget)

    def _fillTable(self, tableName: str) -> None:
        df: Optional[pandas.DataFrame] = None
        if tableName == 'all-elements':
            df = self._df
        elif tableName == 'active-elements':
            df = self._df[self._df['active'] == 1]
        elif tableName == 'uqr-elements':
            df = self._uqr
        if df is not None:
            self._tableWidget.setRowCount(0)
            for row in df.itertuples(index=False):
                self._tableWidget.setRowCount(self._tableWidget.rowCount() + 1)
                for column, value in enumerate(row):
                    item = QtWidgets.QTableWidgetItem()
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                    item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
                    if df.columns[column] == 'condition_id':
                        try:
                            value = int(value)
                        except ValueError:
                            pass
                    elif df.columns[column] == 'active':
                        value = bool(value)
                        if value is True:
                            item.setForeground(QtCore.Qt.GlobalColor.green)
                        else:
                            item.setForeground(QtCore.Qt.GlobalColor.red)
                    item.setText(str(value))
                    self._tableWidget.setItem(self._tableWidget.rowCount() - 1, column, item)

    @QtCore.pyqtSlot(str)
    def setFilter(self, filterName: str) -> None:
        key = filterName.lower().replace(' ', '-')
        self._fillTable(key)
