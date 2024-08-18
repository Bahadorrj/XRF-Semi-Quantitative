import logging
import socket
import threading
import os
import sys

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtWidgets import QApplication

from python.utils import datatypes
from python.utils.paths import resourcePath
from python.utils.database import getDataframe

# from python.controllers import GuiHandler, ClientHandler

# from python.views.plotwindow import PlotWindow
from python.views.calibrationexplorer.explorer import CalibrationExplorer
# from python.views.explorers.methodexplorer.methodexplorer import MethodExplorer


# def connectServerAndGUI(host, port, plotWindow: PlotWindow, app: QApplication):
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         s.bind((host, port))
#         s.listen(1)
#         logging.info(f"Server listening on {host}:{port}")
#         conn, addr = s.accept()
#         logging.info(f"Connected to {addr}")
#         guiHandler = GuiHandler(plotWindow)
#         clientHandler = ClientHandler(conn, guiHandler, app)
#         threading.Thread(target=clientHandler.handleClient).start()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    calibration = datatypes.Calibration(
        datatypes.Analyse.fromTXTFile(r"F:\CSAN\XRF-Semi-Quantitative\Additional\Pure samples\8 Mehr\Au.txt"),
        {},
        {"Au": 100},
        getDataframe("Lines").copy()
    )
    arg = sys.argv
    app = QtWidgets.QApplication(arg)
    app.setWindowIcon(QtGui.QIcon(resourcePath("CSAN.ico")))
    # method = {
    #     "conditions": getDataframe("Conditions").query("active == 1").drop(["condition_id", "active"], axis=1),
    #     "elements": getDataframe("Elements"),
    #     "calibrations": [],
    # }
    window = CalibrationExplorer(calibration=calibration)
    # # connectServerAndGUI('127.0.0.1', 16000, window, app)
    # for root, _, files in os.walk(resourcePath("fonts")):
    #     for file in files:
    #         path = os.path.join(root, file)
    #         QtGui.QFontDatabase.addApplicationFont(path)
    with open(resourcePath("style.qss")) as f:
        _style = f.read()
        app.setStyleSheet(_style)
    window.show()
    sys.exit(app.exec())
