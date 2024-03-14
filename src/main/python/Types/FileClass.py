from dataclasses import dataclass, field, asdict
from pathlib import Path

from numpy import zeros, uint32

from python.Logic.Sqlite import DatabaseConnection, getValue
from python.Types.ConditionClass import Condition

import qrcResources


@dataclass(order=True)
class File:
    name: str = field(init=False)
    conditions: list = field(init=False, repr=True, default_factory=list)
    counts: list = field(init=False, repr=False, default_factory=list)

    def asDict(self):
        return asdict(self)


@dataclass(order=True)
class LocalFile(File):
    path: str

    def __post_init__(self):
        self.name = Path(self.path).stem
        with open(self.path, 'r') as file:
            line = file.readline()  # read line
            counts = zeros(2048, dtype=uint32)
            index = 0
            while line:
                if "Condition" in line:
                    database = DatabaseConnection.getInstance(":fundamentals.db")
                    conditionID = getValue(database, "conditions", where=f"name = '{line.strip()}'")[0]
                    c = Condition(conditionID)
                    self.conditions.append(c)
                try:
                    count = int(line.strip())
                    counts[index] = count
                    index += 1
                    if index == 2048:
                        self.counts.append(counts)
                        counts = zeros(2048, dtype=uint32)
                        index = 0
                except ValueError:
                    pass
                line = file.readline()
