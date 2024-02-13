from dataclasses import dataclass, field

from src.main.python.Logic.Sqlite import getColumnLabels, getValue, getValues
from src.main.python.Types.DataClass import Data
from src.main.python.Types.ElementClass import Element


@dataclass(order=True)
class Condition(Data):
    id: int
    elements: list[Element] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.labels = getColumnLabels("fundamentals", "conditions")
        self.values = getValue("fundamentals", "conditions", where=f"WHERE condition_id = '{self.id}'")
        self._initElements()

    def _initElements(self):
        values = getValues(
                "fundamentals",
                "elements",
                where=f"WHERE condition_id = {self.id} AND active == 1"
        )
        for value in values:
            e = Element(value[0])
            self.elements.append(e)
