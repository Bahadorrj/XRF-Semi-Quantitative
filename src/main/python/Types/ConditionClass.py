from dataclasses import dataclass, field

from src.main.python.Logic.Sqlite import getColumnLabels, getValue, getValues
from src.main.python.Types.DataClass import Data
from src.main.python.Types.ElementClass import Element


@dataclass(order=True)
class Condition(Data):
    id: int

    def __post_init__(self):
        self.labels = getColumnLabels("fundamentals", "conditions")
        self.values = getValue("fundamentals", "conditions", where=f"condition_id = '{self.id}'")
