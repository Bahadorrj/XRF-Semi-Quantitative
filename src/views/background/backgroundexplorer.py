from PyQt6 import QtCore, QtWidgets

from src.utils import datatypes
from src.utils.database import getDatabase

from src.views.base.explorerwidget import ExplorerWidget
from src.views.background.backgroundgeneraldatawidget import BackgroundGeneralDataWidget


class BackgroundExplorer(ExplorerWidget):
    saved = QtCore.pyqtSignal(datatypes.BackgroundProfile)
    requestNewMethod = QtCore.pyqtSignal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        profile: datatypes.BackgroundProfile | None = None,
    ):
        super().__init__(parent)
        self._profile = None
        self._initProfile = None
        self._widgets = {
            "General Data": BackgroundGeneralDataWidget(self, editable=True)
        }
        self._initializeUi()
        if profile is not None:
            self.supply(profile)

    def _initializeUi(self) -> None:
        super()._initializeUi()
        self.setObjectName("background-explorer")
        self.setWindowTitle("Background explorer")

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        actions = {
            "new": self.newMethod,
            "save": self.saveMethod,
            "open": self.openMethod,
        }
        if action := actions.get(key):
            action()

    def newMethod(self):
        if self._profile != self._initProfile:
            messageBox = QtWidgets.QMessageBox(self)
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
            messageBox.setText(
                "Do you want to save the changes before opening a new profile?"
            )
            messageBox.setWindowTitle("New profile")
            messageBox.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
            )
            messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)
            if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
                self.close()
                self.requestNewMethod.emit()
        else:
            self.close()
            self.requestNewMethod.emit()

    def saveMethod(self) -> None:
        if self._profile == self._initProfile:
            return
        self._profile.state = 1
        self._profile.save()
        self._initProfile = self._profile.copy()
        getDatabase().executeQuery(
            "UPDATE BackgroundProfiles "
            f"SET filename = '{self._profile.filename}', "
            f"description = '{self._profile.description}', "
            f"state = {self._profile.state} "
            f"WHERE profile_id = {self._profile.profileId}"
        )
        self.saved.emit(self._profile)

    def openMethod(self):
        messageBox = QtWidgets.QMessageBox(self)
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
        messageBox.setText(
            "Do you want to save the changes before opening another profile?"
        )
        messageBox.setWindowTitle("Open profile")
        messageBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)
        if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open Background Profile", "./", "Antique'X background (*.atxb)"
            )
            if filePath:
                self.supply(datatypes.BackgroundProfile.fromATXBFile(filePath))

    @QtCore.pyqtSlot()
    def _changeWidget(self) -> None:
        if selectedItems := self._treeWidget.selectedItems():
            selectedItem = selectedItems[0]
            label = selectedItem.text(0)
            oldWidget = self.mainLayout.itemAt(1).widget()
            oldWidget.hide()
            newWidget = self._widgets[label]
            newWidget.setContentsMargins(20, 20, 20, 20)
            self.mainLayout.replaceWidget(oldWidget, newWidget)
            newWidget.show()
            newWidget.setFocus()

    def _supplyWidgets(self) -> None:
        for widget in self._widgets.values():
            widget.supply(self._profile)

    def supply(self, profile: datatypes.BackgroundProfile) -> None:
        if profile is None:
            return
        if self._profile and self._profile == profile:
            return
        self.blockSignals(True)
        self._profile = profile
        self._initProfile = self._profile.copy()
        self._supplyWidgets()
        self.blockSignals(False)
        self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))

    def closeEvent(self, a0) -> None:
        if self._profile != self._initProfile:
            messageBox = QtWidgets.QMessageBox(self)
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
            messageBox.setText(
                "Do you want to save the changes before closing the profile explorer?"
            )
            messageBox.setWindowTitle("Close profile explorer")
            messageBox.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
            )
            messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)
            if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
                self.saveMethod()
        return super().closeEvent(a0)
