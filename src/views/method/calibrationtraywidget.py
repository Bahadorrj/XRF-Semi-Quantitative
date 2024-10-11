import pandas

from pathlib import Path
from PyQt6 import QtWidgets

from src.utils import datatypes
from src.views.calibration.traywidget import (
    AnalyseAcquisitionWidget,
    CalibrationTrayWidget,
)
from src.views.calibration.coefficientwidget import CoefficientWidget
from src.views.calibration.generaldatawidget import (
    CalibrationGeneralDataWidget,
)
from src.views.calibration.linestablewidget import LinesTableWidget


class MethodCalibrationTrayWidget(CalibrationTrayWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
    ):
        super(CalibrationTrayWidget, self).__init__(parent)
        self._method = None
        self._df = None
        self._calibration = None
        self._widgets = {
            "General Data": CalibrationGeneralDataWidget(self),
            "Coefficient": CoefficientWidget(self),
            "Lines": LinesTableWidget(self),
        }
        self._acquisitionWidget = AnalyseAcquisitionWidget()
        self._acquisitionWidget.getAnalyseFile.connect(self._getAnalyseFile)
        self._initializeUi()
        if method is not None:
            self.supply(method)
        self.hide()

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
                        "calibration_id": self._calibration.calibrationId,
                        "filename": self._calibration.filename,
                        "element": f"{'/'.join(self._calibration.concentrations.keys())}",
                        "concentration": f"{'/'.join(list(map(str,(self._calibration.concentrations.values()))))}",
                        "state": self._calibration.state,
                    },
                    index=[0],
                )
                self._df.loc[len(self._df)] = row.iloc[0]
                self._method.addCalibrationLines(self._calibration)
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
            self._method.removeCalibrationLines(self._calibration)
            self._tableWidget.removeRow(self._tableWidget.currentRow())

    def supply(self, method: datatypes.Method) -> None:
        if method is None:
            return
        if self._method and self._method == method:
            return
        self._method = method
        super().supply(method.calibrations)
