from pathlib import Path

from src.Logic.TextReader import set_counts
from src.Types.ConditionClass import Condition


class File:
    def __init__(self, path: str):
        self.__path = path
        self.__name = Path(path).stem
        self.__conditions = list()
        set_counts(self)

    def get_name(self) -> str:
        return self.__name

    def get_conditions(self) -> list:
        return self.__conditions

    def get_condition(self, index) -> Condition:
        return self.__conditions[index]

    def get_counts(self) -> list:
        l = list()
        for condition in self.get_conditions():
            l.append(condition.get_counts())
        return l

    def get_path(self) -> str:
        return self.__path
