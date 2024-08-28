import pandas
from PyQt6 import QtCore, QtWidgets

from python.utils import datatypes
from python.utils.database import getDataframe, getDatabase, reloadDataframes
from python.utils.datatypes import Calibration, Method
from python.views.base.explorerwidget import Explorer
from python.views.base.tablewidget import TableItem
from python.views.base.traywidget import TrayWidget
from python.views.trays.calibrationtray import CalibrationTrayWidget
from python.views.widgets.analytewidget import AnalytesAndConditionsWidget
from python.views.widgets.coefficientwidget import CoefficientWidget
from python.views.widgets.generaldatawidget import GeneralDataWidget
from python.views.widgets.linestablewidget import LinesTableWidget


class MethodsCalibrationTrayWidget(CalibrationTrayWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
    ):
        super(TrayWidget, self).__init__(parent)
        self._df = method.calibrations
        self._calibration = None
        self._widgets = None
        self._initializeUi()
        if self._df is not None:
            self._widgets = {
                "General Data": GeneralDataWidget(calibration=self._calibration),
                "Coefficient": CoefficientWidget(calibration=self._calibration),
                "Lines": LinesTableWidget(calibration=self._calibration)
            }
            self._tableWidget.reinitialize(self._df)
            self._connectSignalsAndSlots()
            if self._df.empty is False:
                df = self._df.copy()
                status = list(
                    map(Calibration.convertStateToStatus, df["state"].tolist())
                )
                df["state"] = status
                self._tableWidget.reinitialize(df)
                self._tableWidget.setCurrentCell(0, 0)

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

    def _insertCalibration(self) -> None:
        filename = self._calibration.filename
        element = self._calibration.element
        concentration = self._calibration.concentration
        state = self._calibration.state
        row = pandas.DataFrame(
            {
                "filename": [filename],
                "element": [element],
                "concentration": [concentration],
                "state": [state],
            }
        )
        self._df.loc[len(self._df)] = row.iloc[0]
        status = self._calibration.status()
        items = {
            "filename": TableItem(filename),
            "element": TableItem(element),
            "concentration": TableItem(f"{concentration:.1f}"),
            "status": TableItem(status),
        }
        self._tableWidget.addRow(items)
        self._tableWidget.setCurrentCell(self._tableWidget.rowCount() - 1, 0)


class MethodExplorer(Explorer):
    saved = QtCore.pyqtSignal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        method: datatypes.Method | None = None,
    ):
        super(MethodExplorer, self).__init__(parent)
        self._method = method
        self._initMethod = None
        self._widgets = None
        self._initializeUi()
        if self._method is not None:
            self._initMethod = self._method.copy()
            self._widgets = {
                "Analytes And Conditions": AnalytesAndConditionsWidget(
                    method=self._method, editable=True
                ),
                "Calibrations": MethodsCalibrationTrayWidget(method=self._method),
                "Properties": QtWidgets.QWidget(),
            }
            self._connectSignalsAndSlots()
            self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))

    def _resetClassVariables(self, method: datatypes.Method):
        self._method = method
        self._initMethod = self._method.copy()

    def _initializeUi(self) -> None:
        self.setObjectName("method-explorer")
        self.setWindowTitle("Method explorer")
        self._createActions(("New", "Open", "Save", "Close", "What's this"))
        self._createMenus(("&File", "&Edit", "&Window", "&Help"))
        self._fillMenusWithActions()
        self._createToolBar()
        self._fillToolBarWithActions()
        self._createTreeWidget()
        self._fillTreeWithItems(
            "Method Contents", ("Analytes And Conditions", "Calibrations", "Properties")
        )
        self._setUpView()

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        if key == "new":
            self._newMethod()
        elif key == "save":
            self._saveMethod()
        elif key == "open":
            self._openMethod()

    def _newMethod(self):
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
                self.hide()
                self._openAddDialog()
        else:
            self.hide()
            self._openAddDialog()

    def _openAddDialog(self):
        pass
        # addDialog = MethodFormDialog(inputs=getDataframe("Methods").columns[1:-1])
        # if addDialog.exec() == QtWidgets.QMessageBox.StandardButton.Ok:
        #     filename = addDialog.fields["filename"]
        #     description = addDialog.fields["description"]
        #     methodId = int(getDataframe("Methods").iloc[-1].values[0])
        #     method = Method(methodId, filename, description)
        #     method.save()
        #     getDatabase().executeQuery(
        #         f"INSERT INTO Methods (filename, description, state) VALUES (?, ?, ?)",
        #         (filename, description, method.state),
        #     )
        #     reloadDataframes()
        #     self.reinitialize(method)
        # self.show()

    def _saveMethod(self) -> None:
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
        reloadDataframes()
        self.saved.emit()

    def _openMethod(self):
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
                method = Method.fromATXMFile(filePath)
                self.reinitialize(method)

    def _fillMenusWithActions(self) -> None:
        self._menusMap["file"].addAction(self._actionsMap["new"])
        self._menusMap["file"].addAction(self._actionsMap["open"])
        self._menusMap["file"].addAction(self._actionsMap["save"])
        self._menusMap["file"].addAction(self._actionsMap["close"])
        self._menusMap["help"].addAction(self._actionsMap["what's-this"])

    def _fillToolBarWithActions(self) -> None:
        self._toolBar.addAction(self._actionsMap["new"])
        self._toolBar.addAction(self._actionsMap["open"])
        self._toolBar.addAction(self._actionsMap["save"])

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

    def reinitialize(self, method: datatypes.Method) -> None:
        self.blockSignals(True)
        self._resetClassVariables(method)
        self._connectSignalsAndSlots()
        self._widgets["Analytes And Conditions"].reinitialize(method)
        self._widgets["Calibrations"].reinitialize(method.calibrations)
        self.blockSignals(False)
        self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))
