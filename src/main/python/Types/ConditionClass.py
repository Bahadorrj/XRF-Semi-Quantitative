from dataclasses import dataclass

from src.main.python.dependencies import DATABASES
from src.main.python.Logic.Sqlite import getColumnLabels, getValue, DatabaseConnection
from src.main.python.Types.DataClass import Data


@dataclass(order=True)
class Condition(Data):
    id: int

    def __post_init__(self):
        database = DatabaseConnection.getInstance(DATABASES['fundamentals'])
        self.labels = getColumnLabels(database, "conditions")
        self.values = getValue(database, "conditions", where=f"condition_id = '{self.id}'")