import socket

HOST = "127.0.0.1"
PORT = 16000


def getData():
    with open(r"F:\CSAN\Master\Additional\Test -Int\test.txt", 'r') as f:
        data = []
        line = f.readline()  # read line
        while line:
            data.append(line.strip())
            line = f.readline()
    return data

def sendMethodOne():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.send(b'-als')
        s.sendall(b'test')
        with open(r"F:\CSAN\Master\Additional\Test -Int\test.txt", 'r') as f:
            line = f.readline()  # read line
            while line:
                s.send(f"{line.strip()}\\".encode('utf-8'))
                line = f.readline()
        s.send(b'-stp')

def sendMethodTwo():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.send(b'-als')
        s.sendall(b'test')
        data = getData()
        for d in data:
            s.send(f"{d}\\".encode('utf-8'))
        s.send(b'-stp')

def sendMethodThree():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        out = "-als"
        out += "test\\"
        data = getData()
        for d in data:
            out += f"{d}\\"
        out += "-stp"
        s.send(out.encode('utf-8'))


if __name__ == '__main__':
    # sendMethodOne()
    # sendMethodTwo()
    sendMethodThree()
