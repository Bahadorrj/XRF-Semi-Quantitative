from functools import partial

from PyQt6 import QtCore, QtWidgets
from numpy import nan

from python.utils import datatypes
from python.views.base.tablewidget import DataframeTableWidget


class AnalytesAndConditionsWidget(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
        editable: bool = False,
    ):
        super(AnalytesAndConditionsWidget, self).__init__(parent)
        self._method = method
        self._editable = editable
        self.buttonsMap = {}
        self._initializeUi()
        if self._method is not None:
            self._conditionTable.reinitialize(self._method.conditions)
            self._connectSignalsAndSlots()
            self._conditionTable.setCurrentCell(0, 0)

    def _resetClassVariables(self, method: datatypes.Method):
        self._method = method

    def _initializeUi(self) -> None:
        self.setObjectName("analyte-widget")
        self._createPeriodicLayout()
        self._createConditionTable()
        self._setUpView()

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(30, 30, 30, 30)
        self.mainLayout.setSpacing(30)
        self.mainLayout.addLayout(self._periodicTableLayout)
        self.mainLayout.addWidget(self._conditionTable)
        self.setLayout(self.mainLayout)

    def _connectSignalsAndSlots(self) -> None:
        for symbol, button in self.buttonsMap.items():
            button.toggled.connect(partial(self._addElementToCondition, symbol))
        self._conditionTable.currentCellChanged.connect(self._currentCellChanged)

    def _createPeriodicLayout(self) -> None:
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
                    button = QtWidgets.QPushButton(symbol)
                    button.setCheckable(True)
                    if self._editable is False:
                        button.setDisabled(True)
                    button.setSizePolicy(
                        QtWidgets.QSizePolicy.Policy.Fixed,
                        QtWidgets.QSizePolicy.Policy.Fixed,
                    )
                    layout.addWidget(button)
                    if symbol not in ["L", "A"]:
                        self.buttonsMap[symbol] = button
                    else:
                        button.setDisabled(True)
                        button.setStyleSheet(
                            "background-color: #F5F5F5; color: #FE7099; border: 2px inset #CB0E44; font-weight: bold"
                        )
                else:
                    layout.addStretch() if len(row) > 1 else vLayout.addSpacing(30)
            vLayout.addLayout(layout)
        self._periodicTableLayout = QtWidgets.QHBoxLayout()
        self._periodicTableLayout.setContentsMargins(0, 0, 0, 0)
        self._periodicTableLayout.addStretch()
        self._periodicTableLayout.addLayout(vLayout)
        self._periodicTableLayout.addStretch()

    @QtCore.pyqtSlot(bool)
    def _addElementToCondition(self, symbol: str, checked: bool) -> None:
        index = self._method.elements.query(f"symbol == '{symbol}'").index
        for i in index:
            self._method.elements.at[i, "active"] = int(checked)
            self._method.elements.at[i, "condition_id"] = (
                int(
                    self._conditionTable.item(self._conditionTable.currentRow(), 0)
                    .text()
                    .split(" ")[-1]
                )
                if checked
                else nan
            )

    def _createConditionTable(self) -> None:
        self._conditionTable = DataframeTableWidget(autofill=True)
        self._conditionTable.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self._conditionTable.verticalHeader().setVisible(False)

    @QtCore.pyqtSlot(int, int, int, int)
    def _currentCellChanged(
        self, currentRow: int, currentColumn: int, previousRow: int, previousColumn: int
    ) -> None:
        conditionId = int(
            self._conditionTable.item(currentRow, 0).text().split(" ")[-1]
        )
        self._toggleConditionElements(conditionId)

    def _toggleConditionElements(self, conditionId: int) -> None:
        symbols = self._method.elements.query(
            f"condition_id == {conditionId} and active == 1"
        )["symbol"].values
        for symbol, button in self.buttonsMap.items():
            button.blockSignals(True)
            button.setChecked(symbol in symbols)
            button.blockSignals(False)

    def setFocus(self):
        self._conditionTable.setFocus()

    def reinitialize(self, method: datatypes.Method) -> None:
        self.blockSignals(True)
        self._resetClassVariables(method)
        self._conditionTable.reinitialize(method.conditions)
        self._connectSignalsAndSlots()
        self.blockSignals(False)
        self._conditionTable.setCurrentCell(0, 0)
