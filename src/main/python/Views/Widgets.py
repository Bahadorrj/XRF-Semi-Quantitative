from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QTableWidget, QFrame, QHeaderView, QTreeWidget, QMenu, QTreeWidgetItem


class Table(QTableWidget):
    def __init__(self, headers):
        super().__init__()
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self._headers = headers
        self._rowIds = list()
        self._nonWidgetHeaders = self._initNonWidgetHeaders()
        self.setupUI()

    def setupUI(self):
        self.setColumnCount(len(self._nonWidgetHeaders))
        self.setHorizontalHeaderLabels(self._nonWidgetHeaders)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def getHeaders(self):
        return self._headers

    def setHeaders(self, headers):
        self._headers = headers

    def getNonWidgetHeaders(self):
        return self._nonWidgetHeaders

    def setNonWidgetHeaders(self, headers):
        self._nonWidgetHeaders = headers

    def _initNonWidgetHeaders(self):
        headers = list()
        for header in self.getHeaders():
            if "Widget" not in header:
                headers.append(header)
        return headers

    def getRowIds(self):
        return self._rowIds

    def getRowId(self, index):
        return self._rowIds[index]

    def getCurrentRowId(self):
        return self.getRowId(self.currentRow())

    def getRowById(self, id):
        index = self.getRowIds().index(id)
        return self.getRow(index)

    def setRowID(self, id):
        self._rowIds = id

    def addRow(self, items: list, id):
        self.getRowIds().append(id)
        if self.rowCount() == 0:
            headers = list()
            for header in self.getHeaders():
                if "Widget" not in header:
                    headers.append(header)
                else:
                    headers.append("")
            self.setColumnCount(len(headers))
            self.setHorizontalHeaderLabels(headers)
            for index, header in enumerate(self.getHeaders()):
                if "Widget" not in header:
                    self.horizontalHeader().setSectionResizeMode(
                        index, QHeaderView.ResizeMode.Stretch
                    )
                else:
                    self.horizontalHeader().setSectionResizeMode(
                        index, QHeaderView.ResizeMode.ResizeToContents
                    )
        self.blockSignals(True)
        index = self.rowCount()
        self.setRowCount(index + 1)
        for i, item in enumerate(items):
            try:
                self.setItem(index, i, item)
            except TypeError:
                self.setCellWidget(index, i, item)

            try:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            except AttributeError:
                pass
        self.blockSignals(False)
        self.setCurrentCell(self.rowCount() - 1, 0)

    def removeRow(self, row_index):
        super().removeRow(row_index)
        self.getRowIds().pop(row_index)
        if self.rowCount() == 0:
            self.setupUI()

    def getRow(self, row):
        row_dictionary = dict()
        for column, header in enumerate(self.getHeaders()):
            if "Widget" in header:
                row_dictionary[header] = self.cellWidget(row, column)
            else:
                row_dictionary[header] = self.item(row, column)
        return row_dictionary

    def getCurrentRow(self):
        return self.getRow(self.currentRow())

    def removeButtons(self):
        temp_header = list()
        for header in self.getHeaders():
            if "Button" not in header:
                temp_header.append(header)
        self.setColumnCount(len(temp_header))
        self.setHorizontalHeaderLabels(temp_header)

    def clear(self):
        for row in range(self.rowCount()):
            self.removeRow(0)
        super().clear()

class Tree(QTreeWidget):
    itemDeleted = pyqtSignal(QTreeWidgetItem)

    def __init__(self):
        super().__init__()

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not self.itemIsTopLevel(item) and self.currentColumn() == 0:
            contextMenu = QMenu(self)
            actionEdit = QAction("Edit", self)
            actionDelete = QAction("Delete", self)

            contextMenu.addAction(actionEdit)
            contextMenu.addAction(actionDelete)

            action = contextMenu.exec(self.mapToGlobal(event.pos()))
            if action == actionEdit:
                item = self.itemAt(event.pos())
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.editItem(item)
            elif action == actionDelete:
                item = self.itemAt(event.pos())
                self.itemDeleted.emit(item)

    def itemIsTopLevel(self, item):
        if self.indexOfTopLevelItem(item) != -1:
            return True
        return False
