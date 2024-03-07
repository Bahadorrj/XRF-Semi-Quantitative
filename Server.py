import logging
import socket

HOST = "127.0.0.1"
PORT = 16000


def writeToFile(dataToWrite, filename):
    with open(filename, "wb") as f:
        f.write(dataToWrite)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        logging.info(f"Server listening on {HOST}:{PORT}")
        conn, addr = s.accept()
        logging.info(f"Connected to {addr}")
        while True:
            command = conn.recv(4)
            if not command:
                break
            logging.info(f"Received command: {command}")
            data = conn.recv(2048 * 128)
            if not data:
                break
            logging.info(f"Received data: {data}")
