import os
import pytest
import socket
import json
import threading

import numpy as np

from src.utils import datatypes

# testing AnalyseData
class TestAnalyseData:
    def test_fromHashableDict(self):
        hashableDict = {
            "conditionId": 1,
            "x": list(range(2048)),
            "y": [1 for _ in range(2048)],
        }
        analyseData = datatypes.AnalyseData(
            1,
            np.arange(0, 2048, 1),
            np.full(2048, 1)
        )
        assert analyseData == datatypes.AnalyseData.fromHashableDict(hashableDict)

# testing Analayse
@pytest.fixture(scope="class")
def example_Analyse():
    # Load the Analyse object from the .txt file for all tests in the class
    return datatypes.Analyse.fromTXTFile("tests/Au.txt")

@pytest.fixture(scope="class")
def shared_tmp_path(tmp_path_factory, example_Analyse):
    # Create a shared temporary directory for the whole class
    shared_path = tmp_path_factory.mktemp("shared_data")
    
    # Create and save the .atx file during the setup
    tmp_file = shared_path / "test.atx"
    example_Analyse.saveTo(str(tmp_file))

    # Return the path to be used in tests
    return shared_path

@pytest.fixture
def socket_pair():
    """Creates a pair of connected sockets (server, client)"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 16000))  # Bind to a free port
    server_socket.listen(1)

    # Get the server address and connect the client
    server_address = server_socket.getsockname()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(server_address)

    server_conn, _ = server_socket.accept()

    yield server_conn, client_socket

    # Close sockets after test
    server_conn.close()
    client_socket.close()
    server_socket.close()


class TestAnalyse:
    def test_post_init(self, example_Analyse):
        # Test the initialization of the Analyse object
        assert example_Analyse.filename == "Au"
        assert example_Analyse.extension == "txt"

    def test_getDataByConditionId(self, example_Analyse):
        # Test retrieving data by condition ID
        assert example_Analyse.getDataByConditionId(1).conditionId == 1

    def test_copy(self, example_Analyse):
        # Test copying the Analyse object
        assert example_Analyse == example_Analyse.copy()

    def test_save(self, shared_tmp_path):
        # Test if the saved file exists
        tmp_file = shared_tmp_path / "test.atx"
        assert os.path.exists(tmp_file)

    def test_fromATXFile(self, example_Analyse, shared_tmp_path):
        # Test loading the Analyse object from the .atx file
        tmp_file = shared_tmp_path / "test.atx"
        loaded_analyse = datatypes.Analyse.fromATXFile(tmp_file)
        assert loaded_analyse == example_Analyse\
            
    def test_fromSocket(self, socket_pair, example_Analyse):
        server_conn, client_socket = socket_pair

        # Convert the Analyse object to a hashable dict, then to a JSON string
        analyse_dict = example_Analyse.toHashableDict()
        json_data = f"{json.dumps(analyse_dict)}-stp"

        # Client sends data
        def client_send_data():
            client_socket.sendall(json_data.encode('utf-8'))

        client_thread = threading.Thread(target=client_send_data)
        client_thread.start()

        # Server uses fromSocket to receive and process the data
        received_analyse = datatypes.Analyse.fromSocket(server_conn)

        # Ensure that the received Analyse object is the same as the sent one
        assert received_analyse == example_Analyse

        # Ensure the client thread finishes
        client_thread.join()