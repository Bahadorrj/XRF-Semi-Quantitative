import logging
import socket
import threading

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtWidgets import QMainWindow, QApplication

from python.main.controllers import GuiHandler, ClientHandler
from python.main.utils import paths
from python.main.utils.paths import sys
from python.main.views.plotwindow import PlotWindow


def connectServerAndGUI(host, port, mainWindow: QMainWindow, app: QApplication):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(1)
        logging.info(f"Server listening on {host}:{port}")
        conn, addr = s.accept()
        logging.info(f"Connected to {addr}")
        guiHandler = GuiHandler(mainWindow)
        clientHandler = ClientHandler(conn, guiHandler, app)
        threading.Thread(target=clientHandler.handleClient).start()


def main() -> None:
    arg = sys.argv
    app = QtWidgets.QApplication(arg)
    app.setWindowIcon(QtGui.QIcon(paths.resource_path('CSAN.ico')))
    window = PlotWindow()
    # connectServerAndGUI('127.0.0.1', 16000, window, app)
    window.show()
    sys.exit(app.exec())
