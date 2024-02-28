from dataclasses import dataclass, field
from pathlib import Path

from numpy import zeros, uint32, ndarray

from src.main.python.Logic import Sqlite
from src.main.python.Types.ConditionClass import Condition


@dataclass(order=True)
class LocalFile:
    path: str
    name: str = field(init=False)
    conditions: list[Condition] = field(init=False, repr=False, default_factory=list)
    counts: list[ndarray] = field(init=False, repr=False, default_factory=list)

    def __post_init__(self):
        self.name = Path(self.path).stem
        with open(self.path, 'r') as file:
            line = file.readline()  # read line
            counts = zeros(2048, dtype=uint32)
            index = 0
            while line:
                if "Condition" in line:
                    conditionID = Sqlite.getValue("fundamentals", "conditions", where=f"name = '{line.strip()}'")[0]
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

@dataclass(order=True)
class PacketFile:
    name: str
    conditions: list[Condition] = field(init=False, repr=False, default_factory=list)
    counts: list[ndarray] = field(init=False, repr=False, default_factory=list)
