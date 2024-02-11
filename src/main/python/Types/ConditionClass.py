from src.main.python.Logic import Sqlite
from src.main.python.Types.DataClass import Data
from src.main.python.Types.ElementClass import Element


class Condition(Data):
    def __init__(self, name: str):
        super().__init__()
        self.setDatabaseLabels(Sqlite.getColumnLabels("fundamentals", "conditions"))
        self.setDatabaseValues(Sqlite.getValue("fundamentals", "conditions", where=f"WHERE name = '{name}'"))
        self._initElements()

    def getElements(self):
        return self._elements

    def _initElements(self):
        self._elements = list()
        values = Sqlite.getValues(
                "fundamentals",
                "elements",
                where=f"WHERE condition_id = {self.getAttribute('condition_id')} AND active == 1"
        )
        for value in values:
            e = Element(value[0])
            self._elements.append(e)
