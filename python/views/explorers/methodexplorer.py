from PyQt6 import QtCore, QtWidgets

from python.utils import datatypes
from python.views.base.explorerwidget import Explorer
from python.views.widgets.analytewidget import AnalytesAndConditionsWidget


class MethodExplorer(Explorer):
    def __init__(self, parent: QtWidgets.QWidget | None = None, method: datatypes.Method | None = None):
        super(MethodExplorer, self).__init__(parent)
        self._method = method
        self._initMethod = None
        self._widgets = None
        self._initializeUi()
        if self._method is not None:
            self._initMethod = self._method.copy()
            self._widgets = {
                "Analytes And Conditions": AnalytesAndConditionsWidget(method=self._method),
                "Calibrations": QtWidgets.QWidget(self),
                "Properties": QtWidgets.QWidget(self)
            }
            self._connectSignalsAndSlots()
            self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))

    def _initializeUi(self) -> None:
        self.setObjectName("method-explorer")
        self.setWindowTitle("Method explorer")
        self._createActions(("New", "Open", "Save", "Close"))
        self._createMenus(("&File", "&Edit", "&View", "&Window", "&Help"))
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
        pass

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
    def _changeWidget(self) -> None:
        selectedItems = self._treeWidget.selectedItems()
        if selectedItems:
            selectedItem = selectedItems[0]
            label = selectedItem.text(0)
            oldWidget = self.mainLayout.itemAt(1).widget()
            oldWidget.hide()
            newWidget = self._widgets[label]
            self.mainLayout.replaceWidget(oldWidget, newWidget)
            newWidget.show()
            newWidget.setFocus()

    def reinitialize(self, method: datatypes.Method) -> None:
        pass
