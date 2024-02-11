import sys

from PyQt6 import QtWidgets, QtGui

from src.main.python.Controllers.PlotWindowController import PlotWindowController
from src.main.python.Views.Icons import ICONS
from src.main.python.Views.PlotWindow import Window

def main():
    app = QtWidgets.QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()
    app.setWindowIcon(QtGui.QIcon(ICONS["CSAN"]))
    mainWindow = Window(size)
    PlotWindowController(mainWindow)
    mainWindow.showMaximized()
    sys.exit(app.exec())
