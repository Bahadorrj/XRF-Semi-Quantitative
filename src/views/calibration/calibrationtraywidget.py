import os
from pathlib import Path

import pandas
from PyQt6 import QtCore, QtWidgets

from src.utils.database import getDataframe, getDatabase, reloadDataframes
from src.utils.datatypes import Calibration, Analyse
from src.utils.paths import resourcePath

from src.views.base.tablewidget import TableItem
from src.views.base.traywidget import TrayWidget

from src.views.calibration.analyseacquisitionswidget import AnalyseAcquisitionWidget
from src.views.calibration.calibrationfiledialog import CalibrationFormDialog
from src.views.calibration.calibrationexplorerwidget import CalibrationExplorerWidget
from src.views.calibration.calibrationgeneraldatawidget import (
    CalibrationGeneralDataWidget,
)
from src.views.calibration.coefficientwidget import CoefficientWidget
from src.views.calibration.linestablewidget import LinesTableWidget


class CalibrationTrayWidget(TrayWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        dataframe: pandas.DataFrame | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowFlag(QtCore.Qt.WindowType.Window)
        self._df = None
        self._calibration = None
        self._widgets = {
            "General Data": CalibrationGeneralDataWidget(),
            "Coefficient": CoefficientWidget(),
            "Lines": LinesTableWidget(),
        }
        self._acquisitionWidget = AnalyseAcquisitionWidget()
        self._acquisitionWidget.getAnalyseFile.connect(self._getAnalyseFile)
        self._calibrationExplorer = None
        self._initializeUi()
        if dataframe is not None:
            self.supply(dataframe)

    def _initializeUi(self) -> None:
        super()._initializeUi()
        self.setWindowTitle("Calibration Tray List")

    @QtCore.pyqtSlot(str)
    def _actionTriggered(self, action: str) -> None:
        actions = {
            "add": self.addCalibration,
            "remove": self.removeCurrentCalibration,
            "import": self.importCalibration,
            "edit": lambda: (
                self.editCurrentCalibration()
                if self._calibration.state == 0
                else self._openCalibrationExplorer()
            ),
        }
        if action in actions:
            actions[action]()

    def addCalibration(self) -> Calibration:
        """Add a new calibration entry.

        This function opens a dialog for the user to input calibration details,
        and if confirmed, it saves the new calibration to the database and updates
        the internal data structures.

        Args:
            self: The instance of the class.

        Returns:
            Calibration: The newly created Calibration object.

        Raises:
            ValueError: If the concentration cannot be converted to a float.
        """
        addDialog = CalibrationFormDialog(self, inputs=self._df.columns[1:-1])
        addDialog.setWindowTitle("Add calibration")
        if addDialog.exec():
            filename = addDialog.fields["filename"]
            element = addDialog.fields["element"]
            concentration = float(addDialog.fields["concentration"])
            getDatabase().executeQuery(
                "INSERT INTO Calibrations (filename, element, concentration, state) VALUES (?, ?, ?, ?)",
                (filename, element, concentration, 0),
            )
            reloadDataframes()
            self._df = getDataframe("Calibrations")
            calibrationId = int(self._df.iloc[-1].values[0])
            self._calibration = Calibration(
                calibrationId, filename, element, concentration
            )
            self._calibration.save()
            self._insertCalibration()
            return self._calibration

    def _insertCalibration(self) -> None:
        filename = self._calibration.filename
        element = self._calibration.element
        concentration = self._calibration.concentration
        status = self._calibration.status()
        items = {
            "filename": TableItem(filename),
            "element": TableItem(element),
            "concentration": TableItem(f"{concentration:.1f}"),
            "state": TableItem(status),
        }
        self._tableWidget.addRow(items)

    def editCurrentCalibration(self) -> None:
        if self._calibration is None:
            return
        (
            self._editBeforeAcquisition()
            if self._calibration.state == 0
            else self._openCalibrationExplorer()
        )

    def _editBeforeAcquisition(self):
        currentRow = self._tableWidget.getCurrentRow()
        previousFilename = currentRow["filename"].text()
        previousElement = currentRow["element"].text()
        previousConcentration = currentRow["concentration"].text()
        editDialog = CalibrationFormDialog(
            inputs=self._df.columns[1:-1],
            values=(previousFilename, previousElement, previousConcentration),
        )
        editDialog.setWindowTitle("Edit calibration")
        if editDialog.exec():
            os.remove(resourcePath(f"calibrations/{previousFilename}.atxc"))
            filename = editDialog.fields["filename"]
            element = editDialog.fields["element"]
            concentration = float(editDialog.fields["concentration"])
            self._calibration.filename = filename
            self._calibration.element = element
            self._calibration.concentration = concentration
            self._calibration.save()
            currentRow["filename"].setText(filename)
            currentRow["element"].setText(element)
            currentRow["concentration"].setText(f"{concentration:.1f}")
            getDatabase().executeQuery(
                "UPDATE Calibrations "
                f"SET filename = '{filename}', element = '{element}', concentration = {concentration} "
                f"WHERE filename = '{previousFilename}'"
            )
            reloadDataframes()
            self._df = getDataframe("Calibrations")

    def _openCalibrationExplorer(self) -> None:
        if self._calibration is not None:
            if self._calibrationExplorer and self._calibrationExplorer.isVisible():
                self._calibrationExplorer.close()
            else:
                self._calibrationExplorer = CalibrationExplorerWidget(
                    parent=self, calibration=self._calibration.copy()
                )
                self._calibrationExplorer.showMaximized()
                self._calibrationExplorer.saved.connect(self._saveSignalArrived)

    def _saveSignalArrived(self, calibration: Calibration) -> None:
        self._calibration = calibration
        self._supplyWidgets()
        self._updateCurrentRow()

    def _updateCurrentRow(self) -> None:
        tableRow = self._tableWidget.getCurrentRow()
        tableRow["filename"].setText(self._calibration.filename)
        tableRow["element"].setText(self._calibration.element)
        tableRow["concentration"].setText(str(self._calibration.concentration))
        tableRow["state"].setText(self._calibration.status())

    @QtCore.pyqtSlot()
    def _requestNewCalibration(self) -> None:
        if self.addCalibration() and self._getAnalyseFile():
            self._openCalibrationExplorer()

    @QtCore.pyqtSlot()
    def _getAnalyseFile(self) -> bool:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open Analyse File",
            "./",
            "Antique'X Spectrum (*.atx);;Text Spectrum (*.txt)",
        )
        if path:
            analyse = (
                Analyse.fromTXTFile(path)
                if path.endswith(".txt")
                else Analyse.fromATXFile(path)
            )
            self._calibration.analyse = analyse
            self._calibration.state = 1
            self._calibration.save()
            getDatabase().executeQuery(
                f"UPDATE Calibrations SET state = 1 WHERE filename = '{self._calibration.filename}'"
            )
            reloadDataframes()
            self._df = getDataframe("Calibrations")
            self._tableWidget.getCurrentRow().get("state").setText(
                self._calibration.status()
            )
            self._supplyWidgets()
            return True
        return False

    def removeCurrentCalibration(self) -> None:
        """Remove the currently selected calibration from the application.

        This function prompts the user for confirmation before deleting the selected calibration. If confirmed, it removes the calibration file from the filesystem and updates the database and the user interface accordingly.

        Args:
            self: The instance of the class.

        Raises:
            ValueError: If no calibration is currently selected.

        Returns:
            None
        """
        if not self._calibration:
            raise ValueError("No calibration selected")
        # Ask the user if they are sure to remove the calibration
        messageBox = QtWidgets.QMessageBox(self)
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        messageBox.setText("Are you sure you want to remove the selected calibration?")
        messageBox.setWindowTitle("Remove Calibration")
        messageBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            filename = self._calibration.filename
            os.remove(resourcePath(f"calibrations/{filename}.atxc"))
            getDatabase().executeQuery(
                "DELETE FROM Calibrations WHERE filename = ?", (filename,)
            )
            reloadDataframes()
            self._df = getDataframe("Calibrations")
            self._tableWidget.removeRow(self._tableWidget.currentRow())
            if self._tableWidget.rowCount() == 0:
                self._tabWidget.clear()

    def importCalibration(self) -> None:
        """Import a calibration from an ATXC file into the application.

        This function allows the user to select an ATXC file and imports the calibration data contained within it. If the calibration does not already exist in the database, it is added; otherwise, a warning message is displayed to the user.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        filePaths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Open Calibration", "./", "Antique'X calibration (*.atxc)"
        )
        for filePath in filePaths:
            if self._df.query(f"filename == '{Path(filePath).stem}'").empty:
                self._calibration = Calibration.fromATXCFile(filePath)
                getDatabase().executeQuery(
                    "INSERT INTO Calibrations (filename, element, concentration, state) VALUES (?, ?, ?, ?)",
                    (
                        self._calibration.filename,
                        self._calibration.element,
                        self._calibration.concentration,
                        self._calibration.state,
                    ),
                )
                reloadDataframes()
                self._insertCalibration()
            else:
                messageBox = QtWidgets.QMessageBox(self)
                messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                messageBox.setText(
                    "The selected calibration already exists in the database."
                )
                messageBox.setWindowTitle("Import Calibration Failed")
                messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
                messageBox.exec()

    @QtCore.pyqtSlot()
    def _itemSelectionChanged(self) -> None:
        super()._itemSelectionChanged()
        row = self._tableWidget.currentRow()
        if row != -1:
            tableRow = self._tableWidget.getCurrentRow()
            filename = tableRow.get("filename").text()
            path = resourcePath(f"calibrations/{filename}.atxc")
            self._calibration = Calibration.fromATXCFile(path)
            self._supplyWidgets()
        else:
            self._calibration = None

    def _supplyWidgets(self) -> None:
        if self._calibration.state != 0:
            self._addWidgets(self._widgets)
            for widget in self._widgets.values():
                widget.supply(self._calibration)
        else:
            self._addWidgets({"Acquisition": self._acquisitionWidget})

    def supply(self, dataframe: pandas.DataFrame) -> None:
        """Supply data to the table widget from a given DataFrame.

        This function processes the provided DataFrame by removing the 'calibration_id' column and converting the 'state' values to a more user-friendly format. It then updates the table widget with the modified DataFrame and sets the current cell to the first row if the DataFrame is not empty.

        Args:
            self: The instance of the class.
            dataframe (pandas.DataFrame): The DataFrame containing the data to supply.

        Returns:
            None
        """
        super().supply(dataframe)
        self.blockSignals(True)
        df = self._df.drop("calibration_id", axis=1)
        df["state"] = df["state"].apply(Calibration.convertStateToStatus)
        self._tableWidget.supply(df)
        self._tableWidget.clearSelection()
        self._tableWidget.selectRow(0)
        self._tableWidget.setFocus()
        self.blockSignals(False)

    @property
    def calibration(self):
        return self._calibration
