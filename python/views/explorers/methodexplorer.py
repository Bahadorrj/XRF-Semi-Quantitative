from PyQt6 import QtCore, QtWidgets

from python.utils import datatypes
from python.views.base.explorerwidget import Explorer
from python.views.widgets.analytewidget import AnalytesAndConditionsWidget
from python.views.widgets.calibrationwidget import CalibrationWidget


class MethodExplorer(Explorer):
    def __init__(self, parent: QtWidgets.QWidget | None = None, method: datatypes.Method | None = None):
        assert method is not None, "Method must be provided!"
        super(MethodExplorer, self).__init__(parent)
        self._method = method
        self._initMethod = self._method.copy()
        self._widgets = {
            "Analytes And Conditions": AnalytesAndConditionsWidget(method=self._method),
            "Calibrations": CalibrationWidget(method=self._method),
            "Properties": QtWidgets.QWidget(self)
        }

        self.setObjectName("method-explorer")
        self.setWindowTitle("Method explorer")

        self._createActions(("New", "Open", "Save", "Close"))
        self._createMenus(("&File", "&Edit", "&View", "&Window", "&Help"))
        self._fillMenusWithActions({"file": ["new", "open", "save", "close"]})
        self._createToolBar()
        self._fillToolBarWithActions(("new", "open", "save"))
        self._createTreeWidget()
        self._fillTreeWithItems(
            "Method Contents", ("Analytes And Conditions", "Calibrations", "Properties")
        )
        self._setUpView()
        self._connectSignalsAndSlots()
        self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        if key == "new":
            messageBox = QtWidgets.QMessageBox()
            messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
            messageBox.setWindowTitle("New method")
            messageBox.setText("Are you sure you want to open a new method?")
            messageBox.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
            )
            result = messageBox.exec()
            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                self.reinitialize(self._initMethod)
        elif key == "open":
            filename, filters = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Open File",
                "./",
                "Antique'X Method (*.atxm)",
            )
            if filename:
                pass
        elif key == "save-as":
            filename, filters = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save Method",
                "./",
                "Antique'X Method (*.atxm)",
            )
            if filename:
                pass
        elif key == "close":
            self.close()

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
