# echo-Client.py

import socket
import struct

import numpy as np


def initFile(path):
    """
    this function opens a .txt file and initialize an array with the first condition counts.
    :param path: path of the .txt file
    :return: an array of integers with 32-bit integer values
    """
    with open(path, 'r') as file:
        line = file.readline()  # read line
        counts = np.zeros(2048, dtype=np.int32)
        index = 0
        while line:
            try:
                count = int(line.strip())
                counts[index] = count
                index += 1
                if index == 2048:
                    return counts
            except ValueError:
                pass
            line = file.readline()
        return None


# TCP socket initialization
HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 16000  # The port used by the server
array = initFile("S.txt")
data = struct.pack('2048i', *array)  # Convert array to bytes

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(data)
