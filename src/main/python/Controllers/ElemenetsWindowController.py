class ElementsWindowController:
    def __init__(self, view):
        self._view = view
        self.connectSignalsAndSlots()

    def connectSignalsAndSlots(self):
        self._view.getFilter().currentIndexChanged.connect(self._view.filterTable)
