import sys
import socket
import threading
from PyQt6 import QtWidgets, QtGui, QtCore
from numpy import ndarray, uint32

from src.main.python.Types.FileClass import PacketFile
from src.main.python.Types.ConditionClass import Condition
from src.main.python.Controllers.PlotWindowController import PlotWindowController
from src.main.python.Views.Icons import ICONS
from src.main.python.Views.PlotWindow import Window
from src.main.python.Logic.Sqlite import getValue

HOST = "127.0.0.1"
PORT = 16000

app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon(ICONS["CSAN"]))
size = app.primaryScreen().size()
mainWindow = Window(size)
PlotWindowController(mainWindow)


def openGui():
    mainWindow.show()
    app.exec()


def closeGui():
    mainWindow.close()


def addFile(data):
    pointer = 0
    sampleFileName = data[pointer]
    pointer += 1
    new = PacketFile(sampleFileName)
    while data[pointer] != "-stp":
        conditionName = data[pointer]
        pointer += 1
        conditionID = getValue("fundamentals", "conditions", where=f"name = '{conditionName}'")[0]
        condition = Condition(conditionID)
        counts = ndarray(2048, dtype=uint32)
        for i in range(2048):
            counts[i] = data[pointer]
            pointer += 1
        new.conditions.append(condition)
        new.counts.append(counts)
    mainWindow.createFile(new)


class ClientHandler(QtCore.QObject):
    openGuiSignal = QtCore.pyqtSignal()
    closeGuiSignal = QtCore.pyqtSignal()
    addFileSignal = QtCore.pyqtSignal(list)

    def handleClient(self, connection):
        while True:
            command = connection.recv(4).decode("utf-8")
            if not command:
                return
            if command == "-opn":
                self.openGuiSignal.emit()
            elif command == "-cls":
                self.closeGuiSignal.emit()
            elif command == "-als":
                data = connection.recv(2048 * 128).decode("utf-8").split("\\")
                self.addFileSignal.emit(data)


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    print(f"Connected by: {addr}")

    clientHandler = ClientHandler()
    clientThread = threading.Thread(target=clientHandler.handleClient, args=(conn,))
    clientThread.start()

    clientHandler.openGuiSignal.connect(openGui)
    clientHandler.closeGuiSignal.connect(closeGui)
    clientHandler.addFileSignal.connect(addFile)
    clientHandler.handleClient(conn)
