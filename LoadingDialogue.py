import pyqtspinner
from PyQt5 import QtWidgets, QtCore
import time


class Window(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        # size and window config
        self.setFixedWidth(350)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)  # Disabling close button
        # components
        self.layout = QtWidgets.QHBoxLayout(self)
        self.spinner = pyqtspinner.WaitingSpinner(self, False, radius=15)
        self.spacerOne = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.spacerTwo = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.label = QtWidgets.QLabel()
        # variables
        self.animateCounter = 0
        self.textChangeTime = 0
        self.animated = False
        self.processFinished = False
        # place components
        self.layout.addWidget(self.spinner)
        self.layout.addItem(self.spacerOne)
        self.layout.addWidget(self.label)
        self.layout.addItem(self.spacerTwo)

    def get_label(self) -> str:
        return self.label.text()

    def set_label(self, text: str) -> None:
        self.label.setText(text)

    def use_animation(self, text_change_time: float) -> None:
        self.animated = True
        self.set_text_change_time(text_change_time)

    def set_text_change_time(self, text_change_time: float) -> None:
        self.textChangeTime = text_change_time

    def animate_text(self) -> None:
        if self.animated:
            if self.animateCounter == self.textChangeTime * 10:
                self.animateCounter = 0
                label = self.get_label()
                if label[-3:-1] == "...":
                    self.set_label(self.get_label()[:-3])
                else:
                    self.set_label(self.get_label() + ".")
            else:
                self.animateCounter += 1
            QtWidgets.QApplication.processEvents()
            time.sleep(0.1)

    def closeEvent(self, a0):
        if self.processFinished:
            a0.accept()
        else:
            a0.ignore()

    def setup_ui(self, title, label):
        self.setWindowTitle(title)
        self.label.setText(label)
        self.spinner.start()
