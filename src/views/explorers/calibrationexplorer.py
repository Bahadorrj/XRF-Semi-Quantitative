from PyQt6 import QtCore, QtGui, QtWidgets

from src.utils import datatypes
from src.utils.paths import resourcePath
from src.views.base.explorerwidget import Explorer
from src.views.widgets.coefficientwidget import CoefficientWidget
from src.views.widgets.generaldatawidget import GeneralDataWidget
from src.views.widgets.peaksearchwidget import PeakSearchWidget


class CalibrationExplorer(Explorer):
    def __init__(self, parent: QtWidgets.QWidget | None = None, calibration: datatypes.Calibration | None = None):
        super(CalibrationExplorer, self).__init__(parent)
        self._calibration = calibration
        self._initCalibration = None
        self._widgets = None
        self._initializeUi()
        if self._calibration is not None:
            self._initCalibration = self._calibration.copy()
            self._widgets = {
                "General Data": GeneralDataWidget(calibration=calibration),
                "Condition": PeakSearchWidget(calibration=self._calibration),
                "Coefficient": CoefficientWidget(calibration=self._calibration)
            }
            self._implementAnalyse()
            self._connectSignalsAndSlots()
            self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))

    def _initializeUi(self) -> None:
        self.setObjectName("calibration-explorer")
        self.setWindowTitle("Calibration explorer")

        self._createActions(("New", "Open", "Save", "Close"))
        self._createMenus(("&File", "&Edit", "&View", "&Window", "&Help"))
        self._fillMenusWithActions()
        self._createToolBar()
        self._fillToolBarWithActions()
        self._createTreeWidget()
        self._fillTreeWithItems(
            "Calibration Contents",
            ("General Data", "Peak Search", "Coefficient"),
        )
        self._setUpView()

    def _connectSignalsAndSlots(self) -> None:
        super()._connectSignalsAndSlots()
        self._widgets["Condition"].analyseRadiationChanged.connect(
            self._widgets["Coefficient"].reinitializeRadiations
        )

    def _resetClassVariables(self, calibration: datatypes.Calibration) -> None:
        self._calibration = calibration
        self._initCalibration = calibration.copy()

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        if key == "new":
            messageBox = QtWidgets.QMessageBox()
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
            messageBox.setWindowTitle("New method")
            messageBox.setText("Are you sure you want to reset all the changes?")
            messageBox.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
            )
            result = messageBox.exec()
            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                self.reinitialize(self._initCalibration)

    def _fillMenusWithActions(self) -> None:
        self._menusMap["file"].addAction(self._actionsMap["new"])
        self._menusMap["file"].addAction(self._actionsMap["open"])
        self._menusMap["file"].addAction(self._actionsMap["save"])
        self._menusMap["file"].addAction(self._actionsMap["close"])

    def _fillToolBarWithActions(self) -> None:
        self._toolBar.addAction(self._actionsMap["new"])
        self._toolBar.addAction(self._actionsMap["open"])
        self._toolBar.addAction(self._actionsMap["save"])

    @QtCore.pyqtSlot()
    def _changeWidget(self):
        selectedItems = self._treeWidget.selectedItems()
        if selectedItems:
            selectedItem = selectedItems[0]
            label = selectedItem.text(0)
            if label == 'Peak Search':
                return
            oldWidget = self.mainLayout.itemAt(1).widget()
            oldWidget.hide()
            if "Condition" in label:
                newWidget = self._widgets["Condition"]
                newWidget.displayAnalyseData(int(label.split(' ')[-1]))
            else:
                newWidget = self._widgets[label]
            self.mainLayout.replaceWidget(oldWidget, newWidget)
            newWidget.show()

    def _implementAnalyse(self) -> None:
        for topLevelIndex in range(1, self._treeWidget.topLevelItemCount()):
            item = self._treeWidget.topLevelItem(topLevelIndex)
            while item.childCount() != 0:
                item.takeChild(0)
        for data in self._calibration.analyse.data:
            child = QtWidgets.QTreeWidgetItem()
            child.setText(0, f"Condition {data.conditionId}")
            child.setIcon(0, QtGui.QIcon(resourcePath("icons/condition.png")))
            self._treeItemMap['peak-search'].addChild(child)
            self._treeWidget.expandItem(self._treeItemMap['peak-search'])

    def reinitialize(self, calibration: datatypes.Calibration):
        self.blockSignals(True)
        self._resetClassVariables(calibration)
        self._implementAnalyse()
        self._connectSignalsAndSlots()
        for widget in self._widgets.values():
            widget.reinitialize(calibration)
        self.blockSignals(False)
        self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))
