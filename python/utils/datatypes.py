import socket
from dataclasses import dataclass, field
from json import loads
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt6.QtCore import Qt

from python.utils import calculation
from python.utils import encryption


@dataclass
class AnalyseData:
    condition: int
    x: np.ndarray
    y: np.ndarray

    def toDict(self) -> dict:
        return {"condition": self.condition, "x": self.x.tolist(), "y": self.y.tolist()}

    @classmethod
    def fromDict(cls, data: dict) -> "AnalyseData":
        return cls(data["condition"], np.array(data["x"]), np.array(data["y"]))

    @classmethod
    def fromList(cls, data: list) -> "AnalyseData":
        temp = list()
        condition = None
        for d in data:
            if d.isdigit():
                temp.append(int(d))
            elif "condition" in d.lower():
                condition = int(d.split()[-1])
        y = np.array(temp)
        x = np.arange(0, y.size, 1)
        return cls(condition, x, y) if condition is not None else None


@dataclass
class Analyse:
    filename: str = field(default=None)
    name: str = field(default=None)
    extension: str = field(default=None)
    generalData: dict[str] = field(default_factory=dict)
    data: list[AnalyseData] = field(default_factory=list)
    classification: str = field(default=None)
    concentrations: dict[str, float] = field(default_factory=dict)

    def __init__(self, **kwargs) -> None:
        if "data" not in kwargs:
            raise ValueError("Data is required for initialization in class Analyse")
        if "concentrations" not in kwargs:
            self.classification = "DEF"
            self.concentrations = {}
        else:
            self.classification = "CAL"
        if "generalData" not in kwargs:
            self.generalData = {}
        for key, value in kwargs.items():
            setattr(self, key, value)
            if key == "filename":
                setattr(self, "name", Path(value).stem)
                setattr(self, "extension", value.split(".")[-1])

    def getDataByConditionId(self, condition: int) -> AnalyseData:
        return self.data[condition - 1]

    def toDict(self) -> dict:
        return {
            "filename": getattr(self, "filename"),
            "name": getattr(self, "name"),
            "extension": getattr(self, "extension"),
            "generalData": getattr(self, "generalData"),
            "data": [d.toDict() for d in getattr(self, "data")],
            "concentrations": getattr(self, "concentrations"),
        }

    @classmethod
    def fromDict(cls, analyseDict: dict) -> "Analyse":
        analyseDict["data"] = [
            AnalyseData.fromDict(dataDict) for dataDict in analyseDict["data"]
        ]
        return cls(**analyseDict)

    @classmethod
    def fromTextFile(cls, filename: str) -> "Analyse":
        # TODO change in future
        analyseDict = {}
        data = []
        with open(filename, "r") as f:
            lines = list(map(lambda s: s.strip(), f.readlines()))
            start = 0
            stop = 0
            for line in lines:
                if "<<EndData>>" in line:
                    analyseData = AnalyseData.fromList(lines[start:stop])
                    if analyseData is not None:
                        start = stop
                        if analyseData.y.size != 0:
                            data.append(analyseData)
                else:
                    stop += 1
        data.sort(key=lambda x: x.condition)
        analyseDict["data"] = data
        analyseDict["filename"] = filename
        return cls(**analyseDict)

    @classmethod
    def fromATXFile(cls, filename: str) -> "Analyse":
        key = encryption.loadKey()
        with open(filename, "r") as f:
            encryptedText = f.readline()
            decryptedText = encryption.decryptText(encryptedText, key)
            analyseDict = loads(decryptedText)
        return cls.fromDict(analyseDict)

    @classmethod
    def fromSocket(cls, connection: socket.socket) -> "Analyse":
        received = ""
        while True:
            received += connection.recv(10).decode("utf-8")
            if received[-4:] == "stp":
                break
        analyseDict = loads(received)
        return cls.fromDict(analyseDict)


@dataclass
class PlotData:
    def __init__(
        self,
        rowId: int,
        spectrumLine: pg.InfiniteLine,
        peakLine: pg.InfiniteLine,
        region: pg.LinearRegionItem,
        visible: bool,
        active: bool,
        condition: int,
    ):
        self.rowId = rowId
        self.spectrumLine = spectrumLine
        self.peakLine = peakLine
        self.region = region
        self.visible = visible
        self.active = active
        self.condition = condition

    def activate(self):
        self.active = True
        self.peakLine.pen.setStyle(Qt.PenStyle.SolidLine)
        self.spectrumLine.pen.setStyle(Qt.PenStyle.SolidLine)

    def deactivate(self):
        self.active = False
        self.peakLine.pen.setStyle(Qt.PenStyle.DashLine)
        self.spectrumLine.pen.setStyle(Qt.PenStyle.DashLine)

    @classmethod
    def fromSeries(cls, rowId: int, series: pd.Series) -> "PlotData":
        active = bool(series["active"])
        spectrumLine = cls._generateLine(series)
        peakLine = cls._generateLine(series, lineType="peak")
        rng = (
            calculation.evToPx(float(series["low_kiloelectron_volt"])),
            calculation.evToPx(float(series["high_kiloelectron_volt"])),
        )
        region = cls._generateRegion(rng, not bool(series["active"]))
        try:
            conditionId = int(series["condition_id"])
        except ValueError:
            conditionId = None
        return PlotData(
            rowId, spectrumLine, peakLine, region, False, active, conditionId
        )

    @staticmethod
    def _generateLine(series: pd.Series, lineType: str = "spectrum") -> pg.InfiniteLine:
        value = calculation.evToPx(float(series["kiloelectron_volt"]))
        line = pg.InfiniteLine()
        line.setAngle(90)
        line.setMovable(False)
        line.setValue(value)
        active = bool(series["active"])
        pen = pg.mkPen()
        if active:
            pen.setStyle(Qt.PenStyle.SolidLine)
        else:
            pen.setStyle(Qt.PenStyle.DashLine)
        radiation = series["radiation_type"]
        match radiation:
            case "Ka":
                pen.setColor(pg.mkColor("#00FFFF"))
            case "Kb":
                pen.setColor(pg.mkColor("#FF00FF"))
            case "La":
                pen.setColor(pg.mkColor("#FFFF00"))
            case "Lb":
                pen.setColor(pg.mkColor("#00FF00"))
            case "Ly":
                pen.setColor(pg.mkColor("#FFA500"))
            case "Ma":
                pen.setColor(pg.mkColor("#ADD8E6"))
        if lineType == "peak":
            pen.setWidth(2)
            pos = 1
            for label in [radiation, series["symbol"]]:
                pos -= 0.1
                pg.InfLineLabel(line, text=label, movable=False, position=pos)
        else:
            pen.setWidth(1)
        line.setPen(pen)
        return line

    @staticmethod
    def _generateRegion(
        rng: Union[list[float, float], tuple[float, float]], movable: bool = True
    ):
        region = pg.LinearRegionItem(swapMode="push")
        region.setZValue(10)
        region.setRegion(rng)
        region.setBounds((0, 2048))
        region.setMovable(movable)
        return region
