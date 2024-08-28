import os
import pytest

import numpy as np

from src.utils import datatypes
from src.utils.database import getDataframe

# testing AnalyseData
def test_fromHashableDict():
    hashableDict = {
        "conditionId": 1,
        "x": list(range(2048)),
        "y": [1 for _ in range(2048)],
    }
    analyseData = datatypes.AnalyseData(
        1,
        np.arange(0, 2048, 1),
        np.full(2048, 1)
    )
    assert analyseData == datatypes.AnalyseData.fromHashableDict(hashableDict)
