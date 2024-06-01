import sys
from collections import defaultdict

import pandas as pd
from PyQt6 import QtCore, QtWidgets

from python.utils.database import getDatabase
from python.utils.paths import resource_path


class InterferenceWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(InterferenceWindow, self).__init__(parent)
        self._db = getDatabase(resource_path('fundamentals.db'))
        self._interferenceDf = self._db.dataframe('SELECT * FROM interference')
        self._elementsDf = self._db.dataframe('SELECT * FROM elements')
        self.resize(1200, 800)
        self._createTableWidget()
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self._tableWidget)
        centralWidget = QtWidgets.QWidget(self)
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

    def _createTableWidget(self) -> None:
        self._tableWidget = QtWidgets.QTableWidget(self)
        self._headers = ['Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K',
                         'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br',
                         'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb',
                         'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho',
                         'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi',
                         'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am']
        horizontalHeaders = self._headers.copy()
        horizontalHeaders.insert(0, '')
        self._tableWidget.setColumnCount(len(horizontalHeaders))
        self._tableWidget.setHorizontalHeaderLabels(horizontalHeaders)
        self._tableWidget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self._tableWidget.setRowCount(len(self._headers))
        self._tableWidget.setVerticalHeaderLabels(self._headers)
        self._tableWidget.setGridStyle(QtCore.Qt.PenStyle.DashDotDotLine)
        self._tableWidget.setAlternatingRowColors(True)
        self._tableWidget.setStyleSheet("font-size: 12pt;")
        self._fillTable()

    def _fillTable(self) -> None:
        for i in range(self._tableWidget.rowCount()):
            for j in range(1, self._tableWidget.columnCount()):
                self._tableWidget.setItem(i, j, QtWidgets.QTableWidgetItem())
        self._addComboBoxes()
        for rowIndex in range(self._tableWidget.rowCount()):
            radiation: str = self._tableWidget.cellWidget(rowIndex, 0).currentText()
            self._fillRow(rowIndex, radiation)

    def _addComboBoxes(self) -> None:
        self._comboBoxMap = defaultdict(QtWidgets.QComboBox)
        for index, series in self._elementsDf.iterrows():
            symbol = series['symbol']
            self._comboBoxMap[symbol].addItem(series['radiation_type'])
        for symbol, comboBox in self._comboBoxMap.items():
            comboBox.setStyleSheet("""
                QComboBox {
                    border: 1px solid gray;
                    border-radius: 3px;
                    padding: 1px 18px 1px 3px;
                }
                QComboBox:hover {
                    border: 1px solid darkblue;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 15px;
                    border-left-width: 1px;
                    border-left-color: darkgray;
                    border-left-style: solid;
                    border-top-right-radius: 3px;
                    border-bottom-right-radius: 3px;
                }
                QComboBox::down-arrow {
                    image: url(down-arrow-resized.png)
                }
                QComboBox QAbstractItemView {
                    border-radius: 3px;
                    border: 1px solid gray;
                    selection-background-color: lightgray;
                    background-color: lightblue; /* Custom background color for the drop-down menu */
                }
            """)
            comboBox.currentTextChanged.connect(self._changeRowRadiation)
            row = self._headers.index(symbol)
            self._tableWidget.setCellWidget(row, 0, comboBox)

    def _fillRow(self, rowIndex: int, radiation: str):
        symbol = self._headers[rowIndex]
        elementId: int = self._elementsDf.query(
            f"radiation_type == '{radiation}' and symbol == '{symbol}'"
        )["element_id"].values[0]
        row: pd.DataFrame = self._interferenceDf.query(f"element_id == {elementId}")
        for _, series in row.iterrows():
            interfererId = series["interferer_id"]
            interfereSymbol = self._elementsDf.query(f"element_id == {interfererId}")["symbol"].values[0]
            coefficient = series["coefficient"]
            columnIndex = self._headers.index(interfereSymbol) + 1
            item = self._tableWidget.item(rowIndex, columnIndex)
            item.setText(str(coefficient))
            self._tableWidget.setItem(rowIndex, columnIndex, item)

    @QtCore.pyqtSlot(str)
    def _changeRowRadiation(self, radiation: str) -> None:
        rowIndex = self._tableWidget.currentRow()
        for i in range(1, self._tableWidget.columnCount()):
            item = self._tableWidget.item(rowIndex, i)
            item.setText("")
        self._fillRow(rowIndex, radiation)

    def _saveToDatabase(self) -> None:
        pass


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = InterferenceWindow()
    window.show()
    sys.exit(app.exec())
