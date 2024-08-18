# import pandas as pd
#
# from json import dumps, loads
# from PyQt6 import QtCore, QtGui, QtWidgets
#
# from python.utils import encryption
#
# from python.views.base.explorer import Explorer
# from python.views.methodexplorer.calibrationwidget import CalibrationWidget
#
#
# class MethodExplorer(Explorer):
#     def __init__(self, parent: QtWidgets.QWidget | None = None, method: dict | None = None):
#         assert method is not None, "Method must be provided!"
#         super(MethodExplorer, self).__init__(parent)
#         self._method = method
#         self._editedMethod = self._method.copy()
#         self._widgets = {
#             "Analytes And Conditions": AnalytesAndConditionsWidget(self, self._editedMethod),
#             "Calibrations": CalibrationWidget(self, self._editedMethod)
#         }
#         self._widgets = {}
#
#         self.setObjectName("method-explorer")
#         self.setWindowTitle("Method explorer")
#
#         self._createActions(("New", "Open", "Save as", "Close"))
#         self._createMenus(("&File", "&Edit", "&View", "&Window", "&Help"))
#         self._fillMenusWithActions({"file": ["new", "open", "save-as", "close"]})
#         self._createToolBar()
#         self._fillToolBarWithActions(("new", "open", "save-as"))
#         self._createTreeWidget()
#         self._fillTreeWithItems(
#             "Method Contents", ("Analytes And Conditions", "Calibrations")
#         )
#         self._setUpView()
#         self._treeWidget.setCurrentItem(self._treeWidget.topLevelItem(0))
#
#     @QtCore.pyqtSlot()
#     def _actionTriggered(self, key: str) -> None:
#         if key == "new":
#             messageBox = QtWidgets.QMessageBox()
#             messageBox.setIcon(QtWidgets.QMessageBox.Icon.Question)
#             messageBox.setWindowTitle("New method")
#             messageBox.setText("Are you sure you want to open a new method?")
#             messageBox.setStandardButtons(
#                 QtWidgets.QMessageBox.StandardButton.Yes
#                 | QtWidgets.QMessageBox.StandardButton.No
#             )
#             result = messageBox.exec()
#             if result == QtWidgets.QMessageBox.StandardButton.Yes:
#                 self._reinitializeWidget()
#         elif key == "open":
#             filename, filters = QtWidgets.QFileDialog.getOpenFileName(
#                 self,
#                 "Open File",
#                 "./",
#                 "Antique'X Method (*.atxm)",
#             )
#             if filename:
#                 with open(filename, "r") as f:
#                     encryptionKey = encryption.loadKey()
#                     encryptedText = f.readline()
#                     decryptedText = encryption.decryptText(encryptedText, encryptionKey)
#                     method = loads(decryptedText)
#                     self._method = {
#                         "conditions": pd.DataFrame(method["conditions"]),
#                         "lines": pd.DataFrame(method["lines"]),
#                         "calibrations": method["calibrations"],
#                     }
#                     self._reinitializeWidget()
#         elif key == "save-as":
#             filename, filters = QtWidgets.QFileDialog.getSaveFileName(
#                 self,
#                 "Save Method",
#                 "./",
#                 "Antique'X Method (*.atxm)",
#             )
#             if filename:
#                 key = encryption.loadKey()
#                 with open(filename, "wb") as f:
#                     hashableDict = self._toHashableDict(self._method)
#                     jsonText = dumps(hashableDict)
#                     encryptedText = encryption.encryptText(jsonText, key)
#                     f.write(encryptedText + b"\n")
#         elif key == "close":
#             self.close()
#
#     def _reinitializeWidget(self):
#         self._editedMethod = self._method.copy()
#
#         widget = self._mainLayout.itemAt(1).widget()
#         # Get the class name of the widget
#         className = type(widget).__name__
#
#         # Delete the existing widget
#         widget.deleteLater()
#
#         # Dynamically get the class from globals() and create a new instance
#         widgetClass = globals()[className]
#         newWidget = widgetClass(self, self._method)
#         self._mainLayout.addWidget(newWidget)
#
#     @staticmethod
#     def _toHashableDict(method: dict):
#         hashableDicy = method.copy()
#         hashableDicy["conditions"] = method["conditions"].to_dict()
#         hashableDicy["lines"] = method["lines"].to_dict()
#         return hashableDicy
#
#     @QtCore.pyqtSlot()
#     def _changeWidget(self) -> None:
#         oldWidget = self._mainLayout.itemAt(1).widget()
#         oldWidget.hide()
#         selectedItems = self._treeWidget.selectedItems()
#         if selectedItems:
#             selectedItem = selectedItems[0]
#             label = selectedItem.text(0)
#             newWidget = self._widgets[label]
#             self._mainLayout.replaceWidget(oldWidget, newWidget)
#             newWidget.show()
