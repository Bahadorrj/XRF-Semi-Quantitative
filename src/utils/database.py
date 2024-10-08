import os
import sqlite3
import logging
import pandas as pd

from src.utils.paths import resourcePath


class Database:
    def __init__(self, path: str) -> None:
        try:
            self.conn = sqlite3.connect(path, check_same_thread=False)
            self.path = os.path.abspath(path)
        except sqlite3.Error as e:
            self.conn = None
            self.path = None
            logging.error(
                f"Database initialization failed for path: {path}\nError: {e}"
            )

    def executeQuery(self, query: str, values: list | tuple | None = None):
        try:
            cursor = self.conn.cursor()
            if values is None:
                cursor.execute(query)
            else:
                cursor.execute(query, values)
            self.conn.commit()
            return cursor
        except sqlite3.Error as e:
            logging.error(
                f"Executing query failed with query: {query} and values: {values}\nError: {e}"
            )

    def fetchData(self, query: str, values: list | tuple | None = None) -> list:
        try:
            cursor = self.conn.cursor()
            if values is None:
                cursor.execute(query)
            else:
                cursor.execute(query, values)
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(
                f"Fetching data failed with query: {query} and values: {values}\nError: {e}"
            )

    def closeConnection(self):
        if self.conn is not None:
            self.conn.close()

    def dataframe(self, query: str) -> pd.DataFrame:
        return pd.read_sql_query(query, self.conn)


_db = Database(resourcePath("fundamentals.db"))
_dataframes = {
    "Lines": _db.dataframe("SELECT * FROM Lines"),
    "Elements": _db.dataframe("SELECT * FROM Elements"),
    "Conditions": _db.dataframe("SELECT * FROM Conditions"),
    "Calibrations": _db.dataframe("SELECT * FROM Calibrations"),
    "Methods": _db.dataframe("SELECT * FROM Methods"),
    "BackgroundProfiles": _db.dataframe("SELECT * FROM BackgroundProfiles"),
}


def reloadDataframes():
    global _dataframes
    _dataframes = {
        "Lines": _db.dataframe("SELECT * FROM Lines"),
        "Elements": _db.dataframe("SELECT * FROM Elements"),
        "Conditions": _db.dataframe("SELECT * FROM Conditions"),
        "Calibrations": _db.dataframe("SELECT * FROM Calibrations"),
        "Methods": _db.dataframe("SELECT * FROM Methods"),
        "BackgroundProfiles": _db.dataframe("SELECT * FROM BackgroundProfiles"),
    }


def getDatabase() -> Database:
    global _db
    return _db


def getDataframe(dataframeName: str) -> pd.DataFrame:
    global _dataframes
    return _dataframes[dataframeName]
