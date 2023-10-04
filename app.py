from backend import *
import sys


class Ui_conditionsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.df = SQLITE.read(Addr['dbFundamentals'], 'conditions')
        self.gridLayout = QtWidgets.QGridLayout(self)
        row = 0
        column = 0
        for i in self.df.index:
            self.formLayout = QtWidgets.QFormLayout()
            self.formLayout.setFieldGrowthPolicy(
                QtWidgets.QFormLayout.ExpandingFieldsGrow
            )
            self.conditionLabel = QtWidgets.QLabel(
                self.df.at[i, 'name']
            )
            self.formLayout.addWidget(self.conditionLabel)
            self.KvLabel = QtWidgets.QLabel('Kv')
            self.KvValue = QtWidgets.QLabel(str(self.df.at[i, 'Kv']))
            self.formLayout.addRow(self.KvLabel, self.KvValue)
            self.mALabel = QtWidgets.QLabel('mA')
            self.mAValue = QtWidgets.QLabel(str(self.df.at[i, 'mA']))
            self.formLayout.addRow(self.mALabel, self.mAValue)
            self.timeLabel = QtWidgets.QLabel('time')
            self.timeValue = QtWidgets.QLabel(str(self.df.at[i, 'time']))
            self.formLayout.addRow(self.timeLabel, self.timeValue)
            self.rotationLabel = QtWidgets.QLabel('rotation')
            self.rotationValue = QtWidgets.QLabel(
                str(self.df.at[i, 'rotation']))
            self.formLayout.addRow(self.rotationLabel, self.rotationValue)
            self.environmentLabel = QtWidgets.QLabel('enviroment')
            self.environmentValue = QtWidgets.QLabel(
                self.df.at[i, 'environment'])
            self.formLayout.addRow(self.environmentLabel,
                                   self.environmentValue)
            self.filterLabel = QtWidgets.QLabel('filter')
            self.filterValue = QtWidgets.QLabel(str(self.df.at[i, 'filter']))
            self.formLayout.addRow(self.filterLabel, self.filterValue)
            self.maskLabel = QtWidgets.QLabel('mask')
            self.maskValue = QtWidgets.QLabel(str(self.df.at[i, 'mask']))
            self.formLayout.addRow(self.maskLabel, self.maskValue)
            self.gridLayout.addLayout(self.formLayout, row, column)
            column += 1
            if column > 4:
                column = 0
                row += 1


class Ui_PeakSearchWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

    def setupUi(self, file, condition):
        # variables
        self.dfGeneralData = pd.read_excel(
            Addr['xlsxGeneralData'],
            'sheet1'
        )
        self.dfElements = SQLITE.read(Addr['dbFundamentals'], 'elements')
        self.file = file
        self.condition = condition
        self.intensity = TEXTREADER.listItems(
            file['path'],
            file['conditions'][condition],
            int
        )
        self.px = np.arange(0, len(self.intensity), 1)
        self.rowCount = 0
        # pens
        self.plotPen = mkPen('w', width=2)
        self.deactivePen = mkPen('r', width=2)
        self.activePen = mkPen('g', width=2)
        self.items = []

        # window config
        self.setMinimumSize(
            QtCore.QSize(
                int(size.width()*0.75), int(size.height()*0.75)
            )
        )
        self.setWindowTitle(
            f"{Path(file['path']).stem} - {condition}"
        )
        self.showMaximized()

        # layout
        self.mainLayout = QtWidgets.QVBoxLayout()

        # form
        self.form = QtWidgets.QTableWidget()
        self.form.setColumnCount(4)
        self.form.setHorizontalHeaderLabels(
            ['Element', 'Type', 'Intensity', 'Status']
        )
        self.form.setMaximumHeight(int(self.size().height()*0.3))
        self.form.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        self.form.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.form.setFrameShape(QtWidgets.QFrame.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Plain)

        # graphics
        self.graph = GraphicsLayoutWidget()
        self.peakPlot = self.graph.addPlot(row=0, col=0)
        self.spectrumPlot = self.graph.addPlot(row=1, col=0)
        self.region = LinearRegionItem()
        self.region.setZValue(10)
        self.region.sigRegionChanged.connect(self.update)
        # plot initialising
        self.spectrumPlot.showGrid(x=True, y=True)
        self.spectrumPlot.addItem(self.region, ignoreBounds=True)
        self.spectrumPlot.setLimits(xMin=0, xMax=max(self.px),
                                    yMin=0, yMax=1.1*max(self.intensity))
        self.spectrumPlot.plot(
            x=self.px, y=self.intensity, pen=self.plotPen
        )
        self.spectrumPlot.setMouseEnabled(y=False)
        self.spectrumPlot.scene().sigMouseMoved.connect(self.mouseMoved)
        self.peakPlot.setMinimumHeight(int(self.size().height()*0.4))
        self.peakPlot.showGrid(x=True, y=True)
        self.peakPlot.setLimits(xMin=0, xMax=max(self.px),
                                yMin=0, yMax=1.1*max(self.intensity))
        self.peakPlot.plot(
            x=self.px, y=self.intensity, pen=self.plotPen
        )
        self.peakPlot.setMouseEnabled(x=False)  # Only allow zoom in Y-axis
        self.peakPlot.sigRangeChanged.connect(self.updateRegion)
        self.peakPlot.scene().sigMouseClicked.connect(self.openPopUp)

        self.region.setClipItem(self.spectrumPlot)
        self.region.setRegion([0, 100])
        self.region.setBounds((0, max(self.px)))

        self.vLine = InfiniteLine(angle=90, movable=False)
        self.hLine = InfiniteLine(angle=0, movable=False)
        self.peakPlot.addItem(self.vLine, ignoreBounds=True)
        self.peakPlot.addItem(self.hLine, ignoreBounds=True)

        self.peakPlotVB = self.peakPlot.vb
        self.peakPlotVB.scaleBy(center=(0, 0))
        self.peakPlotVB.menu.clear()
        self.sepctrumPlotVB = self.spectrumPlot.vb

        self.cordinateLabel = QtWidgets.QLabel()

        self.mainLayout.addWidget(self.form)
        self.mainLayout.addWidget(self.graph)
        self.mainLayout.addWidget(self.cordinateLabel)

        self.mainWidget = QtWidgets.QWidget()
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

        self.writeToTable()

    def update(self):
        self.region.setZValue(10)
        minX, maxX = self.region.getRegion()
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

    def updateRegion(self, window, viewRange):
        rng = viewRange[0]
        self.region.setRegion(rng)

    def openPopUp(self, event):
        ev = CALCULATION.px_to_ev(int(self.mousePoint.x()))
        if event.button() == QtCore.Qt.RightButton:
            self.peakPlotVB.menu.clear()
            df = CALCULATION.findElementParam(ev, self.dfGeneralData)
            for type in ['Ka', 'Kb', 'La', 'Lb', 'Ma']:
                msk = df['Type'] == type
                if df['Sym'][msk].empty is False:
                    menu = self.peakPlotVB.menu.addMenu(type)
                    menu.triggered.connect(self.actionClicked)
                    for sym in df['Sym'][msk].tolist():
                        menu.addAction(sym)

    def findLines(self, index):
        lines = []
        for i in index:
            line = InfiniteLine()
            line.setAngle(90)
            line.setMovable(False)
            ev = self.dfGeneralData.at[i, 'Kev']
            px = CALCULATION.ev_to_px(ev)
            line.setValue(px)
            symLabel = InfLineLabel(
                line,
                self.dfGeneralData.at[i, 'Sym'],
                movable=False,
                position=0.9
            )
            type = self.dfGeneralData.at[i, 'Type']
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

    def setItem(self, sym, type, ev, intensity, active, specLines, peakLines):
        self.removeButton = QtWidgets.QPushButton(icon=QtGui.QIcon(icon_cross))
        self.removeButton.clicked.connect(self.remove)
        self.hideButton = QtWidgets.QPushButton(icon=QtGui.QIcon(icon_unhide))
        self.hideButton.clicked.connect(self.hide)
        self.elementItem = QtWidgets.QTableWidgetItem(sym)
        self.typeItem = QtWidgets.QTableWidgetItem(f"{type} - {ev}")
        self.intensityItem = QtWidgets.QTableWidgetItem(str(intensity))
        if active:
            self.statusItem = QtWidgets.QTableWidgetItem('Activated')
            self.statusButton = QtWidgets.QPushButton('Deactivate')
        else:
            self.statusItem = QtWidgets.QTableWidgetItem('Deactivated')
            self.statusButton = QtWidgets.QPushButton('Activate')
        self.statusButton.clicked.connect(self.statusChanged)

        if self.form.columnCount() == 4:
            self.form.setColumnCount(7)
            self.form.setHorizontalHeaderLabels(
                ['', '', 'Element', 'Type', 'Intensity', 'Status', '']
            )
            for i in [0, 1, 6]:
                self.form.horizontalHeader().setSectionResizeMode(
                    i, QtWidgets.QHeaderView.ResizeToContents
                )
            for i in [2, 3, 4, 5]:
                self.form.horizontalHeader().setSectionResizeMode(
                    i, QtWidgets.QHeaderView.Stretch
                )

        self.form.setRowCount(self.rowCount + 1)
        self.form.setCellWidget(self.rowCount, 0, self.removeButton)
        self.form.setCellWidget(self.rowCount, 1, self.hideButton)
        self.form.setItem(self.rowCount, 2, self.elementItem)
        self.form.setItem(self.rowCount, 3, self.typeItem)
        self.form.setItem(self.rowCount, 4, self.intensityItem)
        self.form.setItem(self.rowCount, 5, self.statusItem)
        self.form.setCellWidget(self.rowCount, 6, self.statusButton)
        self.rowCount += 1

        self.item = {
            'sym': sym,
            'type': type,
            'intensity': intensity,
            'specLines': specLines,
            'peakLines': peakLines,
            'active': active,
            'hide': False
        }
        self.items.append(self.item)

        self.plotItems()

    def initItem(self, sym, index):
        specLines = self.findLines(index)
        peakLines = self.findLines(index)
        intensity = 0
        for i in index:
            ev = self.dfGeneralData.at[i, 'Kev']
            type = self.dfGeneralData.at[i, 'Type']
            if (type == 'Ka' and ev < 30) or (type == 'La'):
                itemType = type
                itemEv = ev
                low = self.dfGeneralData.at[i, 'Low']
                high = self.dfGeneralData.at[i, 'High']
                if type == 'Ka':
                    break
        for px in range(CALCULATION.ev_to_px(low), CALCULATION.ev_to_px(high)):
            intensity += self.intensity[px]

        self.setItem(sym, itemType, itemEv, intensity,
                     False, specLines, peakLines)

    def actionClicked(self, action):
        sym = action.text()
        index = self.dfGeneralData[self.dfGeneralData['Sym'] == sym].index
        self.initItem(sym, index)

    def hide(self):
        row = self.form.currentRow()
        hideButton = self.form.cellWidget(row, 1)
        item = self.items[row]
        if item['hide']:
            hideButton.setIcon(QtGui.QIcon(icon_unhide))
            item['hide'] = False
        else:
            hideButton.setIcon(QtGui.QIcon(icon_hide))
            item['hide'] = True
        self.plotItems()

    def statusChanged(self):
        row = self.form.currentRow()
        statusItem = self.form.item(row, 5)
        statusButton = self.form.cellWidget(row, 6)
        item = self.items[row]
        if statusItem.text() == 'Deactivated':
            SQLITE.activeElement(self.condition, item)
            statusItem.setText('Activated')
            statusButton.setText('Deactivate')
            item['active'] = True
        else:
            SQLITE.deactiveElement(item['sym'])
            statusItem.setText('Deactivated')
            statusButton.setText('Activate')
            item['active'] = False
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

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self.remove()
        else:
            super().keyPressEvent(event)

    def writeToTable(self):
        if self.form.colorCount() == 4:
            self.form.setColumnCount(7)
            self.form.setHorizontalHeaderLabels(
                ['', '', 'Element', 'Type', 'Intensity', 'Status', ''])
            for i in [0, 1, 6]:
                self.form.horizontalHeader().setSectionResizeMode(
                    i, QtWidgets.QHeaderView.ResizeToContents
                )
            for i in [2, 3, 4, 5]:
                self.form.horizontalHeader().setSectionResizeMode(
                    i, QtWidgets.QHeaderView.Stretch
                )

        for i in self.dfElements.index:
            sym = self.dfElements.at[i, 'symbol']
            type = self.dfElements.at[i, 'radiation_type']
            ev = self.dfElements.at[i, 'Kev']
            intensity = self.dfElements.at[i, 'intensity']
            index = self.dfGeneralData[self.dfGeneralData['Sym']
                                       == sym].index
            specLines = self.findLines(index)
            peakLines = self.findLines(index)
            self.setItem(sym, type, ev, intensity, True, specLines, peakLines)


class Ui_PlotWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        # variables
        self.xLim = 0
        self.yLim = 0
        self.colorIndex = 0
        self.files = []  # a list containing dictionaries of opened files

        # window config
        self.windowSize = QtCore.QSize(
            int(size.width()*0.75), int(size.height()*0.75)
        )
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle('Graph')
        self.showMaximized()

        # toolbar
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(32, 32))
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        # actions
        self.actionOpen = QtWidgets.QAction(
            QtGui.QIcon(icon_open), 'Open')
        self.actionOpen.triggered.connect(lambda: self.openFilesDialog())
        # self.menuFiles.addAction(self.actionOpen)
        self.actionPeakSearch = QtWidgets.QAction(
            QtGui.QIcon(icon_toolbar_peak_search), 'Peak Search'
        )
        self.actionPeakSearch.setStatusTip('Find elements in spectrum')
        self.actionPeakSearch.setDisabled(True)
        self.actionPeakSearch.triggered.connect(lambda: self.openPeakSearch())
        self.actionConditions = QtWidgets.QAction(
            QtGui.QIcon(icon_conditions), 'Conditions'
        )
        self.actionConditions.triggered.connect(lambda: self.openConditions())

        # self.menubar.addAction(self.menuFiles.menuAction())
        self.toolbar.addAction(self.actionOpen)
        self.toolbar.addAction(self.actionPeakSearch)
        self.toolbar.addAction(self.actionConditions)

        # statubar
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)

        # main layout
        self.mainLayout = QtWidgets.QGridLayout()

        # curve plot widget
        self.curvePlot = PlotWidget()
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
        self.proxy = SignalProxy(self.curvePlot.scene(
        ).sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

        # files path
        self.form = QtWidgets.QTreeWidget()
        self.form.setFixedWidth(int(self.windowSize.width()*0.25))
        self.form.setColumnCount(3)
        self.form.setHeaderLabels(['File', 'Condition', 'Color'])
        self.form.setFrameShape(QtWidgets.QFrame.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Plain)
        self.form.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.form.customContextMenuRequested.connect(self.showContextMenu)
        self.form.itemChanged.connect(self.itemChanged)
        self.form.itemClicked.connect(self.itemClicked)
        self.form.itemDoubleClicked.connect(lambda: self.openPeakSearch())

        self.actionDelete = QtWidgets.QAction()
        self.actionDelete.setText('Delete')
        self.actionDelete.setIcon(QtGui.QIcon(icon_cross))
        self.actionDelete.triggered.connect(self.remove)
        self.actionDirectory = QtWidgets.QAction()
        self.actionDirectory.setText('Open file location')
        self.actionDirectory.triggered.connect(self.openDirectory)
        self.customMenu = QtWidgets.QMenu(self.form)
        self.customMenu.addAction(self.actionDelete)
        self.customMenu.addSeparator()
        self.customMenu.addAction(self.actionDirectory)

        # cordinate
        self.cordinateLabel = QtWidgets.QLabel()

        self.mainLayout.addWidget(self.curvePlot, 0, 0)
        self.mainLayout.addWidget(self.form, 0, 1)
        self.mainLayout.addWidget(self.cordinateLabel, 1, 0)

        self.mainWidget = QtWidgets.QWidget()
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

    def openDirectory(self):
        item = self.form.selectedItems()[0]
        path = self.files[self.form.indexOfTopLevelItem(item)]['path']
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
        self.files.pop(index)
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
        if self.fileDialog.exec_():
            self.initItem()

    def initItem(self):
        selected = self.fileDialog.selectedFiles()
        filePath = selected[0]

        fileItem = QtWidgets.QTreeWidgetItem()
        fileItem.setText(0, Path(filePath).stem)
        fileItem.setCheckState(0, QtCore.Qt.Unchecked)

        conditionsDictionary = TEXTREADER.conditionDictionary(filePath)
        buttons = []
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
            button.sigColorChanged.connect(self.colorChanged)
            buttons.append(button)
            self.form.setItemWidget(conditionItem, 2, button)

        file = {
            'path': filePath,
            'conditions': conditionsDictionary,
            'buttons': buttons
        }
        self.files.append(file)

    def colorChanged(self):
        childIndex = self.form.currentIndex()
        childRow = childIndex.row()
        itemIndex = childIndex.parent()
        itemRow = itemIndex.row()
        color = self.files[itemRow]['buttons'][childRow].color()
        self.plotFiles()

    def plotFiles(self):
        self.curvePlot.clear()
        for i in range(self.form.topLevelItemCount()):
            file = self.files[i]
            topLevel = self.form.topLevelItem(i)
            for j in range(topLevel.childCount()):
                child = topLevel.child(j)
                if self.state(child, 1):
                    condition = child.text(1)
                    intensity = TEXTREADER.listItems(
                        file['path'],
                        file['conditions'][condition],
                        int
                    )
                    px = np.arange(0, len(intensity), 1)
                    if max(intensity) > self.yLim:
                        self.yLim = max(intensity)
                    if len(intensity) > self.xLim:
                        self.xLim = len(intensity)
                    self.curvePlot.setLimits(xMin=0, xMax=self.xLim,
                                             yMin=0, yMax=1.1*self.yLim)
                    color = file['buttons'][j].color()
                    pen = mkPen(color, width=2)
                    self.curvePlot.plot(x=px, y=intensity, pen=pen)

    def openPeakSearch(self):
        try:
            item = self.form.currentItem()
            topLevel = item.parent()
            topLevelIndex = self.form.indexOfTopLevelItem(topLevel)
            self.peakSearchWindow = Ui_PeakSearchWindow()
            self.peakSearchWindow.setupUi(
                self.files[topLevelIndex], item.text(1))
            self.peakSearchWindow.show()
        except KeyError:
            pass

    def openConditions(self):
        self.conditionsWindow = Ui_conditionsWindow()
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
                    # self.currentItem = (i, j)
                    break

    def state(self, item, column):
        if item.checkState(column):
            return True
        else:
            return False

    def itemChanged(self, item):
        for topLevelIndex in range(self.form.topLevelItemCount()):
            topLevelItem = self.form.topLevelItem(topLevelIndex)
            if topLevelItem.isSelected():
                topLevelItem.setSelected(False)
            for childIndex in range(topLevelItem.childCount()):
                child = topLevelItem.child(childIndex)
                if child.isSelected():
                    child.setSelected(False)
        item.setSelected(True)
        self.form.setCurrentItem(item)
        self.form.blockSignals(True)
        topLevelIndex = self.form.indexOfTopLevelItem(item)
        if topLevelIndex != -1:  # if toplevel changed
            for i in range(item.childCount()):
                item.child(i).setCheckState(1, item.checkState(0))
        else:
            topLevel = item.parent()
            state = []
            for i in range(topLevel.childCount()):
                state.append(self.state(topLevel.child(i), 1))
            if all(state):
                topLevel.setCheckState(0, QtCore.Qt.Checked)
            else:
                topLevel.setCheckState(0, QtCore.Qt.Unchecked)
                for i in range(len(state)):
                    if state[i] is True:
                        topLevel.child(i).setCheckState(1, QtCore.Qt.Checked)
                    else:
                        topLevel.child(i).setCheckState(1, QtCore.Qt.Unchecked)
        self.form.blockSignals(False)
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
        if table == 'r':
            self.elementsTable.setItemDelegate(TEXTDELEGATE())
        else:
            self.elementsTable.setItemDelegate(FLOATDELEGATE)
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
        self.setupUi()

    def setupUi(self):
        # window config
        self.windowSize = QtCore.QSize(
            int(size.width()*0.75), int(size.height()*0.75)
        )
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle('XRF')
        self.showMaximized()

        # sub windows setup
        self.table_a = Ui_TableWindow()
        self.table_a.setupUi('a')
        self.table_b = Ui_TableWindow()
        self.table_b.setupUi('b')
        self.table_c = Ui_TableWindow()
        self.table_c.setupUi('c')
        self.table_r = Ui_TableWindow()
        self.table_r.setupUi('r')
        self.table_cp = Ui_TableWindow()
        self.table_cp.setupUi('cp')

        self.plotWindow = Ui_PlotWindow()

        # menubar
        self.menubar = QtWidgets.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 18))
        self.menuCalculate = QtWidgets.QMenu(self.menubar)
        self.menuCalculate.setTitle('Calculate')
        self.menuCoefficient = QtWidgets.QMenu(self.menubar)
        self.menuCoefficient.setTitle('Coefficient')
        self.menuCalibration = QtWidgets.QMenu(self.menubar)
        self.menuCalibration.setTitle('Calibration')
        self.menuIdentification = QtWidgets.QMenu(self.menubar)
        self.menuIdentification.setTitle('Identification')
        self.setMenuBar(self.menubar)

        # status bar
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)

        self.actionTable_a = QtWidgets.QAction("Table a")
        self.actionTable_a.triggered.connect(
            lambda: self.openTable(self.table_a)
        )
        self.actionTable_b = QtWidgets.QAction("Table b")
        self.actionTable_b.triggered.connect(
            lambda: self.openTable(self.table_b)
        )
        self.actionTable_c = QtWidgets.QAction("Table c")
        self.actionTable_c.triggered.connect(
            lambda: self.openTable(self.table_c)
        )
        self.actionRelations = QtWidgets.QAction("Relations")
        self.actionRelations.triggered.connect(
            lambda: self.openTable(self.table_r)
        )
        self.actionCP = QtWidgets.QAction("Calibration Parameters")
        self.actionCP.triggered.connect(
            lambda: self.openTable(self.table_cp,)
        )
        self.actionPlot = QtWidgets.QAction("Plot")
        self.actionPlot.triggered.connect(
            lambda: self.openPlotWindow()
        )

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
        tableWindow.show()

    def openPlotWindow(self):
        self.plotWindow.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()
    # app.setStyleSheet(tr.getString(r"F:\CSAN\XRF\Text Files\style.txt"))
    app.setWindowIcon(QtGui.QIcon(icon_CSAN))
    MainWindow = Ui_PlotWindow()
    MainWindow.show()
    sys.exit(app.exec())
