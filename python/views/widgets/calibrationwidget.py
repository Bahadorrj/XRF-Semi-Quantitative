from functools import partial
from pathlib import Path

from PyQt6 import QtWidgets, QtGui, QtCore

from python.utils import datatypes
from python.utils.database import getDatabase
from python.utils.datatypes import Calibration
from python.utils.paths import resourcePath
from python.views.base.tablewidget import DataframeTableWidget, TableItem


class CalibrationWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None, method: datatypes.Method | None = None):
        super().__init__(parent)
        self._method = method
        self._df = None
        self._initializeUi()
        if self._method is not None and self._method.calibrations:
            filenames = "(" + ", ".join(map(lambda x: f"'{x}'", self._method.calibrations.keys())) + ")"
            df = getDatabase().dataframe(
                "SELECT * FROM Calibrations "
                "WHERE calibration_id IN "
                f"(SELECT calibration_id FROM Methods WHERE filename in {filenames})"
            )
            self._tableWidget.reinitialize(dataframe=df)

    def _initializeUi(self) -> None:
        self._createActions()
        self._createToolBar()
        self._createToolBar()
        self._fillToolBarWithActions()
        self._createTableWidget()
        self._setUpView()

    def _resetClassVariables(self) -> None:
        pass

    def _createActions(self) -> None:
        self._actionsMap = {}
        actions = ("Import", "Remove")
        for label in actions:
            action = QtGui.QAction(label)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"icons/{key}.png")))
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))

    @QtCore.pyqtSlot()
    def _actionTriggered(self, action: str) -> None:
        if action == "remove":
            self._removeCalibration()
        elif action == "import":
            self._importCalibration()

    def _removeCalibration(self) -> None:
        # Ask the user if they are sure to remove the calibration
        message_box = QtWidgets.QMessageBox()
        message_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        message_box.setText("Are you sure you want to remove the selected calibration?")
        message_box.setWindowTitle("Remove calibration")
        message_box.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        message_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        if message_box.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            calibrationPath = "calibrations/" + self._tableWidget.getCurrentRow().get("filename").text() + ".atxc"
            self._method.calibrations.pop(calibrationPath)
            self._tableWidget.removeRow(self._tableWidget.currentRow())

    def _importCalibration(self) -> None:
        if self._method.state == 0:
            self._method.state = 1

        filePaths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Open Calibration",
            "./",
            "Antique'X calibration (*.atxc)"
        )
        for filePath in filePaths:
            if filePath not in self._method.calibrations:
                self._calibration = Calibration.fromATXCFile(filePath)
                self._method.calibrations[filePath] = self._calibration
                filename = Path(filePath).stem
                element = self._calibration.element
                concentration = self._calibration.concentration
                if self._calibration.state == 0:
                    status = "Proceed to acquisition"
                elif self._calibration.state == 1:
                    status = "Initial state"
                else:
                    status = "Edited by user"
                items = {
                    "filename": TableItem(filename),
                    "element": TableItem(element),
                    "concentration": TableItem(f"{concentration:.1f}"),
                    "status": TableItem(status)
                }
                self._tableWidget.addRow(items)
                self._tableWidget.setCurrentCell(self._tableWidget.rowCount() - 1, 0)

    def _createToolBar(self) -> None:
        self._toolBar = QtWidgets.QToolBar()
        self._toolBar.setIconSize(QtCore.QSize(16, 16))
        self._toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self._toolBar.setMovable(False)
        self._fillToolBarWithActions()

    def _fillToolBarWithActions(self) -> None:
        self._toolBar.addAction(self._actionsMap["import"])
        self._toolBar.addSeparator()
        self._toolBar.addAction(self._actionsMap["remove"])

    def _createTableWidget(self) -> None:
        self._tableWidget = DataframeTableWidget(autofill=True)

    def _setUpView(self) -> None:
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(30, 30, 30, 30)
        self.mainLayout.addWidget(self._toolBar)
        self.mainLayout.addWidget(self._tableWidget)
        self.setLayout(self.mainLayout)
