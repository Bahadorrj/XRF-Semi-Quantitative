from json import dumps, loads
import logging
import socket
import threading

from PyQt6 import QtCore, QtWidgets

from src.utils.database import getDatabase, getDataframe
from src.utils.datatypes import Analyse, Method
from src.utils.paths import resourcePath
from src.views.windows.plotwindow import PlotWindow


class GuiHandler(QtCore.QObject):
    openGuiSignal = QtCore.pyqtSignal()
    hideGuiSignal = QtCore.pyqtSignal()
    addAnalyseSignal = QtCore.pyqtSignal(Analyse)
    exit = QtCore.pyqtSignal()

    def __init__(self, window: PlotWindow):
        super().__init__()
        self.window = window
        self.openGuiSignal.connect(self.openGui)
        self.hideGuiSignal.connect(self.hideGui)
        self.addAnalyseSignal.connect(self.window.addAnalyse)
        self.exit.connect(self.closeGui)

    def openGui(self):
        self.window.show()
        logging.info("GUI opened")

    def hideGui(self):
        self.window.hide()
        logging.info("GUI hide")

    def closeGui(self):
        if not self.window.isHidden():
            self.window.close()
        logging.info("GUI closed")


class ClientHandler(QtCore.QObject):
    dataLock = threading.Lock()
    commandLock = threading.Lock()

    def __init__(
        self, conn: socket.socket, guiHandler: GuiHandler, app: QtWidgets.QApplication
    ):
        super().__init__()
        self.conn = conn
        self.guiHandler = guiHandler
        self.app = app

    def handleClient(self):
        try:
            while True:
                with self.commandLock:
                    logging.info("Listening for command...")
                    command = self.conn.recv(4).decode("utf-8")
                    logging.info(f"Received command: {command}")
                    self.processCommand(command)
                    if command == "-ext":
                        break
                if not command:
                    break
        except Exception as e:
            logging.error(f"Error handling client: {e}", exc_info=True)
        finally:
            self.conn.close()  # Ensure connection is closed

    def processCommand(self, command):
        if command == "-opn":
            self.guiHandler.openGuiSignal.emit()
        elif command == "-cls":
            self.guiHandler.hideGuiSignal.emit()
        elif command == "-chk":
            self.sendServerStatus()
        elif command == "-als":
            threading.Thread(target=self.addAnalyse).start()
        elif command == "-ext":
            self.exitApplication()
        elif command == "-met":
            self.handleMethodRequest()
        else:
            logging.warning(
                f"There is not any action related to {command}. "
                f"make sure you are sending the correct command."
            )

    def sendServerStatus(self):
        message = f"Server is running on {self.conn.getsockname()}"
        logging.info(message)
        self.conn.sendall(message.encode("utf-8"))

    def exitApplication(self):
        self.guiHandler.exit.emit()
        getDatabase().closeConnection()
        logging.info("Database closed")
        self.conn.close()
        logging.info("Connection closed")
        self.app.exit()
        logging.info("Application exit")

    def handleMethodRequest(self):
        logging.info("Requesting method name...")
        methodName = self.conn.recv(255).decode("utf-8")
        message = f"Received method: {methodName}"
        logging.info(message)
        if (
            df := getDataframe("Methods").query(f"filename == '{methodName}'")
        ).empty is False:
            filename = df["filename"].values[0]
            method = Method.fromATXMFile(resourcePath(f"methods/{filename}.atxm"))
            conditions = {
                row[1]: dict(zip(method.conditions.columns[2:], row[2:]))
                for row in method.conditions.itertuples(index=False)
            }
            calibrationIds = method.calibrations["calibration_id"].values.tolist()
            obj = {
                "conditions": conditions,
                "calibration_ids": calibrationIds,
            }
            self.conn.sendall(dumps(obj).encode("utf-8"))

    def addAnalyse(self):
        with self.dataLock:
            analyse = Analyse.fromSocket(self.conn)
            self.guiHandler.addAnalyseSignal.emit(analyse)
