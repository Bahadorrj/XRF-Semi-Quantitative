import sys

from PyQt5 import QtWidgets, QtGui

import PlotWindow
from Backend import icon

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()
    app.setWindowIcon(QtGui.QIcon(icon["CSAN"]))
    main_window = PlotWindow.Window(size)
    main_window.setup_ui()
    main_window.show()
    sys.exit(app.exec())
