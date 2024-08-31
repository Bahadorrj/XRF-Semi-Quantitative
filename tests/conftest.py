import pytest
import pandas as pd


@pytest.fixture(scope="session")
def shared_tmp_path(tmp_path_factory):
    # Create a shared temporary directory for the whole test session
    shared_path = tmp_path_factory.mktemp("shared_data")

    # You can also create files or subdirectories within this path
    shared_file = shared_path / "shared_example.txt"
    shared_file.write_text("Initial shared content")

    # Return the path
    return shared_path


@pytest.fixture(scope="session")
def mock_lines():
    # Create a sample dataframe similar to what getDataframe("Lines") would return
    return pd.DataFrame(
        {
            "line_id": [1, 2],
            "element_id": [1, 2],
            "atomic_number": [3, 4],
            "symbol": ["Li", "Be"],
            "name": ["Lithium", "Beryllium"],
            "radiationType": ["Ka", "Ka"],
            "kiloelectron_volt": [0.0543, 0.1085],
            "low_kiloelectron_volt": [-0.2457, 10.1915],
            "high_kiloelectron_volt": [0.3543, 0.4085],
            "active": [1, 1],
            "condition_id": [1, 1],
        }
    )


@pytest.fixture(scope="session")
def mock_calibrations():
    # Create a sample dataframe similar to what getDataframe("Calibrations") would return
    return pd.DataFrame(
        {
            "calibration_id": [1, 2],
            "filename": ["Cal01", "Cal02"],
            "element": ["Fe", "Cu"],
            "concentration": [10.0, 20.0],
            "state": [0, 1],
        }
    )


@pytest.fixture(scope="session")
def mock_conditions():
    # Create a sample dataframe similar to what getDataframe("Conditions") would return
    return pd.DataFrame(
        {
            "condition_id": [1, 2],
            "name": ["Condition 1", "Condition 2"],
            "kilovolt": [8, 10],
            "milliampere": [0.2, 0.3],
            "time": [120, 120],
            "rotation": [1, 1],
            "environment": ["Vacuum", "Vacuum"],
            "filter": [1, 1],
            "mask": [3, 3],
            "active": [1, 1],
        }
    )


@pytest.fixture(scope="session")
def mock_elements():
    # Create a sample dataframe similar to what getDataframe("Elements") would return
    return pd.DataFrame(
        {
            "element_id": [1, 2],
            "atomic_number": [3, 4],
            "symbol": ["Li", "Be"],
            "name": ["Lithium", "Beryllium"],
            "active": [1, 1],
            "condition_id": [7, 8],
        }
    )


@pytest.fixture(scope="session")
def mock_methods():
    return pd.DataFrame(
        {
            "method_id": [1],
            "filename": ["method_1"],
            "description": ["none"],
            "state": [0],
        }
    )
