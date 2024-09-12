# import os
# import pandas

# from pathlib import Path
# from PyQt6 import QtCore, QtWidgets

# from src.utils import datatypes
# from src.utils.database import getDataframe, getDatabase, reloadDataframes
# from src.utils.datatypes import Method
# from src.views.base.formdialog import FormDialog
# from src.views.base.tablewidget import TableItem, DataframeTableWidget
# from src.views.base.traywidget import TrayWidget
# from src.views.explorers.methodexplorer import MethodExplorer
# from src.views.base.generaldatawidget import GeneralDataWidget


# class BackgroundGeneralDatWidget(GeneralDataWidget):
#     def __init__(
#         self,
#         parent: QtWidgets.QWidget | None = None,
#         calibration: datatypes.Calibration | None = None,
#         editable: bool = False,
#     ) -> None:
#         super(BackgroundGeneralDatWidget, self).__init__(parent, editable)


# # class BackgroundTrayWidget(TrayWidget):
# #     def __init__(
# #         self,
# #         parent: QtWidgets.QWidget | None = None,
# #         dataframe: pandas.DataFrame | None = None,
# #     ) -> None:
# #         super(BackgroundTrayWidget, self).__init__(parent)
# #         self._df = None
# #         self._profile = None
# #         self._widgets = {
# #             "General Data": GeneralDataWidget()
# #         }
# #         self._initializeUi()
# #         if dataframe is not None:
# #             self.supply(dataframe)

# #     def _initializeUi(self) -> None:
# #         super()._initializeUi()
# #         self.setWindowTitle("Method Tray List")

# #     @QtCore.pyqtSlot(str)
# #     def _actionTriggered(self, action: str) -> None:
# #         actions = {
# #             "add": self.addMethod,
# #             "edit": self.editCurrentMethod,
# #             "remove": self.removeCurrentMethod,
# #             "import": self.importMethod,
# #         }
# #         if action in actions:
# #             actions[action]()

# #     def addMethod(self) -> datatypes.Method:
# #         """Add a new method to the application.

# #         This function opens a dialog for the user to input the method's filename and description. Upon confirmation, it saves the new method to the database and updates the internal data structures accordingly.

# #         Args:
# #             self: The instance of the class.

# #         Returns:
# #             None
# #         """

# #         addDialog = MethodFormDialog(inputs=self._df.columns[1:-1])
# #         addDialog.setWindowTitle("Add method")
# #         if addDialog.exec():
# #             filename = addDialog.fields["filename"]
# #             description = addDialog.fields["description"]
# #             db = getDatabase()
# #             db.executeQuery(
# #                 "INSERT INTO Methods (filename, description, state) VALUES (?, ?, ?)",
# #                 (filename, description, 0),
# #             )
# #             reloadDataframes()
# #             self._df = getDataframe("Methods")
# #             methodId = int(self._df.iloc[-1].values[0]) + 1
# #             self._profile = Method(methodId, filename, description)
# #             self._profile.save()
# #             self._insertMethod()
# #             return self._profile

# #     def _insertMethod(self) -> None:
# #         filename = self._profile.filename
# #         description = self._profile.description
# #         status = self._profile.status()
# #         items = {
# #             "filename": TableItem(filename),
# #             "description": TableItem(description),
# #             "status": TableItem(status),
# #         }
# #         self._tableWidget.addRow(items)
# #         self._tableWidget.setCurrentCell(self._tableWidget.rowCount() - 1, 0)

# #     def editCurrentMethod(self) -> datatypes.Method:
# #         if self._profile is not None:
# #             methodExplorer = MethodExplorer(method=self._profile)
# #             methodExplorer.show()
# #             methodExplorer.saved.connect(self._supplyWidgets)
# #             methodExplorer.requestNewMethod.connect(self._requestNewMethod)
# #         return self._profile

# #     def _requestNewMethod(self):
# #         self.addMethod()
# #         self.editCurrentMethod()

# #     def removeCurrentMethod(self) -> None:
# #         """Remove the currently selected method from the application.

# #         This function prompts the user for confirmation before removing the selected method. If confirmed, it deletes the method's associated file and updates the database accordingly.

# #         Args:
# #             self: The instance of the class.

# #         Raises:
# #             ValueError: If no method is currently selected.
# #         """

# #         if not self._profile:
# #             raise ValueError("No method selected")
# #         # Ask the user if they are sure to remove the calibration
# #         messageBox = QtWidgets.QMessageBox()
# #         messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
# #         messageBox.setText("Are you sure you want to remove the selected method?")
# #         messageBox.setWindowTitle("Remove Method")
# #         messageBox.setStandardButtons(
# #             QtWidgets.QMessageBox.StandardButton.Yes
# #             | QtWidgets.QMessageBox.StandardButton.No
# #         )
# #         messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
# #         if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
# #             filename = self._profile.filename
# #             os.remove(f"methods/{filename}.atxm")
# #             getDatabase().executeQuery(
# #                 "DELETE FROM Methods WHERE filename = ?", (filename,)
# #             )
# #             reloadDataframes()
# #             self._df = getDataframe("Methods")
# #             self._tableWidget.removeRow(self._tableWidget.currentRow())
# #             self._tableWidget.setCurrentCell(self._tableWidget.currentRow(), 0, -1, -1)

# #     def importMethod(self) -> None:
# #         """Import a method from an ATXM file into the application.

# #         This function allows the user to select an ATXM file and imports the method contained within it. If the method does not already exist in the database, it is added; otherwise, a warning message is displayed.

# #         Args:
# #             self: The instance of the class.

# #         Returns:
# #             None
# #         """

# #         filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
# #             self, "Open Method", "./", "Antique'X method (*.atxm)"
# #         )
# #         if filePath:
# #             if self._df.query(f"filename == '{Path(filePath).stem}'").empty:
# #                 self._profile = Method.fromATXMFile(filePath)
# #                 getDatabase().executeQuery(
# #                     "INSERT INTO Methods (filename, description, state) VALUES (?, ?, ?)",
# #                     (
# #                         self._profile.filename,
# #                         self._profile.description,
# #                         self._profile.state,
# #                     ),
# #                 )
# #                 reloadDataframes()
# #                 self._df = getDataframe("Methods")
# #                 self._insertMethod()
# #             else:
# #                 messageBox = QtWidgets.QMessageBox()
# #                 messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
# #                 messageBox.setText(
# #                     "The selected method already exists in the database."
# #                 )
# #                 messageBox.setWindowTitle("Import method failed")
# #                 messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
# #                 messageBox.exec()

# #     def _currentCellChanged(
# #         self, currentRow: int, currentColumn: int, previousRow: int, previousColumn: int
# #     ):
# #         super()._currentCellChanged(
# #             currentRow, currentColumn, previousRow, previousColumn
# #         )
# #         if currentRow not in [previousRow, -1]:
# #             tableRow = self._tableWidget.getRow(currentRow)
# #             filename = tableRow.get("filename").text()
# #             path = f"methods/{filename}.atxm"
# #             self._profile = Method.fromATXMFile(path)
# #             self._supplyWidgets()
# #         elif currentRow == -1:
# #             self._profile = None

# #     def _supplyWidgets(self):
# #         for widget in self._widgets.values():
# #             widget.supply(self._profile)

# #     def supply(self, dataframe: pandas.DataFrame) -> None:
# #         """Supply data to the table widget from a given DataFrame.

# #         This function processes the provided DataFrame by dropping the 'method_id' column and converting the 'state' values to a more user-friendly status. It then updates the table widget with the modified DataFrame and sets the current cell to the first row if the DataFrame is not empty.

# #         Args:
# #             self: The instance of the class.
# #             dataframe (pandas.DataFrame): The DataFrame containing the data to supply.

# #         Returns:
# #             None
# #         """
# #         super().supply(dataframe)
# #         df = self._df.drop("method_id", axis=1)
# #         df["state"] = df["state"].apply(Method.convertStateToStatus)
# #         self._tableWidget.supply(df)
# #         if self._df.empty is False:
# #             self._tableWidget.setCurrentCell(0, 0)

# #     @property
# #     def method(self):
# #         return self._profile