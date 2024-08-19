import logging
import os
import sys

from PyQt6 import QtWidgets, QtGui

from python.utils import datatypes
from python.utils.database import getDataframe
from python.utils.paths import resourcePath
# from python.views.plotwindow import PlotWindow
from python.views.methodexplorer.explorer import MethodExplorer


# from python.controllers import GuiHandler, ClientHandler


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
    arg = sys.argv
    app = QtWidgets.QApplication(arg)
    app.setWindowIcon(QtGui.QIcon(resourcePath("CSAN.ico")))
    calibration = datatypes.Calibration(
        datatypes.Analyse.fromTXTFile(r"F:\CSAN\XRF-Semi-Quantitative\Additional\Pure samples\8 Mehr\Au.txt"),
        {},
        {"Au": 100},
        getDataframe("Lines").copy()
    )
    method = datatypes.Method(
        getDataframe("Conditions").query("active == 1").drop(["condition_id", "active"], axis=1),
        getDataframe("Elements").copy(),
        [],
    )
    # window = CalibrationExplorer(calibration=calibration)
    window = MethodExplorer(method=method)
    # # connectServerAndGUI('127.0.0.1', 16000, window, app)
    for root, _, files in os.walk(resourcePath("fonts")):
        for file in files:
            path = os.path.join(root, file)
            QtGui.QFontDatabase.addApplicationFont(path)
    with open(resourcePath("style.qss")) as f:
        _style = f.read()
        app.setStyleSheet(_style)
    window.show()
    sys.exit(app.exec())
