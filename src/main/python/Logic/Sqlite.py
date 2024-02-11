import sqlite3
from pathlib import Path

import pandas as pd

ADDRESS = {
    "fundamentals": r"DB\fundamentals.db"
}


class Database:
    def __init__(self, address):
        self._address = address
        self._name = Path(address).stem
        self._connection = None
        self.initConnection()

    def getConnection(self):
        return self._connection

    def setConnection(self, connection):
        self._connection = connection

    def initConnection(self):
        if self.getConnection() is None:
            self.setConnection(sqlite3.connect(self._address))

    def closeConnection(self):
        if self.getConnection() is not None:
            self.getConnection().close()


DATABASES = {"fundamentals": Database(ADDRESS["fundamentals"])}


def getColumnLabels(databaseName, tableName):
    # Connect to the SQLite database
    connection = DATABASES.get(databaseName).getConnection()
    cursor = connection.cursor()
    # Get column labels from the specified table
    cursor.execute(f"PRAGMA table_info({tableName})")
    columns = cursor.fetchall()
    # Extract column labels
    column_labels = [col[1] for col in columns]
    return column_labels


def getValue(databaseName, tableName, columnName="*", where=""):
    connection = DATABASES.get(databaseName).getConnection()
    cur = connection.cursor()
    query = "SELECT " + columnName + " FROM " + tableName + " " + where + ";"
    cur.execute(query)
    result = cur.fetchone()
    return list(result)


def getValues(databaseName, tableName, columnName="*", where=""):
    connection = DATABASES.get(databaseName).getConnection()
    cur = connection.cursor()
    query = "SELECT " + columnName + " FROM " + tableName + " " + where + ";"
    cur.execute(query)
    result = cur.fetchall()
    return result


def getDatabaseDataframe(databaseName, tableName, columnName='*', where=''):
    connection = DATABASES.get(databaseName).getConnection()
    if where == '':
        dataframe = pd.read_sql_query(f"SELECT {columnName} FROM {tableName}", connection)
    else:
        dataframe = pd.read_sql_query(
            f"SELECT {columnName} FROM {tableName} WHERE {where}", connection)
    return dataframe
