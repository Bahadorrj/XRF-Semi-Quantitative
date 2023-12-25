from PyQt5 import QtWidgets, QtCore, QtGui


class Form(QtWidgets.QTableWidget):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setFrameShadow(QtWidgets.QFrame.Plain)

    def setup_ui(self, headers):
        header_count = len(headers)
        self.setColumnCount(header_count)
        self.setHorizontalHeaderLabels(headers)
        if "" in headers:
            for i, header in enumerate(headers):
                if header == "":
                    self.horizontalHeader().setSectionResizeMode(
                        i, QtWidgets.QHeaderView.ResizeToContents
                    )
                else:
                    self.horizontalHeader().setSectionResizeMode(
                        i, QtWidgets.QHeaderView.Stretch
                    )

    def add_row(self, items: list):
        self.blockSignals(True)
        index = self.rowCount()
        self.setRowCount(index + 1)
        for i, item in enumerate(items):
            try:
                self.setItem(index, i, item)
            except TypeError:
                self.setCellWidget(index, i, item)
        self.blockSignals(False)

    # def get_row(self, row) -> list:
    #     new = list()
    #     self.setCurrentCell(row, 0)
    #     for item
