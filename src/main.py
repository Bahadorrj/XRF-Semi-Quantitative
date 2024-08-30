import logging
import os
import socket
import sys
import threading

from PyQt6 import QtWidgets, QtGui

from src.controllers import GuiHandler, ClientHandler
from src.utils.database import getDataframe
from src.utils.datatypes import Method
from src.utils.paths import resourcePath
from src.views.explorers.methodexplorer import MethodExplorer
from src.views.trays.calibrationtray import CalibrationTrayWidget
from src.views.trays.methodtray import MethodTrayWidget
from src.views.windows.plotwindow import PlotWindow


def connectServerAndGUI(
    host, port, plotWindow: PlotWindow, app: QtWidgets.QApplication
) -> None:
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
    for root, _, files in os.walk(resourcePath("resources/fonts")):
        for file in files:
            path = os.path.join(root, file)
            QtGui.QFontDatabase.addApplicationFont(path)
    with open(resourcePath("style.qss")) as f:
        _style = f.read()
        app.setStyleSheet(_style)
    # window = CalibrationTrayWidget(dataframe=getDataframe("Calibrations"))
    # window = PlotWindow()
    # method = Method.fromATXMFile(resourcePath("methods/test1.atxm"))
    # window = MethodExplorer(method=method)
    window = MethodTrayWidget(dataframe=getDataframe("Methods"))
    window.show()
    sys.exit(app.exec())
