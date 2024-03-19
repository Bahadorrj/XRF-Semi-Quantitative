import threading
from functools import partial

class PlotWindowController:
    def __init__(self, view):
        self._view = view
        self._connectSignalsAndSlots()

    def _connectSignalsAndSlots(self):
        # mouse
        self._view.getPlotWidget().scene().sigMouseMoved.connect(self._view.mouseMoved)
        # action
        for label, action in self._view.getActionsMap().items():
            action.triggered.connect(partial(self._connectActionsAndSlots, label))
        # form
        self._view.form.itemClicked.connect(self._view.itemClicked)
        self._view.form.itemChanged.connect(self._view.itemChanged)
        self._view.form.itemDoubleClicked.connect(self._view.openPeakSearchWindow)
        self._view.form.itemDeleted.connect(self._view.itemDeleted)

    def _connectActionsAndSlots(self, label):
        if label == "open-append":
            path = self._view.openFileDialog()
            if path:
                self._view.addProject(path)
        elif label == "open-as-new-project":
            path = self._view.openFileDialog()
            if path:
                threading.Thread(target=self._view.openNewProject(path)).start()
        elif label == "new":
            self._view.resetWindow()
        elif label == "save-as":
            self._view.exportProject()
        elif label == "conditions":
            self._view.openConditionsWindow()
        elif label == "elements":
            self._view.openElementsWindow()
        elif label == "peak-search":
            self._view.openPeakSearchWindow()
        elif label == "close":
            self._view.close()
