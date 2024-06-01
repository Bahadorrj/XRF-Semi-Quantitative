import sys

from PyQt6 import QtCore, QtWidgets

from python.utils.database import getDatabase
from python.utils.paths import resource_path


class InterferenceWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(InterferenceWindow, self).__init__(parent)
        self._db = getDatabase(resource_path('fundamentals.db'))
        self._df = self._db.dataframe('SELECT * FROM interference')
        self.resize(1200, 800)
        self._createTableWidget()
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self._tableWidget)
        centralWidget = QtWidgets.QWidget(self)
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

    def _createTableWidget(self):
        self._tableWidget = QtWidgets.QTableWidget(self)
        self._headers = ['Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K',
                         'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br',
                         'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb',
                         'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho',
                         'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi',
                         'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am']
        self._tableWidget.setColumnCount(len(self._headers))
        self._tableWidget.setHorizontalHeaderLabels(self._headers)
        self._tableWidget.setRowCount(len(self._headers))
        self._tableWidget.setVerticalHeaderLabels(self._headers)
        self._tableWidget.setGridStyle(QtCore.Qt.PenStyle.DashDotDotLine)
        self._tableWidget.setAlternatingRowColors(True)
        self._fillTable()

    def _fillTable(self):
        for _, series in self._df.iterrows():
            elementId = series['element_id']
            interfererId = series['interferer_id']
            coefficient = series['coefficient']

    def _saveToDatabase(self):
        pass

    def addCoefficient(self, element: str, interferer: str, coefficient: float) -> None:
        row = self._headers.index(element)
        column = self._headers.index(interferer)
        item = QtWidgets.QTableWidgetItem(str(coefficient))
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._tableWidget.setItem(row, column, item)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = InterferenceWindow()
    window.addCoefficient('Ne', 'Mg', 0.88)
    window.show()
    sys.exit(app.exec())
