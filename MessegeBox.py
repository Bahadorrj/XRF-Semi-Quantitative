from PyQt5 import QtWidgets


class Dialog(QtWidgets.QMessageBox):
    def __init__(self, QtIcon, title, message):
        super().__init__()
        self.setIcon(QtIcon)
        self.setWindowTitle(title)
        self.setText(message)
