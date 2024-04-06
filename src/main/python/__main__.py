import logging
import socket
import sys
import threading
import unittest

from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow
from numpy import ndarray, uint32

from python.Controllers.PlotWindowController import PlotWindowController
from python.Logic.Sqlite import DatabaseConnection, getValue
from python.Types.ConditionClass import Condition
from python.Types.FileClass import File
from python.Views.PlotWindow import Window
from src.test import TestSqlite


class GuiHandler(QObject):
    openGuiSignal = pyqtSignal()
    closeGuiSignal = pyqtSignal()
    addFileSignal = pyqtSignal(str)
    exit = pyqtSignal()

    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        self.openGuiSignal.connect(self.openGui)
        self.closeGuiSignal.connect(self.hideGui)
        self.addFileSignal.connect(self.addFile)
        self.exit.connect(self.exitApplication)

    def openGui(self):
        self.mainWindow.showMaximized()
        logging.info("GUI opened")

    def hideGui(self):
        self.mainWindow.hide()

    def exitApplication(self):
        self.mainWindow.close()
        QApplication.quit()
        DatabaseConnection.getInstance(":fundamentals.db").closeConnection()
        logging.info("Application exit")

    def addFile(self, data: str):
        seperated = data.split('\\')
        pointer = 0
        sampleFileName = seperated[pointer]
        pointer += 1
        new = File()
        new.name = sampleFileName
        while seperated[pointer] != "-stp":
            conditionName = seperated[pointer]
            pointer += 1
            database = DatabaseConnection.getInstance(":fundamentals.db")
            conditionID = getValue(database, "conditions", where=f"name = '{conditionName}'")[0]
            condition = Condition(conditionID)
            counts = ndarray(2048, dtype=uint32)
            for i in range(2048):
                counts[i] = seperated[pointer]
                pointer += 1
            new.conditions.append(condition)
            new.counts.append(counts)
        self.mainWindow.createFileItem(new)
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
                    self.guiHandler.closeGuiSignal.emit()
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
                    break
                else:
                    logging.warning(f"There is not any action related to {command}. "
                                    f"make sure you are sending the correct command.")
        except Exception as e:
            logging.error(f"Error handling client: {e}", exc_info=True)
        finally:
            self.conn.close()  # Ensure connection is closed


def connectServerAndGUI(host, port, mainWindow: QMainWindow):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(1)
        logging.info(f"Server listening on {host}:{port}")
        conn, addr = s.accept()
        logging.info(f"Connected to {addr}")
        guiHandler = GuiHandler(mainWindow)
        clientHandler = ClientHandler(conn, guiHandler)
        clientThread = threading.Thread(target=clientHandler.handleClient)
        clientThread.start()


def main():
    logging.basicConfig(level=logging.DEBUG)
    testResult = unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromModule(TestSqlite))
    if testResult.wasSuccessful():
        logging.info("Test Successful!")
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(":CSAN.ico"))
        size = app.primaryScreen().size()
        mainWindow = Window(size)
        PlotWindowController(mainWindow)
        # connectServerAndGUI('127.0.0.1', 16000, mainWindow)
        mainWindow.showMaximized()
        sys.exit(app.exec())
    else:
        logging.info("No valid fundamentals.db was found. "
                     "Please make sure that you have the proper database in src/main/db path.")
