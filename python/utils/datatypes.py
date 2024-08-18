import socket
import pandas

import numpy as np
import pyqtgraph as pg

from dataclasses import dataclass, field
from json import loads
from pathlib import Path
from collections import defaultdict

from PyQt6.QtCore import Qt

from python.utils import calculation
from python.utils import encryption
from python.utils.database import getDataframe

@dataclass(order=True)
class AnalyseData:
    conditionId: int
    x: np.ndarray
    y: np.ndarray

    def calculateIntensities(self, lines: pandas.DataFrame) -> dict:
        intensities = defaultdict(dict)
        for row in lines.itertuples():
            intensity = self.y[
                int(calculation.evToPx(row.low_kiloelectron_volt)):
                int(calculation.evToPx(row.high_kiloelectron_volt))
            ].sum()
            intensities[row.symbol][row.radiation_type] = intensity
        return intensities

    def toHashableDict(self) -> dict:
        return {"condition": self.conditionId, "x": self.x.tolist(), "y": self.y.tolist()}

    @classmethod
    def fromHashableDict(cls, data: dict) -> "AnalyseData":
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


@dataclass(order=True)
class Analyse:
    filename: str = field(default=None)
    data: list[AnalyseData] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = Path(self.filename).stem
        self.extension = self.filename.split(".")[-1]

    def getDataByConditionId(self, conditionId: int) -> AnalyseData:
        return list(filter(lambda d: d.conditionId == conditionId, self.data))[0]

    def toHashableDict(self) -> dict:
        return {
            "filename": getattr(self, "filename"),
            "data": [d.toHashableDict() for d in self.data],
        }

    @classmethod
    def fromHashableDict(cls, analyseDict: dict) -> "Analyse":
        analyseDict["data"] = [
            AnalyseData.fromHashableDict(dataDict) for dataDict in analyseDict["data"]
        ]
        return cls(**analyseDict)

    @classmethod
    def fromTXTFile(cls, filename: str) -> "Analyse":
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
        data.sort(key=lambda x: x.conditionId)
        analyseDict["data"] = data
        analyseDict["filename"] = filename
        return cls(filename, data)

    @classmethod
    def fromATXFile(cls, filename: str) -> "Analyse":
        key = encryption.loadKey()
        with open(filename, "r") as f:
            encryptedText = f.readline()
            decryptedText = encryption.decryptText(encryptedText, key)
            analyseDict = loads(decryptedText)
        return cls.fromHashableDict(analyseDict)

    @classmethod
    def fromSocket(cls, connection: socket.socket) -> "Analyse":
        received = ""
        while True:
            received += connection.recv(10).decode("utf-8")
            if received[-4:] == "stp":
                break
        analyseDict = loads(received)
        return cls.fromHashableDict(analyseDict)


@dataclass(order=True)
class Calibration:
    analyse: Analyse = field(default=None)
    generalData: dict = field(default_factory=dict)
    concentrations: dict = field(default_factory=dict)
    lines: pandas.DataFrame = field(default=None)
    
    def calculateCoefficients(self, lines: pandas.DataFrame) -> dict:
        coefficients = {}
        for symbol, concentration in self.concentrations.items():
            row = lines.query(f"symbol == '{symbol}' and active == 1")
            conditionId = row["condition_id"].values[0]
            radiationType = row["radiation_type"].values[0]
            data = self.analyse.getDataByConditionId(conditionId)
            intensity = data.calculateIntensities(lines)[symbol][radiationType]
            coefficient = concentration / intensity if intensity != 0 else 0
            coefficients[symbol] = coefficient
        return coefficients
    
    def calculateInterferences(self, lines: pandas.DataFrame) -> dict:
        interferences = {}
        for symbol in self.concentrations.keys():
            row = lines.query(f"symbol == '{symbol}' and active == 1")
            conditionId = row["condition_id"].values[0]
            radiationType = row["radiation_type"].values[0]
            data = self.analyse.getDataByConditionId(conditionId)
            intensities = data.calculateIntensities(lines)
            intensity = intensities[symbol][radiationType]
            interference = defaultdict(dict)
            for interfererSymbol, values in intensities.items():
                for interfererRadiationType, interfererIntensity in values.items():
                    if interfererSymbol != symbol and interfererRadiationType != radiationType:
                        interference[interfererSymbol][interfererRadiationType] = interfererIntensity / intensity
            interferences[symbol] = interference
        return interferences
    
    @classmethod
    def fromATXCFile(cls, filename: str) -> "Calibration":
        key = encryption.loadKey()
        with open(filename, "r") as f:
            encryptedText = f.readline()
        decryptedText = encryption.decryptText(encryptedText, key)
        calibrationAsDict = loads(decryptedText)
        kwargs = calibrationAsDict
        analyse = Analyse.fromHashableDict(calibrationAsDict["analyse"])
        kwargs["analyse"] = analyse
        kwargs["lines"] = pandas.DataFrame(kwargs["lines"])
        return cls(**kwargs)

    def copy(self) -> "Calibration":
        calibration = Calibration(self.analyse, self.generalData.copy(), self.concentrations.copy(), self.lines.copy())
        return calibration

@dataclass(order=True)
class PlotData:
    rowId: int
    spectrumLine: pg.InfiniteLine
    peakLine: pg.InfiniteLine
    region: pg.LinearRegionItem
    visible: bool
    active: bool
    conditionId: int

    def activate(self):
        self.active = True
        self.peakLine.pen.setStyle(Qt.PenStyle.SolidLine)
        self.spectrumLine.pen.setStyle(Qt.PenStyle.SolidLine)

    def deactivate(self):
        self.active = False
        self.peakLine.pen.setStyle(Qt.PenStyle.DashLine)
        self.spectrumLine.pen.setStyle(Qt.PenStyle.DashLine)

    @classmethod
    def fromSeries(cls, rowId: int, series: pandas.Series) -> "PlotData":
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
    def _generateLine(series: pandas.Series, lineType: str = "spectrum") -> pg.InfiniteLine:
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
        rng: list[float, float] | tuple[float, float], movable: bool = True
    ):
        region = pg.LinearRegionItem(swapMode="push")
        region.setZValue(10)
        region.setRegion(rng)
        region.setBounds((0, 2048))
        region.setMovable(movable)
        return region


@dataclass(order=True)
class Method:
    conditions: pandas.DataFrame = field(default=None)
    elements: pandas.DataFrame = field(default=None)
    calibrations: list[Calibration] = field(default_factory=list)
