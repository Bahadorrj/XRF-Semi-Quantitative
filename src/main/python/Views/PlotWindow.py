from numpy import arange
from pathlib import Path
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QStatusBar,
    QToolBar,
    QTreeWidgetItem,
    QMenu,
    QFrame,
    QFileDialog,
    QApplication,
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
from python.Views.Widgets import Tree

COLORS = ["#FF0000", "#FFD700", "#00FF00", "#00FFFF", "#000080", "#0000FF", "#8B00FF",
          "#FF1493", "#FFC0CB", "#FF4500", "#FFFF00", "#FF00FF", "#00FF7F", "#FF7F00"]
PX_COUNT = 2048

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
        self._projects = list()

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
        # fileMenu.addAction(self._actionMap['save'])
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
        # self.toolBar.addAction(self._actionMap['save'])
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
        self.form = Tree()
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
        projectPath, _ = QFileDialog.getSaveFileName(
            self, "Save project", default_dir, filter="*.xdd"
        )
        if projectPath:
            for index in range(self.form.topLevelItemCount()):
                self._projects[index].name = self.form.topLevelItem(index).text(0)
            self.saveProjectTo(projectPath)

    def addProject(self, path):
        if not self._actionMap["save"].isEnabled():
            self._actionMap["save"].setDisabled(False)
            self._actionMap["save-as"].setDisabled(False)
        project = ProjectFile(path)
        projectItem = QTreeWidgetItem()
        projectItem.setText(0, Path(project.path).stem)
        for file in project.files:
            fileItem, buttons = self.addFile(file)
            projectItem.addChild(fileItem)
        self._projects.append(project)
        self.form.addTopLevelItem(projectItem)

    def openNewProject(self, path):
        newWindow = Window(self._screenSize, self)
        newWindow.addProject(path)
        newWindow.show()
        PlotWindowController(newWindow)

    def addFile(self, file) -> tuple:
        fileItem = QTreeWidgetItem()
        fileItem.setText(0, file.name)
        fileItem.setCheckState(0, Qt.CheckState.Unchecked)
        buttons = list()
        for index, condition in enumerate(file.conditions):
            conditionItem = QTreeWidgetItem()
            conditionItem.setText(1, condition.getName())
            conditionItem.setCheckState(1, Qt.CheckState.Unchecked)
            fileItem.addChild(conditionItem)
            colorButton = ColorButton()
            colorButton.setColor(COLORS[index])
            self.form.setItemWidget(conditionItem, 2, colorButton)
            buttons.append(colorButton)
            colorButton.sigColorChanged.connect(self.plot)

        return fileItem, buttons

    def resetWindow(self):
        self._projects.clear()
        self.plotWidget.clear()
        self.form.clear()

    def itemClicked(self, item):
        if item.childCount() == 0:
            self._actionMap.get("peak-search").setDisabled(False)
        else:
            self._actionMap.get("peak-search").setDisabled(True)

    def itemDeleted(self, index):
        self._projects.pop(index)
        if not self._projects:
            self._actionMap["save"].setDisabled(True)
            self._actionMap["save-as"].setDisabled(True)

    def itemChanged(self, item: QTreeWidgetItem):
        if self.form.indexOfTopLevelItem(item) == -1:
            self.form.setCurrentItem(item)
            self.form.blockSignals(True)
            if item.childCount() != 0:
                if item.checkState(0) == Qt.CheckState.Unchecked:
                    for childIndex in range(item.childCount()):
                        item.child(childIndex).setCheckState(1, Qt.CheckState.Unchecked)
                elif item.checkState(0) == Qt.CheckState.Checked:
                    for childIndex in range(item.childCount()):
                        item.child(childIndex).setCheckState(1, Qt.CheckState.Checked)
            else:
                fileItem = item.parent()
                flag = False
                for i in range(fileItem.childCount()):
                    if fileItem.child(i).checkState(1) == Qt.CheckState.Unchecked:
                        fileItem.setCheckState(0, Qt.CheckState.Unchecked)
                        flag = True
                        break
                if not flag:
                    fileItem.setCheckState(0, Qt.CheckState.Checked)
            self.form.blockSignals(False)
            self.plot()

    def plot(self):
        self.plotWidget.clear()
        self.setLimits()
        for projectIndex in range(self.form.topLevelItemCount()):
            projectItem = self.form.topLevelItem(projectIndex)
            project = self._projects[projectIndex]
            for fileIndex in range(projectItem.childCount()):
                fileItem = projectItem.child(fileIndex)
                file = project.files[fileIndex]
                for conditionIndex in range(fileItem.childCount()):
                    conditionItem = fileItem.child(conditionIndex)
                    if conditionItem.checkState(1) == Qt.CheckState.Checked:
                        counts = file.counts[conditionIndex]
                        px = arange(0, len(counts), 1)
                        color = self.form.itemWidget(conditionItem, 2).color()
                        self.plotWidget.plot(x=px, y=counts, pen=mkPen(color=color, width=3))

    def setLimits(self):
        y = 0
        for project in self._projects:
            for file in project.files:
                for counts in file.counts:
                    if y < max(counts):
                        y = max(counts)
        self.plotWidget.setLimits(xMin=0, xMax=PX_COUNT, yMin=0, yMax=1.1 * y)

    def openConditionsWindow(self):
        self.conditionWindow.show()

    def openElementsWindow(self):
        self.elementsWindow.show()

    def openPeakSearchWindow(self):
        if self.form.currentItem().childCount() == 0:
            conditionItem = self.form.currentItem()
            fileItem = conditionItem.parent()
            projectItem = fileItem.parent()
            projectIndex = self.form.indexOfTopLevelItem(projectItem)
            fileIndex = projectItem.indexOfChild(fileItem)
            conditionIndex = fileItem.indexOfChild(conditionItem)
            file = self._projects[projectIndex].files[fileIndex]
            self.peakSearchWindow.init(
                file.counts[conditionIndex],
                file.conditions[conditionIndex]
            )

    def saveProjectTo(self, projectPath):
        FileHandler.writeFiles(self._projects, projectPath)

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
