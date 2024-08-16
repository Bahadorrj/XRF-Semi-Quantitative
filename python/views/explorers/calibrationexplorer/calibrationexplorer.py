from PyQt6 import QtCore, QtGui, QtWidgets

from python.views.explorers.explorer import Explorer
from python.utils.paths import resourcePath

from python.views.explorers.calibrationexplorer.generaldatawidget import GeneralDataWidget
from python.views.explorers.calibrationexplorer.plotwidget import PlotWidget
from python.views.explorers.calibrationexplorer.linestablewidget import LinesTableWidget
from python.views.explorers.calibrationexplorer.peaksearchwidget import PeakSearchWidget
from python.views.explorers.calibrationexplorer.coefficientwidget import CoefficientWidget


class CalibrationExplorer(Explorer):
    def __init__(self, parent: QtWidgets.QWidget | None = None, calibration: dict | None = None):
        assert calibration is not None, "Calibration must be provided"
        super(CalibrationExplorer, self).__init__(parent)
        self._calibration = calibration
        self._widgets = {
            "General Data": GeneralDataWidget(),
            "Spectrum": PlotWidget(calibration=self._calibration),
            "Peak Search": LinesTableWidget(calibration=self._calibration),
            "Condition": PeakSearchWidget(calibration=self._calibration),
            "Coefficient": CoefficientWidget(calibration=self._calibration)
        }
        
        self.setObjectName("calibration-explorer")
        self.setWindowTitle("Calibration explorer")

        self._createActions(("New", "Open", "Save as", "Close"))
        self._createMenus(("&File", "&Edit", "&View", "&Window", "&Help"))
        self._fillMenusWithActions({"file": ["new", "open", "save-as", "close"]})
        self._createToolBar()
        self._fillToolBarWithActions(("new", "open", "save-as"))
        self._createTreeWidget()
        self._fillTreeWithItems(
            "Calibration Contents",
            ("General Data", "Spectrum", "Peak Search", "Coefficient", "Interferences"),
        )
        self._implementAnalyse()
        self._setUpView()
        self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))
    
    def _implementAnalyse(self) -> None:
        for data in self._calibration["analyse"].data:
            child = QtWidgets.QTreeWidgetItem()
            child.setText(0, f"Condition {data.condition}")
            child.setIcon(0, QtGui.QIcon(resourcePath("icons/condition.png")))
            self._treeItemMap['peak-search'].addChild(child)

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        pass

    @QtCore.pyqtSlot()
    def _changeWidget(self):
        selectedItems = self._treeWidget.selectedItems()
        if selectedItems:
            selectedItem = selectedItems[0]
            label = selectedItem.text(0)
            oldWidget = self._mainLayout.itemAt(1).widget()
            oldWidget.hide()
            if "Condition" in label:
                newWidget = self._widgets["Condition"]
                newWidget.displayAnalyseData(int(label.split(' ')[-1]))
            else:
                newWidget = self._widgets[label]
            self._mainLayout.replaceWidget(oldWidget, newWidget)
            newWidget.show()
