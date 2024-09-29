import logging
import socket
import pandas
import numpy as np
import pyqtgraph as pg

from collections import defaultdict
from dataclasses import dataclass, field, asdict
from json import JSONDecodeError, dump, loads, dumps
from pathlib import Path
from typing import Sequence
from PyQt6.QtCore import Qt
from scipy.interpolate import CubicSpline
from scipy.signal import find_peaks

from src.utils import calculation
from src.utils import encryption
from src.utils.database import getDataframe
from src.utils.paths import resourcePath


@dataclass(order=True)
class AnalyseData:
    conditionId: int
    y: np.ndarray
    optimalY: np.ndarray = field(init=False)
    x: np.ndarray = field(init=False)

    def __post_init__(self):
        self.x = np.arange(0, len(self.y))
        self.optimalY = self.y.copy()

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
                logging.error(f"ValueError while calculating intensities for {row}")
        return intensities

    def applyBackgroundProfile(self, profile: "BackgroundProfile") -> None:
        self.optimalY = self.y.copy()
        if not profile:
            return
        xSmooth, ySmooth = self.smooth(self.x, self.y, profile.smoothness)
        if kwargs := profile.peakKwargs():
            peaks, _ = find_peaks(-ySmooth, **kwargs)
        else:
            peaks, _ = find_peaks(-ySmooth)
        if peaks.size != 0:
            regressionCurve = np.interp(self.x, xSmooth[peaks], ySmooth[peaks])
            self.optimalY = (self.y - regressionCurve).clip(0)

    @staticmethod
    def smooth(
        x: np.ndarray, y: np.ndarray, level: float
    ) -> tuple[np.ndarray, np.ndarray]:
        cs = CubicSpline(x, y)
        # Generate finer x values for smoother plot
        X = np.linspace(0, x.size, int(x.size / level))
        # Interpolate y values for the smoother plot
        Y = cs(X)
        return X, Y

    def toHashableDict(self) -> dict:
        return {
            "conditionId": self.conditionId,
            "y": self.y.tolist(),
        }

    @classmethod
    def fromHashableDict(cls, data: dict) -> "AnalyseData":
        return cls(data["conditionId"], np.array(data["y"]))

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
    conditions: pandas.DataFrame = field(
        default_factory=lambda: getDataframe("Conditions").copy()
    )
    _backgroundProfile: "BackgroundProfile" = field(default=None)
    generalData: dict = field(default_factory=dict)
    filename: str | None = field(default=None)
    extension: str | None = field(default=None)

    def __post_init__(self) -> None:
        self.generalData = {
            "Element": None,
            "Concentration": None,
            "Type": None,
            "Area": None,
            "Mass": None,
            "Rho": None,
            "Background Profile": None,
            "Rest": None,
            "Diluent": None,
        }
        if self.filePath:
            self.filename = Path(self.filePath).stem
            self.extension = self.filePath.split(".")[-1]

    @property
    def backgroundProfile(self) -> "BackgroundProfile":
        return self._backgroundProfile

    @backgroundProfile.setter
    def backgroundProfile(self, profile: "BackgroundProfile") -> None:
        self._backgroundProfile = profile
        for d in self.data:
            d.applyBackgroundProfile(profile)
        self.generalData["Background Profile"] = profile.filename

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        assert isinstance(
            other, Analyse
        ), f"Comparison Error: between {type(self)} and {type(other)}"
        return (
            all(self.data[i] == other.data[i] for i in range(len(self.data)))
            and self.conditions.equals(other.conditions)
            and self.backgroundProfile == other.backgroundProfile
            and self.generalData == other.generalData
        )

    def getDataByConditionId(self, conditionId: int) -> AnalyseData:
        return next((d for d in self.data if d.conditionId == conditionId), None)

    def isEmpty(self) -> bool:
        return len(self.data) == 0

    def copy(self) -> "Analyse":
        return Analyse(
            self.filePath,
            self.data.copy(),
            self.conditions.copy(),
            self.backgroundProfile.copy() if self.backgroundProfile else None,
            self.generalData.copy(),
            self.filename or None,
            self.extension or None,
        )

    def saveTo(self, filePath) -> None:
        hashableDict = self.toHashableDict()
        hashableDict["filePath"] = filePath
        hashableDict["filename"] = Path(filePath).stem
        hashableDict["extension"] = filePath.split(".")[-1]
        if filePath.endswith(".atx"):
            key = encryption.loadKey()
            jsonText = dumps(hashableDict)
            encryptedText = encryption.encryptText(jsonText, key)
            with open(filePath, "wb") as f:
                f.write(encryptedText + b"\n")
        elif filePath.endswith(".txt"):
            with open(filePath, "w") as f:
                dump(hashableDict, f, indent=4)

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

    def calculateConcentrations(self, method: "Method") -> dict:
        concentrations = {}
        activeIntensities = self.calculateActiveIntensities(method.lines)
        allIntensities = {
            d.conditionId: d.calculateIntensities(method.lines) for d in self.data
        }

        # Pre-filter method.lines for active elements
        activeLines = method.lines[method.lines["active"] == 1]

        for activeElement, d in activeIntensities.items():
            if activeElement != "Sm":
                continue
            conditionId = int(
                activeLines.query(f"symbol == '{activeElement}'")[
                    "condition_id"
                ].values[0]
            )
            for activeRadiation, intensity in d.items():
                key = f"{activeElement}-{activeRadiation}"
                if (
                    key not in method.interferences.index
                    or key not in method.coefficients.index
                ):
                    continue
                row = method.interferences.loc[key]
                for interfererElement, interference in row.items():
                    if interfererElement == activeElement:
                        continue
                    interfererRows = activeLines.query(
                        f"symbol == '{interfererElement}'"
                    )
                    for interfererRow in interfererRows.itertuples(index=False):
                        interfererRadiation = interfererRow.radiation_type
                        interfererIntensity = allIntensities[conditionId][
                            interfererElement
                        ][interfererRadiation]
                        intensity -= interfererIntensity * interference
                        if intensity <= 0:
                            break
                    if intensity <= 0:
                        break
                if intensity <= 0:
                    break
                concentrations[activeElement] = {
                    activeRadiation: float(
                        intensity
                        * method.coefficients.loc[
                            f"{activeElement}-{activeRadiation}"
                        ].values[0]
                    )
                }
        return concentrations

    def toHashableDict(self) -> dict:
        return {
            "filePath": self.filePath,
            "data": [d.toHashableDict() for d in self.data],
            "conditions": self.conditions.to_dict(),
            "backgroundProfile": (
                self.backgroundProfile.toHashableDict()
                if self.backgroundProfile
                else None
            ),
            "generalData": self.generalData.copy(),
        }

    @classmethod
    def fromHashableDict(cls, analyseDict: dict) -> "Analyse":
        analyseDict["data"] = [
            AnalyseData.fromHashableDict(dataDict) for dataDict in analyseDict["data"]
        ]
        if "conditions" in analyseDict:
            analyseDict["conditions"] = pandas.DataFrame(analyseDict.pop("conditions"))
            analyseDict["conditions"].reset_index(inplace=True, drop=True)
        if "backgroundProfile" in analyseDict:
            if (profileDict := analyseDict.pop("backgroundProfile", None)) is not None:
                analyseDict["_backgroundProfile"] = BackgroundProfile.fromHashableDict(
                    profileDict
                )
        return cls(**analyseDict)

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
        default_factory=lambda: getDataframe("Lines").iloc[:, 9:]
    )
    activeIntensities: dict = field(default_factory=dict)
    coefficients: dict = field(default_factory=dict)
    interferences: dict = field(default_factory=dict)

    def __post_init__(self):
        df = getDataframe("Lines").copy()
        df[["condition_id", "active"]] = self._lines[["condition_id", "active"]]
        df.reset_index(drop=True, inplace=True)
        self._lines = df
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
            self.calibrationId == other.calibrationId
            and self.filename == other.filename
            and self.element == other.element
            and self.concentration == other.concentration
            and self.state == other.state
            and self._analyse == other._analyse
            and self._lines.equals(other._lines)
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
        df = self._lines.query(f"symbol == '{self.element}' and active == 1")
        for row in df.itertuples(index=False):
            data = self.analyse.getDataByConditionId(row.condition_id)
            if data is None:
                continue
            intensity = data.calculateIntensities(self.lines)[self.element][
                row.radiation_type
            ]
            self.coefficients[row.radiation_type] = self.concentration / intensity

    def calculateInterferences(self) -> None:
        if self.element in self.activeIntensities:
            for activeRadiation, activeIntensity in self.activeIntensities[
                self.element
            ].items():
                interferences = defaultdict(dict)
                for symbol, values in self.activeIntensities.items():
                    for radiation, intensity in values.items():
                        if symbol == self.element and radiation == activeRadiation:
                            interferences[symbol][radiation] = (
                                self.concentration / intensity
                            )
                        else:
                            interferences[symbol][radiation] = (
                                intensity / activeIntensity
                            )
                self.interferences[activeRadiation] = interferences

    def status(self) -> str:
        return self.convertStateToStatus(self.state)

    def copy(self) -> "Calibration":
        return Calibration(
            self.calibrationId,
            self.filename,
            self.element,
            self.concentration,
            self.state,
            self._analyse.copy() if self._analyse else None,
            self._lines.copy(),
            self.activeIntensities.copy(),
            self.coefficients.copy() if self._analyse else None,
            self.interferences.copy() if self._analyse else None,
        )

    def save(self) -> None:
        if self.analyse:
            self.activeIntensities = self.analyse.calculateActiveIntensities(
                self._lines
            )
            self.calculateCoefficients()
            self.calculateInterferences()
        filePath = resourcePath(resourcePath(f"calibrations/{self.filename}.atxc"))
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
            "analyse": self._analyse.toHashableDict() if self.analyse else None,
            "lines": self._lines.to_dict(),
            "activeIntensities": self.activeIntensities,
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
    lines: pandas.DataFrame = field(
        default_factory=lambda: getDataframe("Lines").copy()
    )
    coefficients: pandas.DataFrame | None = field(default=None)
    interferences: pandas.DataFrame | None = field(default=None)

    def __post_init__(self):
        if self.calibrations.empty:
            return
        if self.coefficients is None or self.interferences is None:
            calibrations = [
                Calibration.fromATXCFile(resourcePath(f"calibrations/{f}.atxc"))
                for f in self.calibrations["filename"].values
            ]
        if self.coefficients is None:
            self.fillCoefficients(calibrations)
        if self.interferences is None:
            self.fillInterferences(calibrations)

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
            and self.lines.equals(other.lines)
            and self.coefficients.equals(other.coefficients)
            and self.interferences.equals(other.interferences)
        )

    def fillInterferences(self, calibrations: Sequence) -> None:
        interferences = {}
        for calibration in calibrations:
            for activeRadiation, values in calibration.interferences.items():
                interferences[f"{calibration.element}-{activeRadiation}"] = {
                    element: list(v.values())[0] for element, v in values.items()
                }
        self.interferences = pandas.DataFrame.from_dict(interferences, orient="index")

    def fillCoefficients(self, calibrations: Sequence) -> None:
        coefficients = {}
        for calibration in calibrations:
            for radiation, coefficient in calibration.coefficients.items():
                coefficients[f"{calibration.element}-{radiation}"] = coefficient
        self.coefficients = pandas.DataFrame.from_dict(coefficients, orient="index")

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
            self.lines.copy(),
            self.coefficients.copy() if self.coefficients is not None else None,
            self.interferences.copy() if self.interferences is not None else None,
        )

    def save(self) -> None:
        calibrations = [
            Calibration.fromATXCFile(resourcePath(f"calibrations/{f}.atxc"))
            for f in self.calibrations["filename"].values
        ]
        self.fillInterferences(calibrations)
        self.fillCoefficients(calibrations)
        for row in self.elements.itertuples():
            if (
                df := self.lines.query(f"symbol == '{row.symbol}' and active == 1")
            ).empty is False:
                index = int(df.index.values[0])
                try:
                    self.lines.at[index, "conditions_id"] = int(row.condition_id)
                except ValueError:
                    self.lines.at[index, "conditions_id"] = np.nan
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
            "lines": self.lines.to_dict(),
            "coefficients": self.coefficients.to_dict(),
            "interferences": self.interferences.to_dict(),
        }

    @classmethod
    def fromHashableDict(cls, kwargs: dict):
        kwargs["conditions"] = pandas.DataFrame(kwargs["conditions"])
        kwargs["conditions"].reset_index(drop=True, inplace=True)
        kwargs["elements"] = pandas.DataFrame(kwargs["elements"])
        kwargs["elements"].reset_index(drop=True, inplace=True)
        kwargs["lines"] = pandas.DataFrame(kwargs["lines"])
        kwargs["lines"].reset_index(drop=True, inplace=True)
        kwargs["calibrations"] = pandas.DataFrame(kwargs["calibrations"])
        kwargs["calibrations"].reset_index(drop=True, inplace=True)
        kwargs["coefficients"] = pandas.DataFrame(kwargs["coefficients"])
        kwargs["interferences"] = pandas.DataFrame(kwargs["interferences"])
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


@dataclass(order=True, eq=True)
class BackgroundProfile:
    profileId: int
    filename: str
    description: str
    smoothness: float = field(default=1.0)
    height: str | None = field(default=None)
    threshold: str | None = field(default=None)
    distance: str | None = field(default=None)
    prominence: str | None = field(default=None)
    width: str | None = field(default=None)
    wlen: str | None = field(default=None)
    rel_height: str | None = field(default=None)
    plateau_size: str | None = field(default=None)
    state: int = field(default=0)

    def status(self) -> str:
        return self.convertStateToStatus(self.state)

    def peakKwargs(self) -> dict:
        return {
            f: eval(value)
            for f, value in self.__dict__.items()
            if f not in ["profileId", "filename", "description", "smoothness", "state"]
            and value is not None
        }

    def copy(self) -> "BackgroundProfile":
        return BackgroundProfile(**self.__dict__)

    def save(self) -> None:
        filePath = resourcePath(resourcePath(f"backgrounds/{self.filename}.atxb"))
        key = encryption.loadKey()
        jsonText = dumps(self.toHashableDict())
        encryptedText = encryption.encryptText(jsonText, key)
        with open(filePath, "wb") as f:
            f.write(encryptedText + b"\n")

    def toHashableDict(self) -> dict:
        return asdict(self)

    @classmethod
    def fromHashableDict(cls, kwargs: dict):
        return None if kwargs is None else cls(**kwargs)

    @classmethod
    def fromATXBFile(cls, filePath: str) -> "BackgroundProfile":
        key = encryption.loadKey()
        with open(filePath, "r") as f:
            encryptedText = f.readline()
        decryptedText = encryption.decryptText(encryptedText, key)
        kwargs = loads(decryptedText)
        return cls(**kwargs)

    @classmethod
    def convertStateToStatus(cls, state: int) -> str:
        if state == 0:
            return "Initial state"
        elif state == 1:
            return "Edited by user"


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
