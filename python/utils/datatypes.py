import socket
from dataclasses import dataclass, field
from json import loads
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
import pyqtgraph as pg

from python.utils import calculation
from python.utils import encryption


@dataclass
class AnalyseData:
    condition: int
    x: np.ndarray
    y: np.ndarray

    def toDict(self) -> dict:
        return {
            'condition': self.condition,
            'x': self.x.tolist(),
            'y': self.y.tolist()
        }

    @classmethod
    def fromDict(cls, data: dict) -> 'AnalyseData':
        return cls(data['condition'], np.array(data['x']), np.array(data['y']))

    @classmethod
    def fromList(cls, data: list) -> 'AnalyseData':
        temp = list()
        condition = 0
        for d in data:
            if d.isdigit():
                temp.append(int(d))
            elif "condition" in d.lower():
                condition = int(d.split()[-1])
        y = np.array(temp)
        x = np.arange(0, y.size, 1)
        return cls(condition, x, y)


@dataclass
class Analyse:
    filename: str = field(default=None)
    name: str = field(default=None)
    extension: str = field(default=None)
    generalData: dict[str] = field(default_factory=dict)
    data: list[AnalyseData] = field(default_factory=list)
    concentrations: dict[str, float] = field(default_factory=dict)

    def __init__(self, **kwargs) -> None:
        if "data" not in kwargs:
            raise ValueError("Data is required for initialization in class Analyse")
        if "concentrations" not in kwargs:
            self.concentrations = {}
        if "generalData" not in kwargs:
            self.generalData = {}
        for key, value in kwargs.items():
            setattr(self, key, value)
            if key == "filename":
                setattr(self, 'name', Path(value).stem)
                setattr(self, "extension", value.split(".")[-1])

    def toDict(self) -> dict:
        return {
            "filename": getattr(self, "filename"),
            "name": getattr(self, "name"),
            "extension": getattr(self, "extension"),
            "generalData": getattr(self, "generalData"),
            "data": [d.toDict() for d in getattr(self, "data")],
            "concentrations": getattr(self, "concentrations")
        }

    @classmethod
    def fromDict(cls, analyseDict: dict) -> 'Analyse':
        analyseDict['data'] = [AnalyseData.fromDict(dataDict) for dataDict in analyseDict['data']]
        return cls(**analyseDict)

    @classmethod
    def fromTextFile(cls, filename: str) -> 'Analyse':
        # TODO this has to change in future
        analyseDict = {}
        data = []
        with open(filename, 'r') as f:
            lines = list(map(lambda s: s.strip(), f.readlines()))
            start = 0
            stop = 0
            for line in lines:
                if "<<EndData>>" in line:
                    analyseData = AnalyseData.fromList(lines[start:stop])
                    start = stop
                    if analyseData.y.size != 0:
                        data.append(analyseData)
                else:
                    stop += 1
        data.sort(key=lambda x: x.condition)
        analyseDict['data'] = data
        analyseDict['filename'] = filename
        return cls(**analyseDict)

    @classmethod
    def fromATXFile(cls, filename: str) -> 'Analyse':
        key = encryption.loadKey()
        with open(filename, 'r') as f:
            encryptedText = f.readline()
            decryptedText = encryption.decryptText(encryptedText, key)
            analyseDict = loads(decryptedText)
        return cls.fromDict(analyseDict)

    @classmethod
    def fromSocket(cls, connection: socket.socket) -> 'Analyse':
        received = ""
        while True:
            received += connection.recv(10).decode('utf-8')
            if received[-4:] == 'stp':
                break
        analyseDict = loads(received)
        return cls.fromDict(analyseDict)


class PlotData:
    def __init__(self, rowId: int, spectrumLine: pg.InfiniteLine, peakLine: pg.InfiniteLine,
                 region: pg.LinearRegionItem, visible: bool, active: bool, condition: int):
        self.rowId = rowId
        self.spectrumLine = spectrumLine
        self.peakLine = peakLine
        self.region = region
        self.visible = visible
        self.active = active
        self.condition = condition

    def activate(self):
        self.active = True
        self.peakLine.setPen(pg.mkPen(color=(0, 255, 0, 150), width=2))
        self.spectrumLine.setPen(pg.mkPen(color=(0, 255, 0, 150), width=2))

    def deactivate(self):
        self.active = False
        self.peakLine.setPen(pg.mkPen(color=(255, 0, 0, 150), width=2))
        self.spectrumLine.setPen(pg.mkPen(color=(255, 0, 0, 150), width=2))

    @classmethod
    def fromSeries(cls, rowId: int, series: pd.Series) -> 'PlotData':
        active = bool(series['active'])
        value = calculation.evToPx(float(series['kiloelectron_volt']))
        labels = [str(series['symbol']), str(series['radiation_type'])]
        spectrumLine = cls._generateLine(value, active=active)
        peakLine = cls._generateLine(value, labels=labels, active=active)
        rng = (
            calculation.evToPx(float(series['low_kiloelectron_volt'])),
            calculation.evToPx(float(series['high_kiloelectron_volt']))
        )
        region = cls._generateRegion(rng)
        try:
            conditionId = int(series['condition_id'])
        except ValueError:
            conditionId = None
        return PlotData(rowId, spectrumLine, peakLine, region, False, active, conditionId)

    @staticmethod
    def _generateLine(value: float, **kwargs) -> pg.InfiniteLine:
        line = pg.InfiniteLine()
        line.setAngle(90)
        line.setMovable(False)
        line.setValue(value)
        pos = 1
        for key, val in kwargs.items():
            if key == 'active':
                if val is True:
                    line.setPen(pg.mkPen(color=(0, 255, 0, 150), width=2))
                else:
                    line.setPen(pg.mkPen(color=(255, 0, 0, 150), width=2))
            if key == 'labels':
                for label in val:
                    pos -= 0.1
                    pg.InfLineLabel(
                        line, text=label, movable=False, position=pos
                    )
        return line

    @staticmethod
    def _generateRegion(rng: Union[list[float, float], tuple[float, float]]):
        region = pg.LinearRegionItem(swapMode='push')
        region.setZValue(10)
        region.setRegion(rng)
        region.setBounds((0, 2048))
        return region
