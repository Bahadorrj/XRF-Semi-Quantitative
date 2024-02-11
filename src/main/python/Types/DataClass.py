class Data:
    def __init__(self) -> None:
        self._databaseValues = None
        self._databaseLabels = None

    def getDatabaseValues(self) -> list:
        return self._databaseValues

    def setDatabaseValues(self, database_values: list):
        self._databaseValues = database_values

    def getDatabaseLabels(self) -> list:
        return self._databaseLabels

    def setDatabaseLabels(self, labels: list):
        self._databaseLabels = labels

    def getAttribute(self, attribute: str):
        index = self.getDatabaseLabels().index(attribute)
        return self.getDatabaseValues()[index]

    def setAttribute(self, attribute: str, value):
        index = self.getDatabaseLabels().index(attribute)
        self.getDatabaseValues()[index] = value

    def getName(self):
        return self.getAttribute("name")
