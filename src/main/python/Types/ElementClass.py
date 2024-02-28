from dataclasses import dataclass, field

from numpy import uint32
from pyqtgraph import InfiniteLine, InfLineLabel, mkPen, LinearRegionItem

from src.main.python.Logic import Calculation
from src.main.python.Logic.Sqlite import getColumnLabels, getValue
from src.main.python.Types.DataClass import Data


@dataclass(order=True)
class Element(Data):
    id: int
    hidden: bool = field(default=False, init=False, repr=False)
    lowKev: float = field(init=False)
    highKev: float = field(init=False)
    intensity: uint32 = field(init=False)
    activated: bool = field(init=False)
    spectrumLine: InfiniteLine = field(init=False, repr=False)
    peakLine: InfiniteLine = field(init=False, repr=False)
    region: LinearRegionItem = field(init=False, repr=False)
    range: list[int] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.labels = getColumnLabels("fundamentals", "elements")
        self.values = getValue("fundamentals", "elements", where=f"element_id = {self.id}")
        self.lowKev = self.getAttribute("low_Kev")
        self.highKev = self.getAttribute("high_Kev")
        self.intensity = self.getAttribute("intensity")
        self.activated = bool(self.getAttribute("active"))
        self.range = [Calculation.evToPx(self.lowKev),
                      Calculation.evToPx(self.highKev)]
        self.region = self._initRegion()
        self.spectrumLine = self._generateLine()
        self.peakLine = self._generateLine()

    def _initRegion(self):
        region = LinearRegionItem()
        region.setZValue(10)
        region.setRegion(self.range)
        return region

    def _generateLine(self):
        line = InfiniteLine()
        line.setAngle(90)
        line.setMovable(False)
        kev = self.getAttribute("Kev")
        px = Calculation.evToPx(kev)
        # -1 is for conflict
        # px = px - 1
        line.setValue(px)
        symbolLabel = InfLineLabel(
            line, self.getAttribute("symbol"), movable=False, position=0.9
        )
        radiationTypeLabel = InfLineLabel(
            line, self.getAttribute("radiation_type"), movable=False, position=0.8
        )
        line.setPen(mkPen("r", width=2))
        return line
