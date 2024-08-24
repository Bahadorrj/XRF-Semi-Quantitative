from PyQt6 import QtWidgets


class GeneralDataWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._setUpView()

    def _setUpView(self) -> None:
        self._mainLayout = QtWidgets.QVBoxLayout()
        self._rows = (
            (
                QtWidgets.QLabel("Sample Name:"),
                QtWidgets.QLabel("Fe"),
                QtWidgets.QLabel("Amount:"),
                QtWidgets.QLabel("78.00%"),
                QtWidgets.QLabel("Chemistry:"),
                QtWidgets.QComboBox(),
                QtWidgets.QLabel("Kappa List:"),
                QtWidgets.QComboBox(),
            ),
            (
                QtWidgets.QLabel("Area: [mm^2]"),
                QtWidgets.QLineEdit("653.00"),
                QtWidgets.QLabel("Diameter: [mm]"),
                QtWidgets.QLineEdit("25.00"),
                QtWidgets.QLabel("Height: [mm]"),
                QtWidgets.QLineEdit("13.00"),
                QtWidgets.QLabel("Mass: [mg]"),
                QtWidgets.QLineEdit("180.25"),
                QtWidgets.QLabel("Rho: [g/cm^3]"),
                QtWidgets.QLineEdit("1.00"),
            ),
        )
        for row in self._rows:
            layout = QtWidgets.QHBoxLayout()
            for index, widget in enumerate(row):
                layout.addWidget(widget)
                if index % 2 == 1:
                    layout.addStretch()
            self._mainLayout.addLayout(layout)
        self.setLayout(self._mainLayout)
        
    def reinitialize(self):
        pass