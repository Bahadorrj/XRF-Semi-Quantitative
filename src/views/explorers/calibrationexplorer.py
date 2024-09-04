from functools import partial
from PyQt6 import QtCore, QtGui, QtWidgets

from src.utils import datatypes
from src.utils.database import getDatabase
from src.utils.paths import resourcePath
from src.views.base.explorerwidget import Explorer
from src.views.widgets.coefficientwidget import CoefficientWidget
from src.views.widgets.calibrationgeneraldatawidget import CalibrationGeneralDataWidget
from src.views.widgets.peaksearchwidget import PeakSearchWidget


class CalibrationExplorer(Explorer):
    saved = QtCore.pyqtSignal()
    requestNewCalibration = QtCore.pyqtSignal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        calibration: datatypes.Calibration | None = None,
    ):
        super(CalibrationExplorer, self).__init__(parent)
        self._calibration = None
        self._initCalibration = None
        self._widgets = {
            "General Data": CalibrationGeneralDataWidget(editable=True),
            "Peak Search": PeakSearchWidget(),
            "Coefficient": CoefficientWidget(),
        }
        self._initializeUi()
        if calibration is not None:
            self.supply(calibration)

    def _initializeUi(self) -> None:
        super()._initializeUi()
        self.setObjectName("calibration-explorer")
        self.setWindowTitle("Calibration explorer")

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        actions = {
            "new": self.newCalibration,
            "save": self.saveCalibration,
            "open": self.openCalibration,
        }
        if action := actions.get(key):
            action()

    def newCalibration(self) -> None:
        if self._calibration != self._initCalibration:
            messageBox = QtWidgets.QMessageBox()
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
            messageBox.setText(
                "Do you want to save the changes before opening a new calibration?"
            )
            messageBox.setWindowTitle("New calibration")
            messageBox.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
            )
            messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)
            if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
                self.close()
                self.requestNewCalibration.emit()
        else:
            self.close()
            self.requestNewCalibration.emit()

    def saveCalibration(self) -> None:
        if self._calibration == self._initCalibration:
            return
        self._calibration.state = 2
        self._calibration.save()
        self._initCalibration = self._calibration.copy()
        getDatabase().executeQuery(
            "UPDATE Calibrations "
            f"SET filename = '{self._calibration.filename}', "
            f"element = '{self._calibration.element}', "
            f"concentration = '{self._calibration.concentration}', "
            f"state = {self._calibration.state} "
            f"WHERE calibration_id = {self._calibration.calibrationId}"
        )
        self.saved.emit()

    def openCalibration(self):
        messageBox = QtWidgets.QMessageBox()
        messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
        messageBox.setText(
            "Do you want to save the changes before opening another calibration?"
        )
        messageBox.setWindowTitle("Open calibration")
        messageBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        messageBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)
        if messageBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open Calibration", "./", "Antique'X calibration (*.atxc)"
            )
            if filePath:
                self.supply(self.supply(datatypes.Calibration.fromATXCFile(filePath)))

    @QtCore.pyqtSlot()
    def _changeWidget(self):
        if selectedItems := self._treeWidget.selectedItems():
            selectedItem = selectedItems[0]
            label = selectedItem.text(0)
            if label == "Peak Search":
                return
            oldWidget = self.mainLayout.itemAt(1).widget()
            oldWidget.hide()
            if "Condition" in label:
                newWidget = self._widgets["Peak Search"]
                newWidget.displayAnalyseData(int(label.split(" ")[-1]))
            else:
                newWidget = self._widgets[label]
            if isinstance(newWidget, CoefficientWidget):
                newWidget.supply(self._calibration)
            self.mainLayout.replaceWidget(oldWidget, newWidget)
            newWidget.show()
            newWidget.setFocus()

    def _implementAnalyse(self) -> None:
        for topLevelIndex in range(1, self._treeWidget.topLevelItemCount()):
            item = self._treeWidget.topLevelItem(topLevelIndex)
            while item.childCount() != 0:
                item.takeChild(0)
        for data in self._calibration.analyse.data:
            child = QtWidgets.QTreeWidgetItem()
            child.setText(0, f"Condition {data.conditionId}")
            child.setIcon(0, QtGui.QIcon(resourcePath("resources/icons/condition.png")))
            self._treeItemMap["peak-search"].addChild(child)
            self._treeWidget.expandItem(self._treeItemMap["peak-search"])

    def _supplyWidgets(self) -> None:
        for widget in self._widgets.values():
            if widget:
                widget.supply(self._calibration)

    def supply(self, calibration: datatypes.Calibration):
        self.blockSignals(True)
        self._calibration = calibration
        self._initCalibration = self._calibration.copy()
        self._implementAnalyse()
        self._supplyWidgets()
        self.blockSignals(False)
        self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))
