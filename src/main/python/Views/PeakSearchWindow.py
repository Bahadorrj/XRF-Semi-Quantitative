import numpy as np
from PyQt6 import QtWidgets, QtCore, QtGui
from pyqtgraph import mkPen, GraphicsLayoutWidget, LinearRegionItem, InfiniteLine

from src.main.python.Logic import Calculation
from src.main.python.Logic import Sqlite
from src.main.python.Types.ElementClass import Element
from src.main.python.Views import MessegeBox
from src.main.python.Views.Icons import ICONS
from src.main.python.Views.TableWidget import Form


class Window(QtWidgets.QMainWindow):
    elementAdded = QtCore.pyqtSignal(Element)
    rowAdded = QtCore.pyqtSignal(list)
    windowOpened = QtCore.pyqtSignal()
    windowClosed = QtCore.pyqtSignal()

    def __init__(self, size):
        super().__init__()
        # size
        self.setMinimumWidth(int(size.width() * 0.75))
        self.setMinimumHeight(int(size.height() * 0.75))
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainWidget = QtWidgets.QWidget()
        self._createForm()
        self._createGraph()
        self.coordinateLabel = QtWidgets.QLabel()
        self._placeComponents()
        QtWidgets.QApplication.processEvents()

        self._elementsDf = Sqlite.getDatabaseDataframe("fundamentals", "elements")
        self._condition = None
        self._counts = np.zeros(2048, dtype=np.int32)
        self._px = np.zeros(2048, dtype=np.int16)
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
        self.form = Form(headers)
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
        self.mainLayout.addWidget(self.coordinateLabel)
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

    def _initElements(self):
        self._elements = list()
        self._addedElements = list()
        values = Sqlite.getValues("fundamentals", "elements")
        for value in values:
            e = Element(value[0])
            self._elements.append(e)
            if e.isActivated():
                self._addedElements.append(e)

    def configureWindow(self):
        self._configureGraph()
        for element in self._addedElements:
            element.setHidden(True)
            self._addElementToForm(element)
            self.elementAdded.emit(element)

    def init(self, counts, condition):
        self.setWindowTitle(condition.getName())
        self._counts = counts
        self._px = np.arange(0, len(self._counts), 1)
        self._kiloElectronVolts = [Calculation.px_to_ev(i) for i in self._px]
        self._condition = condition
        self.spectrumPlot.setLimits(
            xMin=0, xMax=max(self._px), yMin=0, yMax=1.1 * max(self._counts)
        )
        self.spectrumPlot.plot(
            x=self._px, y=self._counts, pen=mkPen("w", width=2))
        self.peakPlot.setLimits(
            xMin=0, xMax=max(self._px), yMin=0, yMax=1.1 * max(self._counts)
        )
        self.peakPlot.plot(
            x=self._px, y=self._counts, pen=mkPen("w", width=2))
        self.spectrumRegion.setClipItem(self.spectrumPlot)
        self.spectrumRegion.setRegion((0, 100))
        self.spectrumRegion.setBounds((0, max(self._px)))
        self.peakPlot.setXRange(0, 100, padding=0)

    def _addElementToForm(self, element):
        removeButton = QtWidgets.QPushButton(icon=QtGui.QIcon(ICONS["Cross"]))
        hideButton = QtWidgets.QPushButton()
        if element.isHidden():
            hideButton.setIcon(QtGui.QIcon(ICONS["Hide"]))
        else:
            hideButton.setIcon(QtGui.QIcon(ICONS["Show"]))
        elementItem = QtWidgets.QTableWidgetItem(element.getAttribute("symbol"))
        typeItem = QtWidgets.QTableWidgetItem(element.getAttribute("radiation_type"))
        kevItem = QtWidgets.QTableWidgetItem(str(element.getAttribute("Kev")))
        lowItem = QtWidgets.QTableWidgetItem(str(element.getLowKev()))
        highItem = QtWidgets.QTableWidgetItem(str(element.getHighKev()))
        intensityItem = QtWidgets.QTableWidgetItem(str(element.getIntensity()))
        statusItem = QtWidgets.QTableWidgetItem()
        statusButton = QtWidgets.QPushButton()
        if element.isActivated():
            statusItem.setText("Activated")
            statusItem.setForeground(QtCore.Qt.GlobalColor.green)
            statusButton.setText("Deactivate")
        else:
            statusItem.setText("Deactivated")
            statusItem.setForeground(QtCore.Qt.GlobalColor.red)
            statusButton.setText("Activate")
        items = [removeButton, hideButton, elementItem, typeItem, kevItem,
                 lowItem, highItem, intensityItem, statusItem, statusButton]
        buttons = [removeButton, hideButton, statusButton]
        self.form.addRow(items, element.getAttribute("element_id"))
        self.rowAdded.emit(buttons)

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
        self._goToPx(element.getRange())

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
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            self.peakPlotVB.menu.clear()
            greater = self._elementsDf["low_Kev"] < self._kev
            smaller = self._kev < self._elementsDf["high_Kev"]
            mask = np.logical_and(greater, smaller)
            filteredDataframe = self._elementsDf[mask]
            for radiation_type in ["Ka", "KB", "La", "LB", "Ly", "Ma", "Bg"]:
                type_elements = filteredDataframe[filteredDataframe["radiation_type"] == radiation_type]
                if type_elements.empty is False:
                    menu = self.peakPlotVB.menu.addMenu(radiation_type)
                    menu.triggered.connect(self.actionClicked)
                    for symbol in type_elements["symbol"].tolist():
                        menu.addAction(symbol)

    def actionClicked(self, action):
        elementSymbol = action.text()
        radiationType = action.parent().title()
        mask = np.logical_and(
            self._elementsDf["symbol"] == elementSymbol,
            self._elementsDf["radiation_type"] == radiationType)
        elementId = self._elementsDf[mask]["element_id"].iloc[0]
        if elementId in self.form.getRowIds():
            message_box = MessegeBox.Dialog(
                QtWidgets.QMessageBox.Icon.Information,
                "Duplicate  element!",
                f"{elementSymbol} - {radiationType} is already added to the table."
            )
            message_box.exec()
        else:
            element = self.getElementById(elementId)
            self._addedElements.append(element)
            self._addElementToForm(element)
            self._showAllLinesOfElement(element)
            self.elementAdded.emit(element)

    def _plotLineOfElement(self, element):
        if element.isActivated():
            element.getSpectrumLine().setPen(mkPen("g", width=2))
            element.getPeakLine().setPen(mkPen("g", width=2))
        else:
            element.getSpectrumLine().setPen(mkPen("r", width=2))
            element.getPeakLine().setPen(mkPen("r", width=2))
        self.spectrumPlot.addItem(element.getSpectrumLine())
        self.peakPlot.addItem(element.getPeakLine())

    def _showAllLinesOfElement(self, element):
        relatedElements = list(
            filter(
                lambda x: x.getAttribute("symbol") == element.getAttribute("symbol"),
                self._elements
            )
        )
        for e in relatedElements:
            if e.getAttribute("element_id") in self.form.getRowIds():
                self._showElement(e)
            else:
                self._plotLineOfElement(e)

    def _removeLineOfElement(self, element):
        self.spectrumPlot.removeItem(element.getSpectrumLine())
        self.peakPlot.removeItem(element.getPeakLine())

    def _hideAllLinesOfElement(self, element):
        relatedElements = list(
            filter(
                lambda x: x.getAttribute("symbol") == element.getAttribute("symbol"),
                self._elements
            )
        )
        for e in relatedElements:
            if e.getAttribute("element_id") in self.form.getRowIds():
                self._hideElement(e)
            else:
                self._removeLineOfElement(e)

    def setRange(self, element):
        lowPx, highPx = element.getRegion().getRegion()
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
        rng = [Calculation.ev_to_px(row.get("Low Kev").text()) - 1,
               Calculation.ev_to_px(row.get("High Kev").text()) - 1]
        intensity = Calculation.calculate_intensity_in_range(rng, self._counts)

        row.get("Status").setText("Activated")
        row.get("Status").setForeground(QtCore.Qt.GlobalColor.green)
        row.get("Activate Widget").setText("Deactivate")
        row.get("Intensity").setText(str(intensity))

        element.setActivated(True)
        element.setLowKev(float(row.get("Low Kev").text()))
        element.setHighKev(float(row.get("High Kev").text()))
        element.setRange(rng)
        element.setIntensity(intensity)

        if element.isHidden() is False:
            self._hideAllLinesOfElement(element)
            self.peakPlot.removeItem(element.getRegion())
        self._showElement(element)

    def _deactivateElement(self, element, row):
        row.get("Status").setText("Deactivated")
        row.get("Status").setForeground(QtCore.Qt.GlobalColor.red)
        row.get("Activate Widget").setText("Activate")
        row.get("Intensity").setText("None")

        element.setActivated(False)

        if element.isHidden() is False:
            self._showAllLinesOfElement(element)
        else:
            self._showElement(element)

    def removeRow(self):
        rowIndex = self.form.currentRow()
        element = self.getElementById(self.form.getCurrentRowId())
        messageBox = MessegeBox.Dialog(
            QtWidgets.QMessageBox.Icon.Warning,
            "Warning!",
            f"{element.getAttribute('symbol')} - {element.getAttribute('radiation_type')} will be removed."
        )
        messageBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel)
        returnValue = messageBox.exec()
        if returnValue == QtWidgets.QMessageBox.StandardButton.Ok:
            self._remove(element, rowIndex)

    def _remove(self, element, index):
        self._hideAllLinesOfElement(element)
        self.form.removeRow(index)
        element.setHidden(True)
        element.setActivated(False)

    def visibility(self):
        id = self.form.getCurrentRowId()
        element = self.getElementById(id)
        if element.isHidden():
            if element.isActivated():
                self._showElement(element)
            else:
                self._showAllLinesOfElement(element)
        else:
            if element.isActivated():
                self._hideElement(element)
            else:
                self._hideAllLinesOfElement(element)

    def _hideElement(self, element):
        row = self.form.getRowById(element.getAttribute("element_id"))
        row.get("Hide Widget").setIcon(QtGui.QIcon(ICONS["Hide"]))
        if element.isActivated() is False:
            self.peakPlot.removeItem(element.getRegion())

        self._removeLineOfElement(element)
        element.setHidden(True)

    def _showElement(self, element):
        row = self.form.getRowById(element.getAttribute("element_id"))
        row.get("Hide Widget").setIcon(QtGui.QIcon(ICONS["Show"]))
        if element.isActivated() is False:
            self.peakPlot.addItem(element.getRegion())
        self._plotLineOfElement(element)
        element.setHidden(False)
        self._goToPx(element.getRange())

    def headerClicked(self, column):
        if column == 0:
            self._configureRemoveAll()
        elif column == 1:
            self._configureHideALL()

    def _configureRemoveAll(self):
        messageBox = MessegeBox.Dialog(
            QtWidgets.QMessageBox.Icon.Warning,
            "Warning!",
            "All records will be removed.\nNote that all of the activated elements will also be deactivated.\n"
            "Press OK if you want to continue."
        )
        messageBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel)
        returnValue = messageBox.exec()
        if returnValue == QtWidgets.QMessageBox.StandardButton.Ok:
            for element in self._addedElements:
                self._remove(element, 0)
                QtWidgets.QApplication.processEvents()

    def _configureHideALL(self):
        hidden = self._addedElements[0].isHidden()
        if hidden:
            for element in self._addedElements:
                self._showElement(element)
                QtWidgets.QApplication.processEvents()
        else:
            for element in self._addedElements:
                self._hideElement(element)
                QtWidgets.QApplication.processEvents()

    def selectRow(self, element):
        if element.getAttribute("element_id") in self.form.getRowIds():
            index = self.form.getRowIds().index(element.getAttribute("element_id"))
            self.form.selectRow(index)
        self._goToPx(element.getRange())

    def getElements(self):
        return self._elements

    def getCondition(self):
        return self._condition

    def closeEvent(self, a0):
        self.windowClosed.emit()
        self.peakPlot.clear()
        self.spectrumPlot.clear()
        self.form.clear()
        super().closeEvent(a0)
