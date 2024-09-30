from PyQt6 import QtCore, QtWidgets

from src.utils.datatypes import Method
from src.utils.database import getDatabase

from src.views.base.explorerwidget import ExplorerWidget
from src.views.method.analytesandconditionswidget import AnalytesAndConditionsWidget
from src.views.method.calibrationtraywidget import MethodCalibrationTrayWidget


class MethodExplorer(ExplorerWidget):
    saved = QtCore.pyqtSignal(Method)
    requestNewMethod = QtCore.pyqtSignal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: Method | None = None,
    ):
        super().__init__(parent)
        self._method = None
        self._initMethod = None
        self._widgets = {
            "Analytes And Conditions": AnalytesAndConditionsWidget(self, editable=True),
            "Calibrations": MethodCalibrationTrayWidget(self),
        }
        self._initializeUi()
        if method is not None:
            self.supply(method)

    def _initializeUi(self) -> None:
        super()._initializeUi()
        self.setObjectName("method-explorer")
        self.setWindowTitle("Method explorer")

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
        if self._method != self._initMethod:
            messageBox = QtWidgets.QMessageBox(self)
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
            messageBox.setText(
                "Do you want to save the changes before opening a new method?"
            )
            messageBox.setWindowTitle("New method")
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
        if self._method == self._initMethod:
            return
        self._method.state = 1
        self._method.save()
        self._initMethod = self._method.copy()
        getDatabase().executeQuery(
            "UPDATE Methods "
            f"SET filename = '{self._method.filename}', "
            f"description = '{self._method.description}', "
            f"state = {self._method.state} "
            f"WHERE method_id = {self._method.methodId}"
        )
        self.saved.emit(self._method)

    def openMethod(self):
        messageBox = QtWidgets.QMessageBox(self)
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
        messageBox.setText(
            "Do you want to save the changes before opening another method?"
        )
        messageBox.setWindowTitle("Open method")
        messageBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)
        if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open Method", "./", "Antique'X method (*.atxm)"
            )
            if filePath:
                self.supply(Method.fromATXMFile(filePath))

    @QtCore.pyqtSlot()
    def _changeWidget(self) -> None:
        if selectedItems := self._treeWidget.selectedItems():
            selectedItem = selectedItems[0]
            label = selectedItem.text(0)
            oldWidget = self.mainLayout.itemAt(1).widget()
            oldWidget.hide()
            newWidget = self._widgets[label]
            newWidget.setContentsMargins(20, 20, 20, 20)
            if isinstance(newWidget, AnalytesAndConditionsWidget):
                newWidget.setEditable(self._method.calibrations.empty)
            self.mainLayout.replaceWidget(oldWidget, newWidget)
            newWidget.show()
            newWidget.setFocus()

    def _supplyWidgets(self) -> None:
        for widget in self._widgets.values():
            widget.supply(self._method)

    def supply(self, method: Method) -> None:
        if method is None:
            return
        if self._method and self._method == method:
            return
        self.blockSignals(True)
        self._method = method
        self._initMethod = self._method.copy()
        self._supplyWidgets()
        self.blockSignals(False)
        self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))

    def closeEvent(self, a0) -> None:
        if self._method != self._initMethod:
            messageBox = QtWidgets.QMessageBox(self)
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
            messageBox.setText(
                "Do you want to save the changes before closing the method edit?"
            )
            messageBox.setWindowTitle("Close method edit")
            messageBox.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
            )
            messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)
            if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
                self.saveMethod()
            a0.accept()
        else:
            return super().closeEvent(a0)
