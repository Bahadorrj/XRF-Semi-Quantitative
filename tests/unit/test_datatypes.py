import pytest
import socket
import json
import threading

import numpy as np

from src.utils import datatypes


@pytest.fixture
def encryption_patches(mocker):
    return {
        "mock_encryptText": mocker.patch(
            "src.utils.encryption.encryptText", return_value=b"encrypted_text"
        ),
        "mock_loadKey": mocker.patch(
            "src.utils.encryption.loadKey", return_value=b"key"
        ),
        "mock_open": mocker.patch("builtins.open", new_callable=mocker.MagicMock),
    }


@pytest.fixture
def calibration_patches(mocker):
    yield {
        "mock_calculateCoefficients": mocker.patch(
            "src.utils.datatypes.Calibration.calculateCoefficients", return_value=None
        ),
        "mock_calculateInterferences": mocker.patch(
            "src.utils.datatypes.Calibration.calculateInterferences", return_value=None
        ),
    }


@pytest.fixture
def mock_analyse_data():
    return datatypes.AnalyseData(1, np.arange(0, 2048, 1), np.full(2048, 1))


@pytest.fixture
def mock_analyse(mock_analyse_data):
    # Load the Analyse object from the .txt file for all tests in the class
    return datatypes.Analyse(
        "mock_analyse.txt",
        [mock_analyse_data],
        {},
    )


@pytest.fixture
def mock_socket():
    """Creates a pair of connected sockets (server, client)"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 16000))  # Bind to a free port
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


# testing AnalyseData
class TestAnalyseData:
    def test_fromHashableDict(self, mock_analyse_data):
        hashableDict = {
            "conditionId": 1,
            "x": list(range(2048)),
            "y": [1 for _ in range(2048)],
        }
        assert mock_analyse_data == datatypes.AnalyseData.fromHashableDict(hashableDict)


# testing Analyse
class TestAnalyse:
    def test_post_init(self, mock_analyse):
        # Test the initialization of the Analyse object
        assert mock_analyse.filename == "mock_analyse"
        assert mock_analyse.extension == "txt"

    def test_getDataByConditionId(self, mock_analyse):
        # Test retrieving data by condition ID
        assert mock_analyse.getDataByConditionId(1).conditionId == 1

    def test_copy(self, mock_analyse):
        # Test copying the Analyse object
        assert mock_analyse == mock_analyse.copy()
        assert mock_analyse is not mock_analyse.copy()

    def test_saveTo(self, encryption_patches, mock_analyse):
        # Test saving the Analyse object to a .atx file
        # Act
        mock_analyse.saveTo("test.atx")
        # Assert
        encryption_patches["mock_open"].assert_called_once_with("test.atx", "wb")
        mock_file_handle = encryption_patches[
            "mock_open"
        ].return_value.__enter__.return_value
        mock_file_handle.write.assert_called_once_with(b"encrypted_text\n")

    def test_fromSocket(self, mock_socket, mock_analyse):
        server_conn, client_socket = mock_socket

        # Convert the Analyse object to a hashable dict, then to a JSON string
        analyse_dict = mock_analyse.toHashableDict()
        json_data = f"{json.dumps(analyse_dict)}-stp"

        # Client sends data
        def client_send_data():
            client_socket.sendall(json_data.encode("utf-8"))

        client_thread = threading.Thread(target=client_send_data)
        client_thread.start()

        # Server uses fromSocket to receive and process the data
        received_analyse = datatypes.Analyse.fromSocket(server_conn)

        # Ensure that the received Analyse object is the same as the sent one
        assert received_analyse == mock_analyse

        # Ensure the client thread finishes
        client_thread.join()


# testing Calibration
class TestCalibration:
    @pytest.mark.parametrize(
        "calibrationId, filename, element, concentration, state, expected_status",
        [
            (1, "calib1", "Fe", 10.0, 0, "Proceed to acquisition"),
            (2, "calib2", "Cu", 20.0, 1, "Initial state"),
            (3, "calib3", "Fe", 30.0, 2, "Edited by user"),
        ],
        ids=["status_0", "status_1", "status_2"],
    )
    def test_status(
        self,
        calibration_patches,
        calibrationId,
        filename,
        element,
        concentration,
        state,
        expected_status,
        mock_analyse,
        mock_lines,
    ):
        # Arrange
        calibration = datatypes.Calibration(
            calibrationId,
            filename,
            element,
            concentration,
            state,
            mock_analyse,
            mock_lines,
        )

        # Act
        status = calibration.status()

        # Assert
        assert status == expected_status
        calibration_patches["mock_calculateCoefficients"].assert_called_once()
        calibration_patches["mock_calculateInterferences"].assert_called_once()

    @pytest.mark.parametrize(
        "calibrationId, filename, element, concentration, state",
        [
            (1, "calib1", "Fe", 10.0, 0),
            (2, "calib2", "Cu", 20.0, 1),
        ],
        ids=["copy_1", "copy_2"],
    )
    def test_copy(
        self,
        calibration_patches,
        calibrationId,
        filename,
        element,
        concentration,
        state,
        mock_analyse,
        mock_lines,
    ):
        # Arrange
        calibration = datatypes.Calibration(
            calibrationId,
            filename,
            element,
            concentration,
            state,
            mock_analyse,
            mock_lines,
        )

        # Act
        copied_calibration = calibration.copy()

        # Assert
        assert copied_calibration == calibration
        assert copied_calibration is not calibration

    @pytest.mark.parametrize(
        "calibrationId, filename, element, concentration, state",
        [
            (1, "calib1", "Fe", 10.0, 0),
            (2, "calib2", "Cu", 20.0, 1),
        ],
        ids=["save_1", "save_2"],
    )
    def test_save(
        self,
        calibration_patches,
        encryption_patches,
        calibrationId,
        filename,
        element,
        concentration,
        state,
        mock_analyse,
        mock_lines,
    ):
        # Arrange
        calibration = datatypes.Calibration(
            calibrationId,
            filename,
            element,
            concentration,
            state,
            mock_analyse,
            mock_lines,
        )

        # Act
        calibration.save()

        # Assert
        encryption_patches["mock_open"].assert_called_once_with(
            f"calibrations/{filename}.atxc", "wb"
        )
        mock_file_handle = encryption_patches[
            "mock_open"
        ].return_value.__enter__.return_value
        mock_file_handle.write.assert_called_once_with(b"encrypted_text\n")


# testing Method
class TestMethod:

    @pytest.mark.parametrize(
        "methodId, filename, description, state, expected_status",
        [
            (1, "method1", "Test method 1", 0, "Initial state"),
            (2, "method2", "Test method 2", 1, "Edited"),
        ],
        ids=["status_0", "status_1"],
    )
    def test_status(
        self,
        methodId,
        filename,
        description,
        state,
        expected_status,
        mock_calibrations,
        mock_conditions,
        mock_elements,
    ):
        # Arrange
        method = datatypes.Method(
            methodId,
            filename,
            description,
            state,
            mock_calibrations,
            mock_conditions,
            mock_elements,
        )

        # Act
        status = method.status()

        # Assert
        assert status == expected_status

    @pytest.mark.parametrize(
        "methodId, filename, description, state",
        [
            (1, "method1", "Test method 1", 0),
            (2, "method2", "Test method 2", 1),
        ],
        ids=["copy_1", "copy_2"],
    )
    def test_copy(
        self,
        methodId,
        filename,
        description,
        state,
        mock_calibrations,
        mock_conditions,
        mock_elements,
    ):
        # Arrange
        method = datatypes.Method(
            methodId,
            filename,
            description,
            state,
            mock_calibrations,
            mock_conditions,
            mock_elements,
        )

        # Act
        copied_method = method.copy()

        # Assert
        assert copied_method == method
        assert copied_method is not method

    @pytest.mark.parametrize(
        "methodId, filename, description, state",
        [
            (1, "method1", "Test method 1", 0),
            (2, "method2", "Test method 2", 1),
        ],
        ids=["save_1", "save_2"],
    )
    def test_save(
        self,
        encryption_patches,
        methodId,
        filename,
        description,
        state,
        mock_calibrations,
        mock_conditions,
        mock_elements,
    ):
        # Arrange
        method = datatypes.Method(
            methodId,
            filename,
            description,
            state,
            mock_calibrations,
            mock_conditions,
            mock_elements,
        )

        # Act
        method.save()

        # Assert
        encryption_patches["mock_open"].assert_called_once_with(
            f"methods/{filename}.atxm", "wb"
        )
        mock_file_handle = encryption_patches[
            "mock_open"
        ].return_value.__enter__.return_value
        mock_file_handle.write.assert_called_once_with(b"encrypted_text\n")
