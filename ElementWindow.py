from PyQt5 import QtCore, QtWidgets

import Sqlite
from Backend import addr


class Window(QtWidgets.QWidget):
    def __init__(self, size):
        super().__init__()
        self.windowSize = QtCore.QSize(
            int(size.width() * 0.5), int(size.height() * 0.3)
        )
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.filterLayout = QtWidgets.QHBoxLayout()
        self.filterLabel = QtWidgets.QLabel()
        self.filter = QtWidgets.QComboBox()
        self.spacerItem = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.form = QtWidgets.QTableWidget()
        self.dfElements = Sqlite.read(addr["dbFundamentals"], "elements")
        query = "element_id IN (SELECT element_id FROM UQ ORDER BY element_id)"
        self.dfUQ = Sqlite.read(
            addr["dbFundamentals"], "elements", where=query)
        self.rows = self.dfElements.shape[0]

    def setup_ui(self):
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle("Elements")
        self.showMaximized()

        self.filterLabel.setText('Filter by: ')

        self.filter.addItems(['all elements', 'active elements', 'UQR'])
        self.filter.currentIndexChanged.connect(self.filter_table)

        self.filterLayout.addWidget(self.filterLabel)
        self.filterLayout.addWidget(self.filter)
        self.filterLayout.addItem(self.spacerItem)

        self.mainLayout.addLayout(self.filterLayout)

        self.form.setFrameShape(QtWidgets.QFrame.Box)
        self.form.setFrameShadow(QtWidgets.QFrame.Plain)
        self.form.setColumnCount(10)

        self.setup_table(range(self.rows))

        self.mainLayout.addWidget(self.form)
        self.setLayout(self.mainLayout)

    def setup_table(self, row_list):
        headers = [
            'Atomic No',
            'Name',
            'Symbol',
            'Radiation',
            'Kev',
            'Low Kev',
            'High Kev',
            'Intensity',
            'Active',
            'Activated in'
        ]
        self.form.setHorizontalHeaderLabels(headers)
        self.form.setRowCount(len(row_list))
        self.form.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        for index, row in enumerate(row_list):
            self.atomicNoItem = QtWidgets.QTableWidgetItem(
                str(self.dfElements.at[row, 'atomic_number'])
            )
            self.atomicNoItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.atomicNoItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.nameItem = QtWidgets.QTableWidgetItem(
                self.dfElements.at[row, 'name']
            )
            self.nameItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.nameItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.symbolItem = QtWidgets.QTableWidgetItem(
                self.dfElements.at[row, 'symbol']
            )
            self.symbolItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.symbolItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.radiationItem = QtWidgets.QTableWidgetItem(
                self.dfElements.at[row, 'radiation_type']
            )
            self.radiationItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.radiationItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.KevItem = QtWidgets.QTableWidgetItem(
                str(self.dfElements.at[row, 'Kev'])
            )
            self.KevItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.KevItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.lowItem = QtWidgets.QTableWidgetItem(
                str(self.dfElements.at[row, 'low_Kev'])
            )
            self.lowItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.lowItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.highItem = QtWidgets.QTableWidgetItem(
                str(self.dfElements.at[row, 'high_Kev'])
            )
            self.highItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.highItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.intensityItem = QtWidgets.QTableWidgetItem(
                str(self.dfElements.at[row, 'intensity'])
            )
            self.intensityItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.intensityItem.setFlags(QtCore.Qt.ItemIsEnabled)
            active = self.dfElements.at[row, 'active']

            if active == 1:
                self.activeItem = QtWidgets.QTableWidgetItem(
                    str(True)
                )
                self.activeItem.setForeground(QtCore.Qt.green)
            else:
                self.activeItem = QtWidgets.QTableWidgetItem(
                    str(False)
                )
                self.activeItem.setForeground(QtCore.Qt.red)
            self.activeItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.activeItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.conditionItem = QtWidgets.QTableWidgetItem(
                Sqlite.get_condition_name_where(
                    self.dfElements.at[row, 'condition_id']
                )
            )
            self.conditionItem.setTextAlignment(QtCore.Qt.AlignCenter)
            self.conditionItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.form.setItem(index, 0, self.atomicNoItem)
            self.form.setItem(index, 1, self.nameItem)
            self.form.setItem(index, 2, self.symbolItem)
            self.form.setItem(index, 3, self.radiationItem)
            self.form.setItem(index, 4, self.KevItem)
            self.form.setItem(index, 5, self.lowItem)
            self.form.setItem(index, 6, self.highItem)
            self.form.setItem(index, 7, self.intensityItem)
            self.form.setItem(index, 8, self.activeItem)
            self.form.setItem(index, 9, self.conditionItem)

    def filter_table(self, index):
        self.form.clear()
        if index == 0:
            self.setup_table(range(self.rows))
        elif index == 1:
            # print(self.dfElements[self.dfElements['active'] == 1].index)
            self.setup_table(
                self.dfElements[self.dfElements['active'] == 1].index
            )
        else:
            indexes = self.dfUQ["element_id"].to_list()
            for i in range(len(indexes)):
                indexes[i] -= 1
            self.setup_table(indexes)
