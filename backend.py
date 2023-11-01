import numpy as np
import pandas as pd
import sqlite3
import sqlalchemy
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import (ColorButton, InfiniteLine,
                       PlotWidget, SignalProxy,
                       hsvColor, mkPen,
                       LinearRegionItem, GraphicsLayoutWidget,
                       InfLineLabel)
from pathlib import Path
import os

icon = {'CSAN': r"myIcons\CSAN.ico",
        'peak_search': r"myIcons\peak-search.png",
        'cross': r"myIcons\cross-button.png",
        'hide': r"myIcons\hide.png",
        'unhide': r"myIcons\unhide.png",
        'exclamation': r"myIcons\exclamation.png",
        'open': r"myIcons\folder-horizontal.png",
        'conditions': r"myIcons\database.png"
        }

Addr = {'dbFundamentals': r"myFiles\fundamentals.db",
        'dbTables': r"myFiles\tables.db"}

host = '127.0.0.1'
user = 'CSAN'
password = 'X-Ray2023'

A0 = -0.0255
A1 = 0.01491


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

    def activeElement(condition, sym, type, intensity):
        conn = sqlite3.connect(Addr['dbFundamentals'])
        cur = conn.cursor()
        query = f"""
                UPDATE elements
                SET intensity = {intensity},
                    active = 1,
                    condition_id =
                        (SELECT condition_id
                        FROM conditions
                        WHERE conditions.name = '{condition}')
                WHERE symbol = '{sym}' AND radiation_type = '{type}'
                """
        cur.execute(query)
        conn.commit()

    def deactiveElement(sym):
        conn = sqlite3.connect(Addr['dbFundamentals'])
        cur = conn.cursor()
        query = f"""DELETE FROM elements
                WHERE symbol = '{sym}'"""
        cur.execute(query)
        conn.commit()


class MYSQL:
    def read(host, dbName, user, password, tableName):
        engine = sqlalchemy.create_engine(
            f"mysql+mysqldb://{user}:{password}@{host}/{dbName}"
        )
        df = pd.read_sql(f"SELECT * FROM {tableName}", engine)
        return df

    def activeElement(host, user, password, condition, item):
        engine = sqlalchemy.create_engine(
            f"mysql+mysqldb://{user}:{password}@{host}/fundamentals"
        )
        with engine.connect() as conn:
            dfGeneralData = pd.read_excel(
                Addr['xlsxGeneralData'],
                'sheet1'
            )
            sym = item['sym']
            type = item['type']
            intensity = item['intensity']
            row = dfGeneralData[
                np.logical_and(
                    dfGeneralData['Sym'] == sym,
                    dfGeneralData['Type'] == type
                )
            ]
            query = f"""
                INSERT INTO elements (
                    atomic_number,
                    name,
                    symbol,
                    radiation_type,
                    Kev,
                    low_Kev,
                    high_Kev,
                    intensity,
                    condition_id
                )
                VALUES (
                    {row['Atomic no.'].values[0]},
                    '{row['name'].values[0]}',
                    '{row['Sym'].values[0]}',
                    '{type}',
                    {row['Kev'].values[0]},
                    {row['Low'].values[0]},
                    {row['High'].values[0]},
                    {intensity},
                    (SELECT condition_id FROM conditions
                    WHERE conditions.name = '{condition}')
                )"""
            conn.execute(sqlalchemy.text(query))
            conn.commit()

    def deactiveElement(host, user, password, sym):
        engine = sqlalchemy.create_engine(
            f"mysql+mysqldb://{user}:{password}@{host}/fundamentals"
        )
        with engine.connect() as conn:
            query = f"""DELETE FROM elements
                    WHERE symbol = '{sym}'"""
            conn.execute(sqlalchemy.text(query))
            conn.commit()


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

    def findElementParam(ev, dfElements):
        greaterThanLow = dfElements['low_Kev'] < ev
        smallerThanHigh = ev < dfElements['high_Kev']
        msk = np.logical_and(greaterThanLow, smallerThanHigh)
        return dfElements[msk]


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
