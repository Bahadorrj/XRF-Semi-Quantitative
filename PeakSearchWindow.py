import time
from pathlib import Path

import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from pyqtgraph import mkPen, GraphicsLayoutWidget, LinearRegionItem, InfiniteLine, InfLineLabel

import Calculation
import Sqlite
import TextReader
from Backend import addr, icon

import LoadingDialog


class Window(QtWidgets.QMainWindow):
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

    def __init__(self, size, path, rng, condition):
        super().__init__()
        self.windowSize = QtCore.QSize(
            int(size.width() * 0.75), int(size.height() * 0.75)
        )
        self.dfElements = Sqlite.read(addr["dbFundamentals"], "elements")
        self.path = path
        self.range = rng
        self.condition = condition
        # F:/CSAN/main/myFiles/Au.txt [4126, 6173] Condition 4
        self.intensityRange = TextReader.list_items(self.path, self.range, int)
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
    def setup_ui(self):
        # window config
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle(f"{Path(self.path).stem} - {self.condition}")
        self.showMaximized()

        # form config
        self.form.setMaximumHeight(int(self.size().height() * 0.3))
        self.form.setFrameShape(QtWidgets.QFrame.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Plain)
        self.form.itemChanged.connect(self.item_changed)
        self.form.itemClicked.connect(self.item_clicked)
        self.form.horizontalHeader().sectionClicked.connect(self.header_clicked)
        self.form.setColumnCount(7)
        self.setup_form()

        # graphics config
        self.peakRegion.setZValue(10)
        self.peakRegion.sigRegionChanged.connect(self.change_region_range)
        self.spectrumRegion.setZValue(10)
        self.spectrumRegion.sigRegionChanged.connect(self.scale_peak_plot)
        self.spectrumPlot.showGrid(x=True, y=True)
        self.spectrumPlot.addItem(self.spectrumRegion, ignoreBounds=True)
        self.spectrumPlot.setLimits(
            xMin=0, xMax=max(self.px), yMin=0, yMax=1.1 * max(self.intensityRange)
        )
        self.spectrumPlot.plot(
            x=self.px, y=self.intensityRange, pen=self.plotPen)
        self.spectrumPlot.setMouseEnabled(x=False, y=False)
        self.spectrumPlot.scene().sigMouseMoved.connect(self.mouse_moved)
        self.peakPlot.setMinimumHeight(int(self.size().height() * 0.4))
        self.peakPlot.showGrid(x=True, y=True)
        self.peakPlot.setLimits(
            xMin=0, xMax=max(self.px), yMin=0, yMax=1.1 * max(self.intensityRange)
        )
        self.peakPlot.plot(x=self.px, y=self.intensityRange, pen=self.plotPen)
        self.peakPlot.setMouseEnabled(x=False)  # Only allow zoom in Y-axis
        self.peakPlot.sigRangeChanged.connect(self.update_spectrum_region)
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

    # @runtime_monitor

    def item_clicked(self, item):
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
            current_row = self.form.currentRow()
            if not self.items[current_row]['active']:
                self.set_region(self.items[current_row])
            else:
                message_box = QtWidgets.QMessageBox()
                message_box.setIcon(QtWidgets.QMessageBox.NoIcon)
                message_box.setText(
                    "To use the scaling system, you need to deactivate the element first.")
                message_box.setWindowTitle("Element is Active")
                message_box.exec_()

    # @runtime_monitor
    def item_changed(self, item):
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
            self.low_kev_item_changed(item)
        elif item.column() == 6:
            self.high_kev_item_changed(item)

    def header_clicked(self, column):
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
            self.remove_all()
        elif column == 1:
            self.change_visibility_for_all()

    # @runtime_monitor
    def low_kev_item_changed(self, item):
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
        high_px = self.peakRegion.getRegion()[1]
        low_kev = float(item.text())
        high_kev = Calculation.px_to_ev(high_px)
        self.peakRegion.setRegion([Calculation.ev_to_px(low_kev), high_px])
        self.update_item()

    # @runtime_monitor
    def high_kev_item_changed(self, item):
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
        low_px = self.peakRegion.getRegion()[0]
        low_kev = Calculation.px_to_ev(low_px)
        high_kev = float(item.text())
        self.peakRegion.setRegion([low_px, Calculation.ev_to_px(high_kev)])
        self.update_item()

    def scale_peak_plot(self):
        """
        Scale the peak plot based on the selected region in the spectrum plot.

        This function adjusts the visible range of the peak plot to match the selected region
        in the spectrum plot. It updates the X-axis range of the peak plot to match the
        minimum and maximum values of the selected region in the spectrum plot, ensuring
        that both plots are synchronized.

        This function is called when the user interacts with the spectrum plot to select a
        region, allowing for zooming and focusing on specific areas of the data.

        Returns:
            None

        """
        self.spectrumRegion.setZValue(10)
        min_x, max_x = self.spectrumRegion.getRegion()
        self.peakPlot.setXRange(min_x, max_x, padding=0)

    def mouse_moved(self, event):
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
                    Calculation.px_to_ev(int(self.mousePoint.x())),
                )
            )
            self.vLine.setPos(self.mousePoint.x())
            self.hLine.setPos(self.mousePoint.y())

    def update_spectrum_region(self, window, viewRange):
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

    def change_region_range(self):
        """
        Update the region range based on the user's interaction.

        This function is called when the user adjusts the region selection on the peak plot.
        It calculates the low and high energy values in keV based on pixel positions and
        updates the item's attributes and the displayed values in the user interface.

        Returns:
            None

        """
        low_px, high_px = self.peakRegion.getRegion()
        low_kev = round(Calculation.px_to_ev(low_px), 4)
        high_kev = round(Calculation.px_to_ev(high_px), 4)
        intensity = Calculation.calculate_intensity_in_range(
            low_kev, high_kev, self.intensityRange)
        current_row = self.form.currentRow()
        item = self.items[current_row]
        self.form.blockSignals(True)
        item["lowItem"].setText(str(low_kev))
        item["highItem"].setText(str(high_kev))
        item["intensityItem"].setText(str(intensity))
        self.form.blockSignals(False)

    # @runtime_monitor
    def update_item(self):
        """
        Update an item's attributes with new values.

        This function is responsible for updating the attributes of an element item with
        the provided low and high energy values and intensity. It is called when a change
        is made to the region selection in the user interface.

        Returns:
            None

        """
        current_row = self.form.currentRow()
        self.items[current_row]["low_Kev"] = float(
            self.form.item(current_row, 5).text())
        self.items[current_row]["high_Kev"] = float(
            self.form.item(current_row, 6).text())
        self.items[current_row]["intensity"] = int(
            self.form.item(current_row, 7).text())

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
        ev = Calculation.px_to_ev(int(self.mousePoint.x()))
        if event.button() == QtCore.Qt.RightButton:
            self.peakPlotVB.menu.clear()
            greater_than_low = self.dfElements['low_Kev'] < ev
            smaller_than_high = ev < self.dfElements['high_Kev']
            msk = np.logical_and(greater_than_low, smaller_than_high)
            df = self.dfElements[msk]
            # print(df)
            for radiation_type in ["Ka", "KB", "La", "LB", "Ly", "Ma", "Bg"]:
                new = df[df["radiation_type"] == radiation_type]
                # print(f"{type} df:\n{new}")
                if new.empty is False:
                    menu = self.peakPlotVB.menu.addMenu(radiation_type)
                    menu.triggered.connect(self.action_clicked)
                    for sym in new["symbol"].tolist():
                        menu.addAction(sym)

    # @runtime_monitor
    def write_to_table(self):
        """
        Update the table with information about active elements.

        This function populates the table in the user interface with information about active
        elements, such as their symbols, radiation types, energy values, and intensity.

        Returns:
            None
        """
        if not self.dfElements[self.dfElements["active"] == 1].empty:
            self.loading_dialog = LoadingDialog.Window()
            self.loading_dialog.setup_ui()
            self.loading_dialog.show()
            self.form.setColumnCount(10)
            self.setup_form()
            size_df = self.dfElements[self.dfElements["active"] == 1].shape[0]
            count = 0
            for i in self.dfElements[self.dfElements["active"] == 1].index:
                element_id = self.dfElements.at[i, "element_id"]
                self.addedElements.append(element_id)
                item = dict()
                item["symbol"] = self.dfElements.at[i, "symbol"]
                item["radiation_type"] = self.dfElements.at[i, "radiation_type"]
                item["Kev"] = self.dfElements.at[i, "Kev"]
                item["px"] = Calculation.ev_to_px(item["Kev"])
                item["low_Kev"] = self.dfElements.at[i, "low_Kev"]
                item["high_Kev"] = self.dfElements.at[i, "high_Kev"]
                item["intensity"] = float(self.dfElements.at[i, "intensity"])
                index = self.dfElements[
                    self.dfElements["symbol"] == item["symbol"]
                ].index
                item["specLines"] = self.find_lines(index)
                for line in item.get('specLines'):
                    if line.value() == item['px']:
                        item["specLine"] = line
                        break
                item["peakLines"] = self.find_lines(index)
                for line in item.get("peakLines"):
                    if line.value() == item["px"]:
                        item["peakLine"] = line
                        break
                item["active"] = True
                item["hide"] = False
                item["specLine"].setPen(self.activePen)
                item["peakLine"].setPen(self.activePen)
                self.spectrumPlot.addItem(item['specLine'])
                self.peakPlot.addItem(item['peakLine'])
                self.set_item(item)
                count += 1
                if count > size_df / 2:
                    self.loading_dialog.label.setText("Almost done!")
                QtWidgets.QApplication.processEvents()
                time.sleep(0.05)
            self.loading_dialog.close()

    # @runtime_monitor
    def action_clicked(self, action):
        """
        Handle the user's click on a specific action within the context menu.

        This function is called when the user clicks on a specific action within the context
        menu to add it to the table.

        Args:
            action: The QAction object representing the user's selection.

        Returns:
            None
        """
        symbol = action.text()
        radiation_type = action.parent().title()
        mask = np.logical_and(
            self.dfElements["symbol"] == symbol, self.dfElements["radiation_type"] == radiation_type)
        element_id = self.dfElements[mask]["element_id"].iloc[0]
        if element_id in self.addedElements:
            self.deleteMessageBox = QtWidgets.QMessageBox()
            self.deleteMessageBox.setIcon(QtWidgets.QMessageBox.Information)
            self.deleteMessageBox.setText(
                f"{symbol} - {radiation_type} is already added to the table."
            )
            self.deleteMessageBox.setWindowTitle("Duplicate  element!")
            self.deleteMessageBox.setStandardButtons(
                QtWidgets.QMessageBox.Ok
            )
            self.deleteMessageBox.exec()
        else:
            self.addedElements.append(element_id)
            item = dict()  # init the item dictionary
            item["symbol"] = symbol
            item["radiation_type"] = radiation_type
            index = self.dfElements[self.dfElements["symbol"]
                                    == item["symbol"]].index
            if self.form.columnCount() == 7:
                self.form.setColumnCount(10)
                self.setup_form()
            self.init_item(item, index)

    # @runtime_monitor
    def init_item(self, item, index):
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
        mask = np.logical_and(
            self.dfElements["symbol"] == item["symbol"],
            self.dfElements["radiation_type"] == item["radiation_type"],
        )
        item["Kev"] = self.dfElements[mask]["Kev"].iloc[0]
        item["px"] = Calculation.ev_to_px(item["Kev"])
        item["low_Kev"] = self.dfElements[mask]["low_Kev"].iloc[0]
        item["high_Kev"] = self.dfElements[mask]["high_Kev"].iloc[0]
        item["intensity"] = Calculation.calculate_intensity_in_range(
            item["low_Kev"], item["high_Kev"], self.intensityRange
        )
        item["active"] = False
        item['hide'] = False
        item["specLines"] = self.find_lines(index)
        for line in item["specLines"]:
            line.setPen(self.deactivePen)
            self.spectrumPlot.addItem(line)

        item["peakLines"] = self.find_lines(index)
        for line in item["peakLines"]:
            line.setPen(self.deactivePen)
            self.peakPlot.addItem(line)

        self.set_item(item)
        self.set_region(item)

    # @runtime_monitor
    def set_item(self, item):
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
        self.removeButton.clicked.connect(self.remove_row)
        self.hideButton = QtWidgets.QPushButton(
            icon=QtGui.QIcon(icon["unhide"]))
        self.hideButton.clicked.connect(self.change_visibility)
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
        self.statusButton.clicked.connect(self.status_changed)

        item["lowItem"] = self.lowItem
        item["highItem"] = self.highItem
        item["intensityItem"] = self.intensityItem
        self.items.append(item)

        self.add_item_to_form()

    # @runtime_monitor
    def add_item_to_form(self):
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
    def set_region(self, item):
        """
        Set the region in the peak plot.

        This function sets the region in the peak plot based on the energy values of an
        element.

        Args:
            item: A dictionary containing information about the element.

        Returns:
            None
        """
        lowPx = Calculation.ev_to_px(item["low_Kev"])
        highPx = Calculation.ev_to_px(item["high_Kev"])
        self.peakPlot.removeItem(self.peakRegion)
        self.peakRegion.setRegion([lowPx, highPx])
        self.peakPlot.addItem(self.peakRegion, ignoreBounds=True)
        self.spectrumRegion.setRegion([lowPx - 10, highPx + 10])

    def status_changed(self):
        """
        Handle changes in the status of an element.

        This function is called when the user changes the status (activates or deactivates)
        an element, updating the element's appearance and behavior.

        Returns:
            None
        """
        current_row = self.form.currentRow()
        status_item = self.form.item(current_row, 8)
        status_button = self.form.cellWidget(current_row, 9)
        item = self.items[current_row]
        self.form.blockSignals(True)
        if status_item.text() == "Deactivated":
            status_item.setText("Activated")
            status_button.setText("Deactivate")
            self.activate_Item(item)
            self.peakPlot.removeItem(self.peakRegion)
        else:
            status_item.setText("Deactivated")
            status_button.setText("Activate")
            self.deactiveItem(item)
            self.set_region(item)
        self.form.blockSignals(False)

    # @runtime_monitor
    def activate_Item(self, item):
        """
        Activate an element and update its appearance.

        This function activates an element and updates its appearance, including changing the
        pen style for associated lines in the plots.

        Args:
            item: A dictionary containing information about the element.

        Returns:
            None
        """
        self.update_item()
        Sqlite.activate_element(self.condition, item)
        item["active"] = True
        for line in item["specLines"]:
            self.spectrumPlot.removeItem(line)
            if line.value() == item['px']:
                line.setPen(self.activePen)
                item['specLine'] = line
                self.spectrumPlot.addItem(line)
        for line in item["peakLines"]:
            self.peakPlot.removeItem(line)
            if line.value() == item['px']:
                line.setPen(self.activePen)
                item['peakLine'] = line
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
        Sqlite.deactivate_element(item)
        item["active"] = False
        self.spectrumPlot.removeItem(item['specLine'])
        self.peakPlot.removeItem(item['peakLine'])
        for line in item["specLines"]:
            line.setPen(self.deactivePen)
            self.spectrumPlot.addItem(line)
        for line in item["peakLines"]:
            line.setPen(self.deactivePen)
            self.peakPlot.addItem(line)

    # @runtime_monitor
    def change_visibility(self):
        """
        Hide or unhide an element in the plots.

        This function allows the user to hide or unhide an element's lines in the plots,
        depending on its current visibility.

        Returns:
            None
        """
        current_row = self.form.currentRow()
        hide_button = self.form.cellWidget(current_row, 1)
        item = self.items[current_row]
        if item["hide"]:
            hide_button.setIcon(QtGui.QIcon(icon["unhide"]))
            self.add_item(item)
            item["hide"] = False
        else:
            hide_button.setIcon(QtGui.QIcon(icon["hide"]))
            self.remove_item(item)
            item["hide"] = True

    def change_visibility_for_all(self):
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
            hide_button = self.form.cellWidget(i, 1)
            item = self.items[i]
            if state:
                hide_button.setIcon(QtGui.QIcon(icon["unhide"]))
                self.add_item(item)
            else:
                hide_button.setIcon(QtGui.QIcon(icon["hide"]))
                self.remove_item(item)

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
            self.remove_row()
        else:
            super().keyPressEvent(event)

    # @runtime_monitor
    def remove_row(self):
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
        return_value = self.deleteMessageBox.exec()
        if return_value == QtWidgets.QMessageBox.Ok:
            self.form.removeRow(row)
            Sqlite.deactivate_element(item)
            self.remove_item(item)
            self.items.pop(row)
            if self.form.rowCount() == 0:
                self.peakPlot.removeItem(self.peakRegion)
                self.form.setColumnCount(7)
                self.setup_form()

    def remove_all(self):
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
        return_value = self.deleteMessageBox.exec()
        if return_value == QtWidgets.QMessageBox.Ok:
            for i in range(len(self.items)):
                item = self.items[i]
                self.remove_item(item)
            self.items.clear()
            self.form.setRowCount(0)
        Sqlite.deactivate_all()
        self.peakPlot.removeItem(self.peakRegion)
        self.form.setColumnCount(7)
        self.setup_form()

    def add_item(self, item):
        if item["active"]:
            self.spectrumPlot.addItem(item["specLine"])
            self.peakPlot.addItem(item["peakLine"])
        else:
            for line in item["specLines"]:
                self.spectrumPlot.addItem(line)
            for line in item["peakLines"]:
                self.peakPlot.addItem(line)

    def remove_item(self, item):
        if item["active"]:
            self.spectrumPlot.removeItem(item["specLine"])
            self.peakPlot.removeItem(item["peakLine"])
        else:
            for line in item["specLines"]:
                self.spectrumPlot.removeItem(line)
            for line in item["peakLines"]:
                self.peakPlot.removeItem(line)

    # @runtime_monitor
    def setup_form(self):
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
    def find_lines(self, index):
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
            kev = self.dfElements.at[i, "Kev"]
            px = Calculation.ev_to_px(kev)
            line.setValue(px)
            sym_label = InfLineLabel(
                line, self.dfElements.at[i, "symbol"], movable=False, position=0.9
            )
            radiation_type = self.dfElements.at[i, "radiation_type"]
            radiation_type_label = InfLineLabel(
                line, radiation_type, movable=False, position=0.8)
            lines.append(line)
        return lines
