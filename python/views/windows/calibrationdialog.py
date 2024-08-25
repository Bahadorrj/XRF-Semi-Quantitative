# import re
# from functools import partial

# import numpy as np
# import pandas as pd
# import pyqtgraph as pg
# from PyQt6 import QtCore, QtGui, QtWidgets
# from scipy.interpolate import CubicSpline
# from scipy.signal import find_peaks

# from python.utils import datatypes, calculation
# from python.utils.database import getDatabase
# from python.utils.paths import resourcePath

# pg.setConfigOptions(antialias=True)


# class AddProfileButton(QtWidgets.QPushButton):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setSizePolicy(
#             QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
#         )
#         self.setStyleSheet(
#             """
#             QPushButton {
#                 background-color: white;
#                 color: black;
#                 border: 1px solid gray;
#                 border-radius: 5px;
#                 font-size: 12px;
#                 height: 1.65em;
#                 width: 1.65em;
#             } 
#         """
#         )


# class GroupBoxButton(QtWidgets.QPushButton):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setStyleSheet(
#             """
#                 QPushButton {
#                 background-color: black;
#                 color: white;
#                 border: 1px solid black;
#                 border-radius: 5px;
#                 padding: 10px;
#                 margin: 10px 5px;
#             }

#             QPushButton:hover {
#                 background-color: white;
#                 color: black;
#             }    

#             QPushButton:pressed {
#                 background-color: whitesmoke;
#                 color: black;
#             }
#         """
#         )


# class ProfileComboBox(QtWidgets.QComboBox):
#     def __init__(self, parent=None):
#         super(ProfileComboBox, self).__init__(parent)
#         self.setStyleSheet(
#             """
#             QComboBox {
#                 border: 1px solid gray;
#                 border-radius: 3px;
#                 padding: 5px;
#                 width: 20px;
#             }
#             QComboBox:hover {
#                 border: 1px solid black;
#             }
#             QComboBox::drop-down {
#                 subcontrol-origin: padding;
#                 subcontrol-position: top right;
#                 width: 15px;
#                 border-left-width: 1px;
#                 border-left-color: darkgray;
#                 border-left-style: solid;
#                 border-top-right-radius: 3px;
#                 border-bottom-right-radius: 3px;
#             }
#             QComboBox::down-arrow {
#                 image: url(icons/down-arrow-resized.png)
#             }
#             QComboBox QAbstractItemView {
#                 border-radius: 3px;
#                 border: 1px solid gray;
#                 selection-background-color: lightgray;
#                 background-color: rgba(135, 206, 250, 128); /* Custom background color for the drop-down menu */
#             }
#         """
#         )


# class GroupBox(QtWidgets.QGroupBox):
#     def __init__(self, parent=None):
#         super(GroupBox, self).__init__(parent)
#         self.setFixedWidth(300)
#         self.setStyleSheet(
#             """
#             QGroupBox {
#                 background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #E0E0E0, stop: 1 #FFFFFF);
#                 border: 2px solid gray;
#                 border-radius: 5px;
#                 margin-top: 1ex; /* leave space at the top for the title */
#             }

#             QGroupBox::title {
#                 subcontrol-origin: margin;
#                 subcontrol-position: top center; /* position at the top center */
#                 padding: 0 3px;
#                 border: 2px solid gray;
#                 border-radius: 5px;
#                 background-color: white;
#             }
#         """
#         )
#         layout = QtWidgets.QFormLayout()
#         layout.setFieldGrowthPolicy(
#             QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
#         )
#         self.setLayout(layout)

#     def clear(self) -> None:
#         while self.layout().rowCount() > 0:
#             self.layout().removeRow(0)


# class Label(QtWidgets.QLabel):
#     def __init__(self, parent=None) -> None:
#         super(Label, self).__init__(parent)
#         self.setStyleSheet(
#             """
#                 QLabel {
#                 background-color: transparent;
#                 margin-top: 10px;
#                 padding: 5px 2px;
#             }
#         """
#         )
#         font = QtGui.QFont()
#         font.setPointSize(11)
#         font.setItalic(True)
#         self.setFont(font)


# class LineEdit(QtWidgets.QLineEdit):
#     def __init__(self, parent=None) -> None:
#         super(LineEdit, self).__init__(parent)
#         self.setStyleSheet(
#             """
#             QLineEdit {
#                 border-radius: 5px;
#                 border: 1px solid gray;
#                 padding: 5px 2px;
#                 margin-top: 10px;
#             }
            
#             QLineEdit:focus {
#                 border: 1px solid black;
#             }
#         """
#         )


# class CalibrationDialog(QtWidgets.QDialog):
#     def __init__(
#         self,
#         parent=None,
#         analyse: datatypes.Analyse = None,
#         blank: datatypes.Analyse = None,
#         condition: int = None,
#     ):
#         super(CalibrationDialog, self).__init__(parent)
#         self._analyse = analyse
#         self._blank = blank
#         self._analyseData = analyse.getDataByConditionId(condition)
#         self._blankData = blank.getDataByConditionId(condition)
#         self._db = getDatabase(resourcePath("fundamentals.db"))
#         self._profiles: pd.DataFrame = self._db.dataframe(
#             "SELECT * FROM BackgroundProfiles"
#         )
#         self._profile = self._profiles.iloc[0]
#         self._tempProfile = None
#         self._optimalY = None
#         self.setStyleSheet("background-color: #FFFFFF")
#         self.resize(1200, 800)
#         self._createActions()
#         self._createToolBar()
#         self._createProfileBox()
#         self._createGeneralDataBox()
#         self._createProfileSelectionLayout()
#         self._createPlotWidget()
#         self._setUpView()
#         self.setModal(True)
#         self._displayCurrentProfile()

#     def _createActions(self) -> None:
#         self._actionsMap = {}
#         actions = ("Run",)
#         for label in actions:
#             action = QtGui.QAction(label)
#             key = "-".join(label.lower().split(" "))
#             action.setIcon(QtGui.QIcon(resourcePath(f"icons/{key}.png")))
#             self._actionsMap[key] = action
#             # signals
#             action.triggered.connect(partial(self._actionTriggered, key))

#     @QtCore.pyqtSlot()
#     def _actionTriggered(self, key: str) -> None:
#         if key == "run":
#             query = f"""
#                 SELECT line_id, low_kiloelectron_volt, high_kiloelectron_volt
#                 FROM Lines
#                 WHERE symbol = '{self._analyse.name}' AND active = 1;
#             """
#             rows = self._db.fetchData(query)
#             for row in rows:
#                 calibrationLineId, calibrationLowKev, calibrationHighKev = row
#                 query = f"DELETE FROM NewInterferences WHERE line1_id = {calibrationLineId}"
#                 self._db.executeQuery(query)
#                 calibrationIntensity = self._optimalY[
#                     round(calculation.evToPx(calibrationLowKev)) : round(
#                         calculation.evToPx(calibrationHighKev)
#                     )
#                 ].sum()
#                 query = f"""
#                     SELECT line_id, low_kiloelectron_volt, high_kiloelectron_volt, condition_id
#                     FROM Lines
#                     WHERE symbol != '{self._analyse.name}' AND active = 1;
#                 """
#                 columns = self._db.fetchData(query)
#                 for column in columns:
#                     interfererLineId, lowKev, highKev, conditionId = column
#                     analyseData = self._analyse.getDataByConditionId(conditionId)
#                     blankData = self._blank.getDataByConditionId(conditionId)
#                     optimalY = self._removeBackgroundFromData(
#                         analyseData, blankData, self._profile
#                     )
#                     intensity = optimalY[
#                         round(calculation.evToPx(lowKev)) : round(
#                             calculation.evToPx(highKev)
#                         )
#                     ].sum()
#                     query = f"""
#                         INSERT INTO NewInterferences (line1_id, line2_id, coefficient)
#                         VALUES ({calibrationLineId}, {interfererLineId}, {intensity / calibrationIntensity});
#                     """
#                     self._db.executeQuery(query)
#             self.accept()

#     def _createToolBar(self) -> None:
#         self._toolBar = QtWidgets.QToolBar(self)
#         self._toolBar.setIconSize(QtCore.QSize(16, 16))
#         self._toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
#         self._toolBar.setMovable(False)
#         self._fillToolBarWithActions()

#     def _fillToolBarWithActions(self) -> None:
#         self._toolBar.addAction(self._actionsMap["run"])

#     def _createProfileSelectionLayout(self) -> None:
#         self._profileSelectionLayout = QtWidgets.QHBoxLayout()
#         label = QtWidgets.QLabel("Select profile: ")
#         label.setSizePolicy(
#             QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
#         )
#         self._profileComboBox = ProfileComboBox(self)
#         if not self._profiles.empty:
#             self._profileComboBox.addItems(self._profiles["name"])
#         addProfileButton = AddProfileButton()
#         addProfileButton.setIcon(QtGui.QIcon(resourcePath("icons/plus.png")))
#         editProfileButton = AddProfileButton()
#         editProfileButton.setIcon(QtGui.QIcon(resourcePath("icons/pencil.png")))
#         self._profileSelectionLayout.addWidget(label)
#         self._profileSelectionLayout.addWidget(self._profileComboBox)
#         self._profileSelectionLayout.addWidget(editProfileButton)
#         self._profileSelectionLayout.addWidget(addProfileButton)
#         # signals
#         self._profileComboBox.currentTextChanged.connect(self._profileChanged)
#         addProfileButton.clicked.connect(self._inputProfileBox)
#         editProfileButton.clicked.connect(partial(self._inputProfileBox, "edit"))

#     @QtCore.pyqtSlot(str)
#     def _profileChanged(self, text: str) -> None:
#         self._profile = self._profiles.query(f"name == '{text}'").iloc[0]
#         self._displayCurrentProfile()

#     def _displayCurrentProfile(self) -> None:
#         self.drawAnalyseData(self._analyseData, self._blankData, self._profile)
#         self._profileBox.clear()
#         for name, value in self._profile[1:].items():
#             nameLabel = Label(self)
#             nameLabel.setText(name)
#             valueLabel = Label(self)
#             valueLabel.setText(value)
#             spacerItem = QtWidgets.QSpacerItem(
#                 0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
#             )
#             layout = QtWidgets.QHBoxLayout()
#             layout.addWidget(nameLabel)
#             layout.addItem(spacerItem)
#             layout.addWidget(valueLabel)
#             self._profileBox.layout().addRow(layout)

#     @QtCore.pyqtSlot()
#     def _inputProfileBox(self, mode: str = "new") -> None:
#         self._profileBox.clear()
#         self._tempProfile = self._profile.copy()
#         for name in self._profiles.columns[1:]:
#             nameLabel = Label(self)
#             nameLabel.setText(name)
#             lineEdit = LineEdit(self)
#             if mode == "edit":
#                 lineEdit.setText(self._profile[name])
#             self._profileBox.layout().addRow(nameLabel, lineEdit)
#             # signals
#             lineEdit.editingFinished.connect(
#                 partial(self._editingFinished, name, lineEdit)
#             )
#         addButton = GroupBoxButton(self)
#         if mode == "edit":
#             addButton.setText("Apply")
#             addButton.clicked.connect(self._editProfile)
#         else:
#             for name, value in self._tempProfile.items():
#                 self._tempProfile[name] = None
#             addButton.setText("Add")
#             addButton.clicked.connect(self._addProfile)
#         cancelButton = GroupBoxButton(self)
#         cancelButton.setText("Cancel")
#         cancelButton.clicked.connect(self._displayCurrentProfile)
#         layout = QtWidgets.QHBoxLayout()
#         layout.addWidget(addButton)
#         layout.addWidget(cancelButton)
#         self._profileBox.layout().addRow(layout)

#     @QtCore.pyqtSlot(str, QtWidgets.QLineEdit)
#     def _editingFinished(self, name: str, lineEdit: QtWidgets.QLineEdit) -> None:
#         if name == "name":
#             self._tempProfile["name"] = lineEdit.text()
#             return
#         if name in ["smoothness", "rel_height", "distance"]:
#             pattern = re.compile(r"^\d+(\.\d+)?$|^$")
#         elif name == "wlen":
#             pattern = re.compile(r"^\d+$|^$")
#         else:
#             pattern = re.compile(
#                 r"^-?\d+(\.\d+)?$|^\(-?\d+(\.\d+)?, *-?\d+(\.\d+)?\)$|^$"
#             )
#         if not re.match(pattern, lineEdit.text()):
#             lineEdit.setText("Invalid!")
#         else:
#             if name == "smoothness":
#                 if 1 <= eval(lineEdit.text()) <= 25:
#                     self._tempProfile[name] = lineEdit.text()
#                 else:
#                     lineEdit.setText(self._profile[name])
#             else:
#                 self._tempProfile[name] = (
#                     None if not lineEdit.text() else lineEdit.text()
#                 )
#         self.drawAnalyseData(self._analyseData, self._blankData, self._tempProfile)

#     @QtCore.pyqtSlot()
#     def _addProfile(self) -> None:
#         self._profile = self._tempProfile.copy()
#         columns = ", ".join(self._profile.index[1:])
#         placeholders = ", ".join(["?" for _ in self._profile[1:]])
#         values = [None if v is np.nan else v for v in self._profile.values[1:]]
#         query = (
#             f"INSERT INTO BackgroundProfiles ({columns}) VALUES ({placeholders})"
#         )
#         self._db.executeQuery(query, values)
#         self._profiles = self._db.dataframe("SELECT * FROM BackgroundProfiles")
#         self._profileComboBox.addItem(values[0])
#         self._profileComboBox.setCurrentText(values[0])

#     def _editProfile(self) -> None:
#         self._profile = self._tempProfile.copy()
#         for name, value in self._profile[1:].items():
#             if value is not None:
#                 query = f"UPDATE BackgroundProfiles SET {name} = '{value}' WHERE profile_id = {self._profile['profile_id']}"
#                 self._db.executeQuery(query)
#             else:
#                 query = f"UPDATE BackgroundProfiles SET {name} = NULL WHERE profile_id = {self._profile['profile_id']}"
#                 self._db.executeQuery(query)
#         self._profiles = self._db.dataframe("SELECT * FROM BackgroundProfiles")
#         currentIndex = self._profileComboBox.currentIndex()
#         self._profileComboBox.blockSignals(True)
#         self._profileComboBox.removeItem(currentIndex)
#         self._profileComboBox.insertItem(currentIndex, self._profile.values[1])
#         self._profileComboBox.blockSignals(False)
#         self._displayCurrentProfile()

#     def _createPlotWidget(self) -> None:
#         self._plotWidget = pg.PlotWidget(self)
#         self._plotWidget.setBackground("#FFFFFF")
#         self._plotWidget.setFrameShape(QtWidgets.QFrame.Shape.Box)
#         self._plotWidget.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
#         self._plotWidget.setStyleSheet("border: 1px solid gray;")
#         plotItem = self._plotWidget.getPlotItem()
#         plotItem.setContentsMargins(10, 10, 10, 10)
#         self._legend = plotItem.addLegend(
#             offset=(-25, 25),
#             pen=pg.mkPen(color="#E0E0E0", width=1),
#             brush=pg.mkBrush(color="#F2F2F2"),
#         )

#     def plot(self, x: np.ndarray, y: np.ndarray, *args, **kwargs) -> None:
#         self._plotWidget.plot(x, y, *args, **kwargs)

#     def clearPlot(self) -> None:
#         self._plotWidget.clear()

#     def _setLimit(self) -> None:
#         xMin = -100
#         xMax = self._analyseData.x.max() + 100
#         yMin = -self._analyseData.y.max() * 0.1
#         yMax = self._analyseData.y.max() * 1.1
#         self._plotWidget.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

#     def _createProfileBox(self):
#         self._profileBox = GroupBox(self)
#         self._profileBox.setTitle("Profile")

#     def _createGeneralDataBox(self) -> None:
#         self._generalBox = GroupBox(self)
#         self._generalBox.setTitle("General Data")

#     def _setUpView(self) -> None:
#         self._mainLayout = QtWidgets.QGridLayout()
#         self._mainLayout.addWidget(self._toolBar, 0, 0, 1, 4)
#         self._mainLayout.addLayout(self._profileSelectionLayout, 1, 0, 1, 3)
#         self._mainLayout.addWidget(self._plotWidget, 2, 0, 5, 3)
#         self._mainLayout.addWidget(self._profileBox, 1, 3, 3, 1)
#         self._mainLayout.addWidget(self._generalBox, 4, 3, 3, 1)
#         self.setLayout(self._mainLayout)

#     def drawAnalyseData(
#         self,
#         analyseData: datatypes.AnalyseData,
#         blankData: datatypes.AnalyseData,
#         profile: pd.Series | dict,
#     ) -> None:
#         x = analyseData.x
#         y = analyseData.y
#         self._optimalY = self._removeBackgroundFromData(analyseData, blankData, profile)
#         self.clearPlot()
#         self.plot(x, y, name="Original", pen=pg.mkPen(color="#FF7F0EFF", width=2))
#         self.plot(
#             x, self._optimalY, name="Optimal", pen=pg.mkPen(color="#1F77B4FFf", width=2)
#         )
#         self._setLimit()

#     def _removeBackgroundFromData(
#         self,
#         analyseData: datatypes.AnalyseData,
#         blankData: datatypes.AnalyseData,
#         profile: pd.Series | dict,
#     ) -> np.ndarray:
#         optimalY = analyseData.y - blankData.y
#         if isinstance(profile, pd.Series):
#             kwargs = {}
#             for name, value in profile.items():
#                 if name not in ["profile_id", "name"] and value is not None:
#                     kwargs[name] = eval(str(value))
#         else:
#             kwargs = profile
#         xSmooth, ySmooth = self.smooth(analyseData.x, optimalY, kwargs["smoothness"])
#         kwargs.pop("smoothness")
#         if kwargs:
#             peaks, _ = find_peaks(-ySmooth, **kwargs)
#         else:
#             peaks, _ = find_peaks(-ySmooth)
#         if peaks.size != 0:
#             regressionCurve = np.interp(analyseData.x, xSmooth[peaks], ySmooth[peaks])
#             optimalY = (optimalY - regressionCurve).clip(0)
#         return optimalY

#     @staticmethod
#     def smooth(
#         x: np.ndarray, y: np.ndarray, level: float
#     ) -> tuple[np.ndarray, np.ndarray]:
#         cs = CubicSpline(x, y)
#         # Generate finer x values for smoother plot
#         X = np.linspace(0, x.size, int(x.size / level))
#         # Interpolate y values for the smoother plot
#         Y = cs(X)
#         return X, Y
