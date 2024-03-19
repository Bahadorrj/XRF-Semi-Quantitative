from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSpacerItem,
    QSizePolicy,
    QTableWidgetItem
)

from python.Logic.Sqlite import DatabaseConnection, getDatabaseDataframe
from python.Views.Widgets import Table

import qrcResources


class Window(QWidget):
    def __init__(self, size):
        super().__init__()
        self.setMinimumWidth(int(size.width() * 0.8))
        self.setMinimumHeight(int(size.height() * 0.8))
        self.setWindowTitle("Elements")

        self.mainLayout = QVBoxLayout()
        self.filterLayout = QHBoxLayout()
        self.filterLabel = QLabel()
        self.filter = QComboBox()
        self.spacerItem = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
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
        self.form = Table(headers)
        database = DatabaseConnection.getInstance(":fundamentals.db")
        self._elementsDf = getDatabaseDataframe(database, "elements")
        query = "element_id IN (SELECT element_id FROM UQ ORDER BY element_id)"
        self._UQDf = getDatabaseDataframe(database, "elements", where=query)
        self._conditionsDf = getDatabaseDataframe(database, "conditions")
        self._rowCount = self._elementsDf.shape[0]

        self._setupUI()

    def _setupUI(self):
        self.filterLabel.setText('Filter by: ')

        self.filter.addItems(['all elements', 'active elements', 'UQR'])

        self.filterLayout.addWidget(self.filterLabel)
        self.filterLayout.addWidget(self.filter)
        self.filterLayout.addItem(self.spacerItem)

        self.mainLayout.addLayout(self.filterLayout)

        self._setupTable(range(self._rowCount))

        self.mainLayout.addWidget(self.form)
        self.setLayout(self.mainLayout)

    def _setupTable(self, rowList):
        for row in rowList:
            items = list()
            for label in ['atomic_number', 'name', 'symbol', 'radiation_type',
                          'Kev', 'low_Kev', 'high_Kev', 'intensity']:
                item = QTableWidgetItem(str(self._elementsDf.at[row, label]))
                items.append(item)
            activeItem = QTableWidgetItem()
            if self._elementsDf.at[row, "active"] == 1:
                activeItem.setText("True")
                activeItem.setForeground(Qt.GlobalColor.green)
            else:
                activeItem.setText("False")
                activeItem.setForeground(Qt.GlobalColor.red)
            items.append(activeItem)
            conditionId = self._elementsDf.at[row, 'condition_id']
            conditionName = self._conditionsDf['name'].get(conditionId)
            conditionItem = QTableWidgetItem(conditionName)
            items.append(conditionItem)
            self.form.addRow(items, self._elementsDf.at[row, "element_id"])
        self.form.setCurrentItem(self.form.item(0, 0))

    def filterTable(self, index):
        self.form.clear()
        if index == 0:
            self._setupTable(range(self._rowCount()))
        elif index == 1:
            self._setupTable(
                self._elementsDf[self._elementsDf['active'] == 1].index
            )
        else:
            indexes = self._UQDf["element_id"].to_list()
            for i in range(len(indexes)):
                indexes[i] -= 1
            self._setupTable(indexes)

    def getFilter(self):
        return self.filter
