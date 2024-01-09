from PyQt5 import QtWidgets, QtCore

from src.Logic.Sqlite import dataframe_of_database
from src.UI.TableWidget import Form


class Window(QtWidgets.QWidget):
    def __init__(self, size):
        super().__init__()
        self.windowSize = QtCore.QSize(
            int(size.width() * 0.5), int(size.height() * 0.3)
        )
        self.mainLayout = QtWidgets.QHBoxLayout()
        __header_labels = [
            "Name",
            "Kv",
            "mA",
            "Time",
            "Rotation",
            "Environment",
            "Filter",
            "Mask",
            "Active",
        ]
        self.form = Form(__header_labels)
        self.__df_conditions = dataframe_of_database("fundamentals", "conditions")

    def get_dataframe(self):
        return self.__df_conditions

    def setup_ui(self):
        # window config
        self.setFixedSize(self.windowSize)
        self.setWindowTitle("Conditions")
        self.mainLayout.addWidget(self.form)
        self.setLayout(self.mainLayout)
        self.form.setup_ui()

        for i in self.get_dataframe().index:
            name_item = QtWidgets.QTableWidgetItem(
                self.get_dataframe().at[i, "name"])
            kv_item = QtWidgets.QTableWidgetItem(
                str(self.get_dataframe().at[i, "Kv"]))
            ma_item = QtWidgets.QTableWidgetItem(
                str(self.get_dataframe().at[i, "Kv"]))
            time_item = QtWidgets.QTableWidgetItem(
                str(self.get_dataframe().at[i, "time"])
            )
            rotation_item = QtWidgets.QTableWidgetItem(
                str(self.get_dataframe().at[i, "rotation"])
            )
            environment_item = QtWidgets.QTableWidgetItem(
                self.get_dataframe().at[i, "environment"]
            )
            filter_item = QtWidgets.QTableWidgetItem(
                str(self.get_dataframe().at[i, "filter"])
            )
            mask_item = QtWidgets.QTableWidgetItem(
                str(self.get_dataframe().at[i, "mask"])
            )
            active_item = QtWidgets.QTableWidgetItem(
                str(bool(self.get_dataframe().at[i, "active"]))
            )
            items = [name_item, kv_item, ma_item, time_item, rotation_item,
                     environment_item, filter_item, mask_item, active_item]
            self.form.add_row(items, self.get_dataframe().at[i, "condition_id"])
        self.form.setCurrentItem(self.form.item(0, 0))

