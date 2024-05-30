import os
import sqlite3
from typing import Optional

import pandas as pd


class Database:
    def __init__(self, path: str) -> None:
        try:
            self.conn = sqlite3.connect(path)
            self.path = os.path.abspath(path)
        except sqlite3.Error as e:
            print(e)

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

    def dataframe(self, query: str) -> pd.DataFrame:
        df = pd.read_sql_query(query, self.conn)
        return df


db: Optional[Database] = None


def getDatabase(databasePath: str) -> Database:
    global db
    if not db:
        db = Database(databasePath)
    return db
