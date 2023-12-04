import os
from pathlib import Path

import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from pyqtgraph import PlotWidget, SignalProxy, ColorButton, mkPen

import ConditionWindow
import ElementWindow
import PeakSearchWindow
import TextReader
from Backend import icon


class Window(QtWidgets.QMainWindow):
    """
    This class represents the main user interface for a plot window.

    Attributes:
        xLim (int): The x-axis limit for the plot.
        yLim (int): The y-axis limit for the plot.
        colorIndex (float): The index for color selection.
        addedFiles (dict): A dictionary to store information about added files.
        windowSize (QSize): The size of the main window.
        toolbar (QToolBar): The toolbar for user actions.
        statusbar (QStatusBar): The status bar for messages.
        actionOpen (QAction): Action to open files.
        actionPeakSearch (QAction): Action to perform peak search.
        actionConditions (QAction): Action to manage conditions.
        mainLayout (QGridLayout): The main layout of the user interface.
        mainWidget (QWidget): The main widget for the window.
        curvePlot (PlotWidget): The plot widget for displaying data.
        form (QTreeWidget): The tree widget to display file and condition information.
        customMenu (QMenu): Custom context menu for the tree widget.
        actionDelete (QAction): Action to delete items.
        actionDirectory (QAction): Action to open the file location.
        cordinateLabel (QLabel): Label to display cursor coordinates on the plot.

    Methods:
        setupUi(self): Set up the user interface components and their configurations.
        openDirectory(self): Open the file location of a selected item.
        remove(self): Remove selected items from the tree widget and update the plot.
        showContextMenu(self, position): Display a context menu at a specified position.
        openFilesDialog(self): Open a file dialog to select and initialize new items.
        initItem(self, file): Initialize a new item based on the selected file.
        plotFiles(self): Plot the selected files and conditions on the plot widget.
        openPeakSearch(self, item): Open a peak search window for a selected item.
        openConditions(self): Open a conditions window for managing conditions.
        itemClicked(self, item): Handle item selection in the tree widget.
        itemChanged(self, item): Handle changes in item check states.
        mouseMoved(self, e): Update the cursor coordinates when the mouse is moved over the plot.
    """

    def __init__(self, size):
        super().__init__()
        self.xLim = 0
        self.yLim = 0
        self.colors = ["#FF0000", "#FFD700", "#00FF00", "#00FFFF", "#000080", "#0000FF", "#8B00FF",
                       "#FF1493", "#FFC0CB", "#FF4500", "#FFFF00", "#FF00FF", "#00FF7F", "#FF7F00"]
        self.addedFiles = {}
        self.windowSize = QtCore.QSize(
            int(size.width() * 0.75), int(size.height() * 0.75)
        )
        self.toolbar = QtWidgets.QToolBar()
        self.statusbar = QtWidgets.QStatusBar()
        self.actionOpen = QtWidgets.QAction()
        self.actionPeakSearch = QtWidgets.QAction()
        self.actionConditions = QtWidgets.QAction()
        self.actionElements = QtWidgets.QAction()
        self.mainLayout = QtWidgets.QGridLayout()
        self.mainWidget = QtWidgets.QWidget()
        self.curvePlot = PlotWidget()
        self.form = QtWidgets.QTreeWidget()
        self.customMenu = QtWidgets.QMenu(self.form)
        self.actionDelete = QtWidgets.QAction()
        self.actionDirectory = QtWidgets.QAction()
        self.cordinateLabel = QtWidgets.QLabel()

    def setup_ui(self):
        # window config
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle("Graph")
        self.showMaximized()

        # actions config
        self.actionOpen.setIcon(QtGui.QIcon(icon["open"]))
        self.actionOpen.setText("Open")
        self.actionOpen.triggered.connect(lambda: self.open_files_dialog())
        self.actionPeakSearch.setIcon(QtGui.QIcon(icon["peak_search"]))
        self.actionPeakSearch.setText("Peak Search")
        self.actionPeakSearch.setStatusTip("Find elements in spectrum")
        self.actionPeakSearch.setDisabled(True)
        self.actionPeakSearch.triggered.connect(
            lambda: self.open_peak_search(self.form.currentItem())
        )
        self.actionConditions.setIcon(QtGui.QIcon(icon["conditions"]))
        self.actionConditions.setText("Conditions")
        self.actionConditions.triggered.connect(lambda: self.open_conditions())
        self.actionElements.setIcon(QtGui.QIcon(icon['elements']))
        self.actionElements.setText("Elements")
        self.actionElements.triggered.connect(self.open_elements)

        self.actionDelete.setText("Delete")
        self.actionDelete.setIcon(QtGui.QIcon(icon["cross"]))
        self.actionDelete.triggered.connect(self.remove)
        self.actionDirectory.setText("Open file location")
        self.actionDirectory.triggered.connect(self.open_directory)

        # menu config
        self.customMenu.addAction(self.actionDelete)
        self.customMenu.addSeparator()
        self.customMenu.addAction(self.actionDirectory)

        # toolbar config
        self.toolbar.setIconSize(QtCore.QSize(32, 32))
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.toolbar.setMovable(False)
        self.toolbar.addAction(self.actionOpen)
        self.toolbar.addAction(self.actionPeakSearch)
        self.toolbar.addAction(self.actionConditions)
        self.toolbar.addAction(self.actionElements)
        self.addToolBar(self.toolbar)

        # statusbar config
        self.setStatusBar(self.statusbar)

        # curve plot config
        self.curvePlot.setFrameShape(QtWidgets.QFrame.Box)
        self.curvePlot.setFrameShadow(QtWidgets.QFrame.Plain)
        self.curvePlot.setBackground("#fff")
        self.curvePlot.setLabel(
            "bottom",
            """<span style=\"font-size:1.5rem\">
                                    px</span>
                                """,
        )
        self.curvePlot.setLabel(
            "left",
            """<span style=\"font-size:1.5rem\">
                                    Intensity</span>
                                """,
        )
        self.curvePlot.showGrid(x=True, y=True)
        self.proxy = SignalProxy(
            self.curvePlot.scene().sigMouseMoved, rateLimit=60, slot=self.mouse_moved
        )

        # form config
        self.form.setFixedWidth(int(self.windowSize.width() * 0.25))
        self.form.setColumnCount(3)
        self.form.setHeaderLabels(["File", "Condition", "Color"])
        self.form.setFrameShape(QtWidgets.QFrame.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Plain)
        self.form.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.form.customContextMenuRequested.connect(self.show_context_menu)
        self.form.itemChanged.connect(self.item_changed)
        self.form.itemClicked.connect(self.item_clicked)
        self.form.itemDoubleClicked.connect(self.open_peak_search)

        self.mainLayout.addWidget(self.curvePlot, 0, 0)
        self.mainLayout.addWidget(self.form, 0, 1)
        self.mainLayout.addWidget(self.cordinateLabel, 1, 0)

        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

    def open_directory(self):
        """
        Open the file location of a selected item from the form.
        """
        item = self.form.selectedItems()[0]
        path = self.addedFiles[self.form.indexOfTopLevelItem(item)]["path"]
        while True:
            path = path[:-1]
            if path[-1] == "/":
                break
        os.startfile(path)

    def remove(self):
        """
        Remove a selected item from the form and update the plot.
        """
        item = self.form.selectedItems()[0]
        index = self.form.indexOfTopLevelItem(item)
        self.form.takeTopLevelItem(index)
        self.addedFiles.pop(index)
        self.plot_files()

    def show_context_menu(self, position):
        """
        Display a context menu for the selected item at the specified position.

        Args:
            position (QPoint): The position where the context menu should be displayed.
        """
        item = self.form.itemAt(position)
        if self.form.indexOfTopLevelItem(item) >= 0:
            self.customMenu.exec_(self.form.mapToGlobal(position))

    def open_files_dialog(self):
        """
        Open a file dialog for selecting and initializing new items in the form.
        """
        self.fileDialog = QtWidgets.QFileDialog()
        self.fileDialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        self.fileDialog.setNameFilter("Texts (*.txt)")
        self.fileDialog.show()
        self.fileDialog.fileSelected.connect(self.init_item)

    def init_item(self, file):
        """
        Initialize a new item based on the selected file, including adding conditions and color buttons.

        Args:
            file (str): The path of the selected file.
        """
        file_item = QtWidgets.QTreeWidgetItem()
        file_name = Path(file).stem
        file_item.setText(0, file_name)
        file_item.setCheckState(0, QtCore.Qt.Unchecked)

        conditions_dictionary = TextReader.condition_dictionary(file)
        color_buttons = list()
        for index, condition in enumerate(list(conditions_dictionary.keys())):
            condition_item = QtWidgets.QTreeWidgetItem()
            condition_item.setText(1, condition)
            condition_item.setCheckState(1, QtCore.Qt.Unchecked)

            file_item.addChild(condition_item)
            self.form.addTopLevelItem(file_item)

            button = ColorButton()
            button.setColor(self.colors[index])
            button.sigColorChanged.connect(self.plot_files)
            color_buttons.append(button)
            self.form.setItemWidget(condition_item, 2, button)

        properties = {
            "path": file,
            "conditions": conditions_dictionary,
            "colorButtons": color_buttons,
        }
        self.addedFiles[file_name] = properties

    def plot_files(self):
        """
        Plot the selected files and conditions on the curve plot.
        """
        self.curvePlot.clear()
        for properties in self.addedFiles.values():
            for index, condition in enumerate(properties["conditions"].values()):
                if condition["active"]:
                    intensity = TextReader.list_items(
                        properties["path"], condition["range"], int
                    )
                    px = np.arange(0, len(intensity), 1)
                    if max(intensity) > self.yLim:
                        self.yLim = max(intensity)
                    if len(intensity) > self.xLim:
                        self.xLim = len(intensity)
                    self.curvePlot.setLimits(
                        xMin=0, xMax=self.xLim, yMin=0, yMax=1.1 * self.yLim
                    )
                    color = properties["colorButtons"][index].color()
                    pen = mkPen(color, width=2)
                    self.curvePlot.plot(x=px, y=intensity, pen=pen)

    def open_peak_search(self, item):
        """
        Open a peak search window for the selected item.

        Args:
            item (QTreeWidgetItem): The selected item in the form.
        """
        if self.form.indexOfTopLevelItem(item) == -1:
            item_text = item.text(1)
            top_level_text = item.parent().text(0)
            self.peakSearchWindow = PeakSearchWindow.Window(
                self.size(),
                self.addedFiles[top_level_text]["path"],
                self.addedFiles[top_level_text]["conditions"][item_text]["range"],
                item_text,
            )
            self.peakSearchWindow.setupUi()
            self.peakSearchWindow.show()

    def open_conditions(self):
        """
        Open Conditions window for managing conditions.
        """
        self.conditionsWindow = ConditionWindow.Window(super().size())
        self.conditionsWindow.setup_ui()
        self.conditionsWindow.show()

    def open_elements(self):
        """
        Open Elements window for managing elements.
        """
        self.elementsWindow = ElementWindow.Window(super().size())
        self.elementsWindow.setup_ui()
        self.elementsWindow.show()

    def item_clicked(self, item):
        """
        Handle item selection in the form and enable or disable the 'Peak Search' action accordingly.

        Args:
            item (QTreeWidgetItem): The selected item in the form.
        """
        for i in range(self.form.topLevelItemCount()):
            item = self.form.topLevelItem(i)
            if item.isSelected():
                self.actionPeakSearch.setDisabled(True)
                break
            for j in range(item.childCount()):
                child = item.child(j)
                if child.isSelected():
                    self.actionPeakSearch.setDisabled(False)
                    break

    def item_changed(self, item):
        """
        Handle changes in item check states and update the plot accordingly.

        Args:
            item (QTreeWidgetItem): The item for which the check state has changed.
        """
        self.form.blockSignals(True)
        self.form.setCurrentItem(item)
        top_level_index = self.form.indexOfTopLevelItem(item)
        if top_level_index != -1:
            if item.checkState(0) != 0:
                for index, state in enumerate(self.addedFiles[item.text(0)]["conditions"].values()):
                    state["active"] = True
                    item.child(index).setCheckState(1, QtCore.Qt.Checked)
            else:
                for index, state in enumerate(self.addedFiles[item.text(0)]["conditions"].values()):
                    state["active"] = False
                    item.child(index).setCheckState(1, QtCore.Qt.Unchecked)
        else:
            top_level = item.parent()
            if item.checkState(1) != 0:
                self.addedFiles[top_level.text(0)]["conditions"][item.text(1)][
                    "active"
                ] = True
            else:
                self.addedFiles[top_level.text(0)]["conditions"][item.text(1)][
                    "active"
                ] = False
            flag = False
            for i in range(top_level.childCount()):
                if top_level.child(i).checkState(1) == 0:
                    top_level.setCheckState(0, QtCore.Qt.Unchecked)
                    flag = True
                    break
            if not flag:
                top_level.setCheckState(0, QtCore.Qt.Checked)

        self.plot_files()
        self.form.blockSignals(False)

    def mouse_moved(self, e):
        """
        Update the cursor coordinates when the mouse is moved over the plot.

        Args:
            e (list): A list containing information about the mouse event.
        """
        pos = e[0]
        if self.curvePlot.sceneBoundingRect().contains(pos):
            mouse_point = self.curvePlot.getPlotItem().vb.mapSceneToView(pos)
            self.cordinateLabel.setText(
                "<span style='font-size: 2rem'>x=%0.1f,y=%0.1f</span>"
                % (mouse_point.x(), mouse_point.y())
            )
