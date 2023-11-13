from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import pandas as pd
import sqlite3
import time

icon = {'CSAN': r"myIcons\CSAN.ico",
        'peak_search': r"myIcons\peak-search.png",
        'cross': r"myIcons\cross-button.png",
        'hide': r"myIcons\hide.png",
        'unhide': r"myIcons\unhide.png",
        'exclamation': r"myIcons\exclamation.png",
        'open': r"myIcons\folder-horizontal.png",
        'conditions': r"myIcons\database.png",
        'elements': r"myIcons\map.png"
        }

Addr = {'dbFundamentals': r"myFiles\fundamentals.db",
        'dbTables': r"myFiles\tables.db"}

A0 = -0.0255
A1 = 0.01491


def runtime_monitor(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(
            f"Function '{func.__name__}' took {execution_time:.6f} seconds to run.")
        return result
    return wrapper


class SQLITE:
    def read(dbAddr, tableName):
        con = sqlite3.connect(dbAddr)
        df = pd.read_sql_query(f"SELECT * FROM {tableName}", con)
        con.close()
        return df

    def write(dbAddr, tableName, dataframe):
        conn = sqlite3.connect(dbAddr)
        dataframe.to_sql(tableName, conn, if_exists='replace', index=False)
        conn.commit()
        conn.close()

    def activeElement(condition, item):
        conn = sqlite3.connect(Addr['dbFundamentals'])
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

    def deactiveElement(item):
        conn = sqlite3.connect(Addr['dbFundamentals'])
        cur = conn.cursor()
        query = f"""
                UPDATE elements
                SET active = 0
                WHERE symbol = '{item['symbol']}'
                AND radiation_type = '{item['radiation_type']}'
            """
        cur.execute(query)
        conn.commit()

    def deactiveAll():
        conn = sqlite3.connect(Addr['dbFundamentals'])
        cur = conn.cursor()
        query = f"""
                UPDATE elements
                SET active = 0;
            """
        cur.execute(query)
        conn.commit()

    def getConditionNameWhere(id):
        if np.isnan(id):
            return 'Not Activated'
        conn = sqlite3.connect(Addr['dbFundamentals'])
        cur = conn.cursor()
        query = f"""
                SELECT name
                FROM conditions
                WHERE condition_id = {id};
            """
        cur.execute(query)
        name = cur.fetchone()[0]
        conn.commit()
        return name


class TEXTREADER:
    def getString(input_file_name):
        s = ""
        with open(input_file_name, 'r') as f:
            line = f.readline()
            while line:
                s = s + line.rstrip()
                line = f.readline()
        return s

    def listItems(input_file_name, rng, list_type=str):
        my_list = []
        index = 0
        with open(input_file_name, 'r') as f:
            line = f.readline()
            while line:
                if index >= rng[0] and index <= rng[1]:
                    my_list.append(line.strip())
                line = f.readline()
                index = index + 1
        f.close()
        if list_type == str:
            return my_list
        else:
            return list(map(list_type, my_list))

    def conditionDictionary(input_file_name):
        with open(input_file_name, 'r') as f:
            my_dict = {}
            line = f.readline()  # read line
            index = 0
            while line:
                if 'Condition' in line:
                    condition = line.strip()
                elif 'Environment' in line:
                    start = index + 1
                    stop = index + 2048
                    my_dict[condition] = {
                        'range': [start, stop],
                        'active': False
                    }
                line = f.readline()
                index += 1
        f.close()
        return my_dict

    def writeItems(output_file_name, prefered_list):
        with open(output_file_name, 'w') as f:
            for i in prefered_list:
                f.write(f"{str(i)}\n")
        f.close()


class CALCULATION:
    def ev_to_px(ev):
        return round((ev + A0) / A1)

    def px_to_ev(px):
        return (px * A1) - A0

    def intensity(low, high, intensityRange):
        intensity = 0
        for px in range(CALCULATION.ev_to_px(low), CALCULATION.ev_to_px(high)):
            intensity += intensityRange[px]
        return intensity

    def rawIntensity(df, listCounts, rng):
        intensity = list()
        Ka1 = df['Ka1']
        La1 = df['La1']
        for element in range(rng):
            if Ka1[element] < 30:
                start = CALCULATION.ev_to_px(Ka1[element] - 0.2)
                finish = CALCULATION.ev_to_px(Ka1[element] + 0.2)
            else:
                start = CALCULATION.ev_to_px(La1[element] - 0.2)
                finish = CALCULATION.ev_to_px(La1[element] + 0.2)

            temp = 0
            for px in range(start, finish):
                temp = temp + listCounts[px]
            intensity.append(temp)
        return intensity


class FLOATDELEGATE(QtWidgets.QItemDelegate):
    # a class only for getting float inputs from the user
    def __init__(self, parent=None):
        QtWidgets.QItemDelegate.__init__(self, parent=parent)

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QLineEdit(parent)
        editor.setValidator(QtGui.QDoubleValidator())
        return editor


class TEXTDELEGATE(QtWidgets.QItemDelegate):
    # a class only for getting a, b and c as an input
    def __init__(self, parent=None):
        QtWidgets.QItemDelegate.__init__(self, parent=parent)

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QLineEdit(parent)
        regex = QtCore.QRegExp("[abc ]")
        validator = QtGui.QRegExpValidator(regex)
        editor.setValidator(validator)
        return editor
