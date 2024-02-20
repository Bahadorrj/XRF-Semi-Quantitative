import time
from functools import partial
from PyQt6.QtCore import QObject, pyqtSignal, QThread


class Worker(QObject):
    started = pyqtSignal()
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def run(self, size):
        for i in range(size):
            time.sleep(0.05)
            self.progress.emit(i)


class PeakSearchWindowController:
    def __init__(self, view, model):
        self._view = view
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self._model = model
        self._connectSignalsAndSlots()

    def _connectSignalsAndSlots(self):
        # form
        self._view.form.itemClicked.connect(self._view.itemClicked)
        self._view.form.horizontalHeader().sectionClicked.connect(self._view.headerClicked)
        # graphics
        self._view.peakPlot.scene().sigMouseClicked.connect(self._view.openPopUp)
        self._view.peakPlot.sigRangeChanged.connect(
            self._view.updateSpectrumRegion)
        self._view.spectrumRegion.sigRegionChanged.connect(
            self._view.scalePeakPlot)
        self._view.spectrumPlot.scene().sigMouseMoved.connect(self._view.mouseMoved)
        # self defined signals
        self._view.rowAdded.connect(
            partial(self._connectButtonsSignalsAnsSlots))
        self._view.elementAdded.connect(
            partial(self._connectRegionSignalAndSlot))
        self._view.windowOpened.connect(lambda: self.thread.start())
        self._view.windowOpened.connect(self._view.configureWindow)
        self._view.windowClosed.connect(lambda: self.thread.quit())
        self._view.windowClosed.connect(
            lambda:
            self._model.writeElementToTable(
                self._view.getElements(),
                self._view.getCondition()
            )
        )
        self._view.windowOpened.connect(self._view.configureWindow)
        # self._view.hideAll.connect(partial(self.worker.run, self._view.getNumberOfAddedElements()))
        self._view.showAll.connect(
            partial(self.worker.run, self._view.getNumberOfAddedElements()))
        # thread
        self.worker.progress.connect(self._view.showElement)

    def _connectButtonsSignalsAnsSlots(self, buttons):
        buttons[0].clicked.connect(self._view.removeRow)
        buttons[1].clicked.connect(self._view.visibility)
        buttons[2].clicked.connect(self._view.statusChanged)

    def _connectRegionSignalAndSlot(self, element):
        element.region.sigRegionChanged.connect(
            partial(self._view.setRange, element))
        element.spectrumLine.sigClicked.connect(
            partial(self._view.selectRow, element))
        element.peakLine.sigClicked.connect(
            partial(self._view.selectRow, element))

    def _checkVisibility(self, hide):
        self._hide = hide

    def _connectThreadAndSlots(self, index):
        if self._hide:
            self._view.showElement(index)
        else:
            self._view.hideElement(index)
