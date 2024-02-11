import socket
import struct

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 16000  # Port to listen on (non-privileged ports are > 1023)

exe_path = "XRF.exe"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(2048 * 4)  # Assuming each integer is 4 bytes
            if not data:
                break
            array = struct.unpack('2048i', data)  # Convert byte stream back to array of integers
            print(array)
