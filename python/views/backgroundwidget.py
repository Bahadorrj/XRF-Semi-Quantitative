from typing import Optional

import matplotlib
import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from scipy.interpolate import CubicSpline
from scipy.signal import find_peaks

from python.utils import datatypes
from python.utils.database import getDatabase
from python.utils.paths import resourcePath

matplotlib.use('QtAgg')


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class ComboBox(QtWidgets.QComboBox):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
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
        """)


class CalibrationBackgroundWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, analyseData: datatypes.AnalyseData = None, blank: datatypes.AnalyseData = None):
        super(CalibrationBackgroundWidget, self).__init__(parent)
        self._data = analyseData
        self._blank = blank
        self._db = getDatabase(resourcePath("fundamentals.db"))
        self._plotWidget: Optional[MplCanvas] = None
        self.resize(800, 600)
        self._createPlotWidget()
        self._setUpView()
        self._plotAnalyseData()

    def _createProfileSelectionLayout(self) -> QtWidgets.QHBoxLayout:
        label = QtWidgets.QLabel("Select profile: ")
        label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self._profileComboBox = ComboBox(self)
        query = "SELECT name FROM BackgroundProfiles"
        profiles = [t[0] for t in self._db.executeQuery(query).fetchall()]
        self._profileComboBox.addItems(profiles)
        addProfileButton = QtWidgets.QPushButton(icon=QtGui.QIcon(resourcePath("icons/plus.png")))
        addProfileButton.setStyleSheet("""
            QPushButton {
                border: 1px solid gray;
                background-color: #fff;
                font-size: 12px;
                height: 1.65em;
                width: 1.65em;
                border-radius: 5px;
            }
        """)
        addProfileButton.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        backgroundProfileLayout = QtWidgets.QHBoxLayout()
        backgroundProfileLayout.addWidget(label)
        backgroundProfileLayout.addWidget(self._profileComboBox)
        backgroundProfileLayout.addWidget(addProfileButton)
        self._profileComboBox.currentTextChanged.connect(self._profileChanged)
        addProfileButton.clicked.connect(self._addProfile)
        label.linkActivated.connect(self._openInterferencesWindow)
        return backgroundProfileLayout

    @QtCore.pyqtSlot(str)
    def _profileChanged(self, text: str) -> None:
        pass

    @QtCore.pyqtSlot()
    def _addProfile(self) -> None:
        pass

    @QtCore.pyqtSlot()
    def _openInterferencesWindow(self) -> None:
        pass

    def _createPlotWidget(self) -> None:
        self._canvas = MplCanvas(self)
        self._plt = self._canvas.axes
        self._plotToolBar = NavigationToolbar(self._canvas, self)

    def plot(self, x: np.ndarray, y: np.ndarray, *args, **kwargs) -> None:
        self._plt.plot(x, y, *args, **kwargs)

    def clearPlot(self) -> None:
        self._plt.cla()
        self._canvas.figure.tight_layout()
        self._canvas.draw()

    def _setUpView(self):
        mainLayout = QtWidgets.QVBoxLayout()
        hLayout = self._createProfileSelectionLayout()
        mainLayout.addLayout(hLayout)
        mainLayout.addWidget(self._plotToolBar)
        mainLayout.addWidget(self._canvas)
        self.setLayout(mainLayout)

    def _plotAnalyseData(self) -> None:
        if self._data is None:
            return
        self.clearPlot()
        x = self._data.x
        y = self._data.y
        self.plot(x, y, label="Original")
        if self._blank is not None:
            y -= self._blank.y
        xSmooth, ySmooth = self._smooth(x, y, 2.5)
        peaks, _ = find_peaks(-ySmooth)
        regressionCurve = np.interp(x, xSmooth[peaks], ySmooth[peaks])
        y = (y - regressionCurve).clip(0)
        self.plot(x, y, label="Optimal")
        self._plt.legend()
        self._canvas.figure.tight_layout()
        self._canvas.draw()

    @staticmethod
    def _smooth(x: np.ndarray, y: np.ndarray, level: float) -> tuple[np.ndarray, np.ndarray]:
        cs = CubicSpline(x, y)
        # Generate finer x values for smoother plot
        X = np.linspace(0, x.size, int(x.size / level))
        # Interpolate y values for the smoother plot
        Y = cs(X)
        return X, Y

    @property
    def blank(self):
        return self._blank

    @blank.setter
    def blank(self, value):
        self._blank = value
        self._plotAnalyseData()

    @property
    def analyseData(self):
        return self._data

    @analyseData.setter
    def analyseData(self, value):
        self._data = value
        self._plotAnalyseData()

# class BackgroundWidget(CalibrationBackgroundWidget):
#     def __init__(self, parent: None, analyseData: datatypes.AnalyseData = None, blank: datatypes.AnalyseData = None):
#         super().__init__(parent, analyseData, blank)
#
#     def _createProfileSelectionLayout(self) -> QtWidgets.QVBoxLayout:
#         label = QtWidgets.QLabel("Select profile: ")
#         label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
#         self._profileComboBox = ComboBox(self)
#         query = "SELECT name FROM BackgroundProfiles"
#         profiles = [t[0] for t in self._db.executeQuery(query).fetchall()]
#         self._profileComboBox.addItems(profiles)
#         addProfileButton = QtWidgets.QPushButton(icon=QtGui.QIcon(resourcePath("icons/plus.png")))
#         addProfileButton.setStyleSheet("""
#                     QPushButton {
#                         border: 1px solid gray;
#                         background-color: #fff;
#                         font-size: 12px;
#                         height: 1.65em;
#                         width: 1.65em;
#                         border-radius: 5px;
#                     }
#                 """)
#         addProfileButton.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
#         backgroundProfileLayout = QtWidgets.QHBoxLayout()
#         backgroundProfileLayout.addWidget(label)
#         backgroundProfileLayout.addWidget(self._profileComboBox)
#         backgroundProfileLayout.addWidget(addProfileButton)
#         label = QtWidgets.QLabel('<a href="#">Adjust interference coefficients</a>')
#         label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
#         layout = QtWidgets.QVBoxLayout()
#         layout.addLayout(backgroundProfileLayout)
#         layout.addWidget(label)
#         self._profileComboBox.currentTextChanged.connect(self._profileChanged)
#         addProfileButton.clicked.connect(self._addProfile)
#         label.linkActivated.connect(self._openInterferencesWindow)
#         return layout
#
#     def _plotAnalyseData(self) -> None:
#         if self._data is None:
#             return
#         self.clearPlot()
#         x = self._data.x
#         y = self._data.y
#         self.plot(x, y, label="Original")
#         if self._blank is not None:
#             y -= self._blank.y
#         # TODO add profile properties
#         xSmooth, ySmooth = self._smooth(x, y, 2.5)
#         peaks, _ = find_peaks(-ySmooth)
#         regressionCurve = np.interp(x, xSmooth[peaks], ySmooth[peaks])
#         # TODO add sigma
#         y = (y - regressionCurve).clip(0)
#         self.plot(x, y, label="Optimal")
#         self._plt.legend()
#         self._canvas.draw()
