import os
import pandas

from pathlib import Path
from PyQt6 import QtCore, QtWidgets

from src.utils.database import getDataframe, getDatabase, reloadDataframes
from src.utils.datatypes import Calibration, Analyse
from src.views.base.formdialog import FormDialog
from src.views.base.tablewidget import TableItem
from src.views.base.traywidget import TrayWidget
from src.views.explorers.calibrationexplorer import CalibrationExplorer
from src.views.widgets.coefficientwidget import CoefficientWidget
from src.views.widgets.calibrationgeneraldatawidget import CalibrationGeneralDataWidget
from src.views.widgets.linestablewidget import LinesTableWidget


class AcquisitionWidget(QtWidgets.QWidget):
    """Widget for acquiring data from various sources.

    This widget provides buttons for users to either open files from local storage or retrieve data from a connected XRF analyzer. It emits a signal when the user chooses to open a file, facilitating interaction with other components of the application.

    Args:
        parent (QtWidgets.QWidget | None): An optional parent widget.

    Attributes:
        getAnalyseFile (QtCore.pyqtSignal): Signal emitted to request an analysis file.
    """

    getAnalyseFile = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._initializeUi()

    def _initializeUi(self) -> None:
        layout = QtWidgets.QVBoxLayout()
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addStretch()
        openFromLocalButton = QtWidgets.QPushButton("Open from local storage")
        openFromLocalButton.clicked.connect(lambda: self.getAnalyseFile.emit())
        self.mainLayout.addWidget(openFromLocalButton)
        self.mainLayout.addStretch()
        getFromSocketButton = QtWidgets.QPushButton("Get from connected XRF analyser")
        self.mainLayout.addWidget(getFromSocketButton)
        self.mainLayout.addStretch()
        layout.addStretch()
        layout.addLayout(self.mainLayout)
        layout.addStretch()
        self.setLayout(layout)


class CalibrationFormDialog(FormDialog):
    """Dialog for entering calibration data.

    This dialog allows users to input calibration details, including filename, element, and concentration. It validates the inputs to ensure that the filename does not already exist, the element is valid, and the concentration is within an acceptable range.

    Args:
        parent (QtWidgets.QWidget | None): An optional parent widget.
        inputs (list | tuple | None): Optional list or tuple of input field names.
        values (list | tuple | None): Optional list or tuple of default values for the input fields.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        inputs: list | tuple | None = None,
        values: list | tuple | None = None,
    ) -> None:
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
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        dataframe: pandas.DataFrame | None = None,
    ) -> None:
        super(CalibrationTrayWidget, self).__init__(parent)
        self._df = None
        self._calibration = None
        self._widgets = {
            "General Data": CalibrationGeneralDataWidget(),
            "Coefficient": CoefficientWidget(),
            "Lines": LinesTableWidget(),
        }
        self._acquisitionWidget = AcquisitionWidget()
        self._acquisitionWidget.getAnalyseFile.connect(self._getAnalyseFile)
        self._initializeUi()
        if dataframe is not None:
            self.supply(dataframe)

    def _initializeUi(self) -> None:
        super()._initializeUi()
        self.setWindowTitle("Calibration Tray List")

    @QtCore.pyqtSlot(str)
    def _actionTriggered(self, action: str) -> None:
        if action == "add":
            self.addCalibration()
        elif action == "edit":
            if self._calibration.state == 0:
                self.editCurrentCalibration()
            else:
                self._openCalibrationExplorer()
        elif action == "remove":
            self.removeCurrentCalibration()
        elif action == "import":
            self.importCalibration()

    def addCalibration(self) -> None:
        """Add a new calibration entry to the application.

        This function prompts the user to input details for a new calibration, including the filename, element, and concentration. Upon confirmation, it saves the calibration data to the database and updates the internal data structures accordingly.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        addDialog = CalibrationFormDialog(inputs=self._df.columns[1:-1])
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
            calibrationId = int(self._df.iloc[-1].values[0]) + 1
            self._calibration = Calibration(
                calibrationId, filename, element, concentration
            )
            self._calibration.save()
            self._insertCalibration()

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
        self._tableWidget.setCurrentCell(self._tableWidget.rowCount() - 1, 0)

    def editCurrentCalibration(self) -> None:
        if self._calibration.state == 0:
            self._editBeforeAcquisition()
        else:
            self._openCalibrationExplorer()

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
            os.remove(f"calibrations/{previousFilename}.atxc")
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
            calibrationExplorer = CalibrationExplorer(calibration=self._calibration)
            calibrationExplorer.show()

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
        messageBox = QtWidgets.QMessageBox()
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
            os.remove(f"calibrations/{filename}.atxc")
            getDatabase().executeQuery(
                "DELETE FROM Calibrations WHERE filename = ?", (filename,)
            )
            reloadDataframes()
            self._df = getDataframe("Calibrations")
            self._tableWidget.removeRow(self._tableWidget.currentRow())
            self._currentCellChanged(self._tableWidget.currentRow(), 0, -1, -1)

    def importCalibration(self) -> None:
        """Import a calibration from an ATXC file into the application.

        This function allows the user to select an ATXC file and imports the calibration data contained within it. If the calibration does not already exist in the database, it is added; otherwise, a warning message is displayed to the user.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Calibration", "./", "Antique'X calibration (*.atxc)"
        )
        if filePath:
            if self._df.query(f"filename == '{Path(filePath).stem}'").empty:
                self._calibration = Calibration.fromATXCFile(filePath)
                getDatabase().executeQuery(
                    "INSERT INTO Calibrations (filename, element, concentration, state) VALUES (?, ?, ?, ?)",
                    (
                        self._calibration.filename,
                        self._calibration.element,
                        self._calibration.concentration,
                        0,
                    ),
                )
                reloadDataframes()
                self._insertCalibration()
            else:
                messageBox = QtWidgets.QMessageBox()
                messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                messageBox.setText(
                    "The selected calibration already exists in the database."
                )
                messageBox.setWindowTitle("Import Calibration Failed")
                messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
                messageBox.exec()

    def _currentCellChanged(
        self, currentRow: int, currentColumn: int, previousRow: int, previousColumn: int
    ) -> None:
        super()._currentCellChanged(
            currentRow, currentColumn, previousRow, previousColumn
        )
        if currentRow not in [previousRow, -1]:
            tableRow = self._tableWidget.getCurrentRow()
            filename = tableRow.get("filename").text()
            path = f"calibrations/{filename}.atxc"
            self._calibration = Calibration.fromATXCFile(path)
            self._supplyWidgets()
        elif currentRow == -1:
            self._calibration = None

    def _supplyWidgets(self) -> None:
        if self._calibration.state != 0:
            self._addWidgets(self._widgets)
            for widget in self._widgets.values():
                widget.supply(self._calibration)
        else:
            self._addWidgets({"Acquisition": self._acquisitionWidget})

    def _getAnalyseFile(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open File",
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
        df = self._df.drop("calibration_id", axis=1)
        df["state"] = df["state"].apply(Calibration.convertStateToStatus)
        self._tableWidget.supply(df)
        if self._df.empty is False:
            self._tableWidget.setCurrentCell(0, 0)

    @property
    def calibration(self):
        return self._calibration
