from pathlib import Path
from numpy import zeros, int32

from src.Types.ConditionClass import Condition


class File(object):
    def __init__(self, path: str):
        self.__path = path
        self.__name = Path(path).stem
        self.__conditions = list()
        self.__counts = list()
        self.init_counts()

    def get_name(self) -> str:
        return self.__name

    def get_conditions(self) -> list:
        return self.__conditions

    def get_condition(self, index) -> Condition:
        return self.__conditions[index]

    def get_counts(self) -> list:
        return self.__counts

    def get_path(self) -> str:
        return self.__path

    def init_counts(self) -> None:
        with open(self.get_path(), 'r') as file:
            line = file.readline()  # read line
            counts = zeros(2048, dtype=int32)
            count_index = 0
            while line:
                if "Condition" in line:
                    c = Condition(line.strip())
                    self.get_conditions().append(c)
                try:
                    count = int(line.strip())
                    counts[count_index] = count
                    count_index += 1
                    if count_index == 2048:
                        self.get_counts().append(counts)
                        counts = zeros(2048)
                        count_index = 0
                except ValueError:
                    pass
                line = file.readline()
