import socket
from collections import defaultdict
from dataclasses import dataclass, field
from json import loads, dumps
from pathlib import Path
from typing import Optional

import numpy as np
import pandas
import pyqtgraph as pg
from PyQt6.QtCore import Qt

from src.utils import calculation
from src.utils import encryption
from src.utils.database import getDataframe


@dataclass(order=True)
class AnalyseData:
    conditionId: int
    x: np.ndarray
    y: np.ndarray

    def calculateIntensities(self, lines: pandas.DataFrame) -> dict:
        intensities = defaultdict(dict)
        for row in lines.itertuples():
            intensity = int(self.y[
                int(calculation.evToPx(row.low_kiloelectron_volt)) : 
                int(calculation.evToPx(row.high_kiloelectron_volt))
            ].sum())
            intensities[row.symbol][row.radiation_type] = intensity
        return intensities

    def toHashableDict(self) -> dict:
        return {
            "condition": self.conditionId,
            "x": self.x.tolist(),
            "y": self.y.tolist(),
        }

    @classmethod
    def fromHashableDict(cls, data: dict) -> "AnalyseData":
        return cls(data["condition"], np.array(data["x"]), np.array(data["y"]))

    @classmethod
    def fromList(cls, data: list) -> "AnalyseData":
        temp = [int(d) for d in data if d.isdigit()]
        condition = next(
            (int(d.split()[-1]) for d in data if "condition" in d.lower()), None
        )
        y = np.array(temp)
        x = np.arange(0, y.size, 1)
        return cls(condition, x, y) if condition is not None else None


@dataclass(order=True)
class Analyse:
    filePath: str
    data: list[AnalyseData] = field(default_factory=list)
    generalData: dict = field(default_factory=dict)
    filename: str = field(init=False)
    extension: str = field(init=False)

    def __post_init__(self) -> None:
        self.filename = Path(self.filePath).stem
        self.extension = self.filePath.split(".")[-1]

    def getDataByConditionId(self, conditionId: int) -> AnalyseData:
        return next(d for d in self.data if d.conditionId == conditionId)

    def toHashableDict(self) -> dict:
        return {
            "filePath": self.filePath,
            "data": [d.toHashableDict() for d in self.data],
            "generalData": self.generalData,
        }

    def isEmpty(self) -> bool:
        return len(self.data) == 0

    def copy(self) -> "Analyse":
        return Analyse(self.filePath, self.data.copy(), self.generalData.copy())

    def saveTo(self, filePath) -> None:
        if filePath.endswith(".atx"):
            key = encryption.loadKey()
            with open(filePath, "wb") as f:
                jsonText = dumps(self.toHashableDict())
                encryptedText = encryption.encryptText(jsonText, key)
                f.write(encryptedText + b"\n")
        elif filePath.endswith(".txt"):
            with open(filePath, "w") as f:
                for data in self.data:
                    f.write("<<Data>>\n")
                    f.write("*****\n")
                    f.write(f"Condition {data.conditionId}\n")
                    for i in data.y:
                        f.write(str(i) + "\n")

    @classmethod
    def fromHashableDict(cls, analyseDict: dict) -> "Analyse":
        analyseDict["data"] = [
            AnalyseData.fromHashableDict(dataDict) for dataDict in analyseDict["data"]
        ]
        return cls(**analyseDict)

    @classmethod
    def fromTXTFile(cls, filePath: str) -> "Analyse":
        data = []
        with open(filePath, "r") as f:
            lines = [line.strip() for line in f]
            start = 0
            for stop, line in enumerate(lines):
                if "<<EndData>>" in line:
                    analyseData = AnalyseData.fromList(lines[start:stop])
                    if analyseData and analyseData.y.size != 0:
                        data.append(analyseData)
                    start = stop
        data.sort(key=lambda x: x.conditionId)
        return cls(filePath, data)

    @classmethod
    def fromATXFile(cls, filePath: str) -> "Analyse":
        key = encryption.loadKey()
        with open(filePath, "r") as f:
            encryptedText = f.readline()
        decryptedText = encryption.decryptText(encryptedText, key)
        analyseDict = loads(decryptedText)
        return cls.fromHashableDict(analyseDict)

    @classmethod
    def fromSocket(cls, connection: socket.socket) -> "Analyse":
        received = ""
        while True:
            received += connection.recv(10).decode("utf-8")
            if received[-4:] == "-stp":
                break
        analyseDict = loads(received)
        return cls.fromHashableDict(analyseDict)


@dataclass(order=True)
class Calibration:
    filename: str
    element: str
    concentration: float
    state: int = field(default=0)
    _analyse: Optional[Analyse] = field(default=None)
    _lines: pandas.DataFrame = field(
        default_factory=lambda: getDataframe("Lines").copy()
    )
    coefficients: dict = field(default_factory=dict)
    interferences: dict = field(default_factory=dict)

    def __post_init__(self):
        self.calculateCoefficients()
        self.calculateInterferences()

    @property
    def analyse(self) -> Analyse:
        return self._analyse

    @analyse.setter
    def analyse(self, value: Analyse) -> None:
        self._analyse = value
        self.calculateCoefficients()
        self.calculateInterferences()

    @property
    def lines(self) -> pandas.DataFrame:
        return self._lines

    @lines.setter
    def lines(self, value: pandas.DataFrame) -> None:
        self._lines = value
        self.calculateCoefficients()
        self.calculateInterferences()

    def calculateCoefficients(self) -> None:
        if self.analyse is None:
            return
        df = self.lines.query(f"symbol == '{self.element}' and active == 1")
        for row in df.itertuples(index=False):
            data = self.analyse.getDataByConditionId(row.condition_id)
            intensity = data.calculateIntensities(self.lines)[self.element][
                row.radiation_type
            ]
            self.coefficients[row.radiation_type] = self.concentration / intensity

    def calculateInterferences(self) -> None:
        if self.analyse is None or self.analyse.isEmpty():
            return
        row = self.lines.query(f"symbol == '{self.element}' and active == 1")
        conditionId = row["condition_id"].values[0]
        radiationType = row["radiation_type"].values[0]
        data = self.analyse.getDataByConditionId(conditionId)
        intensities = data.calculateIntensities(self.lines)
        intensity = intensities[self.element][radiationType]
        self.interferences[self.element] = {
            interfererSymbol: {
                interfererRadiationType: interfererIntensity / intensity
                for interfererRadiationType, interfererIntensity in values.items()
                if interfererRadiationType != radiationType
            }
            for interfererSymbol, values in intensities.items()
            if interfererSymbol != self.element
        }

    def status(self) -> str:
        return self.convertStateToStatus(self.state)

    def copy(self) -> "Calibration":
        return Calibration(
            self.filename,
            self.element,
            self.concentration,
            self.state,
            self.analyse.copy() if self.analyse else None,
            self.lines.copy(),
            self.coefficients.copy(),
            self.interferences.copy(),
        )

    def save(self) -> None:
        filePath = f"calibrations/{self.filename}.atxc"
        with open(filePath, "wb") as f:
            key = encryption.loadKey()
            jsonText = dumps(self.toHashableDict())
            encryptedText = encryption.encryptText(jsonText, key)
            f.write(encryptedText + b"\n")

    def toHashableDict(self) -> dict:
        return {
            "element": self.element,
            "concentration": self.concentration,
            "state": self.state,
            "_analyse": self.analyse.toHashableDict() if self.analyse else None,
            "_lines": self.lines.to_dict(),
            "coefficients": self.coefficients,
            "interferences": self.interferences,
        }

    @classmethod
    def fromHashableDict(cls, calibrationDict: dict) -> "Calibration":
        if calibrationDict["_analyse"]:
            analyse = Analyse.fromHashableDict(calibrationDict["_analyse"])
            calibrationDict["_analyse"] = analyse
        calibrationDict["_lines"] = pandas.DataFrame(calibrationDict["_lines"])
        return cls(**calibrationDict)

    @classmethod
    def fromATXCFile(cls, filePath: str) -> "Calibration":
        key = encryption.loadKey()
        with open(filePath, "r") as f:
            encryptedText = f.readline()
        decryptedText = encryption.decryptText(encryptedText, key)
        kwargs = loads(decryptedText)
        kwargs["filename"] = Path(filePath).stem
        return cls.fromHashableDict(kwargs)

    @classmethod
    def convertStateToStatus(cls, state: int) -> str:
        if state == 0:
            status = "Proceed to acquisition"
        elif state == 1:
            status = "Initial state"
        else:
            status = "Edited by user"
        return status


@dataclass(order=True)
class Method:
    methodId: int
    filename: str
    description: str = field(default="")
    state: int = field(default=0)
    calibrations: Optional[pandas.DataFrame] = field(
        default_factory=lambda: pandas.DataFrame(
            columns=getDataframe("Calibrations").columns[1:]
        )
    )
    conditions: pandas.DataFrame = field(
        default_factory=lambda: getDataframe("Conditions").copy()
    )
    elements: pandas.DataFrame = field(
        default_factory=lambda: getDataframe("Elements").copy()
    )

    def status(self) -> str:
        return self.convertStateToStatus(self.state)

    def copy(self) -> "Method":
        return Method(
            self.methodId,
            self.filename,
            self.description,
            self.state,
            self.calibrations.copy(),
            self.conditions.copy(),
            self.elements.copy(),
        )

    def save(self) -> None:
        methodPath = f"methods/{self.filename}.atxm"
        key = encryption.loadKey()
        jsonText = dumps(self.toHashableDict())
        encryptedText = encryption.encryptText(jsonText, key)
        with open(methodPath, "wb") as f:
            f.write(encryptedText + b"\n")

    def toHashableDict(self) -> dict:
        return {
            "methodId": self.methodId,
            "filename": self.filename,
            "description": self.description,
            "state": self.state,
            "calibrations": self.calibrations.to_dict(),
            "conditions": self.conditions.to_dict(),
            "elements": self.elements.to_dict(),
        }

    @classmethod
    def fromHashableDict(cls, kwargs: dict):
        kwargs["conditions"] = pandas.DataFrame(kwargs["conditions"])
        kwargs["elements"] = pandas.DataFrame(kwargs["elements"])
        kwargs["calibrations"] = pandas.DataFrame(kwargs["calibrations"])
        return cls(**kwargs)

    @classmethod
    def fromATXMFile(cls, filePath: str):
        key = encryption.loadKey()
        with open(filePath, "r") as f:
            encryptedText = f.readline()
        decryptedText = encryption.decryptText(encryptedText, key)
        kwargs = loads(decryptedText)
        return cls.fromHashableDict(kwargs)

    @classmethod
    def convertStateToStatus(cls, state: int) -> str:
        if state == 0:
            return "Initial state"
        elif state == 1:
            return "Edited"

    def __eq__(self, other: "Method"):
        assert isinstance(other, Method), "Comparison Error"
        return (
            self.filename == other.filename
            and self.description == other.description
            and self.state == other.state
            and self.calibrations.equals(other.calibrations)
            and self.conditions.equals(other.conditions)
            and self.elements.equals(other.elements)
        )


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
        self.region.setMovable(False)

    def deactivate(self):
        self.active = False
        self.peakLine.pen.setStyle(Qt.PenStyle.DashLine)
        self.spectrumLine.pen.setStyle(Qt.PenStyle.DashLine)
        self.region.setMovable(True)

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
    def _generateLine(
        series: pandas.Series, lineType: str = "spectrum"
    ) -> pg.InfiniteLine:
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
