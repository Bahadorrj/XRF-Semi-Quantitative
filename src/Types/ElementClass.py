from pyqtgraph import InfiniteLine, InfLineLabel, mkPen, LinearRegionItem

from src.Logic import Calculation
from src.Logic.Sqlite import get_column_labels, get_value
from src.Types.DataClass import Data


class Element(Data):
    def __init__(self, id):
        super().__init__()
        self.__hidden = True
        self.set_database_labels(get_column_labels("fundamentals", "elements"))
        self.set_database_values(get_value("fundamentals", "elements", where=f"WHERE element_id = {id}"))
        self.__low_kev = self.get_attribute("low_Kev")
        self.__high_kev = self.get_attribute("high_Kev")
        self.__range = [Calculation.ev_to_px(self.get_attribute("low_Kev")),
                        Calculation.ev_to_px(self.get_attribute("high_Kev"))]
        self.__intensity = self.get_attribute("intensity")
        self.__activated = bool(self.get_attribute("active"))
        self.__spectrum_line = self.generate_line()
        self.__peak_line = self.generate_line()
        self.__region = self.init_region()

    def is_hidden(self) -> bool:
        return self.__hidden

    def set_hidden(self, hidden: bool):
        self.__hidden = hidden

    def get_spectrum_line(self):
        return self.__spectrum_line

    def set_spectrum_line(self, line):
        self.__spectrum_line = line

    def get_peak_line(self):
        return self.__peak_line

    def set_peak_line(self, line):
        self.__peak_line = line

    def generate_line(self):
        line = InfiniteLine()
        line.setAngle(90)
        line.setMovable(False)
        kev = self.get_attribute("Kev")
        px = Calculation.ev_to_px(kev)
        line.setValue(px)
        sym_label = InfLineLabel(
            line, self.get_attribute("symbol"), movable=False, position=0.9
        )
        radiation_type_label = InfLineLabel(
            line, self.get_attribute("radiation_type"), movable=False, position=0.8
        )
        line.setPen(mkPen("r", width=2))
        return line

    def get_region(self):
        return self.__region

    def set_region(self, region):
        self.__region = region

    def init_region(self):
        region = LinearRegionItem()
        region.setZValue(10)
        region.setRegion(self.get_range())
        return region

    def get_low_kev(self):
        return self.__low_kev

    def set_low_kev(self, kev):
        self.__low_kev = kev

    def get_high_kev(self):
        return self.__high_kev

    def set_high_kev(self, kev):
        self.__high_kev = kev

    def get_range(self):
        return self.__range

    def set_range(self, rng):
        self.__range = rng

    def get_intensity(self):
        return self.__intensity

    def set_intensity(self, intensity):
        self.__intensity = intensity

    def is_activated(self):
        return self.__activated

    def set_activated(self, activated):
        self.__activated = activated
        if activated:
            self.get_spectrum_line().setPen(mkPen("g", width=2))
            self.get_peak_line().setPen(mkPen("g", width=2))
        else:
            self.get_spectrum_line().setPen(mkPen("r", width=2))
            self.get_peak_line().setPen(mkPen("r", width=2))




