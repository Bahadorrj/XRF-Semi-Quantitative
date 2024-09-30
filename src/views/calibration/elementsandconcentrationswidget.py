from functools import partial
from typing import Sequence
from PyQt6 import QtCore, QtWidgets, QtGui

from src.views.base.tablewidget import TableWidget, TableItem
from src.views.base.formdialog import FormDialog
from src.utils import datatypes
from src.utils.paths import resourcePath
from src.utils.database import getDataframe


class ElementAndConcentrationFormDialog(FormDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        inputs: Sequence | None = None,
        values: Sequence | None = None,
        concentrations: dict | None = None,
        edit: bool = False,
    ) -> None:
        super().__init__(parent, inputs, values)
        self._concentrations = concentrations
        self._edit = edit

    def _check(self) -> None:
        self._fill()
        self._errorLabel.clear()
        if not all(
            (
                self._isElementValid(),
                self._isConcentrationValid(),
            )
        ):
            QtWidgets.QApplication.beep()
            return
        return super()._check()

    def _isElementValid(self) -> bool:
        elementLineEdit = self._fields["element"][-1]
        element = elementLineEdit.text()
        elementLineEdit.setStyleSheet("color: red;")
        if element not in getDataframe("Elements")["symbol"].values:
            self._addError("This element is not valid!\n")
            return False
        if not self._edit and element in self._concentrations:
            self._addError("This element is already in the list!\n")
            return False
        if element == "":
            self._addError("Please enter an element!\n")
            return False
        elementLineEdit.setStyleSheet("color: black;")
        return True

    def _isConcentrationValid(self) -> bool:
        concentrationLineEdit = self._fields["concentration"][-1]
        concentration = concentrationLineEdit.text()
        concentrationLineEdit.setStyleSheet("color: red;")
        if concentration == "":
            self._addError("Please enter a concentration!\n")
            return False
        if (
            not self._edit
            and (total := sum(self._concentrations.values())) + float(concentration)
            > 100
        ):
            self._addError(
                f"The total concentrations cannot exceed 100! current sum is {total}\n"
            )
            return False
        if not 0 <= float(concentration) <= 100:
            self._addError("This concentration is not valid!\n")
            return False
        concentrationLineEdit.setStyleSheet("color: black;")
        return True


class ElementsAndConcentrationsWidget(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        calibration: datatypes.Calibration | None = None,
        editable: bool = False,
    ) -> None:
        super().__init__(parent)

        self._calibration = None
        self._editable = editable
        self._actionsMap = {}
        self._initializeUi()
        if calibration is not None:
            self.supply(calibration)

    def _initializeUi(self) -> None:
        self.setObjectName("elements-and-concentrations-widget")
        if self._editable:
            self._createActions(
                {
                    "Add": False,
                    "Remove": False,
                    "Edit": False,
                }
            )
            self._createToolBar()
            self._fillToolBarWithActions()
        self._createTableWidget()
        self._setUpView()

    def _createActions(self, labels: dict) -> None:
        for label, disabled in labels.items():
            action = QtGui.QAction(label, self)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"resources/icons/{key}.png")))
            action.setDisabled(disabled)
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))

    @QtCore.pyqtSlot(str)
    def _actionTriggered(self, key: str) -> None:
        if key == "add":
            self._addConcentration()
        elif key == "edit":
            self._editCurrentConcentration()
        else:
            self._removeCurrentConcentration()

    def _addConcentration(self) -> None:
        addDialog = ElementAndConcentrationFormDialog(
            self,
            inputs=["element", "concentration"],
            concentrations=self._calibration.concentrations,
        )
        addDialog.setWindowTitle("Add concentration")
        if addDialog.exec():
            element = addDialog.fields["element"]
            concentration = round(float(addDialog.fields["concentration"]), 1)
            self._calibration.concentrations[element] = concentration
            self._insertConcentration(element, concentration)

    def _editCurrentConcentration(self) -> None:
        currentRow = self._tableWidget.getCurrentRow()
        element = currentRow["element"].text()
        concentration = float(currentRow["concentration"].text())
        editDialog = ElementAndConcentrationFormDialog(
            self,
            inputs=["element", "concentration"],
            values=[element, concentration],
            concentrations=self._calibration.concentrations,
            edit=True,
        )
        editDialog.setWindowTitle("Edit concentration")
        if editDialog.exec():
            element = editDialog.fields["element"]
            concentration = round(float(editDialog.fields["concentration"]), 1)
            self._calibration.concentrations[element] = concentration
            currentRow["element"].setText(element)
            currentRow["concentration"].setText(f"{concentration}")

    def _removeCurrentConcentration(self) -> None:
        messageBox = QtWidgets.QMessageBox(self)
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        messageBox.setText(
            "Are you sure you want to remove the selected concentration?"
        )
        messageBox.setWindowTitle("Remove Concentration")
        messageBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            tableRow = self._tableWidget.getCurrentRow()
            self._calibration.concentrations.pop(tableRow["element"].text())
            self._tableWidget.removeRow(self._tableWidget.currentRow())

    def _insertConcentration(self, element: str, concentration: float) -> None:
        items = {
            "element": TableItem(element),
            "concentration": TableItem(f"{concentration:.1f}"),
        }
        self._tableWidget.addRow(items)

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar(self)
        self._toolBar.setIconSize(QtCore.QSize(16, 16))
        self._toolBar.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self._toolBar.setMovable(False)
        self._fillToolBarWithActions()

    def _fillToolBarWithActions(self) -> None:
        self._toolBar.addAction(self._actionsMap["add"])
        self._toolBar.addAction(self._actionsMap["edit"])
        self._toolBar.addAction(self._actionsMap["remove"])

    def _createTableWidget(self) -> None:
        self._tableWidget = TableWidget(self)
        self._tableWidget.verticalHeader().setVisible(False)
        self._tableWidget.setHeaders(["Element", "Concentration"])

    def _fillTable(self) -> None:
        self._tableWidget.resetTable()
        for element, concentration in self._calibration.concentrations.items():
            items = {
                "element": TableItem(element),
                "concentration": TableItem(f"{concentration:.1f}"),
            }
            self._tableWidget.addRow(items)

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(10)
        if self._editable:
            self.mainLayout.addWidget(self._toolBar)
        self.mainLayout.addWidget(self._tableWidget)
        self.setLayout(self.mainLayout)

    def supply(self, calibration: datatypes.Calibration) -> None:
        self.blockSignals(True)
        self._calibration = calibration
        self._fillTable()
        self.blockSignals(False)
