from backend import *
import sys


class myMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

    def closeEvent(self, event):
        self.closeMessageBox = QtWidgets.QMessageBox()
        self.closeMessageBox.setIcon(QtWidgets.QMessageBox.Warning)
        self.closeMessageBox.setText(
            "There are some unfinished changes in this window.\nAre you sure you want to quit?")
        self.closeMessageBox.setWindowTitle("Warning!")
        self.closeMessageBox.setStandardButtons(
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
        )
        ans = self.closeMessageBox.exec()
        if ans == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


class Ui_conditionsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.windowSize = QtCore.QSize(
            int(size.width()*0.5), int(size.height()*0.3)
        )
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.form = QtWidgets.QTableWidget()
        self.dfConditions = SQLITE.read(Addr['dbFundamentals'], 'conditions')

    def setupUi(self):
        # window config
        self.setFixedSize(self.windowSize)
        self.setWindowTitle('Conditions')

        self.form.setFrameShape(QtWidgets.QFrame.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Plain)
        self.form.setColumnCount(10)
        headers = ['ID', 'Name', 'Kv', 'mA', 'Time',
                   'Rotation', 'Enviroment', 'Filter', 'Mask', 'Active']
        self.form.setHorizontalHeaderLabels(headers)
        self.form.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.form.setRowCount(self.dfConditions.shape[0])
        self.form.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        self.mainLayout.addWidget(self.form)
        self.setLayout(self.mainLayout)

        for i in self.dfConditions.index:
            self.idItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, 'condition_id'])
            )
            self.idItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.nameItem = QtWidgets.QTableWidgetItem(
                self.dfConditions.at[i, 'name']
            )
            self.nameItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.KvItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, 'Kv'])
            )
            self.KvItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.mAItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, 'Kv'])
            )
            self.mAItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.timeItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, 'time'])
            )
            self.timeItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.rotationItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, 'rotation'])
            )
            self.rotationItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.environmentItem = QtWidgets.QTableWidgetItem(
                self.dfConditions.at[i, 'environment']
            )
            self.environmentItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.filterItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, 'filter'])
            )
            self.filterItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.maskItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, 'mask'])
            )
            self.maskItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.activeItem = QtWidgets.QTableWidgetItem(
                str(bool(self.dfConditions.at[i, 'active']))
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
    def __init__(self, path, rng, condition):
        super().__init__()
        self.windowSize = QtCore.QSize(
            int(size.width()*0.75), int(size.height()*0.75)
        )
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.form = QtWidgets.QTableWidget()
        self.graph = GraphicsLayoutWidget()
        self.peakPlot = self.graph.addPlot(row=0, col=0)
        self.spectrumPlot = self.graph.addPlot(row=1, col=0)
        self.peakRegion = LinearRegionItem()
        self.spectrumRegion = LinearRegionItem()
        self.vLine = InfiniteLine(angle=90, movable=False)
        self.hLine = InfiniteLine(angle=0, movable=False)
        self.peakPlotVB = self.peakPlot.vb
        self.sepctrumPlotVB = self.spectrumPlot.vb
        self.cordinateLabel = QtWidgets.QLabel()
        self.mainWidget = QtWidgets.QWidget()
        self.dfElements = SQLITE.read(Addr['dbFundamentals'], 'elements')
        self.path = path
        self.range = rng
        self.condition = condition
        self.intensityRange = TEXTREADER.listItems(
            self.path,
            self.range,
            int
        )
        self.px = np.arange(0, len(self.intensityRange), 1)
        self.rowCount = 0
        # pens
        self.plotPen = mkPen('w', width=2)
        self.deactivePen = mkPen('r', width=2)
        self.activePen = mkPen('g', width=2)
        self.items = []

    def setupUi(self):
        # window config
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle(
            f"{Path(self.path).stem} - {self.condition}"
        )
        self.showMaximized()

        # form config
        self.form.setMaximumHeight(int(self.size().height()*0.3))
        self.form.setFrameShape(QtWidgets.QFrame.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Plain)
        self.form.setColumnCount(7)
        self.form.itemChanged.connect(self.itemChanged)
        self.setupForm()

        # graphics config
        self.peakRegion.setZValue(10)
        self.spectrumRegion.setZValue(10)
        self.spectrumRegion.sigRegionChanged.connect(self.scalePeakPlot)
        self.spectrumPlot.showGrid(x=True, y=True)
        self.spectrumPlot.addItem(self.spectrumRegion, ignoreBounds=True)
        self.spectrumPlot.setLimits(xMin=0, xMax=max(self.px),
                                    yMin=0, yMax=1.1*max(self.intensityRange))
        self.spectrumPlot.plot(
            x=self.px, y=self.intensityRange, pen=self.plotPen
        )
        self.spectrumPlot.setMouseEnabled(x=False, y=False)
        self.spectrumPlot.scene().sigMouseMoved.connect(self.mouseMoved)
        self.peakPlot.setMinimumHeight(int(self.size().height()*0.4))
        self.peakPlot.showGrid(x=True, y=True)
        self.peakPlot.setLimits(xMin=0, xMax=max(self.px),
                                yMin=0, yMax=1.1*max(self.intensityRange))
        self.peakPlot.plot(
            x=self.px, y=self.intensityRange, pen=self.plotPen
        )
        self.peakPlot.setMouseEnabled(x=False)  # Only allow zoom in Y-axis
        self.peakPlot.sigRangeChanged.connect(self.updateSpecRegion)
        self.peakPlot.scene().sigMouseClicked.connect(self.openPopUp)
        self.spectrumRegion.setClipItem(self.spectrumPlot)
        self.spectrumRegion.setRegion([0, 100])
        self.spectrumRegion.setBounds((0, max(self.px)))
        self.peakPlot.addItem(self.vLine, ignoreBounds=True)
        self.peakPlot.addItem(self.hLine, ignoreBounds=True)
        self.peakPlotVB.scaleBy(center=(0, 0))
        self.peakPlotVB.menu.clear()
        self.mainLayout.addWidget(self.form)
        self.mainLayout.addWidget(self.graph)
        self.mainLayout.addWidget(self.cordinateLabel)

        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

        self.writeToTable()

    def itemChanged(self, item):
        if item.column() == 5 or item.column() == 6:
            low = float(self.lowItem.text())
            high = float(self.highItem.text())
            self.peakRegion.setRegion(
                [CALCULATION.ev_to_px(low),
                 CALCULATION.ev_to_px(high)]
            )
            self.recentItem['low'] = low
            self.recentItem['high'] = high

    def scalePeakPlot(self):
        self.spectrumRegion.setZValue(10)
        minX, maxX = self.spectrumRegion.getRegion()
        self.peakPlot.setXRange(minX, maxX, padding=0)

    def mouseMoved(self, event):
        pos = event
        if self.peakPlot.sceneBoundingRect().contains(pos):
            self.mousePoint = self.peakPlotVB.mapSceneToView(pos)
            self.cordinateLabel.setText(
                """<span style='font-size: 2rem'>
                        x=%0.1f,y=%0.1f,kEV= %0.2f
                    </span>""" % (
                    int(self.mousePoint.x()),
                    int(self.mousePoint.y()),
                    CALCULATION.px_to_ev(int(self.mousePoint.x()))
                )
            )
            self.vLine.setPos(self.mousePoint.x())
            self.hLine.setPos(self.mousePoint.y())

    def updateSpecRegion(self, window, viewRange):
        rng = viewRange[0]
        self.spectrumRegion.setRegion(rng)

    def changeRange(self):
        low, high = self.peakRegion.getRegion()
        lowKev = round(CALCULATION.px_to_ev(low), 4)
        highKev = round(CALCULATION.px_to_ev(high), 4)
        self.lowItem.setText(str(lowKev))
        self.highItem.setText(str(highKev))

    def openPopUp(self, event):
        ev = CALCULATION.px_to_ev(int(self.mousePoint.x()))
        if event.button() == QtCore.Qt.RightButton:
            self.peakPlotVB.menu.clear()
            df = CALCULATION.findElementParam(ev, self.dfElements)
            for type in ['Ka', 'Kb', 'La', 'Lb', 'Ma']:
                msk = df['radiation_type'] == type
                if df['symbol'][msk].empty is False:
                    menu = self.peakPlotVB.menu.addMenu(type)
                    menu.triggered.connect(self.actionClicked)
                    for sym in df['symbol'][msk].tolist():
                        menu.addAction(sym)

    def setupForm(self):
        self.form.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        if self.form.columnCount() == 10:
            headers = ['', '', 'Element', 'Type', 'Kev', 'Low Kev',
                       'High Kev', 'Intensity', 'Status', '']
            self.form.setHorizontalHeaderLabels(headers)
            for i, header in enumerate(headers):
                if (header == ''):
                    self.form.horizontalHeader().setSectionResizeMode(
                        i, QtWidgets.QHeaderView.ResizeToContents
                    )
                else:
                    self.form.horizontalHeader().setSectionResizeMode(
                        i, QtWidgets.QHeaderView.Stretch
                    )
        else:
            self.form.setColumnCount(7)
            self.form.setHorizontalHeaderLabels(
                ['Element', 'Type', 'Kev', 'Low Kev',
                    'High Kev', 'Intensity', 'Status']
            )
            self.form.horizontalHeader().setSectionResizeMode(
                QtWidgets.QHeaderView.Stretch
            )

    def initItem(self, sym, index):
        self.form.setColumnCount(10)
        self.setupForm()
        specLines = self.findLines(index)
        peakLines = self.findLines(index)
        intensity = 0
        for i in index:
            Kev = self.dfElements.at[i, 'Kev']
            type = self.dfElements.at[i, 'radiation_type']
            if (type == 'Ka' and Kev < 30) or (type == 'La'):
                itemType = type
                itemEv = Kev
                low = self.dfElements.at[i, 'low_Kev']
                high = self.dfElements.at[i, 'high_Kev']
                if type == 'Ka':
                    break
        for px in range(CALCULATION.ev_to_px(low), CALCULATION.ev_to_px(high)):
            intensity += self.intensityRange[px]
        self.peakPlot.removeItem(self.peakRegion)
        self.peakPlot.addItem(self.peakRegion, ignoreBounds=True)
        self.peakRegion.setRegion(
            [CALCULATION.ev_to_px(low), CALCULATION.ev_to_px(high)])
        self.peakRegion.sigRegionChanged.connect(self.changeRange)
        self.recentItem = {
            'sym': sym,
            'type': type,
            'Kev': itemEv,
            'low': low,
            'high': high,
            'intensity': intensity,
            'specLines': specLines,
            'peakLines': peakLines,
            'active': False,
            'hide': False
        }
        self.items.append(self.recentItem)
        self.setItem(self.recentItem)

    def setItem(self, item):
        self.removeButton = QtWidgets.QPushButton(
            icon=QtGui.QIcon(icon['cross']))
        self.removeButton.clicked.connect(self.remove)
        self.hideButton = QtWidgets.QPushButton(
            icon=QtGui.QIcon(icon['unhide']))
        self.hideButton.clicked.connect(self.hide)
        self.elementItem = QtWidgets.QTableWidgetItem(item['sym'])
        self.typeItem = QtWidgets.QTableWidgetItem(item['type'])
        self.KevItem = QtWidgets.QTableWidgetItem(str(item['Kev']))
        self.lowItem = QtWidgets.QTableWidgetItem(str(item['low']))
        self.highItem = QtWidgets.QTableWidgetItem(str(item['high']))
        self.intensityItem = QtWidgets.QTableWidgetItem(str(item['intensity']))
        if item['active']:
            self.statusItem = QtWidgets.QTableWidgetItem('Activated')
            self.statusButton = QtWidgets.QPushButton('Deactivate')
        else:
            self.statusItem = QtWidgets.QTableWidgetItem('Deactivated')
            self.statusButton = QtWidgets.QPushButton('Activate')
        self.statusButton.clicked.connect(self.statusChanged)

        self.form.setRowCount(self.rowCount + 1)
        self.form.setCellWidget(self.rowCount, 0, self.removeButton)
        self.form.setCellWidget(self.rowCount, 1, self.hideButton)
        self.form.setItem(self.rowCount, 2, self.elementItem)
        self.form.setItem(self.rowCount, 3, self.typeItem)
        self.form.setItem(self.rowCount, 4, self.KevItem)
        self.form.setItem(self.rowCount, 5, self.lowItem)
        self.form.setItem(self.rowCount, 6, self.highItem)
        self.form.setItem(self.rowCount, 7, self.intensityItem)
        self.form.setItem(self.rowCount, 8, self.statusItem)
        self.form.setCellWidget(self.rowCount, 9, self.statusButton)
        self.rowCount += 1

        self.plotItems()

    def findLines(self, index):
        lines = []
        for i in index:
            line = InfiniteLine()
            line.setAngle(90)
            line.setMovable(False)
            ev = self.dfElements.at[i, 'Kev']
            px = CALCULATION.ev_to_px(ev)
            line.setValue(px)
            symLabel = InfLineLabel(
                line,
                self.dfElements.at[i, 'symbol'],
                movable=False,
                position=0.9
            )
            type = self.dfElements.at[i, 'radiation_type']
            typeLabel = InfLineLabel(
                line,
                type,
                movable=False,
                position=0.8
            )
            self.spectrumPlot.addItem(line)
            lines.append(line)
        return lines

    def plotItems(self):
        for item in self.items:
            for line in item['specLines']:
                self.spectrumPlot.removeItem(line)
                if item['hide'] is False:
                    if item['active']:
                        line.setPen(self.activePen)
                        self.spectrumPlot.addItem(line)
                    elif item['active'] is False:
                        line.setPen(self.deactivePen)
                        self.spectrumPlot.addItem(line)
            for line in item['peakLines']:
                self.peakPlot.removeItem(line)
                if item['hide'] is False:
                    if item['active']:
                        line.setPen(self.activePen)
                        self.peakPlot.addItem(line)
                    elif item['active'] is False:
                        line.setPen(self.deactivePen)
                        self.peakPlot.addItem(line)

    def actionClicked(self, action):
        sym = action.text()
        index = self.dfElements[self.dfElements['symbol'] == sym].index
        self.initItem(sym, index)

    def statusChanged(self):
        row = self.form.currentRow()
        statusItem = self.form.item(row, 8)
        statusButton = self.form.cellWidget(row, 9)
        item = self.items[row]
        if statusItem.text() == 'Deactivated':
            SQLITE.activeElement(self.condition, item)
            statusItem.setText('Activated')
            statusButton.setText('Deactivate')
            item['active'] = True
        else:
            SQLITE.deactiveElement(item)
            statusItem.setText('Deactivated')
            statusButton.setText('Activate')
            item['active'] = False
        self.plotItems()

    def hide(self):
        row = self.form.currentRow()
        hideButton = self.form.cellWidget(row, 1)
        item = self.items[row]
        if item['hide']:
            hideButton.setIcon(QtGui.QIcon(icon['unhide']))
            item['hide'] = False
        else:
            hideButton.setIcon(QtGui.QIcon(icon['hide']))
            item['hide'] = True
        self.plotItems()

    def remove(self):
        row = self.form.currentRow()
        item = self.items[row]
        self.deleteMessageBox = QtWidgets.QMessageBox()
        self.deleteMessageBox.setIcon(QtWidgets.QMessageBox.Warning)
        self.deleteMessageBox.setText(
            f"{item['sym']} will be removed. Press ok to continue")
        self.deleteMessageBox.setWindowTitle("Warning!")
        self.deleteMessageBox.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        )
        returnValue = self.deleteMessageBox.exec()
        if returnValue == QtWidgets.QMessageBox.Ok:
            self.form.removeRow(row)
            SQLITE.deactiveElement(item['sym'])
            for line in self.items[row]['specLines']:
                self.spectrumPlot.removeItem(line)
            for line in self.items[row]['peakLines']:
                self.peakPlot.removeItem(line)
            self.items.pop(row)
            self.rowCount -= 1
            if self.rowCount == 0:
                self.form.setColumnCount(7)
                self.setupForm()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self.remove()
        else:
            super().keyPressEvent(event)

    def writeToTable(self):
        if not (self.dfElements[self.dfElements['active'] == 1].empty):
            self.form.setColumnCount(10)
            self.setupForm()
            for i in self.dfElements[self.dfElements['active'] == 1].index:
                sym = self.dfElements.at[i, 'symbol']
                type = self.dfElements.at[i, 'radiation_type']
                Kev = self.dfElements.at[i, 'Kev']
                low = self.dfElements.at[i, 'low_Kev']
                high = self.dfElements.at[i, 'high_Kev']
                intensity = self.dfElements.at[i, 'intensity']
                index = self.dfElements[self.dfElements['symbol']
                                        == sym].index
                specLines = self.findLines(index)
                peakLines = self.findLines(index)
                self.recentItem = {
                    'sym': sym,
                    'type': type,
                    'Kev': Kev,
                    'low': low,
                    'high': high,
                    'intensity': intensity,
                    'specLines': specLines,
                    'peakLines': peakLines,
                    'active': True,
                    'hide': False
                }
                self.items.append(self.recentItem)
                self.setItem(self.recentItem)


class Ui_PlotWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.windowSize = QtCore.QSize(
            int(size.width()*0.75),
            int(size.height()*0.75)
        )
        self.toolbar = QtWidgets.QToolBar()
        self.statusbar = QtWidgets.QStatusBar()
        self.actionOpen = QtWidgets.QAction()
        self.actionPeakSearch = QtWidgets.QAction()
        self.actionConditions = QtWidgets.QAction()
        self.mainLayout = QtWidgets.QGridLayout()
        self.mainWidget = QtWidgets.QWidget()
        self.curvePlot = PlotWidget()
        self.form = QtWidgets.QTreeWidget()
        self.customMenu = QtWidgets.QMenu(self.form)
        self.actionDelete = QtWidgets.QAction()
        self.actionDirectory = QtWidgets.QAction()
        self.cordinateLabel = QtWidgets.QLabel()
        self.proxy = SignalProxy(self.curvePlot.scene(
        ).sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.xLim = 0
        self.yLim = 0
        self.colorIndex = 0
        self.addedFiles = {}

    def setupUi(self):
        # window config
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle("Graph")
        self.showMaximized()

        # actions config
        self.actionOpen.setIcon(QtGui.QIcon(icon['open']))
        self.actionOpen.setText("Open")
        self.actionOpen.triggered.connect(lambda: self.openFilesDialog())
        self.actionPeakSearch.setIcon(QtGui.QIcon(icon['peak_search']))
        self.actionPeakSearch.setText("Peak Search")
        self.actionPeakSearch.setStatusTip('Find elements in spectrum')
        self.actionPeakSearch.setDisabled(True)
        self.actionPeakSearch.triggered.connect(lambda: self.openPeakSearch())
        self.actionConditions.setIcon(QtGui.QIcon(icon['conditions']))
        self.actionConditions.setText("Conditions")
        self.actionConditions.triggered.connect(lambda: self.openConditions())
        self.actionDelete.setText('Delete')
        self.actionDelete.setIcon(QtGui.QIcon(icon['cross']))
        self.actionDelete.triggered.connect(self.remove)
        self.actionDirectory.setText('Open file location')
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
        self.addToolBar(self.toolbar)

        # statubar config
        self.setStatusBar(self.statusbar)

        # curve plot config
        self.curvePlot.setFrameShape(QtWidgets.QFrame.Box)
        self.curvePlot.setFrameShadow(QtWidgets.QFrame.Plain)
        self.curvePlot.setBackground('#fff')
        self.curvePlot.setLabel('bottom',
                                '''<span style=\"font-size:1.5rem\">
                                    px</span>
                                ''')
        self.curvePlot.setLabel('left',
                                '''<span style=\"font-size:1.5rem\">
                                    Intensity</span>
                                ''')
        self.curvePlot.showGrid(x=True, y=True)

        # form config
        self.form.setFixedWidth(int(self.windowSize.width()*0.25))
        self.form.setColumnCount(3)
        self.form.setHeaderLabels(['File', 'Condition', 'Color'])
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
        item = self.form.selectedItems()[0]
        path = self.addedFiles[self.form.indexOfTopLevelItem(item)]['path']
        while True:
            path = path[:-1]
            if path[-1] == '/':
                break
        print(path)
        os.startfile(path)

    def remove(self):
        item = self.form.selectedItems()[0]
        index = self.form.indexOfTopLevelItem(item)
        self.form.takeTopLevelItem(index)
        self.addedFiles.pop(index)
        self.plotFiles()

    def showContextMenu(self, position):
        item = self.form.itemAt(position)
        if self.form.indexOfTopLevelItem(item) >= 0:
            self.customMenu.exec_(self.form.mapToGlobal(position))

    def openFilesDialog(self):
        self.fileDialog = QtWidgets.QFileDialog()
        self.fileDialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        self.fileDialog.setNameFilter("Texts (*.txt)")
        self.fileDialog.show()
        self.fileDialog.fileSelected.connect(self.initItem)

    def initItem(self, file):
        fileItem = QtWidgets.QTreeWidgetItem()
        fileName = Path(file).stem
        fileItem.setText(0, fileName)
        fileItem.setCheckState(0, QtCore.Qt.Unchecked)

        conditionsDictionary = TEXTREADER.conditionDictionary(file)
        colorButtons = list()
        for condition in list(conditionsDictionary.keys()):
            conditionItem = QtWidgets.QTreeWidgetItem()
            conditionItem.setText(1, condition)
            conditionItem.setCheckState(1, QtCore.Qt.Unchecked)

            fileItem.addChild(conditionItem)
            self.form.addTopLevelItem(fileItem)

            button = ColorButton()
            color = hsvColor(self.colorIndex)
            self.colorIndex += 0.05
            if self.colorIndex > 1:
                self.colorIndex = 0
            button.setColor(color)
            button.sigColorChanged.connect(self.plotFiles)
            colorButtons.append(button)
            self.form.setItemWidget(conditionItem, 2, button)

        properties = {
            'path': file,
            'conditions': conditionsDictionary,
            'colorButtons': colorButtons
        }
        self.addedFiles[fileName] = properties

    def plotFiles(self):
        self.curvePlot.clear()
        for properties in self.addedFiles.values():
            for index, condition in enumerate(properties['conditions'].values()):
                if condition['active']:
                    intensity = TEXTREADER.listItems(
                        properties['path'],
                        condition['range'],
                        int
                    )
                    px = np.arange(0, len(intensity), 1)
                    if max(intensity) > self.yLim:
                        self.yLim = max(intensity)
                    if len(intensity) > self.xLim:
                        self.xLim = len(intensity)
                    self.curvePlot.setLimits(xMin=0, xMax=self.xLim,
                                             yMin=0, yMax=1.1*self.yLim)
                    color = properties['colorButtons'][index].color()
                    pen = mkPen(color, width=2)
                    self.curvePlot.plot(x=px, y=intensity, pen=pen)

    def openPeakSearch(self, item):
        if self.form.indexOfTopLevelItem(item) == -1:
            itemText = item.text(1)
            topLevelText = item.parent().text(0)
            self.peakSearchWindow = Ui_PeakSearchWindow(
                self.addedFiles[topLevelText]['path'],
                self.addedFiles[topLevelText]['conditions'][itemText]['range'],
                itemText
            )
            self.peakSearchWindow.setupUi()
            self.peakSearchWindow.show()

    def openConditions(self):
        self.conditionsWindow = Ui_conditionsWindow()
        self.conditionsWindow.setupUi()
        self.conditionsWindow.show()

    def itemClicked(self, item):
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
        topLevelIndex = self.form.indexOfTopLevelItem(item)
        if topLevelIndex != -1:
            if item.checkState(0) != 0:
                for state in self.addedFiles[item.text(0)]['conditions'].values():
                    state['active'] = True
            else:
                for state in self.addedFiles[item.text(0)]['conditions'].values():
                    state['active'] = False
        else:
            topLevel = item.parent()
            if item.checkState(1) != 0:
                self.addedFiles[topLevel.text(
                    0)]['conditions'][item.text(1)]['active'] = True
            else:
                self.addedFiles[topLevel.text(
                    0)]['conditions'][item.text(1)]['active'] = False
            flag = False
            for i in range(topLevel.childCount()):
                if topLevel.child(i).checkState(1) == 0:
                    topLevel.setCheckState(0, QtCore.Qt.Unchecked)
                    flag = True
                    break
            if not flag:
                topLevel.setCheckState(0, QtCore.Qt.Checked)

        self.plotFiles()

    def mouseMoved(self, e):
        pos = e[0]
        if self.curvePlot.sceneBoundingRect().contains(pos):
            mousePoint = self.curvePlot.getPlotItem().vb.mapSceneToView(pos)
            self.cordinateLabel.setText(
                "<span style='font-size: 2rem'>x=%0.1f,y=%0.1f</span>" % (
                    mousePoint.x(), mousePoint.y()
                )
            )


# Table window must be refined later!!!
class Ui_TableWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

    def setupUi(self, table):
        # variables
        self.df = SQLITE.read(Addr['dbTables'], table)
        elementsRng = 93
        self.tables = {'a': {'name': 'Table a',
                             'columnCount': elementsRng,
                             'rowCount': elementsRng},
                       'b': {'name': 'Table b',
                             'columnCount': elementsRng,
                             'rowCount': elementsRng},
                       'c': {'name': 'Table c',
                             'columnCount': elementsRng,
                             'rowCount': elementsRng},
                       'r': {'name': 'Relations',
                             'columnCount': elementsRng,
                             'rowCount': elementsRng},
                       'cp': {'name': 'CalibrationParameters',
                              'columnCount': elementsRng,
                              'rowCount': 2}
                       }

        # window config
        self.windowSize = QtCore.QSize(
            int(size.width()*0.5), int(size.height()*0.5)
        )
        self.setMinimumSize(self.windowSize)
        if table in ['a', 'b', 'c']:
            self.setWindowTitle(f"Table {table}")
        elif table == 'cp':
            self.setWindowTitle('Calibration Parameters')

        # layout
        self.tableLayout = QtWidgets.QVBoxLayout()

        # table config
        self.elementsTable = QtWidgets.QTableWidget()
        self.elementsTable.setTabletTracking(True)
        self.elementsTable.setColumnCount(93)
        self.elementsTable.setHorizontalHeaderLabels(self.df.columns)
        # Calibration Parameters only has 2 rows
        if table == 'cp':
            self.elementsTable.setRowCount(2)
            self.elementsTable.setVerticalHeaderLabels(['A0', 'A1'])
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
            lambda: self.saveToDatabase(table)
        )

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
                        row,
                        column,
                        QtWidgets.QTableWidgetItem(str(value))
                    )

    # a func for saving table contents into a database
    def saveToDatabase(self, table):
        row = self.elementsTable.currentRow()
        column = self.elementsTable.currentColumn()
        tableItem = self.elementsTable.item(row, column)
        value = tableItem.text()
        if table == 'r':
            self.df.iat[row, column] = value
        else:
            self.df.iat[row, column] = float(value)

        SQLITE.write(
            Addr['dbTables'],
            self.tables[table]['name'],
            self.df
        )


class Ui_MainWindow(QtWidgets.QMainWindow):
    # inherit
    def __init__(self):
        super().__init__()
        self.windowSize = QtCore.QSize(
            int(size.width()*0.75),
            int(size.height()*0.75)
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
        self.setWindowTitle('XRF')
        self.showMaximized()

        # sub windows config
        self.table_a.setupUi('a')
        self.table_b.setupUi('b')
        self.table_c.setupUi('c')
        # self.table_r.setupUi('r')
        self.table_cp.setupUi('cp')

        # status bar config
        self.setStatusBar(self.statusbar)

        # actions config
        self.actionTable_a.setText("Table a")
        self.actionTable_a.triggered.connect(
            lambda: self.openTable(self.table_a)
        )
        self.actionTable_b.setText("Table b")
        self.actionTable_b.triggered.connect(
            lambda: self.openTable(self.table_b)
        )
        self.actionTable_c.setText("Table c")
        self.actionTable_c.triggered.connect(
            lambda: self.openTable(self.table_c)
        )
        # self.actionRelations.triggered.connect(
        #     lambda: self.openTable(self.table_r)
        # )
        self.actionCP.setText("Calibration Parameters")
        self.actionCP.triggered.connect(
            lambda: self.openTable(self.table_cp,)
        )
        self.actionPlot.setText("Plot")
        self.actionPlot.triggered.connect(
            lambda: self.openPlotWindow()
        )

        # menubar config
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 18))
        self.menuCalculate.setTitle('Calculate')
        self.menuCoefficient.setTitle('Coefficient')
        self.menuCalibration.setTitle('Calibration')
        self.menuIdentification.setTitle('Identification')
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
    # app.setStyleSheet(tr.getString(r"F:\CSAN\XRF\Text Files\style.txt"))
    app.setWindowIcon(QtGui.QIcon(icon['CSAN']))
    MainWindow = Ui_PlotWindow()
    MainWindow.setupUi()
    MainWindow.show()
    sys.exit(app.exec())
