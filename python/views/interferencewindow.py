from collections import defaultdict

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt6 import QtCore, QtWidgets, QtGui

from python.utils.color import generateGradiant
from python.utils.database import getDatabase
from python.utils.paths import resourcePath


class RadiationComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(RadiationComboBox, self).__init__(parent)
        self.setStyleSheet(
            """
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
                image: url(icons/down-arrow-resized.png)
            }
            QComboBox QAbstractItemView {
                border-radius: 3px;
                border: 1px solid gray;
                selection-background-color: lightgray;
                background-color: lightblue; /* Custom background color for the drop-down menu */
            }
        """
        )


class InterferenceTableWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(InterferenceTableWidget, self).__init__(parent)
        self.setGridStyle(QtCore.Qt.PenStyle.DashDotDotLine)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("font-size: 12pt;")
        self.setStyleSheet(
            """
            QTableWidget::item:selected {
                background-color: lightblue;
            }
            QHeaderView::section {
                padding: 3px;  /* Adjust padding value as needed */
            }
            """
        )


class InterferenceWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None) -> None:
        super(InterferenceWindow, self).__init__(parent)
        self._db = getDatabase(resourcePath("fundamentals.db"))
        self._interferenceDf = self._db.dataframe("SELECT * FROM Interferences")
        self._initialInterferenceDf = self._interferenceDf.copy()
        self._linesDf = self._db.dataframe("SELECT * FROM Lines")
        self._symbols = self._linesDf["symbol"].unique().tolist()
        self.resize(1200, 800)
        self._mainLayout = QtWidgets.QGridLayout()
        # self._createIndexFinderLayout()
        self._createTableWidget()
        self._mainLayout.setColumnStretch(1, 2)
        centralWidget = QtWidgets.QWidget(self)
        centralWidget.setLayout(self._mainLayout)
        self.setCentralWidget(centralWidget)

    def _createTableWidget(self) -> None:
        self._tableWidget = InterferenceTableWidget(self)
        self._tableWidget.setColumnCount(len(self._symbols))
        self._tableWidget.setHorizontalHeaderLabels(self._symbols)
        vHeader = self._symbols.copy()
        vHeader.insert(0, "")
        self._tableWidget.setRowCount(len(vHeader))
        self._tableWidget.setVerticalHeaderLabels(vHeader)
        self._fillTable()
        self._tableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self._tableWidget.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self._tableWidget.setCurrentCell(0, 0)
        self._mainLayout.addWidget(self._tableWidget, 0, 1, 5, 1)
        self._tableWidget.cellChanged.connect(self._cellChanged)
        self._tableWidget.cellClicked.connect(self._cellClicked)

    def _fillTable(self) -> None:
        self._addComboBoxes()
        self._addItems()

    def _addComboBoxes(self) -> None:
        self._hComboBoxMap = defaultdict(RadiationComboBox)
        self._vComboBoxMap = defaultdict(RadiationComboBox)
        for row in self._linesDf.itertuples(index=False):
            symbol = row.symbol
            self._hComboBoxMap[symbol].addItem(f"{row.radiation_type}")
        for symbol, comboBox in self._hComboBoxMap.items():
            column = self._symbols.index(symbol)
            self._tableWidget.setCellWidget(0, column, comboBox)
            comboBox.currentTextChanged.connect(self._changeColumnRadiation)

    def _addItems(self) -> None:
        for i in range(1, self._tableWidget.rowCount()):
            for j in range(1, self._tableWidget.columnCount()):
                item = QtWidgets.QTableWidgetItem()
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self._tableWidget.setItem(i, j, item)
        for i in range(self._tableWidget.columnCount()):
            self._fillColumn(i, "Ka")

    def _fillColumn(self, index: int, interfererRadiation: str) -> None:
        interfererSymbol = self._symbols[index]
        query = f"""
            SELECT line_id FROM Lines WHERE symbol = '{interfererSymbol}' AND radiation_type = '{interfererRadiation}';
        """
        interfererLineId = self._db.executeQuery(query).fetchone()[0]
        for rowIndex in range(1, self._tableWidget.rowCount()):
            symbol = self._symbols[rowIndex - 1]
            query = f"""
                SELECT coefficient 
                FROM Interferences 
                WHERE line1_id = (SELECT line_id FROM Lines WHERE symbol = '{symbol}' AND active = 1) 
                AND line2_id = {interfererLineId}
            """
            if tmp := self._db.executeQuery(query).fetchone():
                coefficient = tmp[0]
                if coefficient is not None:
                    item = self._tableWidget.item(rowIndex, index)
                    item.setText(str(coefficient))

    def _clearColumn(self, columnIndex: int) -> None:
        for i in range(1, self._tableWidget.rowCount()):
            item = self._tableWidget.item(i, columnIndex)
            item.setText("")

    @QtCore.pyqtSlot(str)
    def _changeColumnRadiation(self, radiation: str) -> None:
        self._tableWidget.blockSignals(True)
        columnIndex = self._tableWidget.currentColumn()
        self._clearColumn(columnIndex)
        self._fillColumn(columnIndex, radiation)
        self._tableWidget.blockSignals(False)

    def _createIndexFinderLayout(self) -> None:
        self._createPlotWidget()
        self._createElementLayout()
        self._createInterfererLayout()
        self._createElementInterferenceTable()
        self._createInterfererInterferenceTable()

    def _createPlotWidget(self) -> None:
        self._plotWidget = pg.PlotWidget(self)
        self._plotWidget.setBackground("#fff")
        # self._plotWidget.setLimits(xMin=0, xMax=10, yMin=0, yMax=100)
        plotItem = self._plotWidget.getPlotItem()
        plotItem.setContentsMargins(10, 10, 10, 10)
        self._plotWidget.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self._plotWidget.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self._mainLayout.addWidget(self._plotWidget, 0, 0, 1, 1)

    def _createElementLayout(self) -> None:
        horizontalLayout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel()
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label.setText("Element:")
        horizontalLayout.addWidget(label)
        self._elementSymbol = QtWidgets.QLineEdit()
        self._elementSymbol.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        horizontalLayout.addWidget(self._elementSymbol)
        self._elementRadiation = QtWidgets.QComboBox()
        horizontalLayout.addWidget(self._elementRadiation)
        self._mainLayout.addLayout(horizontalLayout, 1, 0, 1, 1)
        self._elementSymbol.editingFinished.connect(self._elementSelected)
        self._elementRadiation.currentTextChanged.connect(self._elementRadiationChanged)

    @QtCore.pyqtSlot()
    def _elementSelected(self):
        elementSymbol = self._elementSymbol.text()
        if elementSymbol in self._symbols:
            index = self._symbols.index(elementSymbol)
            if self._tableWidget.currentColumn() != 0:
                self._tableWidget.setCurrentCell(
                    index, self._tableWidget.currentColumn()
                )
            else:
                self._tableWidget.selectRow(index)
            self._elementRadiation.blockSignals(True)
            self._elementRadiation.clear()
            comboBox = self._hComboBoxMap[elementSymbol]
            comboBoxTexts = [comboBox.itemText(i) for i in range(comboBox.count())]
            self._elementRadiation.addItems(comboBoxTexts)
            self._elementRadiation.blockSignals(False)
            self._changeElementInterferenceTable()
        else:
            self._elementSymbol.clear()

    @QtCore.pyqtSlot(str)
    def _elementRadiationChanged(self, radiation):
        elementSymbol = self._elementSymbol.text()
        self._vComboBoxMap[elementSymbol].setCurrentText(radiation)
        if self._tableWidget.currentColumn() != 0:
            self._tableWidget.setCurrentCell(
                self._tableWidget.currentRow(), self._tableWidget.currentColumn()
            )
        else:
            self._tableWidget.selectRow(self._tableWidget.currentRow())
        self._changeElementInterferenceTable()

    def _changeElementInterferenceTable(self):
        df = self._interferenceDf.query(
            f"line1_symbol == '{self._elementSymbol.text()}' \
            and line1_radiation_type == '{self._elementRadiation.currentText()}'"
        )
        colors = generateGradiant(df.shape[0])
        self._elementInterferenceTable.setRowCount(0)
        for rowIndex, row in enumerate(df.itertuples()):
            symbol = row.line2_symbol
            radiation = row.line2_radiation_type
            percentage = row.percentage
            self._elementInterferenceTable.setRowCount(rowIndex + 1)
            for columnIndex, value in enumerate([symbol, radiation, percentage]):
                item = QtWidgets.QTableWidgetItem()
                item.setBackground(QtGui.QColor(colors[rowIndex]))
                if columnIndex == 2:
                    item.setText(str(value) + "%")
                else:
                    item.setText(value)
                self._elementInterferenceTable.setItem(rowIndex, columnIndex, item)

    def _createInterfererLayout(self) -> None:
        horizontalLayout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel()
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label.setText("Interferer:")
        horizontalLayout.addWidget(label)
        self._interfererSymbol = QtWidgets.QLineEdit()
        self._interfererSymbol.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        horizontalLayout.addWidget(self._interfererSymbol)
        self._interfererRadiation = QtWidgets.QComboBox()
        horizontalLayout.addWidget(self._interfererRadiation)
        self._mainLayout.addLayout(horizontalLayout, 3, 0, 1, 1)
        self._interfererSymbol.editingFinished.connect(self._interfererSelected)
        self._interfererRadiation.currentTextChanged.connect(
            self._interfererRadiationChanged
        )

    @QtCore.pyqtSlot()
    def _interfererSelected(self):
        interfererSymbol = self._interfererSymbol.text()
        if interfererSymbol in self._symbols:
            index = self._symbols.index(interfererSymbol)
            if self._tableWidget.currentRow() != 0:
                self._tableWidget.setCurrentCell(self._tableWidget.currentRow(), index)
            else:
                self._tableWidget.selectColumn(index)
            self._interfererRadiation.blockSignals(True)
            self._interfererRadiation.clear()
            comboBox = self._hComboBoxMap[interfererSymbol]
            comboBoxTexts = [comboBox.itemText(i) for i in range(comboBox.count())]
            self._interfererRadiation.addItems(comboBoxTexts)
            self._interfererRadiation.blockSignals(False)
            self._changeInterfererInterferenceTable()
        else:
            self._interfererSymbol.clear()

    @QtCore.pyqtSlot(str)
    def _interfererRadiationChanged(self, radiation):
        interfererSymbol = self._interfererSymbol.text()
        self._hComboBoxMap[interfererSymbol].setCurrentText(radiation)
        if self._tableWidget.currentRow() != 0:
            self._tableWidget.setCurrentCell(
                self._tableWidget.currentRow(), self._tableWidget.currentColumn()
            )
        else:
            self._tableWidget.selectColumn(self._tableWidget.currentColumn())
        self._changeInterfererInterferenceTable()

    def _changeInterfererInterferenceTable(self):
        df = self._interferenceDf.query(
            f"line1_symbol == '{self._interfererSymbol.text()}' "
            f"and line1_radiation_type == '{self._interfererRadiation.currentText()}'"
        )
        colors = generateGradiant(df.shape[0])
        self._interfererInterferenceTable.setRowCount(0)
        for rowIndex, row in enumerate(df.itertuples()):
            symbol = row.line2_symbol
            radiation = row.line2_radiation_type
            percentage = row.percentage
            self._interfererInterferenceTable.setRowCount(rowIndex + 1)
            for columnIndex, value in enumerate([symbol, radiation, percentage]):
                item = QtWidgets.QTableWidgetItem()
                item.setBackground(QtGui.QColor(colors[rowIndex]))
                if columnIndex == 2:
                    item.setText(str(value) + "%")
                else:
                    item.setText(value)
                self._interfererInterferenceTable.setItem(rowIndex, columnIndex, item)

    def _createElementInterferenceTable(self) -> None:
        self._elementInterferenceTable = QtWidgets.QTableWidget(self)
        headers = ["Symbol", "Radiation", "Percentage"]
        self._elementInterferenceTable.setColumnCount(len(headers))
        self._elementInterferenceTable.setHorizontalHeaderLabels(headers)
        self._elementInterferenceTable.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self._elementInterferenceTable.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._elementInterferenceTable.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self._elementInterferenceTable.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self._mainLayout.addWidget(self._elementInterferenceTable, 2, 0, 1, 1)
        self._elementInterferenceTable.cellClicked.connect(self._linkElementTable)

    @QtCore.pyqtSlot()
    def _linkElementTable(self) -> None:
        row = self._elementInterferenceTable.currentRow()
        interfererSymbol = self._elementInterferenceTable.item(row, 0).text()
        columnIndex = self._symbols.index(interfererSymbol)
        rowIndex = self._symbols.index(self._elementSymbol.text())
        self._cellClicked(rowIndex, columnIndex)

    def _createInterfererInterferenceTable(self) -> None:
        self._interfererInterferenceTable = QtWidgets.QTableWidget(self)
        headers = ["Symbol", "Radiation", "Percentage"]
        self._interfererInterferenceTable.setColumnCount(len(headers))
        self._interfererInterferenceTable.setHorizontalHeaderLabels(headers)
        self._interfererInterferenceTable.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self._interfererInterferenceTable.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._interfererInterferenceTable.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self._interfererInterferenceTable.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self._mainLayout.addWidget(self._interfererInterferenceTable, 4, 0, 1, 1)
        self._interfererInterferenceTable.cellClicked.connect(self._linkInterfererTable)

    def _linkInterfererTable(self) -> None:
        row = self._interfererInterferenceTable.currentRow()
        symbol = self._interfererInterferenceTable.item(row, 0).text()
        rowIndex = self._symbols.index(symbol)
        columnIndex = self._symbols.index(self._interfererSymbol.text())
        self._cellClicked(rowIndex, columnIndex)

    @QtCore.pyqtSlot(int, int)
    def _cellChanged(self, row: int, column: int):
        try:
            coefficient = float(self._tableWidget.item(row, column).text())
        except ValueError:
            self._tableWidget.item(row, column).setText("")
            return
        if coefficient > 1:
            self._tableWidget.item(row, column).setText("")
            return
        self._plotCoefficient(coefficient)
        elementSymbol = self._symbols[row]
        elementRadiation = self._tableWidget.cellWidget(row, 0).currentText()
        interfererSymbol = self._symbols[column]
        interfererRadiation = self._tableWidget.cellWidget(0, column).currentText()
        elementId = self._linesDf.query(
            f"symbol == '{elementSymbol}' and radiation_type == '{elementRadiation}'"
        )["line_id"].values[0]
        interfererId = self._linesDf.query(
            f"symbol == '{interfererSymbol}' and radiation_type == '{interfererRadiation}'"
        )["line_id"].values[0]
        df = self._interferenceDf.query(
            f"(line1_id == {elementId} and line2_id == {interfererId}) \
            or (line1_id == {interfererId} and line2_id == {elementId})"
        )
        if df.empty:
            interferenceId = self._interferenceDf.iloc[-1, 0] + 1
            df2 = pd.DataFrame(
                {
                    "interference_id": [interferenceId],
                    "line1_id": [elementId],
                    "line1_symbol": [elementSymbol],
                    "line1_radiation_type": [elementRadiation],
                    "line2_id": [interferenceId],
                    "line2_symbol": [interfererSymbol],
                    "line2_radiation_type": [interfererRadiation],
                    "percentage": [0.0],
                    "coefficient": [coefficient],
                    "active": [0],
                }
            )
            df1 = pd.DataFrame(
                {
                    "interference_id": [interferenceId],
                    "line1_id": [interferenceId],
                    "line1_symbol": [interfererSymbol],
                    "line1_radiation_type": [interfererRadiation],
                    "line2_id": [elementId],
                    "line2_symbol": [elementSymbol],
                    "line2_radiation_type": [elementRadiation],
                    "percentage": [0.0],
                    "coefficient": [coefficient],
                    "active": [0],
                }
            )
            self._interferenceDf = pd.concat(
                [self._interferenceDf, df1, df2], ignore_index=True
            )
        else:
            for index in df.index:
                self._interferenceDf.at[index, "coefficient"] = coefficient
        if (
            self._hComboBoxMap[elementSymbol].currentText() == elementRadiation
            and self._vComboBoxMap[interfererSymbol].currentText()
            == interfererRadiation
        ):
            rowIndex = self._symbols.index(interfererSymbol)
            columnIndex = self._symbols.index(elementSymbol)
            item = self._tableWidget.item(rowIndex, columnIndex)
            item.setText(str(coefficient))

    @QtCore.pyqtSlot(int, int)
    def _cellClicked(self, row: int, column: int) -> None:
        if self._tableWidget.currentItem().text():
            self._plotCoefficient(float(self._tableWidget.currentItem().text()))
        else:
            self._plotWidget.clear()
        self._elementSymbol.setText(self._symbols[row])
        self._elementSelected()
        self._elementRadiation.setCurrentIndex(
            self._tableWidget.cellWidget(row, 0).currentIndex()
        )
        self._interfererSymbol.setText(self._symbols[column])
        self._interfererSelected()
        self._interfererRadiation.setCurrentIndex(
            self._tableWidget.cellWidget(0, column).currentIndex()
        )

    def _plotCoefficient(self, coefficient: float) -> None:
        self._plotWidget.clear()
        y = np.linspace(0, 1, 100)
        x = np.linspace(0, 100 / coefficient, 100)
        self._plotWidget.plot(x, y, pen=pg.mkPen(width=1, color="b"))

    def closeEvent(self, a0):
        a0.accept()
        self._saveToDatabase()

    def _saveToDatabase(self) -> None:
        df = self._interferenceDf[self._interferenceDf["coefficient"].notna()]
        for row in df.itertuples():
            availableDf = self._initialInterferenceDf.query(
                f"interference_id == {row.interference_id}"
            )
            if availableDf.empty:
                query = f"""
                    INSERT INTO Interferences (
                        line1_id,
                        line1_symbol,
                        line1_radiation_type,
                        line2_id,
                        line2_symbol,
                        line2_radiation_type,
                        coefficient
                    )
                    VALUES (
                        '{row.line1_id}',
                        '{row.line1_symbol}',
                        '{row.line1_radiation_type}',
                        {row.line2_id},
                        '{row.line2_symbol}',
                        '{row.line2_radiation_type}',
                        {row.coefficient}
                    );
                """
            else:
                query = f"""
                    UPDATE Interferences
                    SET coefficient = {row.coefficient}
                    WHERE interference_id = {row.interference_id};
                """
            self._db.executeQuery(query)
        self._db.closeConnection()
