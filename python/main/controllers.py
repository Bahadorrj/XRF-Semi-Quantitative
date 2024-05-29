import logging
import threading

from PyQt6 import QtCore

from python.main.utils.database import getDatabase
from python.main.utils.paths import resource_path


class GuiHandler(QtCore.QObject):
    openGuiSignal = QtCore.pyqtSignal()
    hideGuiSignal = QtCore.pyqtSignal()
    addFileSignal = QtCore.pyqtSignal(str)
    exit = QtCore.pyqtSignal()

    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        self.openGuiSignal.connect(self.openGui)
        self.hideGuiSignal.connect(self.hideGui)
        self.addFileSignal.connect(self.addFile)
        self.exit.connect(self.exitApplication)

    def openGui(self):
        self.mainWindow.showMaximized()
        logging.info("GUI opened")

    def hideGui(self):
        self.mainWindow.hide()

    def exitApplication(self):
        getDatabase(resource_path('fundamentals.db')).closeConnection()
        if not self.mainWindow.isHidden():
            self.mainWindow.close()
        logging.info("Application exit")

    def addFile(self, data: str):
        pass


class ClientHandler(QtCore.QObject):
    dataLock = threading.Lock()
    commandLock = threading.Lock()

    def __init__(self, conn, guiHandler, app):
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
                    with self.dataLock:
                        data = ""
                        while True:
                            data += self.conn.recv(10).decode("utf-8")
                            if data[-4:] == "-stp":
                                break
                        if data:
                            self.guiHandler.addFileSignal.emit(data)
                elif command == "-ext":
                    # exit is sent when the VB exe closes
                    self.guiHandler.exit.emit()
                    self.app.exit()
                    break
                else:
                    logging.warning(f"There is not any action related to {command}. "
                                    f"make sure you are sending the correct command.")
        except Exception as e:
            logging.error(f"Error handling client: {e}", exc_info=True)
        finally:
            self.conn.close()  # Ensure connection is closed
