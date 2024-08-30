import pytest

import sqlite3
import pandas as pd
from src.utils.database import Database


# Mocking the path to the database for testing purposes
@pytest.fixture
def mock_db_path(tmp_path):
    return tmp_path / "test_db.sqlite"


@pytest.fixture
def setup_database(mock_db_path):
    # Setup a temporary SQLite database for testing
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE Lines (id INTEGER PRIMARY KEY, name TEXT)")
    cursor.execute("INSERT INTO Lines (name) VALUES ('Line1')")
    conn.commit()
    yield mock_db_path
    conn.close()


@pytest.fixture
def database_instance(setup_database):
    # Return an instance of the Database class connected to the temporary database
    return Database(str(setup_database))


class TestDatabase:

    def test_connection_success(self, setup_database):
        # Test successful connection to the database
        db = Database(str(setup_database))
        assert db.conn is not None
        assert db.path == str(setup_database)

    def test_connection_failure(self, mocker):
        # Mock sqlite3.connect to raise an OperationalError
        with mocker.patch("sqlite3.connect", side_effect=sqlite3.OperationalError):
            db = Database("invalid_path")
            assert db.conn is None

    def test_execute_query(self, database_instance):
        # Test executing a query without values
        query = (
            "CREATE TABLE IF NOT EXISTS TestTable (id INTEGER PRIMARY KEY, name TEXT)"
        )
        cursor = database_instance.executeQuery(query)
        assert cursor is not None

    def test_execute_query_with_values(self, database_instance):
        # Test executing a query with values
        query = "INSERT INTO Lines (name) VALUES (?)"
        cursor = database_instance.executeQuery(query, ["Line2"])
        assert cursor is not None

    def test_fetch_data(self, database_instance):
        # Test fetching data from the database
        query = "SELECT * FROM Lines"
        rows = database_instance.fetchData(query)
        assert len(rows) == 1
        assert rows[0][1] == "Line1"

    def test_fetch_data_with_values(self, database_instance):
        # Test fetching data from the database with values
        query = "SELECT * FROM Lines WHERE name = ?"
        rows = database_instance.fetchData(query, ["Line1"])
        assert len(rows) == 1
        assert rows[0][1] == "Line1"

    def test_dataframe(self, database_instance):
        # Test fetching data as a pandas DataFrame
        df = database_instance.dataframe("SELECT * FROM Lines")
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert df.iloc[0]["name"] == "Line1"

    def test_close_connection(self, database_instance):
        # Test closing the database connection
        query = "SELECT * FROM Lines WHERE name = ?"
        assert database_instance.fetchData(query, ["Line1"]) is not None
        database_instance.closeConnection()
        assert database_instance.fetchData(query, ["Line1"]) is None
