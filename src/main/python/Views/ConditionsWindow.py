from PyQt6 import QtWidgets, QtCore

from src.main.python.Logic.Sqlite import getDatabaseDataframe, DatabaseConnection
from src.main.python.Views.TableWidget import Form


class Window(QtWidgets.QWidget):
    def __init__(self, size):
        super().__init__()
        self.setFixedWidth(int(0.8 * size.width()))
        self.setFixedHeight(int(0.3 * size.height()))
        self.mainLayout = QtWidgets.QHBoxLayout()
        headerLabels = [
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
        self.form = Form(headerLabels)
        database = DatabaseConnection.getInstance(r"F:\CSAN\Master\DB\fundamentals.db")
        self._conditionsDf = getDatabaseDataframe(database, "conditions")
        self._setupUI()

    def _setupUI(self):
        # window config
        self.setWindowTitle("Conditions")
        self.mainLayout.addWidget(self.form)
        self.setLayout(self.mainLayout)
        for i in self._conditionsDf.index:
            items = list()
            for label in ["name", "Kv", "mA", "time", "rotation", "environment", "filter", "mask"]:
                item = QtWidgets.QTableWidgetItem(str(self._conditionsDf.at[i, label]))
                items.append(item)
            activeItem = QtWidgets.QTableWidgetItem()
            if self._conditionsDf.at[i, "active"] == 1:
                activeItem.setText("True")
                activeItem.setForeground(QtCore.Qt.GlobalColor.green)
            else:
                activeItem.setText("False")
                activeItem.setForeground(QtCore.Qt.GlobalColor.red)
            items.append(activeItem)
            self.form.addRow(items, self._conditionsDf.at[i, "condition_id"])
        self.form.setCurrentItem(self.form.item(0, 0))
