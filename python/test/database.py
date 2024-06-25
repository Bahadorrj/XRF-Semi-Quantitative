import unittest

from python.utils.database import getDatabase
from python.utils.paths import resourcePath


class TestSqlite(unittest.TestCase):
    def setUp(self):
        self.database = getDatabase(resourcePath('../../fundamentals.db'))

    def test_connection(self):
        self.assertIsNotNone(self.database.conn, "Database connection was not established")

    def test_conditions_existence(self):
        # Check if the table exists
        result = self.database.executeQuery(f"SELECT name FROM sqlite_master WHERE type='table' AND name='conditions'")
        # Assert whether the table exists or not
        self.assertIsNotNone(result.fetchone(), f"Table 'conditions' does not exist")

    def test_elements_existence(self):
        # Check if the table exists
        result = self.database.executeQuery(f"SELECT name FROM sqlite_master WHERE type='table' AND name='elements'")
        # Assert whether the table exists or not
        self.assertIsNotNone(result.fetchone(), f"Table 'elements' does not exist")

    def test_UQ_existence(self):
        # Check if the table exists
        result = self.database.executeQuery(f"SELECT name FROM sqlite_master WHERE type='table' AND name='UQ'")
        # Assert whether the table exists or not
        self.assertIsNotNone(result.fetchone(), f"Table 'UQ' does not exist")
