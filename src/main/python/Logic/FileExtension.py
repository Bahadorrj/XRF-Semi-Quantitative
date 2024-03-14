from json import dump, load
from numpy import array, uint32

from python.Types.FileClass import File
from python.Types.ConditionClass import Condition


class FileHandler:
    @staticmethod
    def writeFiles(files, filePath):
        # Serialize each LocalFile object to a dictionary
        filesDictList = []
        for file in files:
            countsSerializable = [countArray.tolist() for countArray in file.counts]
            idsSerializable = [condition.id for condition in file.conditions]
            localFileDict = {
                "name": file.name,
                "ids": idsSerializable,
                "counts": countsSerializable
            }
            filesDictList.append(localFileDict)

        # Write serialized data to a file
        with open(filePath, 'w') as f:
            dump(filesDictList, f, indent=4)

    @staticmethod
    def readFiles(filePath):
        # Read serialized data from a file
        with open(filePath, 'r') as f:
            filesAsDict = load(f)

        files = []
        for fileAsDict in filesAsDict:
            name = fileAsDict["name"]
            countsArray = [array(countArray, dtype=uint32) for countArray in fileAsDict['counts']]
            ids = fileAsDict['ids']

            file = File()
            file.name = name
            file.conditions = [Condition(id) for id in ids]
            file.counts = countsArray
            files.append(file)
        return files
