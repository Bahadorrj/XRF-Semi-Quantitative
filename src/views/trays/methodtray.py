import os
from pathlib import Path

import pandas
from PyQt6 import QtCore, QtWidgets

from src.utils import datatypes
from src.utils.database import getDataframe, getDatabase, reloadDataframes
from src.utils.datatypes import Calibration, Method
from src.utils.paths import isValidFilename, resourcePath
from src.views.base.formdialog import FormDialog
from src.views.base.tablewidget import TableItem, DataframeTableWidget
from src.views.base.traywidget import TrayWidget
from src.views.explorers.methodexplorer import MethodExplorer
from src.views.widgets.analytesandconditionswidget import AnalytesAndConditionsWidget


class InterferencesTableWidget(DataframeTableWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
    ):
        super().__init__(parent, autoFill=True)
        self._method = None
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        if method is not None:
            self.supply(method)
        self.hide()

    def supply(self, method: datatypes.Method):
        if method is None:
            return
        self.blockSignals(True)
        self._method = method
        super().supply(method.interferences)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.setVerticalHeaderLabels(self._method.interferences.index)
        self.blockSignals(False)


class CalibrationsWidget(QtWidgets.QWidget):
    """A widget for displaying and managing calibrations associated with a method in MethodTrayWidget.

    This class initializes the user interface for calibrations and allows for reinitialization with a new method's calibrations. It provides a structured layout to display calibration data in a table format.

    Args:
        parent (QtWidgets.QWidget | None): The parent widget for this widget.
        method (datatypes.Method | None): An optional method object containing calibration data.

    Methods:
        _initializeUi: Initializes the user interface components.
        _setUpView: Sets up the layout and adds the table widget to the main layout.
        supply: Updates the widget with new calibration data from a method.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
    ) -> None:
        super().__init__(parent)
        self._method = None
        self._initializeUi()
        if method is not None:
            self._tableWidget.supply(
                self._method.calibrations.drop("calibration_id", axis=1)
            )

    def _initializeUi(self) -> None:
        self._tableWidget = DataframeTableWidget(self, autoFill=True)
        self._setUpView()

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(5)
        self.mainLayout.addWidget(self._tableWidget)
        self.setLayout(self.mainLayout)

    def supply(self, method: datatypes.Method) -> None:
        if method is None:
            return
        if self._method and self._method == method:
            return
        self.blockSignals(True)
        self._method = method
        df = method.calibrations.drop("calibration_id", axis=1)
        df["state"] = df["state"].apply(Calibration.convertStateToStatus)
        self._tableWidget.supply(df)
        self.blockSignals(False)

    @property
    def method(self):
        return self._method


class MethodFormDialog(FormDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        inputs: list | tuple | None = None,
        values: list | tuple | None = None,
    ) -> None:
        super().__init__(parent, inputs, values)

    def _check(self) -> None:
        self._fill()
        self._errorLabel.clear()
        if not self._isFilenameValid():
            QtWidgets.QApplication.beep()
            return
        return super()._check()

    def _isFilenameValid(self) -> bool:
        filenameLineEdit = self._fields["filename"][-1]
        filename = filenameLineEdit.text()
        filenameLineEdit.setStyleSheet("color: red;")
        if not isValidFilename(filename):
            self._addError("This filename is not allowed!\n")
            return False
        if os.path.exists(resourcePath(f"methods/{filename}.atxm")):
            self._addError("This filename already exists!\n")
            return False
        if filename == "":
            self._addError("Please enter a filename!\n")
            return False
        filenameLineEdit.setStyleSheet("color: black;")
        return True


class MethodTrayWidget(TrayWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        dataframe: pandas.DataFrame | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowFlag(QtCore.Qt.WindowType.Window)
        self._df = None
        self._method = None
        self._widgets = {
            "Analytes And Conditions": AnalytesAndConditionsWidget(self),
            "Calibrations": CalibrationsWidget(self),
            "Interferences": InterferencesTableWidget(self),
        }
        self._methodExplorer = None
        self._initializeUi()
        if dataframe is not None:
            self.supply(dataframe)

    def _initializeUi(self) -> None:
        super()._initializeUi()
        self.setWindowTitle("Method Tray List")

    @QtCore.pyqtSlot(str)
    def _actionTriggered(self, action: str) -> None:
        actions = {
            "add": self.addMethod,
            "edit": self.editCurrentMethod,
            "remove": self.removeCurrentMethod,
            "import": self.importMethod,
        }
        if action in actions:
            actions[action]()

    def addMethod(self) -> datatypes.Method:
        """Add a new method entry.

        This function opens a dialog for the user to input method details,
        and if confirmed, it saves the new method to the database and updates
        the internal data structures.

        Args:
            self: The instance of the class.

        Returns:
            datatypes.Method: The newly created Method object.

        Raises:
            ValueError: If the method details are invalid or cannot be processed.
        """
        addDialog = MethodFormDialog(self, inputs=self._df.columns[1:-1])
        addDialog.setWindowTitle("Add method")
        if addDialog.exec():
            filename = addDialog.fields["filename"]
            description = addDialog.fields["description"]
            getDatabase().executeQuery(
                "INSERT INTO Methods (filename, description, state) VALUES (?, ?, ?)",
                (filename, description, 0),
            )
            reloadDataframes()
            self._df = getDataframe("Methods")
            methodId = int(self._df.iloc[-1].values[0])
            self._method = Method(methodId, filename, description)
            self._method.save()
            self._insertMethod()
            return self._method

    def _insertMethod(self) -> None:
        filename = self._method.filename
        description = self._method.description
        status = self._method.status()
        items = {
            "filename": TableItem(filename),
            "description": TableItem(description),
            "state": TableItem(status),
        }
        self._tableWidget.addRow(items)
        # self._tableWidget.setCurrentCell(self._tableWidget.rowCount() - 1, 0)

    def editCurrentMethod(self) -> None:
        self._cellClicked(self._tableWidget.currentRow(), 0)
        if self._method is not None:
            if self._methodExplorer and self._methodExplorer.isVisible():
                self._methodExplorer.close()
            else:
                self._methodExplorer = MethodExplorer(parent=self, method=self._method)
                self._methodExplorer.showMaximized()
                self._methodExplorer.saved.connect(self._saveSignalArrived)
                self._methodExplorer.requestNewMethod.connect(self._requestNewMethod)

    def removeCurrentMethod(self) -> None:
        """Remove the currently selected method from the application.

        This function prompts the user for confirmation before removing the selected method. If confirmed, it deletes the method's associated file and updates the database accordingly.

        Args:
            self: The instance of the class.

        Raises:
            ValueError: If no method is currently selected.
        """

        if not self._method:
            raise ValueError("No method selected")
        # Ask the user if they are sure to remove the calibration
        messageBox = QtWidgets.QMessageBox(self)
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        messageBox.setText("Are you sure you want to remove the selected method?")
        messageBox.setWindowTitle("Remove Method")
        messageBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            filename = self._method.filename
            os.remove(resourcePath(f"methods/{filename}.atxm"))
            getDatabase().executeQuery(
                "DELETE FROM Methods WHERE filename = ?", (filename,)
            )
            reloadDataframes()
            self._df = getDataframe("Methods")
            self._tableWidget.removeRow(self._tableWidget.currentRow())
            self._cellClicked(self._tableWidget.currentRow(), 0)

    def importMethod(self) -> None:
        """Import a method from an ATXM file into the application.

        This function allows the user to select an ATXM file and imports the method contained within it. If the method does not already exist in the database, it is added; otherwise, a warning message is displayed.

        Args:
            self: The instance of the class.

        Returns:
            None
        """

        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Method", "./", "Antique'X method (*.atxm)"
        )
        if filePath:
            if self._df.query(f"filename == '{Path(filePath).stem}'").empty:
                self._method = Method.fromATXMFile(filePath)
                getDatabase().executeQuery(
                    "INSERT INTO Methods (filename, description, state) VALUES (?, ?, ?)",
                    (
                        self._method.filename,
                        self._method.description,
                        self._method.state,
                    ),
                )
                reloadDataframes()
                self._df = getDataframe("Methods")
                self._insertMethod()
            else:
                messageBox = QtWidgets.QMessageBox(self)
                messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                messageBox.setText(
                    "The selected method already exists in the database."
                )
                messageBox.setWindowTitle("Import method failed")
                messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
                messageBox.exec()

    def _cellClicked(self, row: int, column: int) -> None:
        super()._cellClicked(row, column)
        if row != -1:
            tableRow = self._tableWidget.getRow(row)
            filename = tableRow.get("filename").text()
            path = resourcePath(f"methods/{filename}.atxm")
            self._method = Method.fromATXMFile(path)
            self._supplyWidgets()
        else:
            self._method = None

    def _saveSignalArrived(self) -> None:
        self._supplyWidgets()
        self._updateCurrentRow()

    def _updateCurrentRow(self) -> None:
        tableRow = self._tableWidget.getCurrentRow()
        tableRow["filename"].setText(self._method.filename)
        tableRow["description"].setText(self._method.description)
        tableRow["state"].setText(self._method.status())

    def _supplyWidgets(self) -> None:
        self._addWidgets(self._widgets)
        for widget in self._widgets.values():
            widget.supply(self._method)

    @QtCore.pyqtSlot()
    def _requestNewMethod(self) -> None:
        self.addMethod()
        self.editCurrentMethod()

    def supply(self, dataframe: pandas.DataFrame) -> None:
        """Supply data to the table widget from a given DataFrame.

        This function processes the provided DataFrame by dropping the 'method_id' column and converting the 'state' values to a more user-friendly status. It then updates the table widget with the modified DataFrame and sets the current cell to the first row if the DataFrame is not empty.

        Args:
            self: The instance of the class.
            dataframe (pandas.DataFrame): The DataFrame containing the data to supply.

        Returns:
            None
        """
        super().supply(dataframe)
        df = self._df.drop("method_id", axis=1)
        df["state"] = df["state"].apply(Method.convertStateToStatus)
        self._tableWidget.supply(df)

    @property
    def method(self):
        return self._method
