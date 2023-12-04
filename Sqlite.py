import sqlite3
import pandas as pd
from Backend import addr


def read(database_address, table_name, column='*', where=''):
    con = sqlite3.connect(database_address)
    if where == '':
        df = pd.read_sql_query(f"SELECT {column} FROM {table_name}", con)
    else:
        df = pd.read_sql_query(
            f"SELECT {column} FROM {table_name} WHERE {where}", con)
    con.close()
    return df


def write(db_addr, table_name, dataframe):
    conn = sqlite3.connect(db_addr)
    dataframe.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()


def activate_element(condition, item):
    conn = sqlite3.connect(addr['dbFundamentals'])
    cur = conn.cursor()
    query = f"""
            UPDATE elements
            SET low_Kev = {item['low_Kev']},
                high_Kev = {item['high_Kev']},
                intensity = {item['intensity']},
                active = 1,
                condition_id =
                    (SELECT condition_id
                    FROM conditions
                    WHERE conditions.name = '{condition}')
            WHERE symbol = '{item['symbol']}'
                    AND radiation_type = '{item['radiation_type']}';
            """
    cur.execute(query)
    conn.commit()


def deactivate_element(item):
    conn = sqlite3.connect(addr['dbFundamentals'])
    cur = conn.cursor()
    query = f"""
            UPDATE elements \
            SET active = 0 \
            WHERE symbol = '{item['symbol']}' \
            AND radiation_type = '{item['radiation_type']}'
        """
    cur.execute(query)
    conn.commit()


def deactivate_all():
    conn = sqlite3.connect(addr['dbFundamentals'])
    cur = conn.cursor()
    query = f"""
            UPDATE elements
            SET active = 0;
        """
    cur.execute(query)
    conn.commit()


def get_condition_name_where(element_id):
    if pd.isnull(element_id):
        return 'Not Activated'
    conn = sqlite3.connect(addr['dbFundamentals'])
    cur = conn.cursor()
    query = f"""
            SELECT name
            FROM conditions
            WHERE condition_id = {element_id};
        """
    cur.execute(query)
    name = cur.fetchone()[0]
    conn.commit()
    return name
