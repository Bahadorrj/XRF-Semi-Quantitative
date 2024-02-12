from functools import partial


class PeakSearchWindowController:
    def __init__(self, view, model):
        self._view = view
        self._model = model
        self._connectSignalsAndSlots()

    def _connectSignalsAndSlots(self):
        # form
        self._view.form.itemClicked.connect(self._view.itemClicked)
        self._view.form.horizontalHeader().sectionClicked.connect(self._view.headerClicked)
        # graphics
        self._view.peakPlot.scene().sigMouseClicked.connect(self._view.openPopUp)
        self._view.peakPlot.sigRangeChanged.connect(self._view.updateSpectrumRegion)
        self._view.spectrumRegion.sigRegionChanged.connect(self._view.scalePeakPlot)
        self._view.spectrumPlot.scene().sigMouseMoved.connect(self._view.mouseMoved)
        # self defined signals
        self._view.rowAdded.connect(partial(self._connectButtonsSignalsAnsSlots))
        self._view.elementAdded.connect(partial(self._connectRegionSignalAndSlot))
        self._view.windowClosed.connect(
            lambda:
            self._model.writeElementToTable(
                self._view.getElements(),
                self._view.getCondition()
            )
        )
        self._view.windowOpened.connect(self._view.configureWindow)

    def _connectButtonsSignalsAnsSlots(self, buttons):
        buttons[0].clicked.connect(self._view.removeRow)
        buttons[1].clicked.connect(self._view.visibility)
        buttons[2].clicked.connect(self._view.statusChanged)

    def _connectRegionSignalAndSlot(self, element):
        element.region.sigRegionChanged.connect(partial(self._view.setRange, element))
        element.spectrumLine.sigClicked.connect(partial(self._view.selectRow, element))
        element.peakLine.sigClicked.connect(partial(self._view.selectRow, element))
