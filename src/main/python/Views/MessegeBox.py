from PyQt6.QtWidgets import QMessageBox


class Dialog(QMessageBox):
    def __init__(self, QtIcon, title, message):
        super().__init__()
        self.setIcon(QtIcon)
        self.setWindowTitle(title)
        self.setText(message)
