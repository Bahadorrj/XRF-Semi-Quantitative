from PyQt5 import QtWidgets, QtCore


class Form(QtWidgets.QTableWidget):
    def __init__(self, headers):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setRowCount(0)
        self.setColumnCount(0)
        self.__headers = headers
        self.__non_widget_headers = self.init_non_widget_headers()
        self.__row_ids = list()
        self.setup_ui()

    def get_headers(self):
        return self.__headers

    def set_headers(self, headers):
        self.__headers = headers

    def get_non_widget_headers(self):
        return self.__non_widget_headers

    def set_non_widget_headers(self, headers):
        self.__non_widget_headers = headers

    def init_non_widget_headers(self):
        headers = list()
        for header in self.get_headers():
            if "Widget" not in header:
                headers.append(header)
        return headers

    def get_row_ids(self):
        return self.__row_ids

    def get_row_id(self, index):
        return self.__row_ids[index]

    def get_current_row_id(self):
        return self.get_row_id(self.currentRow())

    def get_row_by_id(self, id):
        index = self.get_row_ids().index(id)
        return self.get_row(index)

    def set_row_id(self, id):
        self.__row_ids = id

    def setup_ui(self):
        self.setColumnCount(len(self.get_non_widget_headers()))
        self.setHorizontalHeaderLabels(self.get_non_widget_headers())
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def add_row(self, items: list, id):
        self.get_row_ids().append(id)
        if self.rowCount() == 0:
            headers = list()
            for header in self.get_headers():
                if "Widget" not in header:
                    headers.append(header)
                else:
                    headers.append("")
            self.setColumnCount(len(headers))
            self.setHorizontalHeaderLabels(headers)
            for index, header in enumerate(self.get_headers()):
                if "Widget" not in header:
                    self.horizontalHeader().setSectionResizeMode(index, QtWidgets.QHeaderView.Stretch)
                else:
                    self.horizontalHeader().setSectionResizeMode(index, QtWidgets.QHeaderView.ResizeToContents)
        self.blockSignals(True)
        index = self.rowCount()
        self.setRowCount(index + 1)
        for i, item in enumerate(items):
            try:
                self.setItem(index, i, item)
            except TypeError:
                self.setCellWidget(index, i, item)

            try:
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                item.setFlags(QtCore.Qt.ItemIsEnabled)
            except AttributeError:
                pass
        self.blockSignals(False)
        self.setCurrentCell(self.rowCount() - 1, 0)

    def removeRow(self, row_index):
        super().removeRow(row_index)
        self.get_row_ids().pop(row_index)
        if self.rowCount() == 0:
            self.setup_ui()

    def get_row(self, row):
        row_dictionary = dict()
        for column, header in enumerate(self.get_headers()):
            if "Widget" in header:
                row_dictionary[header] = self.cellWidget(row, column)
            else:
                row_dictionary[header] = self.item(row, column)
        return row_dictionary

    def get_current_row(self):
        return self.get_row(self.currentRow())

    def remove_buttons(self):
        temp_header = list()
        for header in self.get_headers():
            if "Button" not in header:
                temp_header.append(header)
        self.setColumnCount(len(temp_header))
        self.setHorizontalHeaderLabels(temp_header)

    def clear(self):
        for row in range(self.rowCount()):
            self.removeRow(0)
        super().clear()
