import os
from pathlib import Path

import pandas
from PyQt6 import QtCore, QtWidgets

from python.utils.database import getDataframe, getDatabase, reloadDataframes
from python.utils.datatypes import Calibration, Analyse
from python.views.base.formdialog import FormDialog
from python.views.base.tablewidget import TableItem
from python.views.base.traywidget import TrayWidget
from python.views.explorers.calibrationexplorer import CalibrationExplorer
from python.views.widgets.coefficientwidget import CoefficientWidget
from python.views.widgets.generaldatawidget import GeneralDataWidget
from python.views.widgets.linestablewidget import LinesTableWidget


class CalibrationFormDialog(FormDialog):
    def __init__(self,
                 parent: QtWidgets.QWidget | None = None,
                 inputs: list | tuple | None = None,
                 values: list | tuple | None = None) -> None:
        super(CalibrationFormDialog, self).__init__(parent, inputs, values)

    def _fill(self, lineEdit: QtWidgets.QLineEdit, key: str) -> None:
        if key == "filename":
            calibrationPath = f"calibrations/{lineEdit.text()}.atxc"
            if os.path.exists(calibrationPath):
                self._errorLabel.setText("This filename already exists!")
        if key == "element":
            if not lineEdit.text() in getDataframe("Lines")["symbol"].values:
                lineEdit.setStyleSheet("color: red;")
                self._errorLabel.setText("Invalid element!")
                return
        elif key == "concentration":
            if not 0 <= float(lineEdit.text()) <= 100:
                lineEdit.setStyleSheet("color: red;")
                self._errorLabel.setText("Concentration must be between 0 and 100!")
                return
        lineEdit.setStyleSheet("color: black;")
        self._errorLabel.setText(None)
        return super()._fill(lineEdit, key)


class CalibrationTrayWidget(TrayWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None, dataframe: pandas.DataFrame | None = None) -> None:
        super().__init__(parent)
        self._df = dataframe
        self._calibration = None
        self._widgets = None
        self._initializeUi()
        if self._df is not None:
            self._tableWidget.reinitialize(self._df.drop("calibration_id", axis=1))
            self._connectSignalsAndSlots()
            if self._df.empty is False:
                self._tableWidget.setCurrentCell(0, 0)

    def _initializeUi(self) -> None:
        self.setWindowTitle("Calibration Tray List")
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
            self._addCalibration()
        elif action == "edit":
            if self._calibration.state == 0:
                self._editCalibration()
            else:
                self._openCalibrationExplorer()
        elif action == "remove":
            self._removeCalibration()
        elif action == "import":
            self._importCalibration()

    def _addCalibration(self) -> None:
        # Ask the user for the filename, element, concentration and create a new calibration
        addDialog = CalibrationFormDialog(inputs=self._df.columns[1:-1])
        addDialog.setWindowTitle("Add calibration")
        if addDialog.exec():
            filename = addDialog.fields["filename"]
            element = addDialog.fields["element"]
            concentration = float(addDialog.fields["concentration"])
            # Find the default radiation type for the element
            if not getDataframe("Lines").query(f"symbol == '{element}' and active == 1").empty:
                self._calibration = Calibration(filename, element, concentration)
                self._calibration.save()
                # Insert the calibration into the database
                self._insertCalibration()

    def _insertCalibration(self) -> None:
        filename = self._calibration.filename
        element = self._calibration.element
        concentration = self._calibration.concentration
        state = self._calibration.state
        status = self._calibration.status()
        getDatabase().executeQuery(
            "INSERT INTO Calibrations (filename, element, concentration, state) VALUES (?, ?, ?, ?)",
            (filename, element, concentration, state)
        )
        reloadDataframes()
        self._resetClassVariables(getDataframe("Calibrations"))
        items = {
            "filename": TableItem(filename),
            "element": TableItem(element),
            "concentration": TableItem(f"{concentration:.1f}"),
            "status": TableItem(status)
        }
        self._tableWidget.addRow(items)
        self._tableWidget.setCurrentCell(self._tableWidget.rowCount() - 1, 0)

    def _editCalibration(self) -> None:
        previousFilename = self._tableWidget.getCurrentRow()["filename"].text()
        previousElement = self._tableWidget.getCurrentRow()["element"].text()
        previousConcentration = self._tableWidget.getCurrentRow()["concentration"].text()
        editDialog = CalibrationFormDialog(
            inputs=self._df.columns[1:-1],
            values=(previousFilename, previousElement, previousConcentration)
        )
        editDialog.setWindowTitle("Edit calibration")
        if editDialog.exec():
            filename = editDialog.fields["filename"]
            element = editDialog.fields["element"]
            concentration = float(editDialog.fields["concentration"])
            # Find the default radiation type for the element
            if not getDataframe("Lines").query(f"symbol == '{element}' and active == 1").empty:
                self._calibration.filename = filename
                self._calibration.element = element
                self._calibration.concentration = concentration
                self._calibration.save()
                self._tableWidget.getCurrentRow()["filename"].setText(filename)
                self._tableWidget.getCurrentRow()["element"].setText(element)
                self._tableWidget.getCurrentRow()["concentration"].setText(f"{concentration:.1f}")
                getDatabase().executeQuery(
                    f"UPDATE Calibrations "
                    f"SET filename = '{filename}', element = '{element}', concentration = {concentration} "
                    f"WHERE filename = '{previousFilename}'"
                )
                reloadDataframes()
                self._resetClassVariables(getDataframe("Calibrations"))

    def _openCalibrationExplorer(self) -> None:
        if self._calibration is not None:
            calibrationExplorer = CalibrationExplorer(calibration=self._calibration)
            calibrationExplorer.show()

    def _removeCalibration(self) -> None:
        # Ask the user if they are sure to remove the calibration
        message_box = QtWidgets.QMessageBox()
        message_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        message_box.setText("Are you sure you want to remove the selected calibration?")
        message_box.setWindowTitle("Remove Calibration")
        message_box.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        message_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        if message_box.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            filename = self._tableWidget.getRow(self._tableWidget.currentRow())["filename"].text()
            os.remove(f"calibrations/{filename}.atxc")
            self._calibration = None
            getDatabase().executeQuery("DELETE FROM Calibrations WHERE filename = ?", (filename,))
            reloadDataframes()
            self._resetClassVariables(getDataframe("Calibrations"))
            self._tableWidget.removeRow(self._tableWidget.currentRow())

    def _importCalibration(self) -> None:
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open Calibration",
            "./",
            "Antique'X calibration (*.atxc)"
        )
        if filePath:
            self._calibration = Calibration.fromATXCFile(filePath)
            filename = Path(filePath).stem
            if self._df.query(f"filename == '{filename}'").empty:
                self._insertCalibration()
            else:
                messageBox = QtWidgets.QMessageBox()
                messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                messageBox.setText("The selected calibration already exists in the database.")
                messageBox.setWindowTitle("Import Calibration Failed")
                messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
                messageBox.exec()

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
            path = f"./calibrations/{filename}.atxc"
            self._calibration = Calibration.fromATXCFile(path)
            self._actionsMap["edit"].setDisabled(False)
            self._actionsMap["remove"].setDisabled(False)
            if self._calibration.state == 0:
                self._addAcquisitionWidget()
            else:
                self._addCalibrationWidgets()
        elif currentRow == -1:
            self._widgets.clear()
            self._tabWidget.clear()
            self._calibration = None

    def _addAcquisitionWidget(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        hLayout = QtWidgets.QHBoxLayout()
        hLayout.addStretch()
        openFromLocalButton = QtWidgets.QPushButton("Open from local storage")
        openFromLocalButton.clicked.connect(self._getAnalyseFile)
        hLayout.addWidget(openFromLocalButton)
        hLayout.addStretch()
        getFromSocketButton = QtWidgets.QPushButton("Get from connected XRF analyser")
        hLayout.addWidget(getFromSocketButton)
        hLayout.addStretch()
        layout.addStretch()
        layout.addLayout(hLayout)
        layout.addStretch()
        widget.setLayout(layout)
        self._addWidgets({"Acquisition": widget})

    def _addCalibrationWidgets(self):
        self._addWidgets(
            {
                "General Data": GeneralDataWidget(calibration=self._calibration),
                "Coefficient": CoefficientWidget(calibration=self._calibration),
                "Lines": LinesTableWidget(calibration=self._calibration)
            }
        )
        for widget in self._widgets.values():
            widget.mainLayout.setContentsMargins(10, 10, 10, 10)

    def _getAnalyseFile(self):
        path, filters = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open File",
            "./",
            "Antique'X Spectrum (*.atx);;Text Spectrum (*.txt)",
        )
        if path:
            analyse = Analyse.fromTXTFile(path) if path.endswith(".txt") else Analyse.fromATXFile(path)
            self._calibration.analyse = analyse
            self._calibration.state = 1
            self._calibration.save()
            getDatabase().executeQuery(
                f"UPDATE Calibrations SET state = 1 WHERE filename = '{self._calibration.filename}'"
            )
            reloadDataframes()
            self._resetClassVariables(getDataframe("Calibrations"))
            tableRow = self._tableWidget.getCurrentRow()
            tableRow.get("status").setText(self._calibration.status())
            self._addCalibrationWidgets()
