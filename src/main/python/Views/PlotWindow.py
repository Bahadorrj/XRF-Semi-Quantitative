import numpy as np
from PyQt6 import QtWidgets, QtCore, QtGui
from pyqtgraph import PlotWidget, ColorButton, mkPen

from src.main.python.Controllers.ElemenetsWindowController import ElementsWindowController
from src.main.python.Controllers.PeakSearchWindowController import PeakSearchWindowController
from src.main.python.Models import PeakSearchWindowModel
from src.main.python.Types.FileClass import File
from src.main.python.Views import ConditionsWindow
from src.main.python.Views import ElementsWindow
from src.main.python.Views import PeakSearchWindow
from src.main.python.Views.Icons import ICONS
from src.main.python.Views.MessegeBox import Dialog

COLORS = ["#FF0000", "#FFD700", "#00FF00", "#00FFFF", "#000080", "#0000FF", "#8B00FF",
          "#FF1493", "#FFC0CB", "#FF4500", "#FFFF00", "#FF00FF", "#00FF7F", "#FF7F00"]
PX_COUNT = 2048


class Window(QtWidgets.QMainWindow):
    def __init__(self, size):
        super().__init__()
        self.setWindowTitle("Plot")
        self.setMinimumWidth(int(0.75 * size.width()))
        self.setMinimumHeight(int(0.75 * size.height()))
        self._createActions()
        self._createToolBar()
        self.generalLayout = QtWidgets.QVBoxLayout()
        self._createMainWidget()
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        self._createPlotWidget()
        self._createForm()
        self.coordinateLabel = QtWidgets.QLabel()
        self._placeComponents()
        QtWidgets.QApplication.processEvents()
        self.conditionWindow = ConditionsWindow.Window(size)
        self.elementsWindow = ElementsWindow.Window(size)
        self.peakSearchWindow = PeakSearchWindow.Window(size)

        ElementsWindowController(self.elementsWindow)
        PeakSearchWindowController(self.peakSearchWindow, PeakSearchWindowModel)

        self._files = list()
        self._colorButtonMap = dict()

    def _createActions(self):
        self._actionMap = {}
        labels = ["Open", "Peak Search", "Conditions", "Elements"]
        for label in labels:
            action = QtGui.QAction()
            action.setText(label)
            action.setIcon(QtGui.QIcon(ICONS[label]))
            self._actionMap[label] = action
        self._actionMap["Peak Search"].setDisabled(True)

    def _createToolBar(self):
        self.toolBar = QtWidgets.QToolBar()
        self.toolBar.setIconSize(QtCore.QSize(32, 32))
        self.toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolBar.setMovable(False)
        for action in self._actionMap.values():
            self.toolBar.addAction(action)
        self.addToolBar(self.toolBar)

    def _createMainWidget(self):
        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(self.generalLayout)
        self.setCentralWidget(mainWidget)

    def _createPlotWidget(self):
        self.plotWidget = PlotWidget()
        self.plotWidget.setBackground("#fff")
        self.plotWidget.setLabel(
            "bottom",
            """<span style=\"font-size:1.5rem\">
                                    px</span>
                                """,
        )
        self.plotWidget.setLabel(
            "left",
            """<span style=\"font-size:1.5rem\">
                                    Intensity</span>
                                """,
        )
        self.plotWidget.showGrid(x=True, y=True)
        self.plotWidget.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.plotWidget.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)

    def _createForm(self):
        self.form = QtWidgets.QTreeWidget()
        self.form.setColumnCount(3)
        self.form.setHeaderLabels(["File", "Condition", "Color"])
        self.form.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.form.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.form.setMaximumWidth(int(self.size().width() * 0.3))

    def _placeComponents(self):
        horizontalLayout = QtWidgets.QHBoxLayout()
        horizontalLayout.addWidget(self.plotWidget, 2)
        horizontalLayout.addWidget(self.form, 1)
        self.generalLayout.addLayout(horizontalLayout)
        self.generalLayout.addWidget(self.coordinateLabel)

    def getPlotWidget(self):
        return self.plotWidget

    def setCoordinate(self, coordinate):
        self.coordinateLabel.setText(
            "<span style='font-size: 2rem'>x=%0.1f,y=%0.1f</span>"
            % (coordinate.x(), coordinate.y())
        )

    def getActionsMap(self):
        return self._actionMap

    def mouseMoved(self, pos):
        if self.plotWidget.sceneBoundingRect().contains(pos):
            mousePoint = self.plotWidget.getPlotItem().vb.mapSceneToView(pos)
            self.setCoordinate(mousePoint)

    def openFileDialog(self, fileFormat):
        fileDialog = QtWidgets.QFileDialog(self)
        fileDialog.setFileMode(QtWidgets.QFileDialog.FileMode.AnyFile)
        fileDialog.setNameFilter(f"Texts (*{fileFormat})")
        fileDialog.show()
        return fileDialog

    def showContextMenu(self, position):
        menu = QtWidgets.QMenu(self.form)
        item = self.form.itemAt(position)
        if self.form.indexOfTopLevelItem(item) != -1:
            menu.exec(self.form.mapToGlobal(position))

    def createFile(self, path):
        f = File(path)
        fileItem = QtWidgets.QTreeWidgetItem()
        fileItem.setText(0, f.name)
        fileItem.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
        buttons = list()
        if f.conditions:
            for index, condition in enumerate(f.conditions):
                conditionItem = QtWidgets.QTreeWidgetItem()
                conditionItem.setText(1, condition.getName())
                conditionItem.setCheckState(1, QtCore.Qt.CheckState.Unchecked)
                fileItem.addChild(conditionItem)
                self.form.addTopLevelItem(fileItem)
                colorButton = ColorButton()
                colorButton.setColor(COLORS[index])
                self.form.setItemWidget(conditionItem, 2, colorButton)
                buttons.append(colorButton)
            self._files.append(f)
            self._colorButtonMap[f.name] = buttons
        else:
            messageBox = Dialog(
                QtWidgets.QMessageBox.Icon.Warning,
                "Warning!",
                "The selected file is not registered properly!"
            )
            messageBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            messageBox.exec()

    def getColorButtonsMap(self):
        return self._colorButtonMap

    def itemClicked(self, item):
        if self.form.indexOfTopLevelItem(item) == -1:
            self._actionMap.get("Peak Search").setDisabled(False)
        else:
            self._actionMap.get("Peak Search").setDisabled(True)

    def itemChanged(self, item):
        self.form.setCurrentItem(item)
        self.form.blockSignals(True)
        top_level_index = self.form.indexOfTopLevelItem(item)
        if top_level_index != -1:
            if item.checkState(0) == QtCore.Qt.CheckState.Unchecked:
                for child_index in range(self.form.topLevelItem(top_level_index).childCount()):
                    item.child(child_index).setCheckState(1, QtCore.Qt.CheckState.Unchecked)
            elif item.checkState(0) == QtCore.Qt.CheckState.Checked:
                for child_index in range(self.form.topLevelItem(top_level_index).childCount()):
                    item.child(child_index).setCheckState(1, QtCore.Qt.CheckState.Checked)
        else:
            top_level = item.parent()
            flag = False
            for i in range(top_level.childCount()):
                if top_level.child(i).checkState(1) == QtCore.Qt.CheckState.Unchecked:
                    top_level.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                    flag = True
                    break
            if not flag:
                top_level.setCheckState(0, QtCore.Qt.CheckState.Checked)
        self.form.blockSignals(False)
        self.plot()

    def plot(self):
        self.plotWidget.clear()
        self.setLimits()
        for top_level_index in range(self.form.topLevelItemCount()):
            top_level_item = self.form.topLevelItem(top_level_index)
            f = self._files[top_level_index]
            for child_index in range(top_level_item.childCount()):
                if top_level_item.child(child_index).checkState(1) == QtCore.Qt.CheckState.Checked:
                    counts = f.counts[child_index]
                    px = np.arange(0, len(counts), 1)
                    color = self._colorButtonMap.get(f.name)[child_index].color()
                    self.plotWidget.plot(x=px, y=counts, pen=mkPen(color=color, width=3))

    def setLimits(self):
        y = 0
        for file in self._files:
            for counts in file.counts:
                if y < max(counts):
                    y = max(counts)
        self.plotWidget.setLimits(xMin=0, xMax=PX_COUNT, yMin=0, yMax=1.1 * y)

    def openConditionsWindow(self):
        self.conditionWindow.show()

    def openElementsWindow(self):
        self.elementsWindow.show()

    def openPeakSearchWindow(self):
        topLevelIndex = self.form.indexOfTopLevelItem(self.form.currentItem().parent())
        childIndex = self.form.currentIndex().row()
        if topLevelIndex != -1:
            file = self._files[topLevelIndex]
            self.peakSearchWindow.init(file.counts[childIndex], file.conditions[childIndex])
            self.peakSearchWindow.showMaximized()
