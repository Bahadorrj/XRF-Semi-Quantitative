from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLabel,
    QStatusBar,
    QPushButton,
    QTableWidgetItem,
    QMessageBox,
    QApplication
)
from multipledispatch import dispatch
from numpy import zeros, arange, logical_and, uint32, uint16
from pyqtgraph import mkPen, GraphicsLayoutWidget, LinearRegionItem, InfiniteLine

from python.Logic import Calculation
from python.Logic.Sqlite import DatabaseConnection, getDatabaseDataframe, getValues
from python.Types.ElementClass import Element
from python.Views.MessegeBox import Dialog
from python.Views.Widgets import Table

import qrcResources


class Window(QMainWindow):
    elementAdded = pyqtSignal(Element)
    rowAdded = pyqtSignal(int)
    windowOpened = pyqtSignal()
    windowClosed = pyqtSignal()
    hideAll = pyqtSignal(bool)

    def __init__(self, size):
        super().__init__()
        # size
        self.setMinimumWidth(int(size.width() * 0.75))
        self.setMinimumHeight(int(size.height() * 0.75))
        self.mainLayout = QVBoxLayout()
        self.mainWidget = QWidget()
        self._createForm()
        self._createGraph()
        self.coordinateLabel = QLabel()
        self.coordinateLabel.setFixedWidth(200)
        self.coordinateLabel.setText(
            """<span style='font-size: 2rem'>x=0, y=0, , kEV= 0</span>""")
        self.statusLabel = QLabel()
        self.statusLabel.setFixedWidth(200)
        self.statusBar = QStatusBar()
        self.statusBar.addWidget(self.coordinateLabel)
        self.statusBar.addWidget(self.statusLabel)
        self._placeComponents()
        database = DatabaseConnection.getInstance(":fundamentals.db")
        self._elementsDf = getDatabaseDataframe(database, "elements")
        self._conditionID = int()
        self._counts = zeros(2048, dtype=uint32)
        self._px = zeros(2048, dtype=uint16)
        self._kiloElectronVolts = list()
        self._kev = float()
        self._initElements()

    def _createForm(self):
        headers = [
            "Remove Widget",
            "Hide Widget",
            "Element",
            "Type",
            "Kev",
            "Low Kev",
            "High Kev",
            "Intensity",
            "Status",
            "Activate Widget"
        ]
        self.form = Table(headers)
        self.form.setMaximumHeight(int(self.size().height() * 0.3))

    def _createGraph(self):
        self.graph = GraphicsLayoutWidget()
        self.peakPlot = self.graph.addPlot(row=0, col=0)
        self.spectrumPlot = self.graph.addPlot(row=1, col=0)
        self.peakPlotVB = self.peakPlot.vb
        self.spectrumPlotVB = self.spectrumPlot.vb
        self.spectrumRegion = LinearRegionItem()
        self.vLine = InfiniteLine(angle=90, movable=False)
        self.hLine = InfiniteLine(angle=0, movable=False)

    def _configureGraph(self):
        self.spectrumPlot.showGrid(x=True, y=True)
        self.spectrumPlot.setMouseEnabled(x=False, y=False)
        self.peakPlot.setMinimumHeight(int(self.size().height() * 0.4))
        self.peakPlot.showGrid(x=True, y=True)
        self.spectrumPlot.addItem(self.spectrumRegion, ignoreBounds=True)
        self.peakPlot.addItem(self.vLine, ignoreBounds=True)
        self.peakPlot.addItem(self.hLine, ignoreBounds=True)
        self.peakPlotVB.scaleBy(center=(0, 0))
        self.peakPlotVB.menu.clear()

    def _placeComponents(self):
        self.mainLayout.addWidget(self.form)
        self.mainLayout.addWidget(self.graph)
        self.mainLayout.addWidget(self.statusBar)
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

    def _initElements(self):
        self._elements = list()
        self._addedElements = list()
        database = DatabaseConnection.getInstance(":fundamentals.db")
        values = getValues(database, "elements")
        for value in values:
            e = Element(value[0])
            self._elements.append(e)
            if e.activated:
                self._addedElements.append(e)

    def configureWindow(self):
        self._configureGraph()
        for element in self._addedElements:
            element.hidden = True
            self._addElementToForm(element)
            self.elementAdded.emit(element)

    def init(self, counts, condition):
        self.setWindowTitle(condition.getName())
        self._counts = counts
        self._px = arange(0, len(self._counts), 1)
        self._kiloElectronVolts = [Calculation.pxToEv(i) for i in self._px]
        self._conditionID = condition.getAttribute("condition_id")
        self.spectrumPlot.setLimits(
            xMin=0, xMax=max(self._px), yMin=0, yMax=1.1 * max(self._counts)
        )
        self.spectrumPlot.plot(x=self._px, y=self._counts, pen=mkPen("w", width=2))
        self.peakPlot.setLimits(
            xMin=0, xMax=max(self._px), yMin=0, yMax=1.1 * max(self._counts)
        )
        self.peakPlot.plot(x=self._px, y=self._counts, pen=mkPen("w", width=2))
        self.spectrumRegion.setClipItem(self.spectrumPlot)
        self.spectrumRegion.setRegion((0, 100))
        self.spectrumRegion.setBounds((0, max(self._px)))
        self.peakPlot.setXRange(0, 100, padding=0)
        self.windowOpened.emit()

    def _addElementToForm(self, element):
        removeButton = QPushButton(icon=QIcon(":cross.png"))
        hideButton = QPushButton()
        if element.hidden:
            hideButton.setIcon(QIcon(":hide.png"))
        else:
            hideButton.setIcon(QIcon(":show.png"))
        elementItem = QTableWidgetItem(
            element.getAttribute("symbol"))
        typeItem = QTableWidgetItem(
            element.getAttribute("radiation_type"))
        kevItem = QTableWidgetItem(str(element.getAttribute("Kev")))
        lowItem = QTableWidgetItem(str(element.lowKev))
        highItem = QTableWidgetItem(str(element.highKev))
        intensityItem = QTableWidgetItem(str(element.intensity))
        statusItem = QTableWidgetItem()
        statusButton = QPushButton()
        if element.activated:
            statusItem.setText("Activated")
            statusItem.setForeground(Qt.GlobalColor.green)
            statusButton.setText("Deactivate")
        else:
            statusItem.setText("Deactivated")
            statusItem.setForeground(Qt.GlobalColor.red)
            statusButton.setText("Activate")
        items = [removeButton, hideButton, elementItem, typeItem, kevItem,
                 lowItem, highItem, intensityItem, statusItem, statusButton]
        self.form.addRow(items, element.getAttribute("element_id"))
        self.rowAdded.emit(self.form.currentRow())

    def getElementById(self, id):
        for element in self._elements:
            if element.getAttribute("element_id") == id:
                return element

    def getCurrentElement(self):
        return self.getElementById(self.form.getCurrentRowId())

    def mouseMoved(self, event):
        mousePoint = self.peakPlotVB.mapSceneToView(event)
        x = int(mousePoint.x())
        y = int(mousePoint.y())
        kev = self._kiloElectronVolts[x]
        self._kev = kev
        self.coordinateLabel.setText(
            f"""<span style='font-size: 2rem'>
                    x={x}, y={y}, , kEV= {kev}
                </span>"""
        )
        self.vLine.setPos(mousePoint.x())
        self.hLine.setPos(mousePoint.y())

    def itemClicked(self):
        element = self.getElementById(self.form.getCurrentRowId())
        self._goToPx(element.range)

    def _goToPx(self, rng):
        if self.peakPlot.viewRange()[0][0] > rng[0] or self.peakPlot.viewRange()[0][1] < rng[1]:
            rng[0] -= 50
            rng[1] += 50
            self.spectrumRegion.setRegion(rng)

    def scalePeakPlot(self):
        minX, maxX = self.spectrumRegion.getRegion()
        self.peakPlot.setXRange(minX, maxX, padding=0)

    # noinspection PyUnusedLocal
    def updateSpectrumRegion(self, window, viewRange):
        rng = viewRange[0]
        self.spectrumRegion.setRegion(rng)

    def openPopUp(self, event):
        pos = event.pos()
        mousePoint = self.peakPlotVB.mapSceneToView(pos)
        self._kev = self._kiloElectronVolts[int(mousePoint.x())]
        if event.button() == Qt.MouseButton.RightButton:
            self.peakPlotVB.menu.clear()
            greater = self._elementsDf["low_Kev"] < self._kev
            smaller = self._kev < self._elementsDf["high_Kev"]
            mask = logical_and(greater, smaller)
            filteredDataframe = self._elementsDf[mask]
            for radiation_type in ["Ka", "KB", "La", "LB", "Ly", "Ma", "Bg"]:
                type_elements = filteredDataframe[filteredDataframe["radiation_type"]
                                                  == radiation_type]
                if type_elements.empty is False:
                    menu = self.peakPlotVB.menu.addMenu(radiation_type)
                    menu.triggered.connect(self.actionClicked)
                    for symbol in type_elements["symbol"].tolist():
                        menu.addAction(symbol)

    def actionClicked(self, action):
        elementSymbol = action.text()
        radiationType = action.parent().title()
        mask = logical_and(
            self._elementsDf["symbol"] == elementSymbol,
            self._elementsDf["radiation_type"] == radiationType)
        elementId = self._elementsDf[mask]["element_id"].iloc[0]
        if elementId in self.form.getRowIds():
            messageBox = Dialog(
                QMessageBox.Icon.Information,
                "Duplicate  element!",
                f"{elementSymbol} - {radiationType} is already added to the table.\n"
                f"Would you like this line to be shown?"
            )
            messageBox.setStandardButtons(QMessageBox.StandardButton.Yes |
                                          QMessageBox.StandardButton.No)
            returnValue = messageBox.exec()
            if returnValue == QMessageBox.StandardButton.Yes:
                e = self.getElementById(elementId)
                self.showElement(e)
                self.selectRow(e)
        else:
            element = self.getElementById(elementId)
            # element.hidden = False
            self._addedElements.append(element)
            self._addElementToForm(element)
            self._showAllLinesOfElement(element)
            self.elementAdded.emit(element)

    def _plotLineOfElement(self, element):
        if element.spectrumLine in self.spectrumPlot.items or element.peakLine in self.peakPlot.items:
            self.spectrumPlot.removeItem(element.spectrumLine)
            self.peakPlot.removeItem(element.peakLine)
        if element.activated:
            element.spectrumLine.setPen(mkPen("g", width=2))
            element.peakLine.setPen(mkPen("g", width=2))
        else:
            if element.getAttribute("element_id") not in self.form.getRowIds():
                element.spectrumLine.setPen(
                    mkPen(color=(255, 111, 0), width=2))
                element.peakLine.setPen(mkPen(color=(255, 111, 0), width=2))
            else:
                element.spectrumLine.setPen(mkPen("r", width=2))
                element.peakLine.setPen(mkPen("r", width=2))
        self.spectrumPlot.addItem(element.spectrumLine)
        self.peakPlot.addItem(element.peakLine)

    def _showAllLinesOfElement(self, element):
        relatedElements = list(
            filter(
                lambda x: x.getAttribute(
                    "symbol") == element.getAttribute("symbol"),
                self._elements
            )
        )
        for e in relatedElements:
            if e.getAttribute("element_id") in self.form.getRowIds():
                self.showElement(e)
                self._goToPx(element.range)
            else:
                self._plotLineOfElement(e)

    def _removeLineOfElement(self, element):
        if element.spectrumLine not in self.spectrumPlot.items:
            return
        self.spectrumPlot.removeItem(element.spectrumLine)
        self.peakPlot.removeItem(element.peakLine)

    def _hideAllLinesOfElement(self, element):
        relatedElements = list(
            filter(
                lambda x: x.getAttribute(
                    "symbol") == element.getAttribute("symbol"),
                self._elements
            )
        )
        for e in relatedElements:
            if e.getAttribute("element_id") in self.form.getRowIds():
                self.hideElement(e)
            else:
                self._removeLineOfElement(e)

    def setRange(self, element):
        lowPx, highPx = element.region.getRegion()
        lowPx = int(lowPx)
        highPx = int(highPx)
        try:
            lowKev = self._kiloElectronVolts[lowPx]
        except IndexError:
            lowKev = self._kiloElectronVolts[0]
        try:
            highKev = self._kiloElectronVolts[highPx]
        except IndexError:
            highKev = self._kiloElectronVolts[-1]
        row = self.form.getRowById(element.getAttribute("element_id"))
        if lowKev > highKev:
            lowKev = 0
        row["Low Kev"].setText(str(lowKev))
        row["High Kev"].setText(str(highKev))

    def statusChanged(self):
        row = self.form.getCurrentRow()
        element = self.getCurrentElement()
        if row.get("Status").text() == "Deactivated":
            self._activateElement(element, row)
        else:
            self._deactivateElement(element, row)

    def _activateElement(self, element, row):
        # -1 is for conflict
        rng = [Calculation.evToPx(row.get("Low Kev").text()) - 1,
               Calculation.evToPx(row.get("High Kev").text()) - 1]
        intensity = Calculation.calculateIntensityInRange(rng, self._counts)

        row.get("Status").setText("Activated")
        row.get("Status").setForeground(Qt.GlobalColor.green)
        row.get("Activate Widget").setText("Deactivate")
        row.get("Intensity").setText(str(intensity))

        element.activated = True
        element.lowKev = float(row.get("Low Kev").text())
        element.highKev = float(row.get("High Kev").text())
        element.range = rng
        element.intensity = intensity

        if element.hidden is False:
            self._hideAllLinesOfElement(element)
            self.peakPlot.removeItem(element.region)
        self.showElement(element)
        self._goToPx(element.range)

    def _deactivateElement(self, element, row):
        row.get("Status").setText("Deactivated")
        row.get("Status").setForeground(Qt.GlobalColor.red)
        row.get("Activate Widget").setText("Activate")
        row.get("Intensity").setText("None")

        element.activated = False

        if element.hidden is False:
            self._showAllLinesOfElement(element)
        else:
            self.showElement(element)
            self._goToPx(element.range)

    def removeRow(self):
        rowIndex = self.form.currentRow()
        element = self.getElementById(self.form.getCurrentRowId())
        messageBox = Dialog(
            QMessageBox.Icon.Warning,
            "Warning!",
            f"{element.getAttribute('symbol')} - {element.getAttribute('radiation_type')} will be removed."
        )
        messageBox.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        returnValue = messageBox.exec()
        if returnValue == QMessageBox.StandardButton.Ok:
            self._remove(element, rowIndex)

    def _remove(self, element, index):
        self._hideAllLinesOfElement(element)
        self.form.removeRow(index)
        element.hidden = True
        element.activated = False

    def visibility(self):
        id = self.form.getCurrentRowId()
        element = self.getElementById(id)
        if element.hidden:
            self.configureShowing(element)
            self._goToPx(element.range)
        else:
            self.configureHiding(element)

    @dispatch(Element)
    def configureShowing(self, element):
        if element.activated:
            self.showElement(element)
        else:
            self._showAllLinesOfElement(element)

    @dispatch(int)
    def configureShowing(self, index):
        element = self._addedElements[index]
        if element.activated:
            self.showElement(element)
        else:
            self._showAllLinesOfElement(element)

    @dispatch(Element)
    def configureHiding(self, element):
        if element.activated:
            self.hideElement(element)
        else:
            self._hideAllLinesOfElement(element)

    @dispatch(int)
    def configureHiding(self, index):
        element = self._addedElements[index]
        if element.activated:
            self.hideElement(element)
        else:
            self._hideAllLinesOfElement(element)

    @dispatch(Element)
    def hideElement(self, element):
        row = self.form.getRowById(element.getAttribute("element_id"))
        row.get("Hide Widget").setIcon(QIcon(":hide.png"))
        if element.activated is False and element.region in self.peakPlot.items:
            self.peakPlot.removeItem(element.region)
        self._removeLineOfElement(element)
        element.hidden = True

    @dispatch(int)
    def hideElement(self, index):
        element = self._addedElements[index]
        row = self.form.getRowById(element.getAttribute("element_id"))
        row.get("Hide Widget").setIcon(QIcon(":hide.png"))
        if element.activated is False and element.region in self.peakPlot.items:
            self.peakPlot.removeItem(element.region)
        self._removeLineOfElement(element)
        element.hidden = True

    @dispatch(Element)
    def showElement(self, element):
        row = self.form.getRowById(element.getAttribute("element_id"))
        row.get("Hide Widget").setIcon(QIcon(":show.png"))
        if element.activated is False and element.region not in self.peakPlot.items:
            self.peakPlot.addItem(element.region)
        self._plotLineOfElement(element)
        element.hidden = False

    @dispatch(int)
    def showElement(self, index):
        element = self._addedElements[index]
        row = self.form.getRowById(element.getAttribute("element_id"))
        row.get("Hide Widget").setIcon(QIcon(":show.png"))
        if element.activated is False and element.region not in self.peakPlot.items:
            self.peakPlot.addItem(element.region)
        self._plotLineOfElement(element)
        element.hidden = False

    def headerClicked(self, column):
        if column == 0:
            self._configureRemoveAll()
        elif column == 1:
            self._configureHideALL()

    def _configureRemoveAll(self):
        messageBox = Dialog(
            QMessageBox.Icon.Warning,
            "Warning!",
            "All records will be removed.\nNote that all of the activated elements will also be deactivated.\n"
            "Press OK if you want to continue."
        )
        messageBox.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        returnValue = messageBox.exec()
        if returnValue == QMessageBox.StandardButton.Ok:
            for element in self._addedElements:
                self._remove(element, 0)
                QApplication.processEvents()

    def _configureHideALL(self):
        hidden = self._addedElements[0].hidden
        if hidden:
            self.hideAll.emit(True)
            self.statusLabel.setText("showing all elements...")
        else:
            self.hideAll.emit(False)
            self.statusLabel.setText("hiding all elements...")

    def selectRow(self, element):
        if element.getAttribute("element_id") in self.form.getRowIds():
            index = self.form.getRowIds().index(element.getAttribute("element_id"))
            self.form.selectRow(index)
        self._goToPx(element.range)

    def getElements(self):
        return self._elements

    def getCondition(self):
        return self._conditionID

    def getNumberOfAddedElements(self):
        return len(self._addedElements)

    def clearStatusLabel(self):
        self.statusLabel.clear()

    def closeEvent(self, a0):
        self.windowClosed.emit()
        self.peakPlot.clear()
        self.spectrumPlot.clear()
        self.form.clear()
        self.coordinateLabel.setText(
            """<span style='font-size: 2rem'>x=0, y=0, , kEV= 0</span>""")
        super().closeEvent(a0)
