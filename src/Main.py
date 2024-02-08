import sys

from PyQt5 import QtWidgets, QtGui

from src.Logic.Backend import icons
from src.UI import PlotWindow
# from src.Types.FileClass import File

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()
    app.setWindowIcon(QtGui.QIcon(icons["CSAN"]))
    main_window = PlotWindow.Window(size)
    main_window.show()
    main_window.setup_ui()
    sys.exit(app.exec())
    # counts = File(r"F:\CSAN\main\Test -Int\S.txt").get_counts()[7]
    # for index, count in enumerate(counts):
    #     print(f"{index}- {count}")
