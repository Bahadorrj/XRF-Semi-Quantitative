import os

import pandas
from PyQt6 import QtCore, QtWidgets

from src.utils import datatypes
from src.utils.database import getDataframe, getDatabase, reloadDataframes
from src.utils.datatypes import Method
from src.views.base.formdialog import FormDialog
from src.views.base.tablewidget import TableItem, DataframeTableWidget
from src.views.base.traywidget import TrayWidget
from src.views.explorers.methodexplorer import MethodExplorer
from src.views.widgets.analytewidget import AnalytesAndConditionsWidget


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
        self._tableWidget = DataframeTableWidget(autofill=True)
        self._setUpView()

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(5)
        self.mainLayout.addWidget(self._tableWidget)
        self.setLayout(self.mainLayout)

    def supply(self, method: datatypes.Method) -> None:
        self.blockSignals(True)
        self._method = method
        self._tableWidget.supply(method.calibrations.drop("calibration_id", axis=1))
        self.blockSignals(False)

    @property
    def method(self):
        return self._method


class MethodFormDialog(FormDialog):
    """Dialog for managing method form inputs.

    This class extends the FormDialog to provide a user interface for inputting method details,
    including validation for filename uniqueness.

    Args:
        parent (QtWidgets.QWidget | None): The parent widget for the dialog.
        inputs (list | tuple | None): The input fields to be displayed in the dialog.
        values (list | tuple | None): The initial values for the input fields.

    Methods:
        _fill(lineEdit: QtWidgets.QLineEdit, key: str) -> None:
            Fills the line edit with the provided key and validates the filename.
            If the filename already exists, an error message is displayed.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        inputs: list | tuple | None = None,
        values: list | tuple | None = None,
    ) -> None:
        super(MethodFormDialog, self).__init__(parent, inputs, values)

    def _fill(self, lineEdit: QtWidgets.QLineEdit, key: str) -> None:
        if key == "filename":
            methodPath = f"methods/{lineEdit.text()}.atxm"
            if os.path.exists(methodPath):
                self._errorLabel.setText("This filename already exists!")
                return
        lineEdit.setStyleSheet("color: black;")
        self._errorLabel.setText(None)
        super()._fill(lineEdit, key)


class MethodTrayWidget(TrayWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        dataframe: pandas.DataFrame | None = None,
    ) -> None:
        super(MethodTrayWidget, self).__init__(parent)
        self._df = None
        self._method = None
        self._widgets = {
            "Analytes And Conditions": AnalytesAndConditionsWidget(),
            "Calibrations": CalibrationsWidget(),
        }
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

    def addMethod(self) -> None:
        """Add a new method to the application.

        This function opens a dialog for the user to input the method's filename and description. Upon confirmation, it saves the new method to the database and updates the internal data structures accordingly.

        Args:
            self: The instance of the class.

        Returns:
            None
        """

        addDialog = MethodFormDialog(inputs=self._df.columns[1:-1])
        addDialog.setWindowTitle("Add method")
        if addDialog.exec():
            filename = addDialog.fields["filename"]
            description = addDialog.fields["description"]
            db = getDatabase()
            db.executeQuery(
                "INSERT INTO Methods (filename, description, state) VALUES (?, ?, ?)",
                (filename, description, 0),
            )
            reloadDataframes()
            self._df = getDataframe("Methods")
            methodId = int(self._df.iloc[-1].values[0]) + 1
            self._method = Method(methodId, filename, description)
            self._method.save()
            self._insertMethod()

    def _insertMethod(self) -> None:
        filename = self._method.filename
        description = self._method.description
        status = self._method.status()
        items = {
            "filename": TableItem(filename),
            "description": TableItem(description),
            "status": TableItem(status),
        }
        self._tableWidget.addRow(items)
        self._tableWidget.setCurrentCell(self._tableWidget.rowCount() - 1, 0)

    def editCurrentMethod(self) -> None:
        if self._method is not None:
            methodExplorer = MethodExplorer(method=self._method)
            methodExplorer.show()
            methodExplorer.saved.connect(self._supplyWidgets)

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
        messageBox = QtWidgets.QMessageBox()
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
            os.remove(f"methods/{filename}.atxm")
            getDatabase().executeQuery(
                "DELETE FROM Methods WHERE filename = ?", (filename,)
            )
            reloadDataframes()
            self._df = getDataframe("Methods")
            self._tableWidget.removeRow(self._tableWidget.currentRow())

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
            self._method = Method.fromATXMFile(filePath)
            if self._df.query(f"filename == '{self._method.filename}'").empty:
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
                messageBox = QtWidgets.QMessageBox()
                messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                messageBox.setText(
                    "The selected method already exists in the database."
                )
                messageBox.setWindowTitle("Import method failed")
                messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
                messageBox.exec()

    def _currentCellChanged(
        self, currentRow: int, currentColumn: int, previousRow: int, previousColumn: int
    ):
        super()._currentCellChanged(
            currentRow, currentColumn, previousRow, previousColumn
        )
        if currentRow not in [previousRow, -1]:
            tableRow = self._tableWidget.getRow(currentRow)
            filename = tableRow.get("filename").text()
            path = f"methods/{filename}.atxm"
            self._method = Method.fromATXMFile(path)
            self._supplyWidgets()
        elif currentRow == -1:
            self._method = None

    def _supplyWidgets(self):
        for widget in self._widgets.values():
            widget.supply(self._method)

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
        if self._df.empty is False:
            self._tableWidget.setCurrentCell(0, 0)

    @property
    def method(self):
        return self._method
