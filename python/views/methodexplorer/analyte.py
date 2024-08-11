from numpy import nan
import pandas as pd

from PyQt6 import QtCore, QtGui, QtWidgets
from functools import partial


class AnalytesAndConditionsWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, method: dict = None):
        assert method is not None, "method must be provided"
        super(AnalytesAndConditionsWidget, self).__init__(parent)
        self.conditionsDataFrame = method["conditions"]
        self.linesDataframe = method["lines"]
        self.buttonMap = {}

        self.setObjectName("analyte-widget")

        self._setUpView()

    def _setUpView(self) -> None:
        vLayout = QtWidgets.QVBoxLayout()
        vLayout.setContentsMargins(30, 30, 30, 30)
        vLayout.setSpacing(30)
        vLayout.addLayout(self._createPeriodicLayout())
        vLayout.addWidget(self._createConditionTable())
        self.setLayout(vLayout)

    def _createPeriodicLayout(self) -> QtWidgets.QVBoxLayout:
        vLayout = QtWidgets.QVBoxLayout()
        vLayout.setSpacing(0)
        vLayout.setContentsMargins(0, 0, 0, 0)
        rows = [
            ["H", "", "He"],
            ["Li", "Be", "", "B", "C", "N", "O", "F", "Ne"],
            ["Na", "Mg", "", "Al", "Si", "P", "S", "Cl", "Ar"],
            ["K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"],
            ["Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe"],
            ["Cs", "Ba", "L", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn"],
            ["Fr", "Ra", "A", ""],
            [""],
            ["", "L", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", ""],
            ["", "A", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", ""]
        ]
        for row in rows:
            layout = QtWidgets.QHBoxLayout()
            layout.setSpacing(0)
            layout.setContentsMargins(0, 0, 0, 0)
            for symbol in row:
                if symbol:
                    button = QtWidgets.QPushButton(symbol, self)
                    button.setCheckable(True)
                    button.toggled.connect(partial(self._addElementToCondition, symbol))
                    layout.addWidget(button)
                    if symbol not in ['L', 'A']:
                        self.buttonMap[symbol] = button
                    else:
                        button.setDisabled(True)
                        button.setStyleSheet(
                            "background-color: #F5F5F5; color: #FE7099; border: 2px inset #CB0E44; font-weight: bold"
                        )
                else:
                    layout.addStretch() if len(row) > 1 else vLayout.addSpacing(30)
            vLayout.addLayout(layout)
        return vLayout

    @QtCore.pyqtSlot(bool)
    def _addElementToCondition(self, symbol: str, checked: bool) -> None:
        index = self.linesDataframe.query(f"symbol == '{symbol}'").index
        for i in index:
            self.linesDataframe.at[i, "active"] = int(checked)
            self.linesDataframe.at[i, "condition_id"] = int(
                self._conditionTable.item(self._conditionTable.currentRow(), 0)
                .text()
                .split(" ")[-1]
            ) if checked else nan

    def _createConditionTable(self) -> QtWidgets.QTableWidget:
        self._conditionTable = ConditionTableWidget(self, self.conditionsDataFrame, self.linesDataframe)
        return self._conditionTable


class ConditionTableWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None, conditionsDataFrame: pd.DataFrame = None, linesDataframe: pd.DataFrame = None):
        super(ConditionTableWidget, self).__init__(parent)
        self.conditionsDataFrame = conditionsDataFrame
        self.linesDataframe = linesDataframe

        self.setObjectName("condition-table")
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        # self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)

        self._setHeaders()
        self._setUpTable()
        self.selectCondition(1)

        self.cellClicked.connect(self._cellClicked)

    def _setHeaders(self) -> None:
        labels = self.conditionsDataFrame.columns.str.title()
        self.setColumnCount(self.conditionsDataFrame.shape[1])
        self.setHorizontalHeaderLabels(labels)

    def _setUpTable(self) -> None:
        self.setRowCount(self.conditionsDataFrame.shape[0])
        for rowIndex, row in enumerate(self.conditionsDataFrame.itertuples(index=False)):
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
        symbols = self.linesDataframe.query(f"condition_id == {conditionId} and active == 1")['symbol'].values
        for symbol, button in self.parent().buttonMap.items():
            button.blockSignals(True)
            button.setChecked(symbol in symbols)
            button.blockSignals(False)
    
    def selectCondition(self, conditionId: int) -> None:
        self.selectRow(conditionId - 1)
        self._toggleConditionElements(conditionId)
