from PyQt5 import QtWidgets, QtCore

import Sqlite
from Backend import addr


class Window(QtWidgets.QWidget):
    def __init__(self, size):
        super().__init__()
        self.windowSize = QtCore.QSize(
            int(size.width() * 0.5), int(size.height() * 0.3)
        )
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.form = QtWidgets.QTableWidget()
        self.dfConditions = Sqlite.read(addr["dbFundamentals"], "conditions")

    def setup_ui(self):
        # window config
        self.setFixedSize(self.windowSize)
        self.setWindowTitle("Conditions")

        self.form.setFrameShape(QtWidgets.QFrame.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Plain)
        self.form.setColumnCount(10)
        headers = [
            "ID",
            "Name",
            "Kv",
            "mA",
            "Time",
            "Rotation",
            "Enviroment",
            "Filter",
            "Mask",
            "Active",
        ]
        self.form.setHorizontalHeaderLabels(headers)
        self.form.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.form.setRowCount(self.dfConditions.shape[0])
        self.mainLayout.addWidget(self.form)
        self.setLayout(self.mainLayout)

        for i in self.dfConditions.index:
            self.idItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "condition_id"])
            )
            self.idItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.nameItem = QtWidgets.QTableWidgetItem(
                self.dfConditions.at[i, "name"])
            self.nameItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.KvItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "Kv"]))
            self.KvItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.mAItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "Kv"]))
            self.mAItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.timeItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "time"])
            )
            self.timeItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.rotationItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "rotation"])
            )
            self.rotationItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.environmentItem = QtWidgets.QTableWidgetItem(
                self.dfConditions.at[i, "environment"]
            )
            self.environmentItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.filterItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "filter"])
            )
            self.filterItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.maskItem = QtWidgets.QTableWidgetItem(
                str(self.dfConditions.at[i, "mask"])
            )
            self.maskItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.activeItem = QtWidgets.QTableWidgetItem(
                str(bool(self.dfConditions.at[i, "active"]))
            )
            self.activeItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.form.setItem(i, 0, self.idItem)
            self.form.setItem(i, 1, self.nameItem)
            self.form.setItem(i, 2, self.KvItem)
            self.form.setItem(i, 3, self.mAItem)
            self.form.setItem(i, 4, self.timeItem)
            self.form.setItem(i, 5, self.rotationItem)
            self.form.setItem(i, 6, self.environmentItem)
            self.form.setItem(i, 7, self.filterItem)
            self.form.setItem(i, 8, self.maskItem)
            self.form.setItem(i, 9, self.activeItem)
