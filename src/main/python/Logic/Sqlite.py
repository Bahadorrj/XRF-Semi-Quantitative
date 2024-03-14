import os
import sqlite3

from dataclasses import dataclass
from pandas import read_sql_query


# Define function to resolve alias to file path
def resource_path(relative_path):
    return os.path.join(os.path.abspath("."), f"src\\main\\db\\{relative_path[1:]}")


@dataclass
class DatabaseConnection:
    _instance = None
    conn: sqlite3.Connection

    @classmethod
    def getInstance(cls, databaseFile: str):
        if cls._instance is None:
            conn = cls.createConnection(databaseFile)
            cls._instance = cls(conn)
        return cls._instance

    @staticmethod
    def createConnection(databaseFile: str) -> sqlite3.Connection:
        conn = None
        try:
            db_path = resource_path(databaseFile)
            conn = sqlite3.connect(db_path)
            return conn
        except sqlite3.Error as e:
            print(e)
        return conn

    def executeQuery(self, query: str):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            self.conn.commit()
            return cursor
        except sqlite3.Error as e:
            print(e)

    def fetchData(self, query: str) -> list:
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows
        except sqlite3.Error as e:
            print(e)

    def closeConnection(self):
        if self.conn is not None:
            self.conn.close()


def getColumnLabels(database: DatabaseConnection, tableName: str) -> list:
    # Get column labels from the specified table
    columns = database.fetchData(f"PRAGMA table_info({tableName})")
    # Extract column labels
    columnLabels = [col[1] for col in columns]
    return columnLabels


def getValues(database: DatabaseConnection, tableName: str, columnName: str = "*", where: str = ""):
    if where:
        query = f"SELECT {columnName} FROM {tableName} WHERE {where};"
    else:
        query = f"SELECT {columnName} FROM {tableName};"
    return database.fetchData(query)


def getValue(database: DatabaseConnection, tableName: str, columnName: str = "*", where: str = ""):
    return getValues(database, tableName, columnName, where)[0]


def getDatabaseDataframe(database: DatabaseConnection, tableName: str, columnName: str = "*", where: str = ""):
    connection = database.conn
    if where == '':
        dataframe = read_sql_query(f"SELECT {columnName} FROM {tableName}", connection)
    else:
        dataframe = read_sql_query(
            f"SELECT {columnName} FROM {tableName} WHERE {where}", connection)
    return dataframe
