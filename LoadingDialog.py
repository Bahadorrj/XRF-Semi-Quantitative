import pyqtspinner
from PyQt5 import QtWidgets, QtCore


class Window(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QHBoxLayout(self)
        self.spinner = pyqtspinner.WaitingSpinner(self, False, radius=20)
        self.spacerOne = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.spacerTwo = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.label = QtWidgets.QLabel()

    def setup_ui(self):
        self.setFixedSize(QtCore.QSize(300, 200))
        self.setWindowTitle("Loading")
        self.label.setText("Collecting elements...")
        self.layout.addWidget(self.spinner)
        self.layout.addItem(self.spacerOne)
        self.layout.addWidget(self.label)
        self.layout.addItem(self.spacerTwo)
        self.spinner.start()
