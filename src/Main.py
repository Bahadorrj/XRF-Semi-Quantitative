import sys

from PyQt5 import QtWidgets, QtGui

from src.Logic.Backend import icons
from src.UI import PlotWindow


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()
    app.setWindowIcon(QtGui.QIcon(icons["CSAN"]))
    main_window = PlotWindow.Window(size)
    main_window.setup_ui()
    main_window.show()
    sys.exit(app.exec())
