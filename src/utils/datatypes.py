import logging
import socket
import pandas
import numpy as np
import pyqtgraph as pg

from collections import defaultdict
from dataclasses import dataclass, field
from json import JSONDecodeError, dump, loads, dumps
from pathlib import Path
from typing import Any
from PyQt6.QtCore import Qt

from src.utils import calculation
from src.utils import encryption
from src.utils.database import getDataframe
from src.utils.paths import resourcePath


@dataclass(order=True)
class AnalyseData:
    conditionId: int
    y: np.ndarray
    x: np.ndarray = field(init=False)

    def __post_init__(self):
        self.x = np.arange(0, len(self.y))

    def __eq__(self, others) -> bool:
        assert isinstance(others, AnalyseData), "Comparison Error"
        return np.all(np.equal(self.x, others.x)) and np.all(np.equal(self.y, others.y))

    def calculateIntensities(self, lines: pandas.DataFrame) -> dict:
        intensities = defaultdict(dict)
        for row in lines.itertuples():
            try:
                intensity = int(
                    self.y[
                        round(calculation.evToPx(row.low_kiloelectron_volt)) : round(
                            calculation.evToPx(row.high_kiloelectron_volt)
                        )
                    ].sum()
                )
                intensities[row.symbol][row.radiation_type] = intensity
            except ValueError:
                logging.error(
                    f"ValueError while calculating intensities failed for {row}"
                )
        return intensities

    def toHashableDict(self) -> dict:
        return {
            "condition_id": self.conditionId,
            "y": self.y.tolist(),
        }

    @classmethod
    def fromHashableDict(cls, data: dict) -> "AnalyseData":
        return cls(data["condition_id"], np.array(data["y"]))

    @classmethod
    def fromList(cls, data: list) -> "AnalyseData":
        temp = [int(d) for d in data if d.isdigit()]
        conditionId = next(
            (int(d.split()[-1]) for d in data if "condition" in d.lower()), None
        )
        y = np.array(temp)
        return cls(conditionId, y) if conditionId is not None else None


@dataclass(order=True)
class Analyse:
    filePath: str | None = field(default=None)
    data: list[AnalyseData] = field(default_factory=list)
    conditions: pandas.DataFrame | None = field(default=None)
    generalData: dict = field(default_factory=dict)
    filename: str | None = field(default=None)
    extension: str | None = field(default=None)

    def __post_init__(self) -> None:
        if self.filePath:
            self.filename = Path(self.filePath).stem
            self.extension = self.filePath.split(".")[-1]

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        assert isinstance(
            other, Analyse
        ), f"Comparison Error: between {type(self)} and {type(other)}"
        return (
            all(self.data[i] == other.data[i] for i in range(len(self.data)))
            and self.generalData == other.generalData
        )

    def getDataByConditionId(self, conditionId: int) -> AnalyseData:
        return next((d for d in self.data if d.conditionId == conditionId), None)

    def isEmpty(self) -> bool:
        return len(self.data) == 0

    def copy(self) -> "Analyse":
        return Analyse(self.filePath, self.data.copy(), self.generalData.copy())

    def saveTo(self, filePath) -> None:
        if filePath.endswith(".atx"):
            key = encryption.loadKey()
            jsonText = dumps(self.toHashableDict())
            encryptedText = encryption.encryptText(jsonText, key)
            with open(filePath, "wb") as f:
                f.write(encryptedText + b"\n")
        elif filePath.endswith(".txt"):
            with open(filePath, "w") as f:
                dump(self.toHashableDict(), f, indent=4)

    def calculateActiveIntensities(self, lines: pandas.DataFrame) -> dict:
        allIntensities = [d.calculateIntensities(lines) for d in self.data]
        intensities = defaultdict(dict)
        for row in lines.query("active == 1").itertuples(index=False):
            if row.condition_id in [data.conditionId for data in self.data]:
                intensities[row.symbol] = {
                    row.radiation_type: allIntensities[int(row.condition_id) - 1][
                        row.symbol
                    ][row.radiation_type]
                }
        return intensities

    def toHashableDict(self) -> dict:
        return {
            "file_path": self.filePath,
            "data": [d.toHashableDict() for d in self.data],
            "conditions": self.conditions.to_dict(),
            "general_data": self.generalData,
        }

    @classmethod
    def fromHashableDict(cls, analyseDict: dict) -> "Analyse":
        analyseDict["data"] = [
            AnalyseData.fromHashableDict(dataDict) for dataDict in analyseDict["data"]
        ]
        if "file_path" in analyseDict:
            analyseDict["filePath"] = analyseDict.pop("file_path")
        analyseDict["generalData"] = analyseDict.pop("general_data")
        analyse = cls(**analyseDict)
        if analyseDict.get("filename"):
            analyse.filename = analyseDict["filename"]
        return analyse

    @classmethod
    def fromTXTFile(cls, filePath: str) -> "Analyse":
        try:
            with open(filePath, "r") as f:
                return cls.fromHashableDict(loads(f.read()))
        except JSONDecodeError:
            with open(filePath, "r") as f:
                data = []
                lines = [line.strip() for line in f.readlines()]
                start = 0
                for stop, line in enumerate(lines):
                    if "<<EndData>>" in line:
                        analyseData = AnalyseData.fromList(lines[start:stop])
                        if analyseData and analyseData.y.size != 0:
                            data.append(analyseData)
                        start = stop
                data.sort(key=lambda x: x.conditionId)
                return cls(filePath, data, getDataframe("Conditions"))

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
                received = received[:-4]
                break
        analyseDict = loads(received)
        return cls.fromHashableDict(analyseDict)


@dataclass(order=True)
class Calibration:
    calibrationId: int
    filename: str
    element: str
    concentration: float
    state: int = field(default=0)
    _analyse: Analyse | None = field(default=None)
    _lines: pandas.DataFrame = field(
        default_factory=lambda: getDataframe("Lines").copy()
    )
    activeIntensities: dict = field(default_factory=dict)
    coefficients: dict = field(default_factory=dict)
    interferences: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.analyse is None:
            return
        if not self.activeIntensities:
            self.activeIntensities = self.analyse.calculateActiveIntensities(
                self._lines
            )
        if not self.coefficients:
            self.calculateCoefficients()
        if not self.interferences:
            self.calculateInterferences()

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        return (
            self.filename == other.filename
            and self.element == other.element
            and self.concentration == other.concentration
            and self.state == other.state
            and self.analyse == other.analyse
            and self.lines.equals(other.lines)
        )

    @property
    def analyse(self) -> Analyse:
        return self._analyse

    @analyse.setter
    def analyse(self, value: Analyse) -> None:
        self._analyse = value
        self.activeIntensities = self.analyse.calculateActiveIntensities(self._lines)
        self.calculateCoefficients()
        self.calculateInterferences()

    @property
    def lines(self) -> pandas.DataFrame:
        return self._lines

    def calculateCoefficients(self) -> None:
        self.coefficients = defaultdict(dict)
        df = self.lines.query(f"symbol == '{self.element}' and active == 1")
        for row in df.itertuples(index=False):
            data = self.analyse.getDataByConditionId(row.condition_id)
            if data is None:
                continue
            intensity = data.calculateIntensities(self.lines)[self.element][
                row.radiation_type
            ]
            self.coefficients[row.radiation_type] = self.concentration / intensity

    def calculateInterferences(self) -> None:
        self.interferences = defaultdict(dict)
        tmp = self.activeIntensities.copy()
        mainRadiation = self._lines.query(
            f"symbol == '{self.element}' and active == 1"
        )["radiation_type"].values[0]
        if element := tmp.pop(self.element, None):
            mainIntensity = element[mainRadiation]
            for symbol, values in tmp.items():
                for radiation, intensity in values.items():
                    self.interferences[symbol][radiation] = intensity / mainIntensity

    def status(self) -> str:
        return self.convertStateToStatus(self.state)

    def copy(self) -> "Calibration":
        return Calibration(
            self.calibrationId,
            self.filename,
            self.element,
            self.concentration,
            self.state,
            self.analyse.copy() if self.analyse else None,
            self.lines.copy(),
            self.activeIntensities.copy(),
            self.coefficients.copy() if self.analyse else None,
            self.interferences.copy() if self.analyse else None,
        )

    def save(self) -> None:
        if self.analyse:
            self.activeIntensities = self.analyse.calculateActiveIntensities(
                self._lines
            )
            self.calculateCoefficients()
            self.calculateInterferences()
        filePath = resourcePath(f"calibrations/{self.filename}.atxc")
        key = encryption.loadKey()
        jsonText = dumps(self.toHashableDict())
        encryptedText = encryption.encryptText(jsonText, key)
        with open(filePath, "wb") as f:
            f.write(encryptedText + b"\n")

    def toHashableDict(self) -> dict:
        return {
            "calibrationId": self.calibrationId,
            "filename": self.filename,
            "element": self.element,
            "concentration": self.concentration,
            "state": self.state,
            "analyse": self.analyse.toHashableDict() if self.analyse else None,
            "lines": self.lines.to_dict(),
            "coefficients": self.coefficients,
            "interferences": self.interferences,
        }

    @classmethod
    def fromHashableDict(cls, calibrationDict: dict) -> "Calibration":
        if analyseDict := calibrationDict.pop("analyse"):
            analyse = Analyse.fromHashableDict(analyseDict)
            calibrationDict["_analyse"] = analyse
        calibrationDict["_lines"] = pandas.DataFrame(calibrationDict.pop("lines"))
        calibrationDict["_lines"].reset_index(drop=True, inplace=True)
        return cls(**calibrationDict)

    @classmethod
    def fromATXCFile(cls, filePath: str) -> "Calibration":
        key = encryption.loadKey()
        with open(filePath, "r") as f:
            encryptedText = f.readline()
        decryptedText = encryption.decryptText(encryptedText, key)
        kwargs = loads(decryptedText)
        return cls.fromHashableDict(kwargs)

    @classmethod
    def convertStateToStatus(cls, state: int) -> str:
        if state == 0:
            return "Proceed to acquisition"
        elif state == 1:
            return "Initial state"
        else:
            return "Edited by user"


@dataclass(order=True)
class Method:
    methodId: int
    filename: str
    description: str = field(default="")
    state: int = field(default=0)
    calibrations: pandas.DataFrame = field(
        default_factory=lambda: pandas.DataFrame(
            columns=getDataframe("Calibrations").columns
        )
    )
    conditions: pandas.DataFrame = field(
        default_factory=lambda: getDataframe("Conditions").copy()
    )
    elements: pandas.DataFrame = field(
        default_factory=lambda: getDataframe("Elements").copy()
    )

    def __eq__(self, other: "Method"):
        if other is None:
            return False
        assert isinstance(other, Method), "Comparison Error"
        return (
            self.filename == other.filename
            and self.description == other.description
            and self.state == other.state
            and self.calibrations.equals(other.calibrations)
            and self.conditions.equals(other.conditions)
            and self.elements.equals(other.elements)
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
        methodPath = resourcePath(f"methods/{self.filename}.atxm")
        key = encryption.loadKey()
        jsonText = dumps(self.toHashableDict())
        encryptedText = encryption.encryptText(jsonText, key)
        with open(methodPath, "wb") as f:
            f.write(encryptedText + b"\n")

    def forVB(self) -> str:
        myDict = {
            "calibrations": self.calibrations.to_dict(),
            "conditions": self.conditions.query("active == 1").to_dict(),
        }
        myDict["calibrations"] = {
            k: v
            for k, v in myDict["calibrations"].items()
            if k in ["calibration_id", "filename"]
        }
        return dumps(myDict)

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
        kwargs["conditions"].reset_index(drop=True, inplace=True)
        kwargs["elements"] = pandas.DataFrame(kwargs["elements"])
        kwargs["elements"].reset_index(drop=True, inplace=True)
        kwargs["calibrations"] = pandas.DataFrame(kwargs["calibrations"])
        kwargs["calibrations"].reset_index(drop=True, inplace=True)
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
            return "Edited by user"


@dataclass(order=True)
class BackgroundProfile:
    backgroundId: int
    name: str
    description: str
    smoothness: float = field(default=1.0)
    height: Any | None = field(default=None)
    threshold: Any | None = field(default=None)
    distance: Any | None = field(default=None)
    prominence: Any | None = field(default=None)
    width: Any | None = field(default=None)
    wlen: Any | None = field(default=None)
    rel_height: float = field(default=0.5)
    plateau_size: Any | None = field(default=None)


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
