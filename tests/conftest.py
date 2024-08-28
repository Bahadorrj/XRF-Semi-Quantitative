# conftest.py
import pytest

@pytest.fixture(scope="session")
def shared_tmp_path(tmp_path_factory):
    # Create a shared temporary directory for the whole test session
    shared_path = tmp_path_factory.mktemp("shared_data")
    
    # You can also create files or subdirectories within this path
    shared_file = shared_path / "shared_example.txt"
    shared_file.write_text("Initial shared content")

    # Return the path
    return shared_path
