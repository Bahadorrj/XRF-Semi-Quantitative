import numpy as np
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QStatusBar,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QMenu,
    QFrame,
    QFileDialog,
    QApplication,
    QDialog,
    QFileIconProvider
)
from pyqtgraph import PlotWidget, ColorButton, mkPen

from python.Controllers.PlotWindowController import PlotWindowController
from python.Controllers.ElemenetsWindowController import ElementsWindowController
from python.Controllers.PeakSearchWindowController import PeakSearchWindowController
from python.Logic.FileExtension import FileHandler
from python.Models import PeakSearchWindowModel
from python.Types.ProjectFileClass import ProjectFile
from python.Views import ConditionsWindow
from python.Views import ElementsWindow
from python.Views import PeakSearchWindow

COLORS = ["#FF0000", "#FFD700", "#00FF00", "#00FFFF", "#000080", "#0000FF", "#8B00FF",
          "#FF1493", "#FFC0CB", "#FF4500", "#FFFF00", "#FF00FF", "#00FF7F", "#FF7F00"]
PX_COUNT = 2048


class MyForm(QTreeWidget):
    itemDeleted = pyqtSignal(int)

    def contextMenuEvent(self, event):
        indexOfTopLevel = self.indexOfTopLevelItem(self.itemAt(event.pos()))
        if indexOfTopLevel != -1:
            contextMenu = QMenu(self)
            actionEdit = QAction("Edit", self)
            actionDelete = QAction("Delete", self)

            contextMenu.addAction(actionEdit)
            contextMenu.addAction(actionDelete)

            action = contextMenu.exec(self.mapToGlobal(event.pos()))
            if action == actionEdit:
                item = self.itemAt(event.pos())
                if item and item.parent() is None:  # Check if it's a top-level item
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    self.editItem(item)
            elif action == actionDelete:
                item = self.itemAt(event.pos())
                if item and item.parent() is None:  # Check if it's a top-level item
                    self.takeTopLevelItem(self.indexOfTopLevelItem(item))
                    self.itemDeleted.emit(indexOfTopLevel)
                    del item


class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading...")
        layout = QVBoxLayout()
        label = QLabel("Initializing, please wait...")
        layout.addWidget(label)
        self.setLayout(layout)
        self.setFixedSize(200, 100)

class CustomFileIconProvider(QFileIconProvider):
    def icon(self, fileInfo):
        if fileInfo != QFileIconProvider.IconType.Computer and fileInfo.filePath().endswith(".xdd"):
            return QIcon(":CSAN.ico")
        return super().icon(fileInfo)


class Window(QMainWindow):
    def __init__(self, size, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot")
        self.setMinimumWidth(int(0.75 * size.width()))
        self.setMinimumHeight(int(0.75 * size.height()))
        self._createActions()
        self._createMenus()
        self._createMenuBar()
        self._createToolBar()
        self.generalLayout = QVBoxLayout()
        self._createMainWidget()
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self._createPlotWidget()
        self._createForm()
        self.coordinateLabel = QLabel()
        self._placeComponents()
        QApplication.processEvents()
        self.conditionWindow = ConditionsWindow.Window(size)
        self.elementsWindow = ElementsWindow.Window(size)
        self.peakSearchWindow = PeakSearchWindow.Window(size)

        ElementsWindowController(self.elementsWindow)
        PeakSearchWindowController(self.peakSearchWindow, PeakSearchWindowModel)

        self._screenSize = size
        self._files = list()
        self._colorButtonMap = dict()

    def _createActions(self):
        self._actionMap = {}
        labels = ['new', 'open-as-new-project', 'open-append', 'close',
                  'save-as', 'save', 'peak-search', 'conditions', "elements"]
        for label in labels:
            action = QAction()
            action.setText(label.replace("-", " "))
            action.setIcon(QIcon(f":{label}.png"))
            self._actionMap[label] = action
        self._actionMap['peak-search'].setDisabled(True)
        self._actionMap['save'].setDisabled(True)
        self._actionMap['save-as'].setDisabled(True)

    def _createMenus(self):
        self.openMenu = QMenu('&Open')
        self.openMenu.addAction(self._actionMap['open-as-new-project'])
        self.openMenu.addAction(self._actionMap['open-append'])
        self.recentMenu = QMenu('&Recent Projects')
        self.openMenu.addMenu(self.recentMenu)

    def _createMenuBar(self):
        menuBar = self.menuBar()
        # Creating menus using a QMenu object
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(self._actionMap['new'])
        fileMenu.addMenu(self.openMenu)
        fileMenu.addSeparator()
        fileMenu.addAction(self._actionMap['save'])
        fileMenu.addAction(self._actionMap['save-as'])
        fileMenu.addAction(self._actionMap['close'])
        # editMenu = menuBar.addMenu("&Edit")
        # helpMenu = menuBar.addMenu("&Help")

    def _createToolBar(self):
        self.toolBar = QToolBar()
        self.toolBar.setIconSize(QSize(16, 16))
        self.toolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolBar.setMovable(False)
        self.toolBar.addAction(self._actionMap['open-append'])
        self.toolBar.addAction(self._actionMap['save'])
        self.toolBar.addAction(self._actionMap['save-as'])
        self.toolBar.addAction(self._actionMap['peak-search'])
        self.toolBar.addAction(self._actionMap['conditions'])
        self.toolBar.addAction(self._actionMap['elements'])
        self.addToolBar(self.toolBar)

    def _createMainWidget(self):
        mainWidget = QWidget()
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
        self.plotWidget.setFrameShape(QFrame.Shape.Box)
        self.plotWidget.setFrameShadow(QFrame.Shadow.Plain)

    def _createForm(self):
        self.form = MyForm()
        self.form.setColumnCount(3)
        self.form.setHeaderLabels(["File", "Condition", "Color"])
        self.form.setFrameShape(QFrame.Shape.Box)
        self.form.setFrameShadow(QFrame.Shadow.Plain)
        self.form.header().setDefaultSectionSize(int(self.size().width() * 0.1))
        self.form.header().setHighlightSections(True)
        self.form.setAnimated(True)
        self.form.setExpandsOnDoubleClick(False)
        self.form.setMaximumWidth(int(self.size().width() * 0.3))

    def _placeComponents(self):
        horizontalLayout = QHBoxLayout()
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

    def openFileDialog(self):
        fileDialog = QFileDialog(self)
        # Set file mode to existing file
        fileDialog.setFileMode(QFileDialog.FileMode.AnyFile)
        # Set default directory
        fileDialog.setDirectory("/Additional/xdd")
        # Set custom file filter to only allow files with .xdd extension
        fileDialog.setNameFilter("XDD files (*.xdd)")
        # Set custom icon for files with .xdd extension
        fileDialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)  # This ensures the custom icon works
        fileDialog.setIconProvider(CustomFileIconProvider())

        result = fileDialog.exec()

        return fileDialog.selectedFiles()[0] if result else None

    def exportProject(self):
        default_dir = r"F:\CSAN\Master"
        filePath, _ = QFileDialog.getSaveFileName(
            self, "Save project", default_dir, filter="*.xdd"
        )
        if filePath:
            for index in range(self.form.topLevelItemCount()):
                self._files[index].name = self.form.topLevelItem(index).text(0)
            self.saveProjectTo(filePath)

    def addProject(self, path):
        if not self._actionMap["save"].isEnabled():
            self._actionMap["save"].setDisabled(False)
            self._actionMap["save-as"].setDisabled(False)
        project = ProjectFile(path)
        for f in project.files:
            self.addFile(f)

    def openNewProject(self, path):
        newWindow = Window(self._screenSize, self)
        newWindow.addProject(path)
        newWindow.show()
        PlotWindowController(newWindow)

    def addFile(self, file):
        fileItem = QTreeWidgetItem()
        fileItem.setText(0, file.name)
        fileItem.setCheckState(0, Qt.CheckState.Unchecked)
        buttons = list()
        for index, condition in enumerate(file.conditions):
            conditionItem = QTreeWidgetItem()
            conditionItem.setText(1, condition.getName())
            conditionItem.setCheckState(1, Qt.CheckState.Unchecked)
            fileItem.addChild(conditionItem)
            self.form.addTopLevelItem(fileItem)
            colorButton = ColorButton()
            colorButton.setColor(COLORS[index])
            self.form.setItemWidget(conditionItem, 2, colorButton)
            buttons.append(colorButton)
        self._files.append(file)
        self._colorButtonMap[file.name] = buttons

    def resetWindow(self):
        self._files.clear()
        self.plotWidget.clear()
        self.form.clear()

    def getColorButtonsMap(self):
        return self._colorButtonMap

    def itemClicked(self, item):
        if self.form.indexOfTopLevelItem(item) == -1:
            self._actionMap.get("peak-search").setDisabled(False)
        else:
            self._actionMap.get("peak-search").setDisabled(True)

    def itemDeleted(self, index):
        self._files.pop(index)
        if not self._files:
            self._actionMap["save"].setDisabled(True)
            self._actionMap["save-as"].setDisabled(True)

    def itemChanged(self, item):
        self.form.setCurrentItem(item)
        self.form.blockSignals(True)
        topLevelIndex = self.form.indexOfTopLevelItem(item)
        if topLevelIndex != -1:
            if item.checkState(0) == Qt.CheckState.Unchecked:
                for child_index in range(self.form.topLevelItem(topLevelIndex).childCount()):
                    item.child(child_index).setCheckState(1, Qt.CheckState.Unchecked)
            elif item.checkState(0) == Qt.CheckState.Checked:
                for child_index in range(self.form.topLevelItem(topLevelIndex).childCount()):
                    item.child(child_index).setCheckState(1, Qt.CheckState.Checked)
        else:
            top_level = item.parent()
            flag = False
            for i in range(top_level.childCount()):
                if top_level.child(i).checkState(1) == Qt.CheckState.Unchecked:
                    top_level.setCheckState(0, Qt.CheckState.Unchecked)
                    flag = True
                    break
            if not flag:
                top_level.setCheckState(0, Qt.CheckState.Checked)
        self.form.blockSignals(False)
        self.plot()

    def plot(self):
        self.plotWidget.clear()
        self.setLimits()
        for top_level_index in range(self.form.topLevelItemCount()):
            top_level_item = self.form.topLevelItem(top_level_index)
            f = self._files[top_level_index]
            for child_index in range(top_level_item.childCount()):
                if top_level_item.child(child_index).checkState(1) == Qt.CheckState.Checked:
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

    def saveProjectTo(self, filePath):
        FileHandler.writeFiles(self._files, filePath)

    # def closeEvent(self, event):
    #     # Intercept the close event
    #     # Check if the close is initiated by the close button
    #     if event.spontaneous():
    #         # Hide the window instead of closing
    #         self.hide()
    #         event.ignore()
    #     else:
    #         # Handle the close event normally
    #         event.accept()
