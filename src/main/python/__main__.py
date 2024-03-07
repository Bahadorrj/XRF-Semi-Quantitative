import logging
import socket
import sys
import threading

from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from numpy import ndarray, uint32

from src.main.python.Controllers.PlotWindowController import PlotWindowController
from src.main.python.Logic.Sqlite import DatabaseConnection, getValue
from src.main.python.Types.ConditionClass import Condition
from src.main.python.Types.FileClass import File
from src.main.python.Views.PlotWindow import Window
from src.main.python.dependencies import ICONS, DATABASES

HOST = "0.0.0.0"
PORT = 16000


class GuiHandler(QObject):
    openGuiSignal = pyqtSignal()
    closeAllSignal = pyqtSignal()
    addFileSignal = pyqtSignal(str)

    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        self.openGuiSignal.connect(self.openGui)
        self.closeAllSignal.connect(self.closeAll)
        self.addFileSignal.connect(self.addFile)

    def openGui(self):
        self.mainWindow.showMaximized()
        logging.info("GUI opened")

    def closeAll(self):
        self.mainWindow.close()
        QApplication.quit()
        DatabaseConnection.getInstance(DATABASES['fundamentals']).closeConnection()
        logging.info("Application exit")

    def addFile(self, data: str):
        seperated = data.split('\\')
        pointer = 0
        sampleFileName = seperated[pointer]
        pointer += 1
        new = File(sampleFileName)
        while seperated[pointer] != "-stp":
            conditionName = seperated[pointer]
            pointer += 1
            database = DatabaseConnection.getInstance(DATABASES['fundamentals'])
            conditionID = getValue(database, "conditions", where=f"name = '{conditionName}'")[0]
            condition = Condition(conditionID)
            counts = ndarray(2048, dtype=uint32)
            for i in range(2048):
                counts[i] = seperated[pointer]
                pointer += 1
            new.conditions.append(condition)
            new.counts.append(counts)
        self.mainWindow.createFile(new)
        logging.info(f"Added file: {new}")


class ClientHandler(QObject):
    dataLock = threading.Lock()
    commandLock = threading.Lock()

    def __init__(self, conn, guiHandler):
        super().__init__()
        self.conn = conn
        self.guiHandler = guiHandler

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
                    # close is sent when the VB exe closes
                    self.guiHandler.closeAllSignal.emit()
                    break
                elif command == "-als":
                    with self.dataLock:
                        data = self.conn.recv(2048 * 128).decode("utf-8")
                        print(data)
                        # self.guiHandler.addFileSignal.emit(data)
                else:
                    logging.warning(f"There is not any action related to {command}. "
                                    f"make sure you are sending the correct command.")
        except Exception as e:
            logging.error(f"Error handling client: {e}", exc_info=True)
        finally:
            self.conn.close()  # Ensure connection is closed


def main():
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICONS["CSAN"]))
    size = app.primaryScreen().size()
    mainWindow = Window(size)
    PlotWindowController(mainWindow)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        logging.info(f"Server listening on {HOST}:{PORT}")
        conn, addr = s.accept()
        logging.info(f"Connected to {addr}")
        guiHandler = GuiHandler(mainWindow)
        clientHandler = ClientHandler(conn, guiHandler)
        clientThread = threading.Thread(target=clientHandler.handleClient)
        clientThread.start()
    sys.exit(app.exec())
