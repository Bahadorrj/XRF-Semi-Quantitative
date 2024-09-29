import os
import pandas
from pathlib import Path
from PyQt6 import QtCore, QtWidgets

from src.utils.database import getDataframe, getDatabase, reloadDataframes
from src.utils.datatypes import BackgroundProfile
from src.views.background.formdialog import BackgroundFileDialog
from src.views.base.traywidget import TrayWidget
from src.views.background.generaldatawidget import BackgroundGeneralDataWidget
from src.views.base.tablewidget import TableItem
from src.views.background.explorerwidget import BackgroundExplorer


class BackgroundTrayWidget(TrayWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        dataframe: pandas.DataFrame | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowFlag(QtCore.Qt.WindowType.Window)
        self._df = None
        self._profile = None
        self._widgets = {
            "General Data": BackgroundGeneralDataWidget(self, editable=False)
        }
        self._profileExplorer = None
        self._initializeUi()
        if dataframe is not None:
            self.supply(dataframe)

    def _initializeUi(self) -> None:
        super()._initializeUi()
        self.setWindowTitle("Method Tray List")

    @QtCore.pyqtSlot(str)
    def _actionTriggered(self, action: str) -> None:
        actions = {
            "add": self.addBackground,
            "edit": self.editCurrentProfile,
            "remove": self.removeCurrentProfile,
            "import": self.importProfile,
        }
        if action in actions:
            actions[action]()

    def addBackground(self) -> BackgroundProfile:
        addDialog = BackgroundFileDialog(inputs=self._df.columns[1:3])
        addDialog.setWindowTitle("Add background")
        if addDialog.exec():
            filename = addDialog.fields["filename"]
            description = addDialog.fields["description"]
            db = getDatabase()
            db.executeQuery(
                "INSERT INTO BackgroundProfiles (filename, description, state) VALUES (?, ?, ?)",
                (filename, description, 0),
            )
            reloadDataframes()
            self._df = getDataframe("BackgroundProfiles")
            backgroundId = int(self._df.iloc[-1].values[0]) + 1
            self._profile = BackgroundProfile(backgroundId, filename, description)
            self._profile.save()
            self._insertProfile()
            return self._profile

    def _insertProfile(self) -> None:
        filename = self._profile.filename
        description = self._profile.description
        status = self._profile.status()
        items = {
            "filename": TableItem(filename),
            "description": TableItem(description),
            "state": TableItem(status),
        }
        self._tableWidget.addRow(items)

    def editCurrentProfile(self) -> None:
        if self._profile is not None:
            if self._profileExplorer and self._profileExplorer.isVisible():
                self._profileExplorer.close()
            else:
                self._profileExplorer = BackgroundExplorer(
                    parent=self, profile=self._profile.copy()
                )
                self._profileExplorer.showMaximized()
                self._profileExplorer.saved.connect(self._saveSignalArrived)
                self._profileExplorer.requestNewMethod.connect(self._requestNewProfile)

    def _saveSignalArrived(self, profile: BackgroundProfile) -> None:
        self._profile = profile
        self._supplyWidgets()
        self._updateCurrentRow()

    def _updateCurrentRow(self) -> None:
        tableRow = self._tableWidget.getCurrentRow()
        tableRow["filename"].setText(self._profile.filename)
        tableRow["description"].setText(self._profile.description)
        tableRow["state"].setText(self._profile.status())

    @QtCore.pyqtSlot()
    def _requestNewProfile(self):
        pass

    def removeCurrentProfile(self) -> None:
        if not self._profile:
            raise ValueError("No profile selected selected")
        # Ask the user if they are sure to remove the profile
        messageBox = QtWidgets.QMessageBox()
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        messageBox.setText("Are you sure you want to remove the selected profile?")
        messageBox.setWindowTitle("Remove Profile")
        messageBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            filename = self._profile.filename
            os.remove(f"backgrounds/{filename}.atxb")
            getDatabase().executeQuery(
                "DELETE FROM BackgroundProfiles WHERE filename = ?", (filename,)
            )
            reloadDataframes()
            self._df = getDataframe("BackgroundProfiles")
            self._tableWidget.removeRow(self._tableWidget.currentRow())
            if self._tableWidget.rowCount() == 0:
                self._tabWidget.clear()

    def importProfile(self) -> None:
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Background Profile", "./", "Antique'X background (*.atxb)"
        )
        if filePath:
            if self._df.query(f"filename == '{Path(filePath).stem}'").empty:
                self._profile = BackgroundProfile.fromATXBFile(filePath)
                getDatabase().executeQuery(
                    "INSERT INTO BackgroundProfiles (filename, description, state) VALUES (?, ?, ?)",
                    (
                        self._profile.filename,
                        self._profile.description,
                        self._profile.state,
                    ),
                )
                reloadDataframes()
                self._df = getDataframe("BackgroundProfiles")
                self._insertProfile()
            else:
                messageBox = QtWidgets.QMessageBox()
                messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                messageBox.setText(
                    "The selected profile already exists in the database."
                )
                messageBox.setWindowTitle("Import profile failed")
                messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
                messageBox.exec()

    @QtCore.pyqtSlot()
    def _itemSelectionChanged(self) -> None:
        super()._itemSelectionChanged()
        row = self._tableWidget.currentRow()
        if row != -1:
            tableRow = self._tableWidget.getCurrentRow()
            filename = tableRow.get("filename").text()
            path = f"backgrounds/{filename}.atxb"
            self._profile = BackgroundProfile.fromATXBFile(path)
            self._supplyWidgets()
        else:
            self._profile = None

    def _supplyWidgets(self):
        self._addWidgets(self._widgets)
        for widget in self._widgets.values():
            widget.supply(self._profile)

    def supply(self, dataframe: pandas.DataFrame) -> None:
        super().supply(dataframe)
        self.blockSignals(True)
        df = self._df.drop("profile_id", axis=1)
        df["state"] = df["state"].apply(BackgroundProfile.convertStateToStatus)
        self._tableWidget.supply(df)
        self._tableWidget.clearSelection()
        self._tableWidget.selectRow(0)
        self._tableWidget.setFocus()
        self.blockSignals(False)

    @property
    def BackgroundProfile(self):
        return self._profile
