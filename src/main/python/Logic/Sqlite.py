import sqlite3
import pandas as pd

from attrs import define, field, setters


@define(order=True)
class Database:
    address: str = field(on_setattr=setters.frozen)
    name: str = field(on_setattr=setters.frozen, default="main")
    connection: sqlite3.Connection = field(init=False)

    def connect(self):
        self.connection = sqlite3.connect(self.address)

    def closeConnection(self):
        if self.connection is not None:
            self.connection.close()


ADDRESS = {
    "fundamentals": r"DB/fundamentals.db"
}
DATABASES = {
    "fundamentals": Database(ADDRESS["fundamentals"])
}

DATABASES["fundamentals"].connect()
print(DATABASES)


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
    query = "SELECT " + columnName + " FROM " + tableName + " " + where + ";"
    cur.execute(query)
    result = cur.fetchone()
    return list(result)


def getValues(databaseName, tableName, columnName="*", where=""):
    connection = DATABASES.get(databaseName).connection
    cur = connection.cursor()
    query = "SELECT " + columnName + " FROM " + tableName + " " + where + ";"
    cur.execute(query)
    result = cur.fetchall()
    return result


def getDatabaseDataframe(databaseName, tableName, columnName='*', where=''):
    connection = DATABASES.get(databaseName).connection
    if where == '':
        dataframe = pd.read_sql_query(f"SELECT {columnName} FROM {tableName}", connection)
    else:
        dataframe = pd.read_sql_query(
            f"SELECT {columnName} FROM {tableName} WHERE {where}", connection)
    return dataframe
