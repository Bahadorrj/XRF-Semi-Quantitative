import pandas as pd

from functools import partial

from PyQt6 import QtCore, QtWidgets, QtGui
from numpy import nan

from src.utils import datatypes
from src.utils.paths import resourcePath

from src.views.base.tablewidget import DataframeTableWidget, TableItem

from src.views.method.conditionfomrdialog import ConditionFormDialog


class AnalytesAndConditionsWidget(QtWidgets.QWidget):
    """
    Initializes an instance of the AnalytesAndConditionsWidget class.

    This widget is designed to manage and display analytes and conditions in a user interface. It can be configured to be editable and to automatically fill in data based on the provided method.

    Args:
        parent (QtWidgets.QWidget | None): The parent widget for this widget, or None if there is no parent.
        method (datatypes.Method | None): An optional method to supply to the widget upon initialization.
        autoFill (bool): A flag indicating whether the widget should automatically fill in data. Defaults to False.
        editable (bool): A flag indicating whether the widget should allow user edits. Defaults to False.

    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
        editable: bool = False,
    ):
        super(AnalytesAndConditionsWidget, self).__init__(parent)
        self._method = None
        self._conditions = None
        self._editable = editable
        self._buttonsMap = {}
        self._initializeUi()
        if method is not None:
            self.supply(method)
        self.hide()

    def _initializeUi(self) -> None:
        self.setObjectName("analyte-widget")
        if self._editable:
            self._createActions(
                {
                    "Add": False,
                    "Edit": True,
                    "Remove": True,
                }
            )
            self._createToolBar()
        self._createPeriodicLayout()
        self._createConditionTable()
        self._setUpView()

    def _createActions(self, labels: dict) -> None:
        self._actionsMap = {}
        shortcuts = {"add": QtGui.QKeySequence("Ctrl+=")}
        for label, disabled in labels.items():
            action = QtGui.QAction(label, self)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"resources/icons/{key}.png")))
            action.setDisabled(disabled)
            self._actionsMap[key] = action
            if shortcut := shortcuts.get(key):
                action.setShortcut(shortcut)
            action.triggered.connect(partial(self._actionTriggered, key))

    @QtCore.pyqtSlot(str)
    def _actionTriggered(self, key: str) -> None:
        if key == "add":
            self._addCondition()
        elif key == "edit":
            self._editCurrentCondition()
        else:
            self._removeCurrentCondition()

    def _addCondition(self) -> None:
        addDialog = ConditionFormDialog(self, inputs=self._conditions.columns[1:])
        addDialog.setWindowTitle("Add condition")
        if addDialog.exec():
            fields = addDialog.fields
            fields["condition_id"] = max(self._conditions["condition_id"].values) + 1
            tableRow = {
                k: TableItem(fields[k], editable=self._editable) for k in fields
            }
            row = pd.DataFrame(fields, index=[0])
            self._conditions.loc[len(self._conditions)] = row.iloc[0]
            self._conditionTable.addRow(tableRow)

    def _editCurrentCondition(self) -> None:
        editDialog = ConditionFormDialog(
            self,
            inputs=self._conditions.columns[1:],
            values=self._conditions.iloc[self._conditionTable.currentRow()][
                1:
            ].tolist(),
            previousConditionName=self._conditions.at[
                self._conditionTable.currentRow(), "name"
            ],
        )
        editDialog.setWindowTitle("Edit condition")
        if editDialog.exec():
            fields = editDialog.fields
            tableRow = self._conditionTable.getCurrentRow()
            for column in self._conditions.columns[1:]:
                self._conditionTable.getCurrentRow()[column].setText(fields[column])
                if column in ["kilovolt", "milliampere"]:
                    value = float(fields[column])
                elif column in ["time", "filter", "mask"]:
                    value = int(fields[column])
                elif column in ["rotation", "active"]:
                    value = 0 if fields[column] == "False" else 1
                else:
                    value = fields[column]
                self._conditions.at[self._conditionTable.currentRow(), column] = value
                tableRow[column].setText(fields[column])
                (
                    tableRow["active"].setForeground(QtCore.Qt.GlobalColor.darkGreen)
                    if fields["active"] == "True"
                    else tableRow["active"].setForeground(QtCore.Qt.GlobalColor.red)
                )
                (
                    tableRow["rotation"].setForeground(QtCore.Qt.GlobalColor.darkGreen)
                    if fields["rotation"] == "True"
                    else tableRow["rotation"].setForeground(QtCore.Qt.GlobalColor.red)
                )

    def _removeCurrentCondition(self) -> None:
        if self._conditionTable.currentRow() == -1:
            return
        rowId = self._conditions.query(
            f"name == '{self._conditionTable.item(self._conditionTable.currentRow(), 0).text()}'"
        ).index.values[0]
        self._conditions.drop(rowId, inplace=True)
        self._conditionTable.removeRow(self._conditionTable.currentRow())
        if self._conditionTable.rowCount() == 0:
            self._actionsMap["edit"].setDisabled(True)
            self._actionsMap["remove"].setDisabled(True)

    def _createPeriodicLayout(self) -> None:
        # fmt: off
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
                    button.setObjectName("periodic-button")
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
        # fmt: on

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

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar(self)
        self._toolBar.setIconSize(QtCore.QSize(16, 16))
        self._toolBar.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self._toolBar.setMovable(False)
        self._fillToolBarWithActions()

    def _fillToolBarWithActions(self) -> None:
        for action in self._actionsMap.values():
            self._toolBar.addAction(action)

    def _createConditionTable(self) -> None:
        self._conditionTable = DataframeTableWidget(self, autoFill=True, editable=False)
        self._conditionTable.setMinimumWidth(900)
        self._conditionTable.setMaximumWidth(1200)
        self._conditionTable.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self._conditionTable.verticalHeader().setVisible(False)
        self._conditionTable.cellClicked.connect(self._cellClicked)

    @QtCore.pyqtSlot(int, int)
    def _cellClicked(self, row: int, column: int) -> None:
        if (
            df := (
                self._conditions.query(
                    f"name == '{self._conditionTable.item(row, 0).text()}'"
                )
            )
        ).empty is False:
            conditionId = df["condition_id"].values[0]
            self._toggleConditionElements(conditionId)

    def _isItemValid(self, item) -> tuple:
        value = item.text()
        if self._conditionTable.currentColumn() == 0:
            return (self.isConditionNameValid(value), value)
        if self._conditionTable.currentColumn() == 1:
            return (self.isKiloVoltValid(value), float(value))
        if self._conditionTable.currentColumn() == 2:
            return (self.isMilliAmpereValid(value), float(value))
        if self._conditionTable.currentColumn() == 3:
            return (self.isTimeValid(value), int(value))
        if self._conditionTable.currentColumn() == 5:
            return (self.isEnvironmentValid(value), value)
        if self._conditionTable.currentColumn() == 6:
            return (self.isFilterValid(value), int(value))
        if self._conditionTable.currentColumn() == 7:
            return (self.isMaskValid(value), int(value))
        return (False, value)

    def isConditionNameValid(self, value: str) -> bool:
        return value not in self._conditions["name"].values

    def isKiloVoltValid(self, value: str) -> bool:
        try:
            return 0 < float(value) <= 40
        except ValueError:
            return False

    def isMilliAmpereValid(self, value: str) -> bool:
        try:
            return 0 < float(value) <= 1
        except ValueError:
            return False

    def isTimeValid(self, value: str) -> bool:
        try:
            return 0 < int(value) <= 240
        except ValueError:
            return False

    def isEnvironmentValid(self, value: str) -> bool:
        return True

    def isFilterValid(self, value: str) -> bool:
        try:
            return 0 <= int(value) <= 3
        except ValueError:
            return False

    def isMaskValid(self, value: str) -> bool:
        try:
            return 0 <= int(value) <= 3
        except ValueError:
            return False

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
        self.mainLayout.addLayout(self._periodicTableLayout)
        self.mainLayout.addSpacing(30)
        if self._editable:
            self.mainLayout.addWidget(self._toolBar)
        self.mainLayout.addWidget(self._conditionTable)
        hLayout = QtWidgets.QHBoxLayout()
        hLayout.addStretch()
        hLayout.addLayout(self.mainLayout)
        hLayout.addStretch()
        self.setLayout(hLayout)

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
        if method is None:
            return
        if self._method and self._method == method:
            return
        if self._editable:
            self._actionsMap["edit"].setDisabled(False)
            self._actionsMap["remove"].setDisabled(False)
        self.blockSignals(True)
        self._method = method
        self._conditions = self._method.conditions
        self._conditionTable.supply(self._conditions.drop("condition_id", axis=1))
        self.blockSignals(False)

    @property
    def buttonsMap(self):
        return self._buttonsMap

    @property
    def editable(self):
        return self._editable
