import unittest

from python.Logic.Sqlite import DatabaseConnection
from src.main.python.Logic import Sqlite


class TestSqlite(unittest.TestCase):
    def setUp(self):
        self.database = DatabaseConnection.getInstance(":fundamentals.db")

    def test_get_column_labels(self):
        labels = ['condition_id', 'name', 'Kv', 'mA', 'time', 'rotation', 'environment', 'filter', 'mask', 'active']
        self.assertEqual(
            Sqlite.getColumnLabels(self.database, "conditions"),
            labels,
            "Column labels do not match expected labels."
        )

    def test_get_value(self):
        self.assertEqual(
            Sqlite.getValue(self.database, 'elements', 'radiation_type', 'element_id = 4'),
            ('Ka',),
            "Value is not correctly selected."
        )

    def test_get_values(self):
        self.assertEqual(
            Sqlite.getValues(self.database, 'elements', 'element_id', "name = 'Silicon'"),
            [(15,), (16,), (412,)],
            "Value is not correctly selected."
        )

    def test_get_database_dataframe(self):
        self.assertIsNotNone(
            Sqlite.getDatabaseDataframe(self.database, 'elements', 'radiation_type'),
            msg="No dataframe was returned"
        )
