import os

import pandas
from PyQt6 import QtCore, QtWidgets

from python.utils.database import getDataframe, getDatabase, reloadDataframes
from python.utils.datatypes import Method
from python.views.base.formdialog import FormDialog
from python.views.base.tablewidget import TableItem
from python.views.base.traywidget import TrayWidget
from python.views.widgets.analytewidget import AnalytesAndConditionsWidget
from python.views.widgets.calibrationwidget import CalibrationWidget


class MethodFormDialog(FormDialog):
    def __init__(self,
                 parent: QtWidgets.QWidget | None = None,
                 inputs: list | tuple | None = None,
                 values: list | tuple | None = None) -> None:
        super(MethodFormDialog, self).__init__(parent, inputs, values)

    def _fill(self, lineEdit: QtWidgets.QLineEdit, key: str) -> None:
        if key == "filename":
            methodPath = f"methods/{lineEdit.text()}.atxm"
            if os.path.exists(methodPath):
                self._errorLabel.setText("This filename already exists!")
        super()._fill(lineEdit, key)


class MethodTrayWidget(TrayWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None, dataframe: pandas.DataFrame | None = None) -> None:
        super().__init__(parent)
        self._df = dataframe
        self._method = None
        self._widgets = None
        self._initializeUi()
        if self._df is not None:
            self._tableWidget.reinitialize(self._df.drop("method_id", axis=1))
            self._connectSignalsAndSlots()
            if self._df.empty is False:
                self._tableWidget.setCurrentCell(0, 0)

    def _initializeUi(self) -> None:
        self.setWindowTitle("Method Tray List")
        self.setObjectName("tray-list")
        self._createActions({
            "Add": False,
            "Remove": True,
            "Close": False,
            "Print": True,
            "Print Preview": True,
            "Print Setup": True,
            "Edit": True,
            "Import": False
        })
        self._createMenus(("&File", "&Edit", "&View", "&Window", "&Help"))
        self._fillMenusWithActions()
        self._createToolBar()
        self._fillToolBarWithActions()
        self._createTableWidget()
        self._createTabWidget()
        self._setUpView()

    def _resetClassVariables(self, dataframe: pandas.DataFrame) -> None:
        self._df = dataframe

    @QtCore.pyqtSlot(str)
    def _actionTriggered(self, action: str) -> None:
        if action == "add":
            self._addMethod()
        elif action == "edit":
            if self._method.state == 0:
                self._editMethod()
            else:
                self._openMethodExplorer()
        elif action == "remove":
            self._removeMethod()
        elif action == "import":
            self._importMethod()

    def _addMethod(self) -> None:
        addDialog = MethodFormDialog(inputs=self._df.columns[1:-1])
        if addDialog.exec():
            filename = addDialog.fields["filename"]
            description = addDialog.fields["description"]
            self._method = Method(filename, description)
            self._method.save()
            self._insertMethod()
            self._actionsMap["edit"].setDisabled(False)

    def _insertMethod(self) -> None:
        filename = self._method.filename
        description = self._method.description
        state = self._method.state
        status = self._method.status()
        getDatabase().executeQuery(
            f"INSERT INTO Methods (filename, description, state) VALUES (?, ?, ?)",
            (filename, description, state)
        )
        reloadDataframes()
        self._resetClassVariables(getDataframe("Methods"))
        items = {
            "filename": TableItem(filename),
            "description": TableItem(description),
            "status": TableItem(status)
        }
        self._tableWidget.addRow(items)
        self._tableWidget.setCurrentCell(self._tableWidget.rowCount() - 1, 0)

    def _editMethod(self) -> None:
        previousFilename = self._tableWidget.getCurrentRow()["filename"].text()
        previousDescription = self._tableWidget.getCurrentRow()["description"].text()
        editDialog = MethodFormDialog(
            inputs=self._df.columns[1:-1],
            values=(previousFilename, previousDescription)
        )
        if editDialog.exec():
            filename = editDialog.fields["filename"]
            description = editDialog.fields["description"]
            self._method.filename = filename
            self._method.description = description
            self._method.save()
            self._tableWidget.getCurrentRow()["filename"].setText(filename)
            self._tableWidget.getCurrentRow()["description"].setText(description)
            getDatabase().executeQuery(
                f"UPDATE Methods "
                f"SET filename = '{filename}', description = '{description}' "
                f"WHERE filename = '{previousFilename}'"
            )
            reloadDataframes()
            self._resetClassVariables(getDataframe("Methods"))

    def _openMethodExplorer(self) -> None:
        if self._method is not None:
            pass

    def _removeMethod(self) -> None:
        # Ask the user if they are sure to remove the calibration
        messageBox = QtWidgets.QMessageBox()
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        messageBox.setText("Are you sure you want to remove the selected method?")
        messageBox.setWindowTitle("Remove Method")
        messageBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            filename = self._method.filename
            os.remove(f"methods/{filename}.atxm")
            getDatabase().executeQuery("DELETE FROM Methods WHERE filename = ?", (filename,))
            reloadDataframes()
            self._resetClassVariables(getDataframe("Methods"))
            self._tableWidget.removeRow(self._tableWidget.currentRow())

    def _importMethod(self) -> None:
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open Method",
            "./",
            "Antique'X method (*.atxm)"
        )
        if filePath:
            pass

    def _fillMenusWithActions(self) -> None:
        self._menusMap["file"].addAction(self._actionsMap["import"])
        self._menusMap["file"].addSeparator()
        self._menusMap["file"].addAction(self._actionsMap["print"])
        self._menusMap["file"].addAction(self._actionsMap["print-preview"])
        self._menusMap["file"].addAction(self._actionsMap["print-setup"])
        self._menusMap["file"].addSeparator()
        self._menusMap["file"].addAction(self._actionsMap["close"])

        self._menusMap["edit"].addAction(self._actionsMap["add"])
        self._menusMap["edit"].addAction(self._actionsMap["edit"])
        self._menusMap["edit"].addAction(self._actionsMap["remove"])

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar()
        self._toolBar.setIconSize(QtCore.QSize(16, 16))
        self._toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self._toolBar.setMovable(False)
        self._fillToolBarWithActions()

    def _fillToolBarWithActions(self) -> None:
        self._toolBar.addAction(self._actionsMap["import"])
        self._toolBar.addAction(self._actionsMap["add"])
        self._toolBar.addSeparator()
        self._toolBar.addAction(self._actionsMap["edit"])
        self._toolBar.addSeparator()
        self._toolBar.addAction(self._actionsMap["remove"])

    def _currentCellChanged(self, currentRow: int, currentColumn: int, previousRow: int, previousColumn: int):
        """Called when the current cell in the table changes."""
        if currentRow != previousRow and currentRow != -1:
            if self._widgets:
                self._widgets.clear()
                self._tabWidget.clear()
            tableRow = self._tableWidget.getRow(currentRow)
            filename = tableRow.get("filename").text()
            path = f"methods/{filename}.atxm"
            self._method = Method.fromATXMFile(path)
            self._actionsMap["edit"].setDisabled(False)
            self._actionsMap["remove"].setDisabled(False)
            self._addMethodWidgets()
        elif currentRow == -1:
            self._widgets.clear()
            self._tabWidget.clear()
            self._method = None
            self._actionsMap["edit"].setDisabled(True)
            self._actionsMap["remove"].setDisabled(True)

    def _addMethodWidgets(self) -> None:
        self._addWidgets(
            {
                "Analytes And Conditions": AnalytesAndConditionsWidget(method=self._method),
                "Calibrations": CalibrationWidget(method=self._method),
            }
        )
        for widget in self._widgets.values():
            widget.mainLayout.setContentsMargins(10, 10, 10, 10)
