from PyQt5 import QtCore, QtWidgets

from Sqlite import dataframe_of_database
from TableWidget import Form


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
        self.form = Form(headers)
        self.__df_elements = dataframe_of_database("fundamentals", "elements")
        query = "element_id IN (SELECT element_id FROM UQ ORDER BY element_id)"
        self.__df_uq = dataframe_of_database(
            "fundamentals", "elements", where=query)
        self.__df_conditions = dataframe_of_database("fundamentals", "conditions")
        self.__row_count = self.__df_elements.shape[0]
        
    def get_elements_dataframe(self):
        return self.__df_elements
    
    def get_uq_dataframe(self):
        return self.__df_uq
    
    def get_conditions_dataframe(self):
        return self.__df_conditions
    
    def get_row_count(self):
        return self.__row_count

    def setup_ui(self):
        self.setMinimumSize(self.windowSize)
        self.setWindowTitle("Elements")
        self.showMaximized()
        self.form.setup_ui()

        self.filterLabel.setText('Filter by: ')

        self.filter.addItems(['all elements', 'active elements', 'UQR'])
        self.filter.currentIndexChanged.connect(self.filter_table)

        self.filterLayout.addWidget(self.filterLabel)
        self.filterLayout.addWidget(self.filter)
        self.filterLayout.addItem(self.spacerItem)

        self.mainLayout.addLayout(self.filterLayout)

        self.setup_table(range(self.get_row_count()))

        self.mainLayout.addWidget(self.form)
        self.setLayout(self.mainLayout)

    def setup_table(self, row_list):
        for row in row_list:
            atomic_number_item = QtWidgets.QTableWidgetItem(
                str(self.get_elements_dataframe().at[row, 'atomic_number'])
            )
            atomic_number_item.setTextAlignment(QtCore.Qt.AlignCenter)
            atomic_number_item.setFlags(QtCore.Qt.ItemIsEnabled)
            name_item = QtWidgets.QTableWidgetItem(
                self.get_elements_dataframe().at[row, 'name']
            )
            name_item.setTextAlignment(QtCore.Qt.AlignCenter)
            name_item.setFlags(QtCore.Qt.ItemIsEnabled)
            symbol_item = QtWidgets.QTableWidgetItem(
                self.get_elements_dataframe().at[row, 'symbol']
            )
            symbol_item.setTextAlignment(QtCore.Qt.AlignCenter)
            symbol_item.setFlags(QtCore.Qt.ItemIsEnabled)
            radiation_item = QtWidgets.QTableWidgetItem(
                self.get_elements_dataframe().at[row, 'radiation_type']
            )
            radiation_item.setTextAlignment(QtCore.Qt.AlignCenter)
            radiation_item.setFlags(QtCore.Qt.ItemIsEnabled)
            kev_item = QtWidgets.QTableWidgetItem(
                str(self.get_elements_dataframe().at[row, 'Kev'])
            )
            kev_item.setTextAlignment(QtCore.Qt.AlignCenter)
            kev_item.setFlags(QtCore.Qt.ItemIsEnabled)
            low_item = QtWidgets.QTableWidgetItem(
                str(self.get_elements_dataframe().at[row, 'low_Kev'])
            )
            low_item.setTextAlignment(QtCore.Qt.AlignCenter)
            low_item.setFlags(QtCore.Qt.ItemIsEnabled)
            high_item = QtWidgets.QTableWidgetItem(
                str(self.get_elements_dataframe().at[row, 'high_Kev'])
            )
            high_item.setTextAlignment(QtCore.Qt.AlignCenter)
            high_item.setFlags(QtCore.Qt.ItemIsEnabled)
            intensity_item = QtWidgets.QTableWidgetItem(
                str(self.get_elements_dataframe().at[row, 'intensity'])
            )
            intensity_item.setTextAlignment(QtCore.Qt.AlignCenter)
            intensity_item.setFlags(QtCore.Qt.ItemIsEnabled)
            active = self.get_elements_dataframe().at[row, 'active']
            if active == 1:
                active_item = QtWidgets.QTableWidgetItem(
                    str(True)
                )
                active_item.setForeground(QtCore.Qt.green)
            else:
                active_item = QtWidgets.QTableWidgetItem(
                    str(False)
                )
                active_item.setForeground(QtCore.Qt.red)
            active_item.setTextAlignment(QtCore.Qt.AlignCenter)
            active_item.setFlags(QtCore.Qt.ItemIsEnabled)
            condition_id = self.get_elements_dataframe().at[row, 'condition_id']
            condition_name = self.get_conditions_dataframe()['name'].get(condition_id)
            condition_item = QtWidgets.QTableWidgetItem(condition_name)
            condition_item.setTextAlignment(QtCore.Qt.AlignCenter)
            condition_item.setFlags(QtCore.Qt.ItemIsEnabled)
            items = [atomic_number_item, name_item, symbol_item, radiation_item, kev_item,
                     low_item, high_item, intensity_item, active_item, condition_item]
            self.form.add_row(items, self.get_elements_dataframe().at[row, "element_id"])

    def filter_table(self, index):
        self.form.clear()
        if index == 0:
            self.setup_table(range(self.get_row_count()))
        elif index == 1:
            self.setup_table(
                self.get_elements_dataframe()[self.get_elements_dataframe()['active'] == 1].index
            )
        else:
            indexes = self.get_uq_dataframe()["element_id"].to_list()
            for i in range(len(indexes)):
                indexes[i] -= 1
            self.setup_table(indexes)
