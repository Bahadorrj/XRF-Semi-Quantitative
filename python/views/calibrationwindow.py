from functools import partial

from PyQt6 import QtCore, QtGui, QtWidgets

from python.utils import datatypes
from python.utils.paths import resourcePath
from python.views.backgroundwidget import CalibrationBackgroundWidget


class CalibrationWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(CalibrationWindow, self).__init__(parent)
        self.setStyleSheet("background-color: #fff")
        self.resize(1200, 800)
        self._createActions()
        self._createToolBar()
        self._createBackgroundWidget()
        self._createProfileBox()
        self._createGeneralDataBox()
        self._setUpView()

    def _createActions(self) -> None:
        self._actionsMap = {}
        actions = (
            "Run",
        )
        for label in actions:
            action = QtGui.QAction(label)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"icons/{key}.png")))
            self._actionsMap[key] = action
            action.triggered.connect(partial(self._actionTriggered, key))

    @QtCore.pyqtSlot()
    def _actionTriggered(self, key: str) -> None:
        pass

    def _createToolBar(self) -> None:
        toolBar = QtWidgets.QToolBar(self)
        toolBar.setIconSize(QtCore.QSize(16, 16))
        toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolBar.setMovable(False)
        self._fillToolBarWithActions(toolBar)
        self.addToolBar(toolBar)

    def _fillToolBarWithActions(self, toolBar: QtWidgets.QToolBar) -> None:
        toolBar.addAction(self._actionsMap['run'])

    def _createBackgroundWidget(self) -> None:
        self._backgroundWidget = CalibrationBackgroundWidget(self)

    def _createProfileBox(self):
        self._profileBox = QtWidgets.QGroupBox(self)
        self._profileBox.setStyleSheet("""
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
        """)
        self._profileBox.setTitle('Profile')

    def _createGeneralDataBox(self) -> None:
        self._generalBox = QtWidgets.QGroupBox(self)
        self._generalBox.setStyleSheet("""
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
        """)
        self._generalBox.setFixedWidth(200)
        self._generalBox.setTitle('General Data')

    def _setUpView(self) -> None:
        mainLayout = QtWidgets.QGridLayout()
        mainLayout.addWidget(self._backgroundWidget, 0, 0, 2, 1)
        mainLayout.addWidget(self._profileBox, 0, 1, 1, 1)
        mainLayout.addWidget(self._generalBox, 1, 1, 1, 1)
        mainWidget = QtWidgets.QWidget(self)
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

    def addAnalyseData(self, analyseData: datatypes.AnalyseData) -> None:
        self._backgroundWidget.analyseData = analyseData

    def addBlank(self, blank: datatypes.AnalyseData) -> None:
        self._backgroundWidget.blank = blank
