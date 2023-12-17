import pyqtspinner
from PyQt5 import QtWidgets


class Window(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QHBoxLayout(self)
        self.spinner = pyqtspinner.WaitingSpinner(self, False, radius=15)
        self.spacerOne = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.spacerTwo = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.label = QtWidgets.QLabel()

    def setup_ui(self):
        self.setFixedWidth(300)
        self.setWindowTitle("Please wait")
        self.layout.addWidget(self.spinner)
        self.layout.addItem(self.spacerOne)
        self.layout.addWidget(self.label)
        self.layout.addItem(self.spacerTwo)
        self.label.setText("Collecting elements")
        self.spinner.start()
