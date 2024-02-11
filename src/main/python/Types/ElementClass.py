from pyqtgraph import InfiniteLine, InfLineLabel, mkPen, LinearRegionItem

from src.main.python.Logic import Calculation
from src.main.python.Logic.Sqlite import getColumnLabels, getValue
from src.main.python.Types.DataClass import Data


class Element(Data):
    def __init__(self, id):
        super().__init__()
        self._hidden = False
        self.setDatabaseLabels(getColumnLabels("fundamentals", "elements"))
        self.setDatabaseValues(getValue("fundamentals", "elements", where=f"WHERE element_id = {id}"))
        self._lowKev = self.getAttribute("low_Kev")
        self._highKev = self.getAttribute("high_Kev")
        self._range = [Calculation.ev_to_px(self.getAttribute("low_Kev")),
                       Calculation.ev_to_px(self.getAttribute("high_Kev"))]
        self._intensity = self.getAttribute("intensity")
        self._activated = bool(self.getAttribute("active"))
        self._spectrumLine = self.generateLine()
        self._peakLine = self.generateLine()
        self._region = self.initRegion()

    def isHidden(self) -> bool:
        return self._hidden

    def setHidden(self, hidden: bool):
        self._hidden = hidden

    def getSpectrumLine(self):
        return self._spectrumLine

    def setSpectrumLine(self, line):
        self._spectrumLine = line

    def getPeakLine(self):
        return self._peakLine

    def setPeakLine(self, line):
        self._peakLine = line

    def generateLine(self):
        line = InfiniteLine()
        line.setAngle(90)
        line.setMovable(False)
        kev = self.getAttribute("Kev")
        px = Calculation.ev_to_px(kev)
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

    def getRegion(self):
        return self._region

    def setRegion(self, region):
        self._region = region

    def initRegion(self):
        region = LinearRegionItem()
        region.setZValue(10)
        region.setRegion(self.getRange())
        return region

    def getLowKev(self):
        return self._lowKev

    def setLowKev(self, kev):
        self._lowKev = kev

    def getHighKev(self):
        return self._highKev

    def setHighKev(self, kev):
        self._highKev = kev

    def getRange(self):
        return self._range

    def setRange(self, rng):
        self._range = rng

    def getIntensity(self):
        return self._intensity

    def setIntensity(self, intensity):
        self._intensity = intensity

    def isActivated(self):
        return self._activated

    def setActivated(self, activated):
        self._activated = activated
        if activated:
            self.getSpectrumLine().setPen(mkPen("g", width=2))
            self.getPeakLine().setPen(mkPen("g", width=2))
        else:
            self.getSpectrumLine().setPen(mkPen("r", width=2))
            self.getPeakLine().setPen(mkPen("r", width=2))

    def __str__(self):
        return (
            f"Elemenet(\
            Low Kev: {self._lowKev},\
            High Kev: {self._highKev},\
            Intensity: {self._intensity}\
            Activated: {self._activated}\
            Hidden: {self._hidden})"
        )
