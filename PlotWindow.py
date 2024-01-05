import os

import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from pyqtgraph import PlotWidget, SignalProxy, ColorButton, mkPen

import ConditionWindow
import ElementWindow
import PeakSearchWindow
from Backend import icons
from FileClass import File


class Window(QtWidgets.QMainWindow):
    def __init__(self, size):
        super().__init__()
        self.xLim = 0
        self.yLim = 0
        self.colors = ["#FF0000", "#FFD700", "#00FF00", "#00FFFF", "#000080", "#0000FF", "#8B00FF",
                       "#FF1493", "#FFC0CB", "#FF4500", "#FFFF00", "#FF00FF", "#00FF7F", "#FF7F00"]
        self.addedFiles = list()
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
        self.proxy = SignalProxy(
            self.curvePlot.scene().sigMouseMoved, rateLimit=60, slot=self.mouse_moved
        )
        self.form = QtWidgets.QTreeWidget()
        self.customMenu = QtWidgets.QMenu(self.form)
        self.actionDelete = QtWidgets.QAction()
        self.actionDirectory = QtWidgets.QAction()
        self.coordinateLabel = QtWidgets.QLabel()
        self.conditionsWindow = ConditionWindow.Window(size)
        self.elementsWindow = ElementWindow.Window(size)
        self.peakSearchWindow = PeakSearchWindow.Window(size)

    def setup_ui(self):
        # window config
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle("Graph")
        self.showMaximized()

        # actions config
        self.actionOpen.setIcon(QtGui.QIcon(icons["open"]))
        self.actionOpen.setText("Open")
        self.actionOpen.triggered.connect(self.open_files_dialog)
        self.actionPeakSearch.setIcon(QtGui.QIcon(icons["peak_search"]))
        self.actionPeakSearch.setText("Peak Search")
        self.actionPeakSearch.setStatusTip("Find elements in spectrum")
        self.actionPeakSearch.setDisabled(True)
        self.actionPeakSearch.triggered.connect(self.open_peak_search)
        self.actionConditions.setIcon(QtGui.QIcon(icons["conditions"]))
        self.actionConditions.setText("Conditions")
        self.actionConditions.triggered.connect(self.open_conditions)
        self.actionElements.setIcon(QtGui.QIcon(icons['elements']))
        self.actionElements.setText("Elements")
        self.actionElements.triggered.connect(self.open_elements)

        self.actionDelete.setText("Delete")
        self.actionDelete.setIcon(QtGui.QIcon(icons["cross"]))
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

        # form config
        self.form.setFixedWidth(int(self.size().width() * 0.25))
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
        self.mainLayout.addWidget(self.coordinateLabel, 1, 0)

        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

    def mouse_moved(self, e):
        pos = e[0]
        if self.curvePlot.sceneBoundingRect().contains(pos):
            mouse_point = self.curvePlot.getPlotItem().vb.mapSceneToView(pos)
            self.coordinateLabel.setText(
                "<span style='font-size: 2rem'>x=%0.1f,y=%0.1f</span>"
                % (mouse_point.x(), mouse_point.y())
            )

    def open_files_dialog(self):
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        file_dialog.setNameFilter("Texts (*.txt)")
        file_dialog.show()
        file_dialog.fileSelected.connect(self.init_item)

    def init_item(self, path):
        f = File(path)
        file_item = QtWidgets.QTreeWidgetItem()
        file_item.setText(0, f.get_name())
        file_item.setCheckState(0, QtCore.Qt.Unchecked)
        for index, condition in enumerate(f.get_conditions()):
            condition_item = QtWidgets.QTreeWidgetItem()
            condition_item.setText(1, condition.get_name())
            condition_item.setCheckState(1, QtCore.Qt.Unchecked)
            file_item.addChild(condition_item)
            self.form.addTopLevelItem(file_item)
            color_button = ColorButton()
            color_button.setColor(self.colors[index])
            color_button.sigColorChanged.connect(self.update_color)
            self.form.setItemWidget(condition_item, 2, color_button)
            color_button.sigColorChanged.connect(self.update_color)
        self.addedFiles.append(f)

    def update_color(self):
        self.plot_files()

    def item_changed(self, item):
        self.form.setCurrentItem(item)
        self.form.blockSignals(True)
        top_level_index = self.form.indexOfTopLevelItem(item)
        if top_level_index != -1:
            if item.checkState(0) == 0:
                for child_index in range(self.form.topLevelItem(top_level_index).childCount()):
                    item.child(child_index).setCheckState(
                        1, QtCore.Qt.Unchecked)
            else:
                for child_index in range(self.form.topLevelItem(top_level_index).childCount()):
                    item.child(child_index).setCheckState(1, QtCore.Qt.Checked)
        else:
            top_level = item.parent()
            flag = False
            for i in range(top_level.childCount()):
                if top_level.child(i).checkState(1) == 0:
                    top_level.setCheckState(0, QtCore.Qt.Unchecked)
                    flag = True
                    break
            if not flag:
                top_level.setCheckState(0, QtCore.Qt.Checked)
        self.form.blockSignals(False)
        self.plot_files()

    def plot_files(self):
        self.curvePlot.clear()
        for top_level_index in range(self.form.topLevelItemCount()):
            top_level_item = self.form.topLevelItem(top_level_index)
            f = self.addedFiles[top_level_index]
            for child_index in range(top_level_item.childCount()):
                if top_level_item.child(child_index).checkState(1) != 0:
                    intensity = f.get_counts()[child_index]
                    px = np.arange(0, len(intensity), 1)
                    if max(intensity) > self.yLim:
                        self.yLim = max(intensity)
                    if len(intensity) > self.xLim:
                        self.xLim = len(intensity)
                    self.curvePlot.setLimits(
                        xMin=0, xMax=self.xLim, yMin=0, yMax=1.1 * self.yLim
                    )
                    color = self.form.itemWidget(
                        top_level_item.child(child_index), 2).color()
                    self.curvePlot.plot(x=px, y=intensity,
                                        pen=mkPen(color=color, width=2))

    def item_clicked(self, item):
        if self.form.indexOfTopLevelItem(item) == -1:
            self.actionPeakSearch.setDisabled(False)
        else:
            self.actionPeakSearch.setDisabled(True)

    def open_peak_search(self):
        if self.actionPeakSearch.isEnabled():
            top_level_index = self.form.indexOfTopLevelItem(
                self.form.currentItem().parent())
            child_index = self.form.currentIndex().row()
            self.peakSearchWindow.set_condition(self.addedFiles[top_level_index].get_condition(child_index))
            self.peakSearchWindow.setup_ui()
            self.peakSearchWindow.show()

    def open_conditions(self):
        self.conditionsWindow.setup_ui()
        self.conditionsWindow.show()

    def open_elements(self):
        self.elementsWindow.setup_ui()
        self.elementsWindow.show()

    def show_context_menu(self, position):
        item = self.form.itemAt(position)
        if self.form.indexOfTopLevelItem(item) >= 0:
            self.customMenu.exec_(self.form.mapToGlobal(position))

    def remove(self):
        item = self.form.currentItem()
        top_level_index = self.form.indexOfTopLevelItem(item)
        if top_level_index != -1:
            self.form.takeTopLevelItem(top_level_index)
            self.addedFiles.pop(top_level_index)
            self.plot_files()

    def open_directory(self):
        f = self.addedFiles[self.form.currentIndex().row()]
        path = f.get_path().rstrip("/" + f.get_name() + ".txt")
        os.startfile(path)
