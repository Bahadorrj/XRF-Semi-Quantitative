from dataclasses import dataclass, field
from pathlib import Path

from numpy import zeros, uint32, ndarray

from python.Logic.Sqlite import DatabaseConnection, getValue
from python.Types.ConditionClass import Condition


@dataclass(order=True)
class File:
    name: str = field(init=False)
    conditions: list = field(init=False, repr=True, default_factory=list)
    counts: list = field(init=False, repr=False, default_factory=list)


@dataclass(order=True)
class TextFile(File):
    path: str

    def __post_init__(self):
        self.name = Path(self.path).stem
        with open(self.path, 'r') as f:
            line = f.readline()  # read line
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
                line = f.readline()


@dataclass(order=True)
class PacketFile(File):
    type: str = field(default="ANALYSE", init=False)

    def __init__(self, data: str):
        super().__init__()
        seperated = data.split('\\')
        pointer = 0
        self.type = seperated[pointer]
        pointer += 1
        self.name = seperated[pointer]
        pointer += 1
        while seperated[pointer] != "-stp":
            conditionName = seperated[pointer]
            pointer += 1
            database = DatabaseConnection.getInstance(":fundamentals.db")
            conditionID = getValue(database, "conditions", where=f"name = '{conditionName}'")[0]
            condition = Condition(conditionID)
            counts = ndarray(2048, dtype=uint32)
            for i in range(2048):
                counts[i] = seperated[pointer]
                pointer += 1
            self.conditions.append(condition)
            self.counts.append(counts)


@dataclass
class ProjectFile:
    name: str
    files: list[File] = field(default_factory=list, init=False)
