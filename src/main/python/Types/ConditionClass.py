from dataclasses import dataclass

from python.Logic.Sqlite import getColumnLabels, getValue, DatabaseConnection
from python.Types.DataClass import Data

import qrcResources


@dataclass(order=True)
class Condition(Data):
    id: int

    def __post_init__(self):
        database = DatabaseConnection.getInstance(":fundamentals.db")
        self.labels = getColumnLabels(database, "conditions")
        self.values = getValue(database, "conditions", where=f"condition_id = '{self.id}'")