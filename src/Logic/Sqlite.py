import sqlite3
from pathlib import Path

import pandas as pd

from src.Logic.Backend import addresses


class Database:
    def __init__(self, address):
        self.__address = address
        self.__name = None
        self.set_name(Path(address).stem)
        self.__connection = None
        self.initialize_connection()

    def get_address(self):
        return self.__address

    def get_name(self):
        return self.__name

    def set_name(self, name):
        self.__name = name

    def get_connection(self):
        return self.__connection

    def set_connection(self, connection):
        self.__connection = connection

    def initialize_connection(self):
        if self.get_connection() is None:
            self.set_connection(sqlite3.connect(self.get_address()))

    def close_connection(self):
        if self.get_connection() is not None:
            self.get_connection().close()


databases = {"fundamentals": Database(addresses["fundamentals"])}


def get_column_labels(database_name, table_name):
    # Connect to the SQLite database
    connection = databases.get(database_name).get_connection()
    cursor = connection.cursor()
    # Get column labels from the specified table
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    # Extract column labels
    column_labels = [col[1] for col in columns]
    return column_labels


def get_value(database_name, table_name, column_name="*", where=""):
    connection = databases.get(database_name).get_connection()
    cur = connection.cursor()
    query = "SELECT " + column_name + " FROM " + table_name + " " + where + ";"
    cur.execute(query)
    result = cur.fetchone()
    return list(result)


def get_values(database_name, table_name, column_name="*", where=""):
    connection = databases.get(database_name).get_connection()
    cur = connection.cursor()
    query = "SELECT " + column_name + " FROM " + table_name + " " + where + ";"
    cur.execute(query)
    result = cur.fetchall()
    return result


def dataframe_of_database(database_name, table_name, column='*', where=''):
    connection = databases.get(database_name).get_connection()
    if where == '':
        df = pd.read_sql_query(f"SELECT {column} FROM {table_name}", connection)
    else:
        df = pd.read_sql_query(
            f"SELECT {column} FROM {table_name} WHERE {where}", connection)
    return df


def write_elements_to_table(elements, condition):
    connection = databases.get("fundamentals").get_connection()
    cur = connection.cursor()
    for element in elements:
        if element.is_activated():
            query = f"""
                UPDATE elements
                SET low_Kev = {element.get_low_kev()},
                    high_Kev = {element.get_high_kev()},
                    intensity = {element.get_intensity()},
                    active = 1,
                    condition_id =
                        (SELECT condition_id
                        FROM conditions
                        WHERE conditions.name = '{condition.get_name()}')
                WHERE element_id = {element.get_attribute("element_id")};
            """
            cur.execute(query)
        else:
            query = f"""
                UPDATE elements
                SET intensity = null,
                    active = 0,
                    condition_id = null
                WHERE element_id = {element.get_attribute("element_id")};
            """
            cur.execute(query)
    connection.commit()
