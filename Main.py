import sys

from PyQt5 import QtWidgets, QtGui

import PlotWindow
from Backend import icons
from FileClass import File

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()
    app.setWindowIcon(QtGui.QIcon(icons["CSAN"]))
    f = File(r"additional\Au.txt")
    c = f.get_condition(3)
    main_window = PlotWindow.Window(size)
    main_window.setup_ui()
    main_window.show()
    sys.exit(app.exec())
