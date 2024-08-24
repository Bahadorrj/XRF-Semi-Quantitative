import os
from functools import partial
from json import dumps

import pandas
from PyQt6 import QtCore, QtGui, QtWidgets

from python.utils import encryption
from python.utils.database import getDataframe, getDatabase, reloadDataframes
from python.utils.datatypes import Calibration, Analyse
from python.views.base.tablewidgets import TableItem
from python.views.base.traywidget import TrayWidget
from python.views.calibrationexplorer.coefficientwidget import CoefficientWidget
from python.views.calibrationexplorer.explorer import CalibrationExplorer
from python.views.calibrationexplorer.generaldatawidget import GeneralDataWidget
from python.views.calibrationexplorer.linestablewidget import LinesTableWidget


class AddDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None, inputs: list | tuple | None = None) -> None:
        super(AddDialog, self).__init__(parent)
        self.setFixedSize(250, 200)
        if inputs is not None:
            self._fields = {key: "" for key in inputs}
            self._initializeUi()

    def _initializeUi(self) -> None:
        mainLayout = QtWidgets.QVBoxLayout()
        for key in self._fields.keys():
            label = QtWidgets.QLabel(f"{key}:")
            lineEdit = QtWidgets.QLineEdit()
            if key == "concentration":
                lineEdit.setValidator(QtGui.QDoubleValidator())
            lineEdit.setFixedWidth(100)
            lineEdit.editingFinished.connect(partial(self._fill, lineEdit, key))
            layout = QtWidgets.QHBoxLayout()
            layout.addWidget(label)
            layout.addWidget(lineEdit)
            mainLayout.addLayout(layout)
        mainLayout.addStretch()
        self._errorLabel = QtWidgets.QLabel()
        self._errorLabel.setStyleSheet("color: red;")
        mainLayout.addWidget(self._errorLabel)
        buttonBox = QtWidgets.QDialogButtonBox()
        buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        buttonBox.accepted.connect(self._check)
        buttonBox.rejected.connect(self.reject)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        self.setModal(True)

    def _fill(self, lineEdit: QtWidgets.QLineEdit, key: str) -> None:
        if key == "element":
            if not lineEdit.text() in getDataframe("Lines")["symbol"].values:
                lineEdit.setStyleSheet("color: red;")
                self._errorLabel.setText("Invalid element!")
                return
        elif key == "concentration":
            if not 0 <= float(lineEdit.text()) <= 100:
                lineEdit.setStyleSheet("color: red;")
                self._errorLabel.setText("concentration must be between 0 and 100!")
                return
        lineEdit.setStyleSheet("color: black;")
        self._errorLabel.setText(None)
        self._fields[key] = lineEdit.text()

    def _check(self) -> None:
        if all(value != "" for value in self._fields.values()):
            self.accept()
        else:
            QtWidgets.QApplication.beep()

    @property
    def fields(self):
        return self._fields


class CalibrationTrayWidget(TrayWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None, dataframe: pandas.DataFrame | None = None) -> None:
        super().__init__(parent)
        self._df = dataframe
        self._calibration = None
        self._initializeUi()
        if self._df is not None:
            self._tableWidget.reinitialize(self._df.drop("calibration_id", axis=1))
            self._connectSignalsAndSlots()
            if self._df.empty is False:
                self._tableWidget.setCurrentCell(0, 0)
                self._actionsMap["remove"].setDisabled(False)

    def _initializeUi(self) -> None:
        self.setWindowTitle("Calibration Tray List")
        self.setObjectName("calibration-tray-list")
        self._createActions({
            "Add": False,
            "Remove": True,
            "Close": False,
            "Print": True,
            "Print Preview": True,
            "Print Setup": True,
            "Edit": True
        })
        self._createMenus(("&File", "&Edit", "&View", "&Window", "&Help"))
        self._fillMenusWithActions()
        self._createToolBar()
        self._fillToolBarWithActions()
        self._createTableWidget()
        self._createTabLayout()
        self._setUpView()

    def _resetVariables(self, dataframe: pandas.DataFrame) -> None:
        self._df = dataframe

    @QtCore.pyqtSlot(str)
    def _actionTriggered(self, action: str) -> None:
        if action == "add":
            # Ask the user for the filename, element, concentration and create a new calibration
            add_dialog = AddDialog(inputs=self._df.columns[1:-1])
            if add_dialog.exec():
                filename = add_dialog.fields["filename"]
                element = add_dialog.fields["element"]
                concentration = add_dialog.fields["concentration"]
                status = "Proceed to acquisition"
                # Find the default radiation type for the element
                if not (lines_df := getDataframe("Lines").query(f"symbol == '{element}' and active == 1")).empty:
                    radiation_type = lines_df["radiation_type"].values[0]
                    default_dict = {radiation_type: concentration}
                    calibration_path = f"calibrations/{filename}.atxc"
                    self._calibration = Calibration(
                        Analyse(), {}, {element: default_dict}, pandas.DataFrame([])
                    )
                    self._saveCalibrationFile(calibration_path)
                    # Insert the calibration into the database
                    getDatabase().executeQuery(
                        "INSERT INTO Calibrations (filename, element, concentration, status) VALUES (?, ?, ?, ?)",
                        [filename, element, concentration, status]
                    )
                    reloadDataframes()
                    self._resetVariables(getDataframe("Calibrations"))
                    items = {
                        "filename": TableItem(filename),
                        "element": TableItem(element),
                        "concentration": TableItem(str(concentration)),
                        "status": TableItem(status)
                    }
                    self._tableWidget.addRow(items)
                    self._tableWidget.setCurrentCell(self._tableWidget.rowCount() - 1, 0)
                    # Enable the remove action if there are more than one calibration
                    if not self._actionsMap["remove"].isEnabled():
                        self._actionsMap["remove"].setDisabled(False)
        elif action == "edit":
            self._openCalibrationExplorer()
        elif action == "remove":
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
                getDatabase().executeQuery("DELETE FROM Calibrations WHERE filename = ?", (filename,))
                self._tableWidget.removeRow(self._tableWidget.currentRow())

    def _saveCalibrationFile(self, calibrationPath: str) -> None:
        with open(calibrationPath, "wb") as f:
            key = encryption.loadKey()
            jsonText = dumps(self._calibration.toHashableDict())
            encryptedText = encryption.encryptText(jsonText, key)
            f.write(encryptedText + b"\n")

    def _openCalibrationExplorer(self) -> None:
        if self._calibration is not None:
            calibrationExplorer = CalibrationExplorer(calibration=self._calibration)
            calibrationExplorer.show()

    def _fillMenusWithActions(self) -> None:
        self._menusMap["file"].addAction(self._actionsMap["print"])
        self._menusMap["file"].addAction(self._actionsMap["print-preview"])
        self._menusMap["file"].addAction(self._actionsMap["print-setup"])
        self._menusMap["file"].addSeparator()
        self._menusMap["file"].addAction(self._actionsMap["close"])

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar()
        self._toolBar.setIconSize(QtCore.QSize(16, 16))
        self._toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self._toolBar.setMovable(False)
        self._fillToolBarWithActions()

    def _fillToolBarWithActions(self) -> None:
        self._toolBar.addAction(self._actionsMap["add"])
        self._toolBar.addAction(self._actionsMap["remove"])

    def _currentCellChanged(self, currentRow: int, currentColumn: int, previousRow: int, previousColumn: int):
        """Called when the current cell in the table changes."""
        if currentRow != previousRow and currentRow != -1:
            self._widgets.clear()
            self._tabWidget.clear()
            tableRow = self._tableWidget.getRow(currentRow)
            filename = tableRow.get("filename").text()
            status = tableRow.get("status").text()
            if filename:
                path = f"./calibrations/{filename}.atxc"
                self._calibration = Calibration.fromATXCFile(path)
                if status == "Proceed to acquisition":
                    self._addAcquisitionWidget()
                    self._actionsMap["edit"].setDisabled(True)
                else:
                    self._addCalibrationWidgets()
                    self._actionsMap["edit"].setDisabled(False)
        elif currentRow == -1:
            self._widgets.clear()
            self._tabWidget.clear()
            self._actionsMap["edit"].setDisabled(True)
            self._actionsMap["remove"].setDisabled(True)

    def _addAcquisitionWidget(self):
        """Adds a widget for the acquisition of a calibration."""
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
        """Adds widgets for the calibration."""
        self._addWidgets(
            {
                "General Data": GeneralDataWidget(
                    calibration=self._calibration,
                    element=self._tableWidget.item(self._tableWidget.currentRow(), 1).text()
                ),
                "Coefficient": CoefficientWidget(calibration=self._calibration),
                "Lines": LinesTableWidget(calibration=self._calibration)
            }
        )

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
            self._calibration.lines = getDataframe("Lines").copy()
            tableRow = self._tableWidget.getRow(self._tableWidget.currentRow())
            calibrationPath = f"./calibrations/{tableRow.get('filename').text()}.atxc"
            calibrationId = self._df.at[self._tableWidget.currentRow(), "calibration_id"]
            self._saveCalibrationFile(calibrationPath)
            getDatabase().executeQuery(
                f"UPDATE Calibrations SET status = 'Initial state' WHERE calibration_id = {calibrationId}"
            )
            reloadDataframes()
            self._resetVariables(getDataframe("Calibrations"))
            tableRow.get("status").setText("Initial state")
            self._addCalibrationWidgets()
