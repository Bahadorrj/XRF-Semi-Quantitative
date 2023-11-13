from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import (ColorButton, InfiniteLine,
                       PlotWidget, SignalProxy,
                       mkPen, LinearRegionItem,
                       GraphicsLayoutWidget, InfLineLabel)
from pathlib import Path
import numpy as np
import sys
import os
from backend import *


class Ui_ElementsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.windowSize = QtCore.QSize(
            int(size.width() * 0.5), int(size.height() * 0.3)
        )
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.form = QtWidgets.QTableWidget()
        self.dfElements = SQLITE.read(Addr["dbFundamentals"], "elements")
        self.rows = self.dfElements.shape[0]

    def setupUi(self):
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle("Elements")
        self.showMaximized()

        self.form.setFrameShape(QtWidgets.QFrame.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Plain)
        self.form.setColumnCount(10)
        self.form.setRowCount(self.rows)
        headers = [
            'Atomic No',
            'Name',
            'Symbol',
            'Radiation',
            'Kev',
            'Low Kev',
            'High Kev',
            'Intensity',
            'Active',
            'Activated in'
        ]
        self.form.setHorizontalHeaderLabels(headers)
        self.form.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.form.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        self.mainLayout.addWidget(self.form)
        self.setLayout(self.mainLayout)

        for row in range(self.rows):
            self.atomicNoItem = QtWidgets.QTableWidgetItem(
                str(self.dfElements.at[row, 'atomic_number'])
            )
            self.atomicNoItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.atomicNoItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.nameItem = QtWidgets.QTableWidgetItem(
                self.dfElements.at[row, 'name']
            )
            self.nameItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.nameItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.symbolItem = QtWidgets.QTableWidgetItem(
                self.dfElements.at[row, 'symbol']
            )
            self.symbolItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.symbolItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.radiationItem = QtWidgets.QTableWidgetItem(
                self.dfElements.at[row, 'radiation_type']
            )
            self.radiationItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.radiationItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.KevItem = QtWidgets.QTableWidgetItem(
                str(self.dfElements.at[row, 'Kev'])
            )
            self.KevItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.KevItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.lowItem = QtWidgets.QTableWidgetItem(
                str(self.dfElements.at[row, 'low_Kev'])
            )
            self.lowItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.lowItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.highItem = QtWidgets.QTableWidgetItem(
                str(self.dfElements.at[row, 'high_Kev'])
            )
            self.highItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.highItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.intensityItem = QtWidgets.QTableWidgetItem(
                str(self.dfElements.at[row, 'intensity'])
            )
            self.intensityItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.intensityItem.setFlags(QtCore.Qt.ItemIsEnabled)
            active = bool(self.dfElements.at[row, 'active'])
            self.activeItem = QtWidgets.QTableWidgetItem(
                str(active)
            )
            if active is True:
                self.activeItem.setForeground(QtCore.Qt.green)
            else:
                self.activeItem.setForeground(QtCore.Qt.red)
            self.activeItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.activeItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.conditionItem = QtWidgets.QTableWidgetItem(
                SQLITE.getConditionNameWhere(
                    self.dfElements.at[row, 'condition_id']
                )
            )
            self.conditionItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.conditionItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.form.setItem(row, 0, self.atomicNoItem)
            self.form.setItem(row, 1, self.nameItem)
            self.form.setItem(row, 2, self.symbolItem)
            self.form.setItem(row, 3, self.radiationItem)
            self.form.setItem(row, 4, self.KevItem)
            self.form.setItem(row, 5, self.lowItem)
            self.form.setItem(row, 6, self.highItem)
            self.form.setItem(row, 7, self.intensityItem)
            self.form.setItem(row, 8, self.activeItem)
            self.form.setItem(row, 9, self.conditionItem)


class Ui_ConditionsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.windowSize = QtCore.QSize(
            int(size.width() * 0.5), int(size.height() * 0.3)
        )
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.form = QtWidgets.QTableWidget()
        self.dfConditions = SQLITE.read(Addr["dbFundamentals"], "conditions")

    def setupUi(self):
        # window config
        self.setFixedSize(self.windowSize)
        self.setWindowTitle("Conditions")

        self.form.setFrameShape(QtWidgets.QFrame.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Plain)
        self.form.setColumnCount(10)
        headers = [
            "ID",
            "Name",
            "Kv",
            "mA",
            "Time",
            "Rotation",
            "Enviroment",
            "Filter",
            "Mask",
            "Active",
        ]
        self.form.setHorizontalHeaderLabels(headers)
        self.form.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.form.setRowCount(self.dfConditions.shape[0])
        self.form.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        self.mainLayout.addWidget(self.form)
        self.setLayout(self.mainLayout)

        for i in self.dfConditions.index:
            self.idItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "condition_id"])
            )
            self.idItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.nameItem = QtWidgets.QTableWidgetItem(
                self.dfConditions.at[i, "name"])
            self.nameItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.KvItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "Kv"]))
            self.KvItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.mAItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "Kv"]))
            self.mAItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.timeItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "time"])
            )
            self.timeItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.rotationItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "rotation"])
            )
            self.rotationItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.environmentItem = QtWidgets.QTableWidgetItem(
                self.dfConditions.at[i, "environment"]
            )
            self.environmentItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.filterItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "filter"])
            )
            self.filterItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.maskItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "mask"])
            )
            self.maskItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.activeItem = QtWidgets.QTableWidgetItem(
                str(bool(self.dfConditions.at[i, "active"]))
            )
            self.activeItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.form.setItem(i, 0, self.idItem)
            self.form.setItem(i, 1, self.nameItem)
            self.form.setItem(i, 2, self.KvItem)
            self.form.setItem(i, 3, self.mAItem)
            self.form.setItem(i, 4, self.timeItem)
            self.form.setItem(i, 5, self.rotationItem)
            self.form.setItem(i, 6, self.environmentItem)
            self.form.setItem(i, 7, self.filterItem)
            self.form.setItem(i, 8, self.maskItem)
            self.form.setItem(i, 9, self.activeItem)


class Ui_PeakSearchWindow(QtWidgets.QMainWindow):
    """This class represents a user interface for peak search and analysis.

    Args:
        path (str): The path to the data file.
        rng (list): A list specifying the data range as [start, end].
        condition (str): The condition label.

    Attributes:
        windowSize (QtCore.QSize): The size of the main window.
        dfElements: A DataFrame containing elemental data.
        path (str): The path to the data file.
        range (list): The data range.
        condition (str): The condition label.
        intensityRange: A list of intensity values.
        px: Numpy array for X-axis values.
        plotPen: Pen for plotting data.
        deactivePen: Pen for deactivated elements.
        activePen: Pen for active elements.
        items: A list of element items.
        mainLayout (QtWidgets.QVBoxLayout): The main layout for the user interface.
        form (QtWidgets.QTableWidget): The table widget for displaying element data.
        graph (GraphicsLayoutWidget): The graphical layout widget.
        peakPlot: The plot for displaying peak data.
        spectrumPlot: The plot for displaying spectrum data.
        peakRegion: Linear region for peak selection.
        spectrumRegion: Linear region for spectrum selection.
        vLine: Vertical line for mouse tracking.
        hLine: Horizontal line for mouse tracking.
        cordinateLabel (QtWidgets.QLabel): Label for displaying mouse coordinates.
        mainWidget (QtWidgets.QWidget): The main widget for the user interface.

    Methods:
        setupUi(self): Set up the user interface.
        itemClicked(self, item): Handle item click event.
        itemChanged(self, item): Handle item change event.
        headerClicked(self, column): Handle header click event.
        lowKevItemChanged(self, item): Handle low Kev item change event.
        highKevItemChanged(self, item): Handle high Kev item change event.
        scalePeakPlot(self): Scale the peak plot based on spectrum region.
        mouseMoved(self, event): Handle mouse move event.
        updateSpecRegion(self, window, viewRange): Update the spectrum region.
        changeRegionRange(self): Change the region range.
        updateItem(self, index, lowKev, highKev, intensity): Update item data.
        openPopUp(self, event): Open a popup menu for element options.
        writeToTable(self): Write elemental data to the table.
        actionClicked(self, action): Handle action click event.
        initItem(self, item, index): Initialize an element item.
        setItem(self, item): Set an item in the table.
        addItemToForm(self): Add an item to the table.
        setRegion(self, item): Set the region for an item.
        statusChanged(self): Change the status of an item.
        activeItem(self, item): Activate an item.
        deactiveItem(self, item): Deactivate an item.
        hide(self): Hide an item in the plot.
        hideAll(self): Hide all items in the plot.
        keyPressEvent(self, event): Handle key press events.
        removeRow(self): Remove a row from the table and database.
        removeAll(self): Remove all rows from the table and database.
        setupForm(self): Set up the table form.
        findLines(self, index): Find lines for an element.

    """

    def __init__(self, path, rng, condition):
        super().__init__()
        self.windowSize = QtCore.QSize(
            int(size.width() * 0.75), int(size.height() * 0.75)
        )
        self.dfElements = SQLITE.read(Addr["dbFundamentals"], "elements")
        self.path = path
        self.range = rng
        self.condition = condition
        # F:/CSAN/main/myFiles/Au.txt [4126, 6173] Condition 4
        self.intensityRange = TEXTREADER.listItems(self.path, self.range, int)
        self.px = np.arange(0, len(self.intensityRange), 1)
        self.addedElements = list()
        self.items = []
        # pens
        self.plotPen = mkPen("w", width=2)
        self.deactivePen = mkPen("r", width=2)
        self.activePen = mkPen("g", width=2)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.form = QtWidgets.QTableWidget()
        self.graph = GraphicsLayoutWidget()
        self.peakPlot = self.graph.addPlot(row=0, col=0)
        self.spectrumPlot = self.graph.addPlot(row=1, col=0)
        self.peakRegion = LinearRegionItem()
        self.spectrumRegion = LinearRegionItem()
        self.vLine = InfiniteLine(angle=90, movable=False)
        self.hLine = InfiniteLine(angle=0, movable=False)
        self.cordinateLabel = QtWidgets.QLabel()
        self.mainWidget = QtWidgets.QWidget()

    # @runtime_monitor
    def setupUi(self):
        # window config
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle(f"{Path(self.path).stem} - {self.condition}")
        self.showMaximized()

        # form config
        self.form.setMaximumHeight(int(self.size().height() * 0.3))
        self.form.setFrameShape(QtWidgets.QFrame.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Plain)
        self.form.itemChanged.connect(self.itemChanged)
        self.form.itemClicked.connect(self.itemClicked)
        self.form.horizontalHeader().sectionClicked.connect(self.headerClicked)
        self.form.setColumnCount(7)
        self.setupForm()

        # graphics config
        self.peakRegion.setZValue(10)
        self.peakRegion.sigRegionChanged.connect(self.changeRegionRange)
        self.spectrumRegion.setZValue(10)
        self.spectrumRegion.sigRegionChanged.connect(self.scalePeakPlot)
        self.spectrumPlot.showGrid(x=True, y=True)
        self.spectrumPlot.addItem(self.spectrumRegion, ignoreBounds=True)
        self.spectrumPlot.setLimits(
            xMin=0, xMax=max(self.px), yMin=0, yMax=1.1 * max(self.intensityRange)
        )
        self.spectrumPlot.plot(
            x=self.px, y=self.intensityRange, pen=self.plotPen)
        self.spectrumPlot.setMouseEnabled(x=False, y=False)
        self.spectrumPlot.scene().sigMouseMoved.connect(self.mouseMoved)
        self.peakPlot.setMinimumHeight(int(self.size().height() * 0.4))
        self.peakPlot.showGrid(x=True, y=True)
        self.peakPlot.setLimits(
            xMin=0, xMax=max(self.px), yMin=0, yMax=1.1 * max(self.intensityRange)
        )
        self.peakPlot.plot(x=self.px, y=self.intensityRange, pen=self.plotPen)
        self.peakPlot.setMouseEnabled(x=False)  # Only allow zoom in Y-axis
        self.peakPlot.sigRangeChanged.connect(self.updateSpecRegion)
        self.peakPlot.scene().sigMouseClicked.connect(self.openPopUp)
        self.spectrumRegion.setClipItem(self.spectrumPlot)
        self.spectrumRegion.setBounds((0, max(self.px)))
        self.spectrumRegion.setRegion([0, 100])
        self.peakPlot.addItem(self.vLine, ignoreBounds=True)
        self.peakPlot.addItem(self.hLine, ignoreBounds=True)
        self.peakPlotVB = self.peakPlot.vb
        self.sepctrumPlotVB = self.spectrumPlot.vb
        self.peakPlotVB.scaleBy(center=(0, 0))
        self.peakPlotVB.menu.clear()
        self.mainLayout.addWidget(self.form)
        self.mainLayout.addWidget(self.graph)
        self.mainLayout.addWidget(self.cordinateLabel)

        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

        self.writeToTable()

    # @runtime_monitor
    def itemClicked(self, item):
        """
        Handle the item click event in the table.

        This function is called when an item in the table is clicked. It checks if the clicked item is in column 5 or 6,
        which corresponds to the "Low Kev" or "High Kev" columns in the table. If the clicked item is in one of these
        columns and the corresponding element is not currently active, it triggers the "setRegion" method to update the
        region selection in the plot.

        Args:
            item: The QTableWidgetItem that was clicked.

        Returns:
            None
        """
        if item.column() in [5, 6]:
            currentRow = self.form.currentRow()
            if not self.items[currentRow]['active']:
                self.setRegion(self.items[currentRow])
            else:
                message_box = QtWidgets.QMessageBox()
                message_box.setIcon(QtWidgets.QMessageBox.NoIcon)
                message_box.setText(
                    "To use the scaling system, you need to deactivate the element first.")
                message_box.setWindowTitle("Element is Active")
                message_box.exec_()

    # @runtime_monitor
    def itemChanged(self, item):
        """
        Handle item change event in the element data table.

        This function is called when an item in the element data table is modified.
        It checks the column of the modified item and delegates the handling
        to the appropriate function based on the column:

        - If the item is in column 5, it calls `lowKevItemChanged(item)`.
        - If the item is in column 6, it calls `highKevItemChanged(item)`.

        Args:
            item (QtWidgets.QTableWidgetItem): The item that was changed in the table.

        Returns:
            None
        """
        if item.column() == 5:
            self.lowKevItemChanged(item)
        elif item.column() == 6:
            self.highKevItemChanged(item)

    def headerClicked(self, column):
        """
        Handle header click event in the element data table.

        It checks the column of the clicked header and delegates the handling
        to the appropriate function based on the column:

        - If the item is in column 0, it calls `removeAll()`.
        - If the item is in column 1, it calls `changeVisibilityForAll()`.

        Args:
            column (int): The column of the clicked header.

        Returns:
            None
        """
        if column == 0:
            self.removeAll()
        elif column == 1:
            self.changeVisibilityForAll()

    # @runtime_monitor
    def lowKevItemChanged(self, item):
        """
        Handle the change of the low Kev value for an element in the user interface.

        This function is called when the user edits the low Kev value of an element in the table.
        It updates the displayed region on the peak plot based on the changed low Kev value,
        and recalculates the intensity within the updated region.

        Args:
            item (QtWidgets.QTableWidgetItem): The table item representing the low Kev value.

        Returns:
            None

        Notes:
            - The updated low Kev value affects the displayed region on the peak plot.
            - The calculated intensity is updated and displayed in the corresponding table cell.
        """
        highPx = self.peakRegion.getRegion()[1]
        lowKev = float(item.text())
        highKev = CALCULATION.px_to_ev(highPx)
        self.peakRegion.setRegion([CALCULATION.ev_to_px(lowKev), highPx])
        intensity = CALCULATION.intensity(
            lowKev, highKev, self.intensityRange)
        self.updateItem()

    # @runtime_monitor
    def highKevItemChanged(self, item):
        """
        Handle the change of the high Kev value for an element in the user interface.

        This function is called when the user edits the high Kev value of an element in the table.
        It updates the displayed region on the peak plot based on the changed low Kev value,
        and recalculates the intensity within the updated region.

        Args:
            item (QtWidgets.QTableWidgetItem): The table item representing the low Kev value.

        Returns:
            None

        Notes:
            - The updated low Kev value affects the displayed region on the peak plot.
            - The calculated intensity is updated and displayed in the corresponding table cell.
        """
        lowPx = self.peakRegion.getRegion()[0]
        lowKev = CALCULATION.px_to_ev(lowPx)
        highKev = float(item.text())
        self.peakRegion.setRegion([lowPx, CALCULATION.ev_to_px(highKev)])
        intensity = CALCULATION.intensity(
            lowKev, highKev, self.intensityRange)
        self.updateItem()

    def scalePeakPlot(self):
        """
        Scale the peak plot based on the selected region in the spectrum plot.

        This function adjusts the visible range of the peak plot to match the selected region
        in the spectrum plot. It updates the X-axis range of the peak plot to match the
        minimum and maximum values of the selected region in the spectrum plot, ensuring
        that both plots are synchronized.

        This function is called when the user interacts with the spectrum plot to select a
        region, allowing for zooming and focusing on specific areas of the data.

        Args:
            None

        Returns:
            None

        """
        self.spectrumRegion.setZValue(10)
        minX, maxX = self.spectrumRegion.getRegion()
        self.peakPlot.setXRange(minX, maxX, padding=0)

    def mouseMoved(self, event):
        """
        Handle the mouse movement event within the peak plot.

        This function is called when the mouse moves over the peak plot, updating the mouse position
        and displaying the corresponding coordinates on the user interface.

        Args:
            event: The mouse movement event object.

        Returns:
            None

        """
        pos = event
        if self.peakPlot.sceneBoundingRect().contains(pos):
            self.mousePoint = self.peakPlotVB.mapSceneToView(pos)
            self.cordinateLabel.setText(
                """<span style='font-size: 2rem'>
                        x=%0.1f,y=%0.1f,kEV= %0.2f
                    </span>"""
                % (
                    int(self.mousePoint.x()),
                    int(self.mousePoint.y()),
                    CALCULATION.px_to_ev(int(self.mousePoint.x())),
                )
            )
            self.vLine.setPos(self.mousePoint.x())
            self.hLine.setPos(self.mousePoint.y())

    def updateSpecRegion(self, window, viewRange):
        """
        Update the spectrum region based on the view range.

        This function is called when the view range of the spectrum plot changes. It updates the
        spectrum region to match the new view range, ensuring that the selected region is correctly
        displayed on the spectrum plot.

        Args:
            window: The window object related to the view range.
            viewRange: A tuple containing the new view range.

        Returns:
            None

        """
        rng = viewRange[0]
        self.spectrumRegion.setRegion(rng)

    def changeRegionRange(self):
        """
        Update the region range based on the user's interaction.

        This function is called when the user adjusts the region selection on the peak plot.
        It calculates the low and high energy values in keV based on pixel positions and
        updates the item's attributes and the displayed values in the user interface.

        Returns:
            None

        """
        lowPx, highPx = self.peakRegion.getRegion()
        lowKev = round(CALCULATION.px_to_ev(lowPx), 4)
        highKev = round(CALCULATION.px_to_ev(highPx), 4)
        intensity = CALCULATION.intensity(lowKev, highKev, self.intensityRange)
        currentRow = self.form.currentRow()
        item = self.items[currentRow]
        self.form.blockSignals(True)
        item["lowItem"].setText(str(lowKev))
        item["highItem"].setText(str(highKev))
        item["intensityItem"].setText(str(intensity))
        self.form.blockSignals(False)

    # @runtime_monitor
    def updateItem(self):
        """
        Update an item's attributes with new values.

        This function is responsible for updating the attributes of an element item with
        the provided low and high energy values and intensity. It is called when a change
        is made to the region selection in the user interface.

        Args:
            None

        Returns:
            None

        """
        currentRow = self.form.currentRow()
        self.items[currentRow]["low_Kev"] = float(
            self.form.item(currentRow, 5).text())
        self.items[currentRow]["high_Kev"] = float(
            self.form.item(currentRow, 6).text())
        self.items[currentRow]["intensity"] = int(
            self.form.item(currentRow, 7).text())

    # @runtime_monitor
    def openPopUp(self, event):
        """
        Handle the event when the user opens a pop-up menu in response to a mouse event.

        This function is responsible for creating and displaying a context menu when the
        right mouse button is clicked within the peak plot.

        Args:
            event: The mouse event object.

        Returns:
            None
        """
        ev = CALCULATION.px_to_ev(int(self.mousePoint.x()))
        if event.button() == QtCore.Qt.RightButton:
            self.peakPlotVB.menu.clear()
            greaterThanLow = self.dfElements['low_Kev'] < ev
            smallerThanHigh = ev < self.dfElements['high_Kev']
            msk = np.logical_and(greaterThanLow, smallerThanHigh)
            df = self.dfElements[msk]
            # print(df)
            for type in ["Ka", "Kb", "La", "Lb", "Ma"]:
                df = df[df["radiation_type"] == type]
                if df["symbol"].empty is False:
                    menu = self.peakPlotVB.menu.addMenu(type)
                    menu.triggered.connect(self.actionClicked)
                    for sym in df["symbol"].tolist():
                        menu.addAction(sym)

    # @runtime_monitor
    def writeToTable(self):
        """
        Update the table with information about active elements.

        This function populates the table in the user interface with information about active
        elements, such as their symbols, radiation types, energy values, and intensity.

        Returns:
            None
        """
        if not (self.dfElements[self.dfElements["active"] == 1].empty):
            self.form.setColumnCount(10)
            self.setupForm()
            for i in self.dfElements[self.dfElements["active"] == 1].index:
                item = {}
                item["symbol"] = self.dfElements.at[i, "symbol"]
                item["radiation_type"] = self.dfElements.at[i, "radiation_type"]
                item["Kev"] = self.dfElements.at[i, "Kev"]
                item["low_Kev"] = self.dfElements.at[i, "low_Kev"]
                item["high_Kev"] = self.dfElements.at[i, "high_Kev"]
                item["intensity"] = int(self.dfElements.at[i, "intensity"])
                index = self.dfElements[
                    self.dfElements["symbol"] == item["symbol"]
                ].index
                item["specLines"] = self.findLines(index)
                item["peakLines"] = self.findLines(index)
                item["active"] = True
                item["hide"] = False

                for line in item["specLines"]:
                    self.spectrumPlot.removeItem(line)
                    line.setPen(self.activePen)
                    self.spectrumPlot.addItem(line)
                for line in item["peakLines"]:
                    self.peakPlot.removeItem(line)
                    line.setPen(self.activePen)
                    self.peakPlot.addItem(line)

                self.setItem(item)

    # @runtime_monitor
    def actionClicked(self, action):
        """
        Handle the user's click on a specific action within the context menu.

        This function is called when the user clicks on a specific action within the context
        menu to add it to the table.

        Args:
            action: The QAction object representing the user's selection.

        Returns:
            None
        """
        sym = action.text()
        if sym in self.addedElements:
            self.deleteMessageBox = QtWidgets.QMessageBox()
            self.deleteMessageBox.setIcon(QtWidgets.QMessageBox.Information)
            self.deleteMessageBox.setText(
                f"{sym} is already added to the table."
            )
            self.deleteMessageBox.setWindowTitle("Duplicate  element!")
            self.deleteMessageBox.setStandardButtons(
                QtWidgets.QMessageBox.Ok
            )
            self.deleteMessageBox.exec()
        else:
            self.addedElements.append(sym)
            item = dict()  # init the item dictionary
            item["symbol"] = sym
            item["radiation_type"] = action.parent().title()
            index = self.dfElements[self.dfElements["symbol"]
                                    == item["symbol"]].index
            if self.form.columnCount() == 7:
                self.form.setColumnCount(10)
                self.setupForm()
            self.initItem(item, index)

    # @runtime_monitor
    def initItem(self, item, index):
        """
        Initialize an item with information from the context menu.

        This function initializes an item with details about an element selected from the
        context menu and updates its properties.

        Args:
            item: A dictionary containing information about the element.
            index: The index of the element in the data.

        Returns:
            None
        """
        item["specLines"] = self.findLines(index)
        for line in item["specLines"]:
            line.setPen(self.deactivePen)
            self.spectrumPlot.addItem(line)

        item["peakLines"] = self.findLines(index)
        for line in item["peakLines"]:
            line.setPen(self.deactivePen)
            self.peakPlot.addItem(line)

        mask = np.logical_and(
            self.dfElements["symbol"] == item["symbol"],
            self.dfElements["radiation_type"] == item["radiation_type"],
        )

        item["Kev"] = self.dfElements[mask]["Kev"].iloc[0]
        item["low_Kev"] = self.dfElements[mask]["low_Kev"].iloc[0]
        item["high_Kev"] = self.dfElements[mask]["high_Kev"].iloc[0]
        item["intensity"] = CALCULATION.intensity(
            item["low_Kev"], item["high_Kev"], self.intensityRange
        )
        item["active"] = False
        item['hide'] = False
        self.setItem(item)
        self.setRegion(item)

    # @runtime_monitor
    def setItem(self, item):
        """
        Set an item in the table with information about an element.

        This function creates and displays a new item in the table with information about
        an element, including its symbol, radiation type, energy values, and status.

        Args:
            item: A dictionary containing information about the element.

        Returns:
            None
        """
        self.removeButton = QtWidgets.QPushButton(
            icon=QtGui.QIcon(icon["cross"]))
        self.removeButton.clicked.connect(self.removeRow)
        self.hideButton = QtWidgets.QPushButton(
            icon=QtGui.QIcon(icon["unhide"]))
        self.hideButton.clicked.connect(self.changeVisibility)
        self.elementItem = QtWidgets.QTableWidgetItem(item["symbol"])
        self.elementItem.setTextAlignment(QtCore.Qt.AlignCenter)
        self.elementItem.setFlags(
            self.elementItem.flags() ^ QtCore.Qt.ItemIsEditable)
        self.typeItem = QtWidgets.QTableWidgetItem(item["radiation_type"])
        self.typeItem.setTextAlignment(QtCore.Qt.AlignCenter)
        self.typeItem.setFlags(self.typeItem.flags() ^
                               QtCore.Qt.ItemIsEditable)
        self.KevItem = QtWidgets.QTableWidgetItem(str(item["Kev"]))
        self.KevItem.setTextAlignment(QtCore.Qt.AlignCenter)
        self.KevItem.setFlags(self.KevItem.flags() ^ QtCore.Qt.ItemIsEditable)
        self.lowItem = QtWidgets.QTableWidgetItem(str(item["low_Kev"]))
        self.lowItem.setTextAlignment(QtCore.Qt.AlignCenter)
        self.highItem = QtWidgets.QTableWidgetItem(str(item["high_Kev"]))
        self.highItem.setTextAlignment(QtCore.Qt.AlignCenter)
        self.intensityItem = QtWidgets.QTableWidgetItem(str(item["intensity"]))
        self.intensityItem.setTextAlignment(QtCore.Qt.AlignCenter)
        self.intensityItem.setFlags(
            self.intensityItem.flags() ^ QtCore.Qt.ItemIsEditable
        )
        self.statusItem = QtWidgets.QTableWidgetItem()
        self.statusItem.setTextAlignment(QtCore.Qt.AlignCenter)
        self.statusItem.setFlags(
            self.statusItem.flags() ^ QtCore.Qt.ItemIsEditable)
        self.statusButton = QtWidgets.QPushButton()
        if item["active"]:
            self.statusItem.setText("Activated")
            self.statusButton.setText("Deactivate")
        else:
            self.statusItem.setText("Deactivated")
            self.statusButton.setText("Activate")
        self.statusButton.clicked.connect(self.statusChanged)

        item["lowItem"] = self.lowItem
        item["highItem"] = self.highItem
        item["intensityItem"] = self.intensityItem
        self.items.append(item)

        self.addItemToForm()

    # @runtime_monitor
    def addItemToForm(self):
        """
        Add an item to the table in the user interface.

        This function adds a new item to the table in the user interface, updating the table
        with information about active elements.

        Returns:
            None
        """
        self.form.blockSignals(True)
        self.form.setRowCount(self.form.rowCount() + 1)
        index = self.form.rowCount() - 1
        self.form.setCellWidget(index, 1, self.hideButton)
        self.form.setCellWidget(index, 0, self.removeButton)
        self.form.setItem(index, 2, self.elementItem)
        self.form.setItem(index, 3, self.typeItem)
        self.form.setItem(index, 4, self.KevItem)
        self.form.setItem(index, 5, self.lowItem)
        self.form.setItem(index, 6, self.highItem)
        self.form.setItem(index, 7, self.intensityItem)
        self.form.setItem(index, 8, self.statusItem)
        self.form.setCellWidget(index, 9, self.statusButton)
        self.form.setCurrentItem(self.elementItem)
        self.form.blockSignals(False)

    # @runtime_monitor
    def setRegion(self, item):
        """
        Set the region in the peak plot.

        This function sets the region in the peak plot based on the energy values of an
        element.

        Args:
            item: A dictionary containing information about the element.

        Returns:
            None
        """
        lowPx = CALCULATION.ev_to_px(item["low_Kev"])
        highPx = CALCULATION.ev_to_px(item["high_Kev"])
        self.peakPlot.removeItem(self.peakRegion)
        self.peakRegion.setRegion([lowPx, highPx])
        self.peakPlot.addItem(self.peakRegion, ignoreBounds=True)
        self.spectrumRegion.setRegion([lowPx - 10, highPx + 10])

    def statusChanged(self):
        """
        Handle changes in the status of an element.

        This function is called when the user changes the status (activates or deactivates)
        an element, updating the element's appearance and behavior.

        Returns:
            None
        """
        currentRow = self.form.currentRow()
        lowKevItem = self.form.item(currentRow, 5)
        highKevItem = self.form.item(currentRow, 6)
        statusItem = self.form.item(currentRow, 8)
        statusButton = self.form.cellWidget(currentRow, 9)
        item = self.items[currentRow]
        self.form.blockSignals(True)
        if statusItem.text() == "Deactivated":
            statusItem.setText("Activated")
            statusButton.setText("Deactivate")
            self.activeItem(item)
            self.peakPlot.removeItem(self.peakRegion)
        else:
            statusItem.setText("Deactivated")
            statusButton.setText("Activate")
            self.deactiveItem(item)
            self.setRegion(item)
        self.form.blockSignals(False)

    # @runtime_monitor
    def activeItem(self, item):
        """
        Activate an element and update its appearance.

        This function activates an element and updates its appearance, including changing the
        pen style for associated lines in the plots.

        Args:
            item: A dictionary containing information about the element.

        Returns:
            None
        """
        self.updateItem()
        SQLITE.activeElement(self.condition, item)
        item["active"] = True
        for line in item["specLines"]:
            self.spectrumPlot.removeItem(line)
            line.setPen(self.activePen)
            self.spectrumPlot.addItem(line)
        for line in item["peakLines"]:
            self.peakPlot.removeItem(line)
            line.setPen(self.activePen)
            self.peakPlot.addItem(line)

    # @runtime_monitor
    def deactiveItem(self, item):
        """
        Deactivate an element and update its appearance.

        This function deactivates an element and updates its appearance, including changing
        the pen style for associated lines in the plots.

        Args:
            item: A dictionary containing information about the element.

        Returns:
            None
        """
        SQLITE.deactiveElement(item)
        item["active"] = False
        for line in item["specLines"]:
            self.spectrumPlot.removeItem(line)
            line.setPen(self.deactivePen)
            self.spectrumPlot.addItem(line)
        for line in item["peakLines"]:
            self.peakPlot.removeItem(line)
            line.setPen(self.deactivePen)
            self.peakPlot.addItem(line)

    # @runtime_monitor
    def changeVisibility(self):
        """
        Hide or unhide an element in the plots.

        This function allows the user to hide or unhide an element's lines in the plots, 
        depending on its current visibility.

        Returns:
            None
        """
        currentRow = self.form.currentRow()
        hideButton = self.form.cellWidget(currentRow, 1)
        item = self.items[currentRow]
        if item["hide"]:
            hideButton.setIcon(QtGui.QIcon(icon["unhide"]))
            for line in item["specLines"]:
                self.spectrumPlot.addItem(line)
            for line in item["peakLines"]:
                self.peakPlot.addItem(line)
            item["hide"] = False
        else:
            hideButton.setIcon(QtGui.QIcon(icon["hide"]))
            for line in item["specLines"]:
                self.spectrumPlot.removeItem(line)
            for line in item["peakLines"]:
                self.peakPlot.removeItem(line)
            item["hide"] = True

    def changeVisibilityForAll(self):
        """
        Hide or unhide all the elements in the plots.

        This function allows the user to hide or unhide all the elements in the plots, 
        depending on the first row element visibility.

        Returns:
            None
        """
        state = self.items[0]['hide']
        for i in range(len(self.items)):
            self.items[i]['hide'] = not state
            hideButton = self.form.cellWidget(i, 1)
            if state:
                hideButton.setIcon(QtGui.QIcon(icon["unhide"]))
                for line in self.items[i]["specLines"]:
                    self.spectrumPlot.addItem(line)
                for line in self.items[i]["peakLines"]:
                    self.peakPlot.addItem(line)
            else:
                hideButton.setIcon(QtGui.QIcon(icon["hide"]))
                for line in self.items[i]["specLines"]:
                    self.spectrumPlot.removeItem(line)
                for line in self.items[i]["peakLines"]:
                    self.peakPlot.removeItem(line)

    # @runtime_monitor
    def keyPressEvent(self, event):
        """
        Handle key press events, including deleting rows from the table.

        This function handles key press events, and if the delete key is pressed, it allows
        the user to remove rows from the table.

        Args:
            event: The key press event.

        Returns:
            None
        """
        if event.key() == QtCore.Qt.Key_Delete:
            self.removeRow()
        else:
            super().keyPressEvent(event)

    # @runtime_monitor
    def removeRow(self):
        """
        Remove a row from the table and deactivate the corresponding element.

        This function removes a selected row from the table in the user interface and
        deactivates the corresponding element, including updating the plots.

        Returns:
            None
        """
        row = self.form.currentRow()
        item = self.items[row]
        self.deleteMessageBox = QtWidgets.QMessageBox()
        self.deleteMessageBox.setIcon(QtWidgets.QMessageBox.Warning)
        self.deleteMessageBox.setText(
            f"{item['symbol']} will be removed."
        )
        self.deleteMessageBox.setWindowTitle("Warning!")
        self.deleteMessageBox.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        )
        returnValue = self.deleteMessageBox.exec()
        if returnValue == QtWidgets.QMessageBox.Ok:
            self.form.removeRow(row)
            SQLITE.deactiveElement(item)
            for line in self.items[row]["specLines"]:
                self.spectrumPlot.removeItem(line)
            for line in self.items[row]["peakLines"]:
                self.peakPlot.removeItem(line)
            self.items.pop(row)
            if self.form.rowCount() == 0:
                self.peakPlot.removeItem(self.peakRegion)
                self.form.setColumnCount(7)
                self.setupForm()

    def removeAll(self):
        """
        Remove all rows from the table and deactivate all the corresponding elements.

        Returns:
            None
        """
        self.deleteMessageBox = QtWidgets.QMessageBox()
        self.deleteMessageBox.setIcon(QtWidgets.QMessageBox.Warning)
        self.deleteMessageBox.setText(
            f"All records will be removed. Note that all of the activated elements will also be deactivated.\nPress OK if you want to continue."
        )
        self.deleteMessageBox.setWindowTitle("Warning!")
        self.deleteMessageBox.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        )
        returnValue = self.deleteMessageBox.exec()
        if returnValue == QtWidgets.QMessageBox.Ok:
            for i in range(len(self.items)):
                for line in self.items[i]["specLines"]:
                    self.spectrumPlot.removeItem(line)
                for line in self.items[i]["peakLines"]:
                    self.peakPlot.removeItem(line)
            self.items.clear()
            self.form.setRowCount(0)
        SQLITE.deactiveAll()
        self.peakPlot.removeItem(self.peakRegion)
        self.form.setColumnCount(7)
        self.setupForm()

    # @runtime_monitor
    def setupForm(self):
        """
        Set up the table in the user interface.

        This function configures the appearance and headers of the table in the user
        interface, adjusting the column headers based on the current state of the table.

        Returns:
            None
        """
        headers = [
            "",
            "",
            "Element",
            "Type",
            "Kev",
            "Low Kev",
            "High Kev",
            "Intensity",
            "Status",
            "",
        ]
        if self.form.columnCount() == 10:
            self.form.setHorizontalHeaderLabels(headers)
            for i, header in enumerate(headers):
                if header == "":
                    self.form.horizontalHeader().setSectionResizeMode(
                        i, QtWidgets.QHeaderView.ResizeToContents
                    )
                else:
                    self.form.horizontalHeader().setSectionResizeMode(
                        i, QtWidgets.QHeaderView.Stretch
                    )
        else:
            self.form.setHorizontalHeaderLabels(headers[2:-1])
            self.form.horizontalHeader().setSectionResizeMode(
                QtWidgets.QHeaderView.Stretch
            )

    # @runtime_monitor
    def findLines(self, index):
        """
        Find lines associated with elements.

        This function finds and returns lines associated with the elements specified by
        their index.

        Args:
            index: The index of the elements in the data.

        Returns:
            List of lines associated with the elements.
        """
        lines = []
        for i in index:
            line = InfiniteLine()
            line.setAngle(90)
            line.setMovable(False)
            ev = self.dfElements.at[i, "Kev"]
            px = CALCULATION.ev_to_px(ev)
            line.setValue(px)
            symLabel = InfLineLabel(
                line, self.dfElements.at[i, "symbol"], movable=False, position=0.9
            )
            type = self.dfElements.at[i, "radiation_type"]
            typeLabel = InfLineLabel(line, type, movable=False, position=0.8)
            lines.append(line)
        return lines


class Ui_PlotWindow(QtWidgets.QMainWindow):
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

    def __init__(self):
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

    def setupUi(self):
        # window config
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle("Graph")
        self.showMaximized()

        # actions config
        self.actionOpen.setIcon(QtGui.QIcon(icon["open"]))
        self.actionOpen.setText("Open")
        self.actionOpen.triggered.connect(lambda: self.openFilesDialog())
        self.actionPeakSearch.setIcon(QtGui.QIcon(icon["peak_search"]))
        self.actionPeakSearch.setText("Peak Search")
        self.actionPeakSearch.setStatusTip("Find elements in spectrum")
        self.actionPeakSearch.setDisabled(True)
        self.actionPeakSearch.triggered.connect(
            lambda: self.openPeakSearch(self.form.currentItem())
        )
        self.actionConditions.setIcon(QtGui.QIcon(icon["conditions"]))
        self.actionConditions.setText("Conditions")
        self.actionConditions.triggered.connect(lambda: self.openConditions())
        self.actionElements.setIcon(QtGui.QIcon(icon['elements']))
        self.actionElements.setText("Elements")
        self.actionElements.triggered.connect(self.openElements)

        self.actionDelete.setText("Delete")
        self.actionDelete.setIcon(QtGui.QIcon(icon["cross"]))
        self.actionDelete.triggered.connect(self.remove)
        self.actionDirectory.setText("Open file location")
        self.actionDirectory.triggered.connect(self.openDirectory)

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

        # statubar config
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
            self.curvePlot.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved
        )

        # form config
        self.form.setFixedWidth(int(self.windowSize.width() * 0.25))
        self.form.setColumnCount(3)
        self.form.setHeaderLabels(["File", "Condition", "Color"])
        self.form.setFrameShape(QtWidgets.QFrame.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Plain)
        self.form.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.form.customContextMenuRequested.connect(self.showContextMenu)
        self.form.itemChanged.connect(self.itemChanged)
        self.form.itemClicked.connect(self.itemClicked)
        self.form.itemDoubleClicked.connect(self.openPeakSearch)

        self.mainLayout.addWidget(self.curvePlot, 0, 0)
        self.mainLayout.addWidget(self.form, 0, 1)
        self.mainLayout.addWidget(self.cordinateLabel, 1, 0)

        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

    def openDirectory(self):
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
        self.plotFiles()

    def showContextMenu(self, position):
        """
        Display a context menu for the selected item at the specified position.

        Args:
            position (QPoint): The position where the context menu should be displayed.
        """
        item = self.form.itemAt(position)
        if self.form.indexOfTopLevelItem(item) >= 0:
            self.customMenu.exec_(self.form.mapToGlobal(position))

    def openFilesDialog(self):
        """
        Open a file dialog for selecting and initializing new items in the form.
        """
        self.fileDialog = QtWidgets.QFileDialog()
        self.fileDialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        self.fileDialog.setNameFilter("Texts (*.txt)")
        self.fileDialog.show()
        self.fileDialog.fileSelected.connect(self.initItem)

    def initItem(self, file):
        """
        Initialize a new item based on the selected file, including adding conditions and color buttons.

        Args:
            file (str): The path of the selected file.
        """
        fileItem = QtWidgets.QTreeWidgetItem()
        fileName = Path(file).stem
        fileItem.setText(0, fileName)
        fileItem.setCheckState(0, QtCore.Qt.Unchecked)

        conditionsDictionary = TEXTREADER.conditionDictionary(file)
        colorButtons = list()
        for index, condition in enumerate(list(conditionsDictionary.keys())):
            conditionItem = QtWidgets.QTreeWidgetItem()
            conditionItem.setText(1, condition)
            conditionItem.setCheckState(1, QtCore.Qt.Unchecked)

            fileItem.addChild(conditionItem)
            self.form.addTopLevelItem(fileItem)

            button = ColorButton()
            button.setColor(self.colors[index])
            button.sigColorChanged.connect(self.plotFiles)
            colorButtons.append(button)
            self.form.setItemWidget(conditionItem, 2, button)

        properties = {
            "path": file,
            "conditions": conditionsDictionary,
            "colorButtons": colorButtons,
        }
        self.addedFiles[fileName] = properties

    def plotFiles(self):
        """
        Plot the selected files and conditions on the curve plot.
        """
        self.curvePlot.clear()
        for properties in self.addedFiles.values():
            for index, condition in enumerate(properties["conditions"].values()):
                if condition["active"]:
                    intensity = TEXTREADER.listItems(
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

    def openPeakSearch(self, item):
        """
        Open a peak search window for the selected item.

        Args:
            item (QTreeWidgetItem): The selected item in the form.
        """
        if self.form.indexOfTopLevelItem(item) == -1:
            itemText = item.text(1)
            topLevelText = item.parent().text(0)
            self.peakSearchWindow = Ui_PeakSearchWindow(
                self.addedFiles[topLevelText]["path"],
                self.addedFiles[topLevelText]["conditions"][itemText]["range"],
                itemText,
            )
            self.peakSearchWindow.setupUi()
            self.peakSearchWindow.show()

    def openConditions(self):
        """
        Open Conditions window for managing conditions.
        """
        self.conditionsWindow = Ui_ConditionsWindow()
        self.conditionsWindow.setupUi()
        self.conditionsWindow.show()

    def openElements(self):
        """
        Open Elements window for managing elements.
        """
        self.elementsWindow = Ui_ElementsWindow()
        self.elementsWindow.setupUi()
        self.elementsWindow.show()

    def itemClicked(self, item):
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

    def itemChanged(self, item):
        """
        Handle changes in item check states and update the plot accordingly.

        Args:
            item (QTreeWidgetItem): The item for which the check state has changed.
        """
        self.form.blockSignals(True)
        self.form.setCurrentItem(item)
        topLevelIndex = self.form.indexOfTopLevelItem(item)
        if topLevelIndex != -1:
            if item.checkState(0) != 0:
                for index, state in enumerate(self.addedFiles[item.text(0)]["conditions"].values()):
                    state["active"] = True
                    item.child(index).setCheckState(1, QtCore.Qt.Checked)
            else:
                for index, state in enumerate(self.addedFiles[item.text(0)]["conditions"].values()):
                    state["active"] = False
                    item.child(index).setCheckState(1, QtCore.Qt.Unchecked)
        else:
            topLevel = item.parent()
            if item.checkState(1) != 0:
                self.addedFiles[topLevel.text(0)]["conditions"][item.text(1)][
                    "active"
                ] = True
            else:
                self.addedFiles[topLevel.text(0)]["conditions"][item.text(1)][
                    "active"
                ] = False
            flag = False
            for i in range(topLevel.childCount()):
                if topLevel.child(i).checkState(1) == 0:
                    topLevel.setCheckState(0, QtCore.Qt.Unchecked)
                    flag = True
                    break
            if not flag:
                topLevel.setCheckState(0, QtCore.Qt.Checked)

        self.plotFiles()
        self.form.blockSignals(False)

    def mouseMoved(self, e):
        """
        Update the cursor coordinates when the mouse is moved over the plot.

        Args:
            e (list): A list containing information about the mouse event.
        """
        pos = e[0]
        if self.curvePlot.sceneBoundingRect().contains(pos):
            mousePoint = self.curvePlot.getPlotItem().vb.mapSceneToView(pos)
            self.cordinateLabel.setText(
                "<span style='font-size: 2rem'>x=%0.1f,y=%0.1f</span>"
                % (mousePoint.x(), mousePoint.y())
            )


# Table window must be refined later!!!
class Ui_TableWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

    def setupUi(self, table):
        # variables
        self.df = SQLITE.read(Addr["dbTables"], table)
        elementsRng = 93
        self.tables = {
            "a": {
                "name": "Table a",
                "columnCount": elementsRng,
                "rowCount": elementsRng,
            },
            "b": {
                "name": "Table b",
                "columnCount": elementsRng,
                "rowCount": elementsRng,
            },
            "c": {
                "name": "Table c",
                "columnCount": elementsRng,
                "rowCount": elementsRng,
            },
            "r": {
                "name": "Relations",
                "columnCount": elementsRng,
                "rowCount": elementsRng,
            },
            "cp": {
                "name": "CalibrationParameters",
                "columnCount": elementsRng,
                "rowCount": 2,
            },
        }

        # window config
        self.windowSize = QtCore.QSize(
            int(size.width() * 0.5), int(size.height() * 0.5)
        )
        self.setMinimumSize(self.windowSize)
        if table in ["a", "b", "c"]:
            self.setWindowTitle(f"Table {table}")
        elif table == "cp":
            self.setWindowTitle("Calibration Parameters")

        # layout
        self.tableLayout = QtWidgets.QVBoxLayout()

        # table config
        self.elementsTable = QtWidgets.QTableWidget()
        self.elementsTable.setTabletTracking(True)
        self.elementsTable.setColumnCount(93)
        self.elementsTable.setHorizontalHeaderLabels(self.df.columns)
        # Calibration Parameters only has 2 rows
        if table == "cp":
            self.elementsTable.setRowCount(2)
            self.elementsTable.setVerticalHeaderLabels(["A0", "A1"])
        else:
            self.elementsTable.setVerticalHeaderLabels(self.df.columns)
        # for desired input
        # if table == 'r':
        #     self.elementsTable.setItemDelegate(TEXTDELEGATE())
        # else:
        #     self.elementsTable.setItemDelegate(FLOATDELEGATE)
        self.tableLayout.addWidget(self.elementsTable)
        # fill the table from the database
        self.writeToTable()
        # if the cell content changed, save that content to the database
        self.elementsTable.cellChanged.connect(
            lambda: self.saveToDatabase(table))

        self.mainWidget = QtWidgets.QWidget()
        self.mainWidget.setLayout(self.tableLayout)
        self.setCentralWidget(self.mainWidget)

    # a func for filling the table
    def writeToTable(self):
        for row in range(self.elementsTable.rowCount()):
            for column in range(self.elementsTable.columnCount()):
                value = self.df.iat[row, column]
                if value is not None:
                    self.elementsTable.setItem(
                        row, column, QtWidgets.QTableWidgetItem(str(value))
                    )

    # a func for saving table contents into a database
    def saveToDatabase(self, table):
        row = self.elementsTable.currentRow()
        column = self.elementsTable.currentColumn()
        tableItem = self.elementsTable.item(row, column)
        value = tableItem.text()
        if table == "r":
            self.df.iat[row, column] = value
        else:
            self.df.iat[row, column] = float(value)

        SQLITE.write(Addr["dbTables"], self.tables[table]["name"], self.df)


class Ui_MainWindow(QtWidgets.QMainWindow):
    # inherit
    def __init__(self):
        super().__init__()
        self.windowSize = QtCore.QSize(
            int(size.width() * 0.75), int(size.height() * 0.75)
        )
        self.table_a = Ui_TableWindow()
        self.table_b = Ui_TableWindow()
        self.table_c = Ui_TableWindow()
        self.table_r = Ui_TableWindow()
        self.table_cp = Ui_TableWindow()
        self.plotWindow = Ui_PlotWindow()
        self.menubar = QtWidgets.QMenuBar()
        self.menuCalculate = QtWidgets.QMenu(self.menubar)
        self.menuCoefficient = QtWidgets.QMenu(self.menubar)
        self.menuCalibration = QtWidgets.QMenu(self.menubar)
        self.menuIdentification = QtWidgets.QMenu(self.menubar)
        self.statusbar = QtWidgets.QStatusBar()
        self.actionTable_a = QtWidgets.QAction()
        self.actionTable_b = QtWidgets.QAction()
        self.actionTable_c = QtWidgets.QAction()
        # self.actionRelations = QtWidgets.QAction()
        self.actionCP = QtWidgets.QAction()
        self.actionPlot = QtWidgets.QAction()

    def setupUi(self):
        # window config
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle("XRF")
        self.showMaximized()

        # sub windows config
        self.table_a.setupUi("a")
        self.table_b.setupUi("b")
        self.table_c.setupUi("c")
        # self.table_r.setupUi('r')
        self.table_cp.setupUi("cp")

        # status bar config
        self.setStatusBar(self.statusbar)

        # actions config
        self.actionTable_a.setText("Table a")
        self.actionTable_a.triggered.connect(
            lambda: self.openTable(self.table_a))
        self.actionTable_b.setText("Table b")
        self.actionTable_b.triggered.connect(
            lambda: self.openTable(self.table_b))
        self.actionTable_c.setText("Table c")
        self.actionTable_c.triggered.connect(
            lambda: self.openTable(self.table_c))
        # self.actionRelations.triggered.connect(
        #     lambda: self.openTable(self.table_r)
        # )
        self.actionCP.setText("Calibration Parameters")
        self.actionCP.triggered.connect(
            lambda: self.openTable(
                self.table_cp,
            )
        )
        self.actionPlot.setText("Plot")
        self.actionPlot.triggered.connect(lambda: self.openPlotWindow())

        # menubar config
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 18))
        self.menuCalculate.setTitle("Calculate")
        self.menuCoefficient.setTitle("Coefficient")
        self.menuCalibration.setTitle("Calibration")
        self.menuIdentification.setTitle("Identification")
        self.setMenuBar(self.menubar)
        self.menuCoefficient.addAction(self.actionTable_a)
        self.menuCoefficient.addAction(self.actionTable_b)
        self.menuCoefficient.addAction(self.actionTable_c)
        # self.menuCoefficient.addAction(self.actionRelations)
        self.menuCoefficient.addAction(self.actionCP)
        self.menuIdentification.addAction(self.actionPlot)
        self.menubar.addAction(self.menuCalculate.menuAction())
        self.menubar.addAction(self.menuCoefficient.menuAction())
        self.menubar.addAction(self.menuCalibration.menuAction())
        self.menubar.addAction(self.menuIdentification.menuAction())

    # a func for opening the table
    def openTable(self, tableWindow):
        tableWindow.setupUi()
        tableWindow.show()

    def openPlotWindow(self):
        self.plotWindow.setupUi()
        self.plotWindow.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()
    app.setWindowIcon(QtGui.QIcon(icon["CSAN"]))
    MainWindow = Ui_PlotWindow()
    MainWindow.setupUi()
    MainWindow.show()
    sys.exit(app.exec())
