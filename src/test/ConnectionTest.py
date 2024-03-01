import unittest
import socket


class TestSocketConnection(unittest.TestCase):
    def test_socket_connection(self):
        host = 'localhost'
        port = 16000

        # Attempt to connect to the server
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
        except Exception as e:
            self.fail(f"Failed to connect to {host}:{port}: {e}")

        # If connection was successful, close the socket
        s.close()


class TestSocketSending(unittest.TestCase):
    def setUp(self):
        self.host = 'localhost'
        self.port = 16000

    def test_socket_sending(self):
        # Define the message to be sent
        message = "Hello, server!"

        # Connect to the server
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
        except Exception as e:
            self.fail(f"Failed to connect to {self.host}:{self.port}: {e}")

        # Send the message
        try:
            s.sendall(message.encode())
        except Exception as e:
            self.fail(f"Failed to send message: {e}")

        # Close the socket
        s.close()


if __name__ == '__main__':
    # run a server on local host with port 16000 before testing
    unittest.main()
