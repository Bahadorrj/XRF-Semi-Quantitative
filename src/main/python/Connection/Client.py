import socket

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 16000  # The port used by the server


def getCount():
    with open(r"F:\CSAN\Master\Additional\Test -Int\test.txt", 'r') as file:
        out = ""
        line = file.readline()  # read line
        while line:
            out += line.strip() + "\\"
            line = file.readline()
        return out


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"-als")
    s.sendall(("test1.cal\\" + getCount() + "-stp").encode("utf-8"))
    s.sendall(b"-opn")
    s.sendall(b"-als")
    s.sendall(("test2.cal\\" + getCount() + "-stp").encode("utf-8"))
    inp = input("new command: ")
    s.sendall(inp.encode("utf-8"))

