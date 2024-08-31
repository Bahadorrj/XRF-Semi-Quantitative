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
    """A widget for displaying and managing calibrations associated with a method.

    This class initializes the user interface for calibrations and allows for reinitialization with a new method's calibrations. It provides a structured layout to display calibration data in a table format.

    Args:
        parent (QtWidgets.QWidget | None): The parent widget for this widget.
        method (datatypes.Method | None): An optional method object containing calibration data.

    Methods:
        _resetClassVariables: Resets the class variable to a new method.
        _initializeUi: Initializes the user interface components.
        _setUpView: Sets up the layout and adds the table widget to the main layout.
        reinitialize: Updates the widget with new calibration data from a method.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
    ) -> None:
        super().__init__(parent)
        self._method = method
        self._initializeUi()
        if self._method is not None:
            self._tableWidget.reinitialize(self._method.calibrations)

    def _resetClassVariables(self, method: datatypes.Method) -> None:
        self._method = method

    def _initializeUi(self) -> None:
        self._tableWidget = DataframeTableWidget(autofill=True)
        self._setUpView()

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(5)
        self.mainLayout.addWidget(self._tableWidget)
        self.setLayout(self.mainLayout)

    def reinitialize(self, method: datatypes.Method) -> None:
        self.blockSignals(True)
        self._resetClassVariables(method)
        self._tableWidget.reinitialize(self._method.calibrations)
        self.blockSignals(False)


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
        super().__init__(parent)
        self._df = dataframe
        self._method = None
        self._widgets = None
        self._initializeUi()
        if self._df is not None:
            df = self._df.drop("method_id", axis=1)
            df["state"] = df["state"].apply(Method.convertStateToStatus)
            self._tableWidget.reinitialize(df)
            self._widgets = {
                "Analytes And Conditions": AnalytesAndConditionsWidget(),
                "Calibrations": CalibrationsWidget(),
            }
            self._connectSignalsAndSlots()
            if self._df.empty is False:
                self._tableWidget.setCurrentCell(0, 0)

    def _initializeUi(self) -> None:
        self.setWindowTitle("Method Tray List")
        self.setObjectName("tray-list")
        self._createActions(
            {
                "Add": False,
                "Remove": True,
                "Close": False,
                "Print": True,
                "Print Preview": True,
                "Print Setup": True,
                "Edit": True,
                "Import": False,
            }
        )
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
        actions = {
            "add": self.addMethod,
            "edit": self._openMethodExplorer,
            "remove": self.removeCurrentMethod,
            "import": self.importMethod,
        }
        if action in actions:
            actions[action]()

    def addMethod(self) -> None:
        """Adds a new method to the database and updates the UI.

        This function opens a dialog for the user to input the filename and description of a new method.
        Upon confirmation, it inserts the method into the database, reloads the data, and updates the internal
        state to reflect the newly added method.

        """
        addDialog = MethodFormDialog(inputs=self._df.columns[1:-1])
        if addDialog.exec():
            filename = addDialog.fields["filename"]
            description = addDialog.fields["description"]
            db = getDatabase()
            db.executeQuery(
                "INSERT INTO Methods (filename, description, state) VALUES (?, ?, ?)",
                (filename, description, 0),
            )
            reloadDataframes()
            self._resetClassVariables(getDataframe("Methods"))
            methodId = int(getDataframe("Methods").iloc[-1].values[0]) + 1
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

    def _openMethodExplorer(self) -> None:
        if self._method is not None:
            methodExplorer = MethodExplorer(method=self._method)
            methodExplorer.show()
            methodExplorer.saved.connect(self._reinitializeWidgets)

    def removeCurrentMethod(self) -> None:
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
            self._resetClassVariables(getDataframe("Methods"))
            self._tableWidget.removeRow(self._tableWidget.currentRow())

    def importMethod(self) -> None:
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Method", "./", "Antique'X method (*.atxm)"
        )
        if filePath:
            self._method = Method.fromATXMFile(filePath)
            if self._df.query(f"filename == '{self._method.filename}'").empty:
                self._insertMethod()
                getDatabase().executeQuery(
                    "INSERT INTO Methods (filename, description, state) VALUES (?, ?, ?)",
                    (
                        self._method.filename,
                        self._method.description,
                        self._method.state,
                    ),
                )
                reloadDataframes()
                self._resetClassVariables(getDataframe("Methods"))
            else:
                messageBox = QtWidgets.QMessageBox()
                messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                messageBox.setText(
                    "The selected method already exists in the database."
                )
                messageBox.setWindowTitle("Import method failed")
                messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
                messageBox.exec()

    def _fillMenusWithActions(self) -> None:
        file_actions = [
            self._actionsMap["import"],
            "separator",
            self._actionsMap["print"],
            self._actionsMap["print-preview"],
            self._actionsMap["print-setup"],
            "separator",
            self._actionsMap["close"],
        ]
        edit_actions = [
            self._actionsMap["add"],
            self._actionsMap["edit"],
            self._actionsMap["remove"],
        ]
        for action in file_actions:
            if action == "separator":
                self._menusMap["file"].addSeparator()
            else:
                self._menusMap["file"].addAction(action)
        for action in edit_actions:
            self._menusMap["edit"].addAction(action)

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar()
        self._toolBar.setIconSize(QtCore.QSize(16, 16))
        self._toolBar.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self._toolBar.setMovable(False)
        self._fillToolBarWithActions()

    def _fillToolBarWithActions(self) -> None:
        self._toolBar.addAction(self._actionsMap["import"])
        self._toolBar.addAction(self._actionsMap["add"])
        self._toolBar.addSeparator()
        self._toolBar.addAction(self._actionsMap["edit"])
        self._toolBar.addSeparator()
        self._toolBar.addAction(self._actionsMap["remove"])

    def _currentCellChanged(
        self, currentRow: int, currentColumn: int, previousRow: int, previousColumn: int
    ):
        """Called when the current cell in the table changes."""
        if currentRow not in [previousRow, -1]:
            if self._tabWidget.count() == 0:
                self._addWidgets(self._widgets)
            tableRow = self._tableWidget.getRow(currentRow)
            filename = tableRow.get("filename").text()
            path = f"methods/{filename}.atxm"
            self._method = Method.fromATXMFile(path)
            self._actionsMap["edit"].setDisabled(False)
            self._actionsMap["remove"].setDisabled(False)
            self._reinitializeWidgets()
        elif currentRow == -1:
            self._tabWidget.clear()
            self._method = None
            self._actionsMap["edit"].setDisabled(True)
            self._actionsMap["remove"].setDisabled(True)

    def _reinitializeWidgets(self):
        self._widgets["Analytes And Conditions"].reinitialize(self._method)
        self._widgets["Calibrations"].reinitialize(self._method)

    @property
    def widgets(self):
        return self._widgets

    @property
    def method(self):
        return self._method

    @property
    def tableWidget(self):
        return self._tableWidget
