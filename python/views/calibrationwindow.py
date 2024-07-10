import re
from functools import partial

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt6 import QtCore, QtGui, QtWidgets
from scipy.interpolate import CubicSpline
from scipy.signal import find_peaks

from python.utils import datatypes, calculation
from python.utils.database import getDatabase
from python.utils.paths import resourcePath

pg.setConfigOptions(antialias=True)


class AddProfileButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(AddProfileButton, self).__init__(parent)
        self.setIcon(QtGui.QIcon(resourcePath("icons/plus.png")))
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.setStyleSheet(
            """
            QPushButton {
                border: 1px solid gray;
                background-color: #FFFFFF;
                font-size: 12px;
                height: 1.65em;
                width: 1.65em;
                border-radius: 5px;
            }
        """
        )


class ProfileComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(ProfileComboBox, self).__init__(parent)
        self.setStyleSheet(
            """
            QComboBox {
                border: 1px solid gray;
                border-radius: 3px;
                padding: 5px;
                width: 20px;
            }
            QComboBox:hover {
                border: 1px solid black;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow {
                image: url(icons/down-arrow-resized.png)
            }
            QComboBox QAbstractItemView {
                border-radius: 3px;
                border: 1px solid gray;
                selection-background-color: lightgray;
                background-color: rgba(135, 206, 250, 128); /* Custom background color for the drop-down menu */
            }
        """
        )


class GroupBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(GroupBox, self).__init__(parent)
        self.setFixedWidth(300)
        self.setStyleSheet(
            """
            QGroupBox {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #E0E0E0, stop: 1 #FFFFFF);
                border: 2px solid gray;
                border-radius: 5px;
                margin-top: 1ex; /* leave space at the top for the title */
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center; /* position at the top center */
                padding: 0 3px;
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #FFOECE, stop: 1 #FFFFFF);
            }
        """
        )


class AddProfileDialog(QtWidgets.QDialog):
    profileAdded = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(AddProfileDialog, self).__init__(parent)
        self._db = getDatabase(resourcePath("fundamentals.db"))
        self._profiles: pd.DataFrame = self._db.dataframe(
            "SELECT * FROM BackgroundProfiles"
        )
        self._profile = {key: None for key in self._profiles.columns[1:]}
        self._setUpView()

    def _setUpView(self) -> None:
        mainLayout = QtWidgets.QVBoxLayout()
        formLayout = QtWidgets.QFormLayout()
        for name in self._profiles.columns[1:]:
            lineEdit = QtWidgets.QLineEdit(self)
            formLayout.addRow(name, lineEdit)
            lineEdit.editingFinished.connect(
                partial(self._editingFinished, name, lineEdit)
            )

        mainLayout.addLayout(formLayout)
        spacerItem = QtWidgets.QSpacerItem(
            0,
            30,
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        mainLayout.addItem(spacerItem)
        addButton = QtWidgets.QPushButton("Add")
        cancelButton = QtWidgets.QPushButton("Cancel")
        hLayout = QtWidgets.QHBoxLayout()
        hLayout.addWidget(addButton)
        hLayout.addWidget(cancelButton)
        mainLayout.addLayout(hLayout)
        self.setLayout(mainLayout)
        cancelButton.clicked.connect(self.reject)
        addButton.clicked.connect(self.accept)
        addButton.clicked.connect(self._addProfile)

    @QtCore.pyqtSlot(str, QtWidgets.QLineEdit)
    def _editingFinished(self, name: str, lineEdit: QtWidgets.QLineEdit) -> None:
        if name == "name":
            self._profile["name"] = lineEdit.text()
            return
        if name in ["smoothness", "rel_height", "distance"]:
            pattern = re.compile(r"^\d+(\.\d+)?$")
        elif name == "wlen":
            pattern = re.compile(r"^\d+$")
        else:
            pattern = re.compile(
                r"^("
                r"\d+(\.\d+)?"  # A single number
                r"|\(\d+(\.\d+)?,\s*\d+(\.\d+)?\)"  # A tuple of two numbers
                r")$"
            )
        if not re.match(pattern, lineEdit.text()):
            lineEdit.setText("Invalid!")
        else:
            self._profile[name] = lineEdit.text()

    @QtCore.pyqtSlot()
    def _addProfile(self) -> None:
        columns = ", ".join(self._profile.keys())
        placeholders = ", ".join(["?" for _ in self._profile])
        values = [None if v is None else v for v in self._profile.values()]
        query = f"INSERT INTO BackgroundProfiles ({columns}) VALUES ({placeholders})"
        self._db.executeQuery(query, values)
        self.profileAdded.emit(values[0])


class CalibrationWindow(QtWidgets.QMainWindow):
    def __init__(
        self,
        parent=None,
        analyse: datatypes.Analyse = None,
        blank: datatypes.Analyse = None,
        condition: int = None,
    ):
        super(CalibrationWindow, self).__init__(parent)
        self._analyse = analyse
        self._blank = blank
        self._analyseData = analyse.getDataByConditionId(condition)
        self._blankData = blank.getDataByConditionId(condition)
        self._db = getDatabase(resourcePath("fundamentals.db"))
        self._profiles: pd.DataFrame = self._db.dataframe(
            "SELECT * FROM BackgroundProfiles"
        )
        self.setStyleSheet("background-color: #FFFFFF")
        self.resize(1200, 800)
        self._createActions()
        self._createToolBar()
        self._createProfileBox()
        self._createGeneralDataBox()
        self._createProfileLayout()
        self._createPlotWidget()
        self._setUpView()
        self.drawAnalyseData(self._analyseData, self._blankData, self._profiles.iloc[0])

    def _createActions(self) -> None:
        self._actionsMap = {}
        actions = ("Run",)
        for label in actions:
            action = QtGui.QAction(label)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"icons/{key}.png")))
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        return
        if key == "run":
            query = f"""
                SELECT line_id, low_kiloelectron_volt, high_kiloelectron_volt
                FROM Lines
                WHERE symbol = '{self._calibration.name}' AND active = 1;
            """
            rows = self._db.fetchData(query)
            for row in rows:
                calibrationLineId, calibrationLowKev, calibrationHighKev = row
                calibrationIntensity = self._optimalY[
                    round(calculation.evToPx(calibrationLowKev)) : round(
                        calculation.evToPx(calibrationHighKev)
                    )
                ].sum()
                query = f"""
                    SELECT line_id, low_kiloelectron_volt, high_kiloelectron_volt, condition_id
                    FROM Lines
                    WHERE symbol != '{self._calibration.name}' AND active = 1;
                """
                columns = self._db.fetchData(query)
                for column in columns:
                    interfererLineId, lowKev, highKev, conditionId = column
                    analyseData = self._calibration.getDataByConditionId(conditionId)
                    blankData = self._blank.getDataByConditionId(conditionId)
                    # TODO what profile?
                    optimalY = self._removeBackgroundFromData(
                        analyseData,
                        blankData,
                    )
                    intensity = optimalY[
                        round(calculation.evToPx(lowKev)) : round(
                            calculation.evToPx(highKev)
                        )
                    ].sum()
                    query = f"""
                        INSERT INTO NewInterferences (line1_id, line2_id, coefficient)
                        VALUES ({calibrationLineId}, {interfererLineId}, {intensity / calibrationIntensity});
                    """
                    self._db.executeQuery(query)

    def _createToolBar(self) -> None:
        toolBar = QtWidgets.QToolBar(self)
        toolBar.setIconSize(QtCore.QSize(16, 16))
        toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolBar.setMovable(False)
        self._fillToolBarWithActions(toolBar)
        self.addToolBar(toolBar)

    def _fillToolBarWithActions(self, toolBar: QtWidgets.QToolBar) -> None:
        toolBar.addAction(self._actionsMap["run"])

    def _createProfileLayout(self) -> None:
        self._profileLayout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Select profile: ")
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._profileComboBox = ProfileComboBox(self)
        self._profileComboBox.addItems(self._profiles["name"])
        self._displayProfileInForm(self._profiles.iloc[0])
        addProfileButton = AddProfileButton()
        self._profileLayout.addWidget(label)
        self._profileLayout.addWidget(self._profileComboBox)
        self._profileLayout.addWidget(addProfileButton)
        self._profileComboBox.currentTextChanged.connect(self._profileChanged)
        addProfileButton.clicked.connect(self._openAddProfileDialog)

    @QtCore.pyqtSlot(str)
    def _profileChanged(self, text: str) -> None:
        profile = self._profiles.query(f"name == '{text}'").iloc[0]
        self.drawAnalyseData(self._analyseData, self._blankData, profile)
        self._displayProfileInForm(profile)

    def _displayProfileInForm(self, profile: pd.Series) -> None:
        if self._profileBoxLayout.count() != 0:
            for row in range(1, self._profileBoxLayout.count(), 2):
                self._profileBoxLayout.itemAt(row).widget().setText(
                    f"{profile[self._profileBoxLayout.itemAt(row - 1).widget().text()]}"
                )
        else:
            for name in self._profiles.columns[1:]:
                nameLabel = QtWidgets.QLabel(name)
                nameLabel.setStyleSheet("background-color: transparent;")
                nameLabel.setFixedWidth(150)
                font = QtGui.QFont()
                font.setPointSize(11)
                font.setItalic(True)
                nameLabel.setFont(font)
                valueLabel = QtWidgets.QLabel(f"{profile[name]}")
                valueLabel.setStyleSheet("background-color: transparent;")
                font = QtGui.QFont()
                font.setPointSize(11)
                font.setItalic(True)
                valueLabel.setFont(font)
                self._profileBox.layout().addRow(nameLabel, valueLabel)

    @QtCore.pyqtSlot()
    def _openAddProfileDialog(self) -> None:
        addProfileDialog = AddProfileDialog(self)
        addProfileDialog.show()
        addProfileDialog.profileAdded.connect(self._addProfile)

    @QtCore.pyqtSlot(str)
    def _addProfile(self, text: str) -> None:
        self._profileComboBox.addItem(text)
        self._profiles = self._db.dataframe("SELECT * FROM BackgroundProfiles")

    def _createPlotWidget(self) -> None:
        self._plotWidget = pg.PlotWidget(self)
        self._plotWidget.setBackground("#FFFFFF")
        self._plotWidget.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self._plotWidget.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self._plotWidget.setStyleSheet("border: 1px solid gray;")
        plotItem = self._plotWidget.getPlotItem()
        plotItem.setContentsMargins(10, 10, 10, 10)
        self._legend = plotItem.addLegend(
            offset=(-25, 25),
            pen=pg.mkPen(color="#E0E0E0", width=1),
            brush=pg.mkBrush(color="#F2F2F2"),
        )

    def plot(self, x: np.ndarray, y: np.ndarray, *args, **kwargs) -> None:
        self._plotWidget.plot(x, y, *args, **kwargs)

    def clearPlot(self) -> None:
        self._plotWidget.clear()

    def _setLimit(self) -> None:
        xMin = -100
        xMax = self._analyseData.x.max() + 100
        yMin = -self._analyseData.y.max() * 0.1
        yMax = self._analyseData.y.max() * 1.1
        self._plotWidget.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

    def _createProfileBox(self):
        self._profileBox = GroupBox(self)
        self._profileBoxLayout = QtWidgets.QFormLayout()
        self._profileBoxLayout.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        self._profileBox.setLayout(self._profileBoxLayout)
        self._profileBox.setTitle("Profile")

    def _createGeneralDataBox(self) -> None:
        self._generalBox = GroupBox(self)
        self._generalBox.setTitle("General Data")

    def _setUpView(self) -> None:
        mainLayout = QtWidgets.QGridLayout()
        mainLayout.addLayout(self._profileLayout, 0, 0, 1, 3)
        mainLayout.addWidget(self._plotWidget, 1, 0, 5, 3)
        mainLayout.addWidget(self._profileBox, 0, 3, 3, 1)
        mainLayout.addWidget(self._generalBox, 3, 3, 3, 1)
        mainWidget = QtWidgets.QWidget(self)
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

    def drawAnalyseData(
        self,
        analyseData: datatypes.AnalyseData,
        blankData: datatypes.AnalyseData,
        profile: pd.Series,
    ) -> None:
        x = analyseData.x
        y = analyseData.y
        self._optimalY = self._removeBackgroundFromData(analyseData, blankData, profile)

        self.clearPlot()
        self.plot(x, y, name="Original", pen=pg.mkPen(color="#FF7F0EFF", width=2))
        self.plot(
            x, self._optimalY, name="Optimal", pen=pg.mkPen(color="#1F77B4FFf", width=2)
        )
        self._setLimit()

    def _removeBackgroundFromData(
        self,
        analyseData: datatypes.AnalyseData,
        blankData: datatypes.AnalyseData,
        profile: pd.Series,
    ) -> np.ndarray:
        kwargs = {}
        for name, value in profile.items():
            if name not in ["profile_id", "name"] and value is not None:
                kwargs[name] = eval(str(value))
        optimalY = analyseData.y - blankData.y
        xSmooth, ySmooth = self.smooth(analyseData.x, optimalY, kwargs["smoothness"])
        kwargs.pop("smoothness")
        if kwargs:
            peaks, _ = find_peaks(-ySmooth, **kwargs)
        else:
            peaks, _ = find_peaks(-ySmooth)
        if peaks.size != 0:
            regressionCurve = np.interp(analyseData.x, xSmooth[peaks], ySmooth[peaks])
            optimalY = (optimalY - regressionCurve).clip(0)
        return optimalY

    @staticmethod
    def smooth(
        x: np.ndarray, y: np.ndarray, level: float
    ) -> tuple[np.ndarray, np.ndarray]:
        cs = CubicSpline(x, y)
        # Generate finer x values for smoother plot
        X = np.linspace(0, x.size, int(x.size / level))
        # Interpolate y values for the smoother plot
        Y = cs(X)
        return X, Y
