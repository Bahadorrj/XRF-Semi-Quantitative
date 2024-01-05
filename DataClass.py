class Data:
    def __init__(self) -> None:
        self.__database_values = None
        self.__database_labels = None

    def get_database_values(self) -> list:
        return self.__database_values

    def set_database_values(self, database_values: list):
        self.__database_values = database_values

    def get_database_labels(self) -> list:
        return self.__database_labels

    def set_database_labels(self, labels: list):
        self.__database_labels = labels

    def get_attribute(self, attribute: str):
        index = self.get_database_labels().index(attribute)
        return self.get_database_values()[index]

    def set_attribute(self, attribute: str, value):
        index = self.get_database_labels().index(attribute)
        self.get_database_values()[index] = value

    def get_name(self):
        return self.get_attribute("name")