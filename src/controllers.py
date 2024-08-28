import logging
import socket
import threading

from PyQt6 import QtCore, QtWidgets

from src.utils.database import getDatabase
from src.utils.datatypes import Analyse
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
        self.addAnalyseSignal.connect(self.addFile)
        self.exit.connect(self.exitApplication)

    def openGui(self):
        self.window.show()
        logging.info("GUI opened")

    def hideGui(self):
        self.window.hide()

    def exitApplication(self):
        getDatabase(resourcePath("fundamentals.db")).closeConnection()
        if not self.window.isHidden():
            self.window.close()
        logging.info("Application exit")

    def addFile(self, analyse: Analyse):
        self.window.addAnalyse(analyse)


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
                    command = self.conn.recv(4).decode("utf-8")
                    logging.info(f"Received command: {command}")
                if not command:
                    break
                if command == "-opn":
                    self.guiHandler.openGuiSignal.emit()
                elif command == "-cls":
                    self.guiHandler.hideGuiSignal.emit()
                elif command == "-chk":
                    massage = f"Server is running on {self.conn.getsockname()}"
                    logging.info(massage)
                    self.conn.sendall(massage.encode("utf-8"))
                elif command == "-als":
                    threading.Thread(target=self.addAnalyse).start()
                elif command == "-ext":
                    # exit is sent when the VB exe closes
                    self.guiHandler.exit.emit()
                    self.app.exit()
                    break
                else:
                    logging.warning(
                        f"There is not any action related to {command}. "
                        f"make sure you are sending the correct command."
                    )
        except Exception as e:
            logging.error(f"Error handling client: {e}", exc_info=True)
        finally:
            self.conn.close()  # Ensure connection is closed

    def addAnalyse(self):
        with self.dataLock:
            analyse = Analyse.fromSocket(self.conn)
            self.guiHandler.addAnalyseSignal.emit(analyse)
