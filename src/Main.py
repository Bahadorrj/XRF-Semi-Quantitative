import sys

from PyQt5 import QtWidgets, QtGui

from src.Logic.Backend import icons
from src.UI import PeakSearchWindow
from src.Types.FileClass import File

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()
    app.setWindowIcon(QtGui.QIcon(icons["CSAN"]))
    main_window = PeakSearchWindow.Window(size)
    f = File(r"F:\CSAN\main\additional\Au.txt")
    main_window.setup_ui(f.get_counts()[0], f.get_condition(0))
    main_window.show()
    sys.exit(app.exec())
