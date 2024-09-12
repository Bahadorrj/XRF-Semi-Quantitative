from PyQt6.QtGui import QCloseEvent
import pandas

from pathlib import Path
from PyQt6 import QtCore, QtWidgets

from src.utils import datatypes
from src.utils.database import getDatabase
from src.views.base.explorerwidget import Explorer
from src.views.trays.calibrationtray import AcquisitionWidget, CalibrationTrayWidget
from src.views.widgets.analytesandconditionswidget import AnalytesAndConditionsWidget
from src.views.widgets.coefficientwidget import CoefficientWidget
from src.views.widgets.calibrationgeneraldatawidget import CalibrationGeneralDataWidget
from src.views.widgets.linestablewidget import LinesTableWidget


class MethodsCalibrationTrayWidget(CalibrationTrayWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
    ):
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
        if method is not None:
            self.supply(method)

    def _initializeUi(self) -> None:
        self.setObjectName("tray-widget")
        self._createActions({"Remove": True, "Import": False})
        self._createToolBar()
        self._fillToolBarWithActions()
        self._createTableWidget()
        self._createTabWidget()
        self._setUpView()

    def _fillToolBarWithActions(self) -> None:
        self._toolBar.addAction(self._actionsMap["import"])
        self._toolBar.addAction(self._actionsMap["remove"])

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(10)
        self.mainLayout.addWidget(self._toolBar)
        self.mainLayout.addWidget(self._tableWidget)
        self.mainLayout.addWidget(self._tabWidget)
        self.setLayout(self.mainLayout)

    def importCalibration(self) -> None:
        filePaths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Open Calibration", "./", "Antique'X calibration (*.atxc)"
        )
        for filePath in filePaths:
            if self._df.query(f"filename == '{Path(filePath).stem}'").empty:
                self._calibration = datatypes.Calibration.fromATXCFile(filePath)
                row = pandas.DataFrame(
                    {
                        "calibration_id": [self._calibration.calibrationId],
                        "filename": [self._calibration.filename],
                        "element": [self._calibration.element],
                        "concentration": [self._calibration.concentration],
                        "state": [self._calibration.state],
                    }
                )
                self._df.loc[len(self._df)] = row.iloc[0]
                self._insertCalibration()
            else:
                messageBox = QtWidgets.QMessageBox()
                messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                messageBox.setText(
                    "The selected calibration already exists in the method."
                )
                messageBox.setWindowTitle("Import Calibration Failed")
                messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
                messageBox.exec()

    def removeCurrentCalibration(self) -> None:
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
            index = self._df.query(f"filename == '{filename}'").index
            self._df.drop(index, inplace=True)
            self._tableWidget.removeRow(self._tableWidget.currentRow())
            self._currentCellChanged(self._tableWidget.currentRow(), 0, -1, -1)

    def supply(self, method: datatypes.Method) -> None:
        super().supply(method.calibrations)


class MethodExplorer(Explorer):
    saved = QtCore.pyqtSignal()
    requestNewMethod = QtCore.pyqtSignal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
    ):
        super(MethodExplorer, self).__init__(parent)
        self._method = None
        self._initMethod = None
        self._widgets = {
            "Analytes And Conditions": AnalytesAndConditionsWidget(editable=True),
            "Calibrations": MethodsCalibrationTrayWidget(),
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
            messageBox = QtWidgets.QMessageBox()
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
        self.saved.emit()

    def openMethod(self):
        messageBox = QtWidgets.QMessageBox()
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
                self.supply(datatypes.Method.fromATXMFile(filePath))

    @QtCore.pyqtSlot()
    def _changeWidget(self) -> None:
        if selectedItems := self._treeWidget.selectedItems():
            selectedItem = selectedItems[0]
            label = selectedItem.text(0)
            oldWidget = self.mainLayout.itemAt(1).widget()
            oldWidget.hide()
            newWidget = self._widgets[label]
            self.mainLayout.replaceWidget(oldWidget, newWidget)
            newWidget.show()
            newWidget.setFocus()
            
    def _supplyWidgets(self) -> None:
        for widget in self._widgets.values():
            widget.supply(self._method)

    def supply(self, method: datatypes.Method) -> None:
        self.blockSignals(True)
        self._method = method
        self._initMethod = self._method.copy()
        self._supplyWidgets()
        self.blockSignals(False)
        self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if self._method != self._initMethod:
            messageBox = QtWidgets.QMessageBox()
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
        return super().closeEvent(a0)
