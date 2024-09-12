from functools import partial

from PyQt6 import QtCore, QtWidgets
from numpy import nan

from src.utils import datatypes
from src.views.base.tablewidget import DataframeTableWidget


class AnalytesAndConditionsWidget(QtWidgets.QWidget):
    """Widget for displaying analytes and their associated conditions.

    This class provides a user interface for selecting analytes and managing their conditions through a periodic table layout and a condition table. It allows for interaction with the analytes, enabling users to add or modify conditions based on the selected elements.

    Args:
        parent (QtWidgets.QWidget | None): An optional parent widget.
        method (datatypes.Method | None): An optional method to initialize the widget with.
        editable (bool): A flag indicating whether the widget is editable.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
        editable: bool = False,
    ):
        super(AnalytesAndConditionsWidget, self).__init__(parent)
        self._method = None
        self._editable = editable
        self._buttonsMap = {}
        self._initializeUi()
        if method is not None:
            self.supply(method)

    def _initializeUi(self) -> None:
        self.setObjectName("analyte-widget")
        self._createPeriodicLayout()
        self._createConditionTableLayout()
        self._setUpView()

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
                    else:
                        button.toggled.connect(
                            partial(self._addElementToCondition, symbol)
                        )
                    button.setSizePolicy(
                        QtWidgets.QSizePolicy.Policy.Fixed,
                        QtWidgets.QSizePolicy.Policy.Fixed,
                    )
                    layout.addWidget(button)
                    if symbol not in ["L", "A"]:
                        self._buttonsMap[symbol] = button
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

    def _createConditionTableLayout(self) -> None:
        self._conditionTable = DataframeTableWidget(autofill=True)
        self._conditionTable.setMinimumWidth(900)
        self._conditionTable.setMaximumWidth(1200)
        self._conditionTable.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self._conditionTable.verticalHeader().setVisible(False)
        self._conditionTable.currentCellChanged.connect(self._currentCellChanged)
        self._conditionTableLayout = QtWidgets.QHBoxLayout()
        self._conditionTableLayout.setContentsMargins(0, 0, 0, 0)
        self._conditionTableLayout.addStretch()
        self._conditionTableLayout.addWidget(self._conditionTable)
        self._conditionTableLayout.addStretch()

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
        for symbol, button in self._buttonsMap.items():
            button.blockSignals(True)
            button.setChecked(symbol in symbols)
            button.blockSignals(False)

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(30, 30, 30, 30)
        self.mainLayout.setSpacing(30)
        self.mainLayout.addLayout(self._periodicTableLayout)
        self.mainLayout.addLayout(self._conditionTableLayout)
        self.setLayout(self.mainLayout)

    def setFocus(self):
        self._conditionTable.setFocus()

    def supply(self, method: datatypes.Method) -> None:
        """Supply data to the widget from a given method.

        This function updates the internal method reference and populates the condition table with the method's conditions. It temporarily blocks signals to prevent unnecessary updates during the data supply process and sets the current cell of the condition table to the first row.

        Args:
            self: The instance of the class.
            method (datatypes.Method): The method containing conditions to supply.

        Returns:
            None
        """
        self.blockSignals(True)
        self._method = method
        self._conditionTable.supply(method.conditions.drop("condition_id", axis=1))
        self.blockSignals(False)
        self._conditionTable.setCurrentCell(0, 0)

    @property
    def buttonsMap(self):
        return self._buttonsMap

    @property
    def editable(self):
        return self._editable
