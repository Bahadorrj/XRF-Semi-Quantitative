import sqlite3
import pandas as pd

from dataclasses import dataclass, field


@dataclass(order=True)
class Database:
    address: str
    name: str = field(default="main")
    connection: sqlite3.Connection = field(init=False, repr=False)

    def connect(self):
        self.connection = sqlite3.connect(self.address)

    def closeConnection(self):
        if self.connection is not None:
            self.connection.close()


DATABASES = {
    "fundamentals": Database(r"DB\fundamentals.db")
}


def getColumnLabels(databaseName, tableName):
    # Connect to the SQLite database
    connection = DATABASES.get(databaseName).connection
    cursor = connection.cursor()
    # Get column labels from the specified table
    cursor.execute(f"PRAGMA table_info({tableName})")
    columns = cursor.fetchall()
    # Extract column labels
    column_labels = [col[1] for col in columns]
    return column_labels


def getValue(databaseName, tableName, columnName="*", where=""):
    connection = DATABASES.get(databaseName).connection
    cur = connection.cursor()
    if where:
        query = f"SELECT {columnName} FROM {tableName} WHERE {where};"
    else:
        query = f"SELECT {columnName} FROM {tableName};"
    try:
        cur.execute(query)
        return cur.fetchone()
    except TypeError:
        print("Invalid request!")
    return None


def getValues(databaseName, tableName, columnName="*", where=""):
    connection = DATABASES.get(databaseName).connection
    cur = connection.cursor()
    if where:
        query = f"SELECT {columnName} FROM {tableName} WHERE {where};"
    else:
        query = f"SELECT {columnName} FROM {tableName};"
    try:
        cur.execute(query)
        return cur.fetchall()
    except TypeError:
        print("Invalid request!")
    return None


def getDatabaseDataframe(databaseName, tableName, columnName='*', where=''):
    connection = DATABASES.get(databaseName).connection
    if where == '':
        dataframe = pd.read_sql_query(f"SELECT {columnName} FROM {tableName}", connection)
    else:
        dataframe = pd.read_sql_query(
            f"SELECT {columnName} FROM {tableName} WHERE {where}", connection)
    return dataframe
