import random
from random import shuffle

from python.utils.database import getDatabase
from python.utils.paths import resource_path

if __name__ == "__main__":
    elementOneIds = [i for i in range(1, 400)]
    elementTwoIds = [i for i in range(1, 400)]
    shuffle(elementOneIds)
    shuffle(elementTwoIds)
    db = getDatabase(resource_path('../views/fundamentals.db'))
    for i, j in zip(elementOneIds, elementTwoIds):
        query = f"""
        INSERT INTO Interferences (element1_id, element2_id, coefficient) 
        VALUES ({i}, {j}, {random.random()});
        """
        db.executeQuery(query)
    db.closeConnection()
