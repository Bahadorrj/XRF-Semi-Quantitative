import numpy as np

from src.Logic import Sqlite
from src.Types.DataClass import Data
from src.Types.ElementClass import Element


class Condition(Data):
    def __init__(self, name: str):
        super().__init__()
        self.__elements = list()
        self.set_database_labels(Sqlite.get_column_labels("fundamentals", "conditions"))
        self.set_database_values(Sqlite.get_value("fundamentals", "conditions", where=f"WHERE name = '{name}'"))
        self.init_elements()

    def get_elements(self):
        return self.__elements

    def set_elements(self, elements):
        self.__elements = elements

    def init_elements(self):
        elements = list()
        values = Sqlite.get_values(
                "fundamentals",
                "elements",
                where=f"WHERE condition_id = {self.get_attribute('condition_id')} AND active == 1"
        )
        for value in values:
            e = Element(value[0])
            elements.append(e)
        self.set_elements(elements)
