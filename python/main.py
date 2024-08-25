import logging
import os
import socket
import sys
import threading

from PyQt6 import QtWidgets, QtGui

from python.controllers import GuiHandler, ClientHandler
from python.utils.paths import resourcePath
from python.views.window.plotwindow import PlotWindow


def connectServerAndGUI(host, port, plotWindow: PlotWindow, app: QtWidgets.QApplication) -> None:
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
    app.setWindowIcon(QtGui.QIcon(resourcePath("CSAN.ico")))
    # connectServerAndGUI('127.0.0.1', 16000, window, app)
    for root, _, files in os.walk(resourcePath("fonts")):
        for file in files:
            path = os.path.join(root, file)
            QtGui.QFontDatabase.addApplicationFont(path)
    with open(resourcePath("style.qss")) as f:
        _style = f.read()
        app.setStyleSheet(_style)
    # window = CalibrationTrayWidget(dataframe=getDataframe("Calibrations").copy())
    # method = Method(getDataframe("Conditions").copy(), getDataframe("Elements").copy(), [])
    window = PlotWindow()
    window.show()
    sys.exit(app.exec())
