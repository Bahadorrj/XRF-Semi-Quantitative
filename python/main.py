import logging
import socket
import threading

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtWidgets import QApplication

from python.controllers import GuiHandler, ClientHandler
from python.utils import paths
from python.utils.paths import sys
from python.views.plotwindow import PlotWindow


def connectServerAndGUI(host, port, plotWindow: PlotWindow, app: QApplication):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(1)
        logging.info(f"Server listening on {host}:{port}")
        conn, addr = s.accept()
        logging.info(f"Connected to {addr}")
        guiHandler = GuiHandler(plotWindow)
        clientHandler = ClientHandler(conn, guiHandler, app)
        threading.Thread(target=clientHandler.handleClient).start()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    arg = sys.argv
    app = QtWidgets.QApplication(arg)
    app.setWindowIcon(QtGui.QIcon(paths.resource_path('CSAN.ico')))
    window = PlotWindow()
    # connectServerAndGUI('127.0.0.1', 16000, window, app)
    window.show()
    sys.exit(app.exec())
