from PyQt6 import QtCore, QtGui, QtWidgets

from python.utils.database import getDatabase
from python.utils.paths import resourcePath

class SymbolButton(QtWidgets.QPushButton):
    def __init__(self, symbol, parent=None):
        super(SymbolButton, self).__init__(symbol, parent)
        self.setCheckable(True)
        self.setStyleSheet("""
            QPushButton {
                border: 2px solid darkgray;
                background-color: transparent;
            }
            
            QPushButton:checked {
                background-color: rgba(135, 206, 250, 128);
            }
            
            QPushButton:pressed {
                background-color: rgb(135, 206, 250)
            }
            
            QPushButton:hover {
                background-color: rgb(127, 127, 127);
                color: white;
            }
        """)

class PandasModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        QtCore.QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._data.columns[col]
        return None


class ConditionTable(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super(ConditionTable, self).__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setStyleSheet(
            """
            QTableView {
                border: 1px solid gray;
            }
            
            QTableView::item:selected {
                background-color: rgba(135, 206, 250, 128);  /* LightSkyBlue with 50% opacity */
                color: black;
            }
        """
        )
        db = getDatabase(resourcePath("fundamentals.db"))
        self._df = db.dataframe("SELECT * FROM Conditions").query("active == 1").drop(
            ['condition_id', 'active'], axis=1
        )
        self.setModel(PandasModel(self._df))
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)


class AnalytesAndConditions(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(AnalytesAndConditions, self).__init__(parent)
        vLayout = QtWidgets.QVBoxLayout()
        vLayout.setContentsMargins(30, 30, 30, 30)
        vLayout.setSpacing(30)
        vLayout.addLayout(self._createPeriodicLayout())
        vLayout.addWidget(self._createConditionTable())
        self.setLayout(vLayout)

    def _createPeriodicLayout(self) -> QtWidgets.QVBoxLayout:
        vLayout = QtWidgets.QVBoxLayout()
        vLayout.setSpacing(0)
        rows = [
            ["H", "", "He"],
            ["Li", "Be", "", "B", "C", "N", "O", "F", "Ne"],
            ["Na", "Mg", "", "Al", "Si", "P", "S", "Cl", "Ar"],
            ["K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"],
            ["Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe"],
            ["Cs", "Ba", "L", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn"],
            ["Fr", "Ra", "A", ""],
            [""],
            ["", "L", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", ""],
            ["", "A", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", ""]
        ]
        for row in rows:
            layout = QtWidgets.QHBoxLayout()
            layout.setSpacing(0)
            for symbol in row:
                if symbol:
                    button = SymbolButton(symbol, self)
                    button.setFixedWidth(30)
                    button.setFixedHeight(30)
                    layout.addWidget(button)
                else:
                    spacer = QtWidgets.QSpacerItem(
                        30, 30, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
                    )
                    layout.addItem(spacer)
            vLayout.addLayout(layout)
        return vLayout

    def _createConditionTable(self) -> QtWidgets.QTableView:
        self.conditionTable = ConditionTable(self)
        return self.conditionTable


class MethodExplorer(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MethodExplorer, self).__init__(parent)
        self.setFixedSize(800, 600)
        self.setStyleSheet("background-color: white;")
        self._createActions()
        self._createMenuBar()
        self._createToolBar()
        self._createTreeWidget()
        self._createWidgets()
        self._setUpView()

    def _createActions(self) -> None:
        self._actionsMap = {}
        actions = ()
        for label in actions:
            action = QtGui.QAction(label)
            key = "-".join(label.lower().split(" "))
            action.setIcon(QtGui.QIcon(resourcePath(f"icons/{key}.png")))
            if key in ["save-as", "peak-search", "new"]:
                action.setDisabled(True)
            self._actionsMap[key] = action
            # action.triggered.connect(partial(self._actionTriggered, key))

    def _createMenuBar(self) -> None:
        self._createMenus()
        self._fillMenusWithActions()

    def _createMenus(self) -> None:
        self._menusMap = {}
        menuBar = self.menuBar()
        menus = ["&File", "&Edit", "View", "&Help"]
        for label in menus:
            menu = menuBar.addMenu(label)
            key = label.lower()[1:]
            self._menusMap[key] = menu

    def _fillMenusWithActions(self) -> None:
        pass

    def _createToolBar(self) -> None:
        toolBar = QtWidgets.QToolBar(self)
        toolBar.setIconSize(QtCore.QSize(16, 16))
        toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolBar.setMovable(False)
        self._fillToolBarWithActions(toolBar)
        self.addToolBar(toolBar)

    def _fillToolBarWithActions(self, toolBar: QtWidgets.QToolBar) -> None:
        pass

    def _createTreeWidget(self) -> None:
        self._treeWidget = QtWidgets.QTreeWidget(self)
        self._treeWidget.setFixedHeight(200)

    def _createWidgets(self) -> None:
        self._createAnalytesAndConditionsWidget()

    def _createAnalytesAndConditionsWidget(self) -> None:
        self._analytesAndConditionsWidget = AnalytesAndConditions(self)

    def _setUpView(self) -> None:
        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.addWidget(self._treeWidget)
        mainLayout.addWidget(self._analytesAndConditionsWidget)
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)
