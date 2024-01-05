import numpy as np

from ElementClass import Element
import Sqlite
from DataClass import Data
from Sqlite import get_column_labels, get_value


class Condition(Data):
    def __init__(self, name: str):
        super().__init__()
        self.__counts = np.zeros(2048, dtype=int)
        self.__elements = list()
        self.set_database_labels(get_column_labels("fundamentals", "conditions"))
        self.set_database_values(get_value("fundamentals", "conditions", where=f"WHERE name = '{name}'"))
        self.set_elements(self.init_elements())

    def get_counts(self) -> np.array:
        return self.__counts

    def set_counts(self, counts: np.array):
        self.__counts = counts

    def get_elements(self):
        return self.__elements

    def set_elements(self, elements):
        self.__elements = elements

    def init_elements(self):
        elements = list()
        values = Sqlite.get_values(
                "fundamentals",
                "elements",
                where=f"WHERE condition_id = {self.get_attribute('condition_id')}"
        )
        for value in values:
            e = Element(value[0])
            e.set_activated(True)
            elements.append(e)
        return elements
