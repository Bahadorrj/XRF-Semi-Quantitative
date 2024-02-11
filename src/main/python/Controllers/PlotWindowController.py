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
            action.triggered.connect(partial(self._openRelatedComponent, label))
        # form
        self._view.form.customContextMenuRequested.connect(self._view.showContextMenu)
        self._view.form.itemClicked.connect(self._view.itemClicked)
        self._view.form.itemChanged.connect(self._view.itemChanged)
        self._view.form.itemDoubleClicked.connect(self._view.openPeakSearchWindow)
        # color buttons
        for fileName, buttons in self._view.getColorButtonsMap().items():
            for button in buttons:
                button.sigColorChanged.connect(self._view.plot)

    def _openRelatedComponent(self, label):
        if label == "Open":
            fileDialog = self._view.openFileDialog()
            fileDialog.fileSelected.connect(self._view.createFile)
        elif label == "Conditions":
            self._view.openConditionsWindow()
        elif label == "Elements":
            self._view.openElementsWindow()
        elif label == "Peak Search":
            self._view.openPeakSearchWindow()
