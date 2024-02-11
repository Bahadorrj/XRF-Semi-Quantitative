from pathlib import Path
from numpy import zeros, int32

from src.main.python.Types.ConditionClass import Condition


class File(object):
    def __init__(self, path: str):
        self._path = path
        self._name = Path(path).stem
        self._conditions = list()
        self._countsList = list()
        self.initFile()

    def getName(self) -> str:
        return self._name

    def getConditions(self) -> list:
        return self._conditions

    def getCondition(self, index) -> Condition:
        return self._conditions[index]

    def getCounts(self) -> list:
        return self._countsList

    def getCount(self, index):
        return self._countsList[index]

    def initFile(self) -> None:
        with open(self._path, 'r') as file:
            line = file.readline()  # read line
            counts = zeros(2048, dtype=int32)
            index = 0
            while line:
                if "Condition" in line:
                    c = Condition(line.strip())
                    self._conditions.append(c)
                try:
                    count = int(line.strip())
                    counts[index] = count
                    index += 1
                    if index == 2048:
                        self._countsList.append(counts)
                        counts = zeros(2048)
                        index = 0
                except ValueError:
                    pass
                line = file.readline()
